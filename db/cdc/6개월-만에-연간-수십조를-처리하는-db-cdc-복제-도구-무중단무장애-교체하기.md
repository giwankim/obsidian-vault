---
title: "6개월 만에 연간 수십조를 처리하는 DB CDC 복제 도구 무중단/무장애 교체하기"
source: "https://d2.naver.com/helloworld/6388660"
author:
published:
created: 2026-07-07
description:
tags:
  - "clippings"
---

> [!summary]
> Naver Pay's order team replaced mig-data, their 7-year-old DB CDC replication tool, with ergate — built on Apache Flink 2.0 (session mode on Kubernetes) for replication/verification and Spring for recovery — targeting 10x current QPS and sub-1-second replication. Performance work brought per-record latency from 200ms to 40ms via object reuse, data-skew fixes, a TCP-congestion-control-style DynamicBatchSize extension of JdbcSink, and async verification, while column caching removed DDL ordering constraints that previously caused replication pauses. The team cut over with zero downtime using dual replication (mig-data and ergate running blind to each other, with a sync_seq/rpc_time column preventing stale-data regression), and shares troubleshooting of Flink classloader Metaspace OOM and Kubernetes HA split-brain from misconfigured lease durations.

네이버페이 차세대 아키텍처 개편을 위한 Plasma 프로젝트가 7년의 기간 끝에 2025년 7월부로 공식 종료를 선언했습니다. 이 글에서는 Plasma 프로젝트의 최종장인 DB CDC 복제 도구 ergate 프로젝트의 개발 및 전환 경험을 공유하고자 합니다.

## ergate 프로젝트 소개

ergate 프로젝트는 네이버페이 주문에서 DB 간 복제를 수행하는 프로세스(mig-data)를 전환하는 프로젝트로, 전환 목표는 다음과 같습니다.

- 사용량 증가에 따라 **확장 가능한 구조**
- 주문 백엔드 개발자의 **유지 보수 및 추가 개발이 쉬운 구조와 기술 스택**

이름은 일개미처럼 데이터를 계속 실어 나르는 도구라는 의미에서 ergate라고 지었습니다.

![](https://d2.naver.com/content/images/2025/11/1.png)

## 용어 설명

본격적으로 들어가기 전에 몇 가지 용어를 먼저 소개하겠습니다.

- mig-data: Plasma 프로젝트에서 DB 간 복제를 수행하던 도구. 다양한 기능이 있지만 이 글에서는 'Kafka 이벤트 기반 비동기 복제 프로세스'를 의미합니다.
- forceSync: API 호출 기반으로 실시간 동기 복제를 수행하는 spring-web + mig-data 기반 컴포넌트. mig-data의 지연 및 복제 중단을 대비한 보완 장치입니다.
- nBase-T: 네이버 사내 분산 RDB 플랫폼(실저장소로 mySQL 이용)
- nbase-cdc: nBase-T 환경에서 mySQL binlog를 읽어들여 Kafka 레코드로 발행하는 도구

## 작업 동기

기존 DB 간 복제를 수행하던 mig-data는 DB 코어 개발 경험이 있는 개발자가 순수 Java로 소스 코드를 작성했습니다. Plasma 프로젝트를 마무리하기 위해서는 복제 도구까지 주문 개발로 내재화해야 했는데, 기존 도구를 그대로 인수인계하기에는 백엔드 개발자 입장에서 유지 보수와 추가 개발이 어려웠습니다.

### 개선 필요 사항

mig-data는 7년간 Plasma 프로젝트의 복제를 담당했기에 많은 기능과 그에 따른 제약 사항이 있었는데, 그중 대부분은 Source와 Target 간의 양방향 복제와 관련이 있었습니다. ergate 프로젝트를 진행하는 시점에서는 단방향 복제만 존재했기 때문에 양방향 복제 관련 코드와 다음과 같은 제약 사항을 제거할 필요가 있었습니다.

- 단일 레코드에 대한 복제 실패가 **전체 복제 지연** 으로 이어짐 - 양방향 복제 시 데이터 무결성을 확인하기 위해 의도된 동작이었습니다.
- Source, Target의 **칼럼 추가 순서가 중요** - Target → Source 순서로 칼럼을 추가해야 했습니다. Target이 모르는 칼럼 데이터가 인입된 경우 처리가 불가능해, 잘못된 순서로 수행 시 **일시 복제 중단** 이 발생했습니다.
- mig-data 관련 장애 시 **복구를 수행하는 방법과 인원이 제한적**

### 복제 현황

네이버페이 주문에서는 Source DB로 전부 nBase-T를 사용하고 있었고, Target DB는 nBase-T, Oracle 두 종류가 있습니다. 목록은 다음과 같습니다.

| Source | Target | 용도 |
| --- | --- | --- |
| 주문 | 판매자 | 판매자 단위 조회 기능 및 성능 |
| 주문 | Oracle | 이전 Oracle 조회 앱 대응 |
| 주문 | 정산 |  |
| 주문 | 배송 |  |
| 주문 | 호스팅사 | 호스팅사 단위 뷰 |
| 배송 | 판매자 | 판매자 Target과 동일 |

판매자 DB는 구매자 기준으로 샤딩된 주문 DB 데이터를 판매자 번호 기준으로 샤딩해 만든 DB입니다. Oracle DB는 Plasma 프로젝트 진행 전부터 사용하고 있던 DB로, 아직 해당 DB를 보는 기능과 운영 편의를 위해 유지하고 있습니다.

ergate 프로젝트는 위 복제 프로세스를 전부 전환하는 것을 목표로 시작했습니다.

## 목표

ergate 프로젝트의 목표는 다음과 같았습니다.

- 백엔드 개발자의 **유지 보수 및 추가 개발이 쉬운** 형태로 재개발 - 주문 개발을 내재화해야 했는데 프로젝트 참여 인원 3명 모두 주로 Spring Framework 기반의 개발 경험 보유
- 기존 복제 도구 대비 **기능 개선**
	- **스키마 변경 관련 개선** - 일시 복제 중단 해소, 스키마 변경 순서가 무관하도록 변경
		- 다양한 데이터 **복구 편의 기능** 제공
		- 양방향 복제 등 불필요한 기능 제외
- 현재 QPS의 10배 이상 처리할 수 있도록 **성능 개선**
- CDC 이벤트 발행 후 1초 내 복제 보장

## 기술 스택

ergate 프로젝트에서는 프레임워크로 Apache Flink와 Spring Framework를 선택하고, 사용 언어로는 Flink 레벨에서는 주로 Java 17, Spring 레벨에서는 Kotlin 1.9를 사용했습니다.

![](https://d2.naver.com/content/images/2025/11/2.png)

### Apache Flink 선택 이유

Flink는 저지연, 대용량, 고가용성 처리를 지원하는 것으로 알려져 있습니다. 그래서 프레임워크를 잘 활용하면 성능과 관련된 부분은 직접 구현하지 않고 **복제/검증 구현에 집중** 할 수 있을 것이라고 기대했습니다.

Flink 활용 사례가 늘어나고 있으며 활성화된 프로젝트이기 때문에 추후 버전업을 통한 기능 개선도 꾀할 수 있었습니다.

또한, nbase-cdc는 binlog를 Kafka 레코드로 발행하고 복제 도구가 해당 레코드를 읽어들여 처리해야 하는데, **Flink는 Kafka 연동이 용이** 했습니다.

알리바바에서 Flink 기여 및 사용 사례가 있는 것도 하나의 이유였습니다. 알리바바도 커머스 도메인이며 거래량이 많은 편이기 때문에 네이버페이도 같은 커머스 도메인으로 도입하는 것에 큰 거부감이 없었습니다.

추가로, 여러 게시글에서 사내외 적용 사례가 늘어나는 것을 확인했습니다.

### Apache Flink 구성

- 버전: [2.0.0](https://nightlies.apache.org/flink/flink-docs-release-2.0) (복제 전환 시점의 LTS 버전)
- Kubernetes에서 세션 모드로 클러스터 구성
- 고가용성(high availability, HA): Kubernetes, Amazon S3(Flink가 HA 구성 옵션 제공)
- 기타 런타임 라이브러리 추가 구성
	- 사내 플랫폼 연동
		- 리소스 풀 관리를 위한 fat JAR 추가

#### 세션 모드 선택 이유

Flink 클러스터 구성에는 2가지 모드가 있습니다(참고: [공식 문서](https://nightlies.apache.org/flink/flink-docs-release-2.0/docs/deployment/overview/#deployment-modes)). 각 모드를 간단하게 설명하면 다음과 같습니다.

- 애플리케이션 모드: 전용 클러스터에서 하나의 job만 구동. job과 클러스터의 생명 주기는 동일.
- 세션 모드: 공용 클러스터에 job jar를 제출(submit)하여 구동. job의 시작/종료와 클러스터의 생명 주기는 별개.

저희는 모니터링, 배포 측면에서 검토해 세션 모드를 선택했습니다.

모니터링 측면에서는 상위 6가지 복제 job의 구동 상태를 볼 수 있는 하나의 엔드포인트가 필요한데, 세션 모드로 구동 시 하나의 job manager가 제공하는 웹 UI로 모든 job의 상태를 한 번에 확인할 수 있습니다.

그리고 배포 측면에서는 구동 시 개별 복제 job에 대응되는 검증 job까지 구동하기 때문에 총 12개의 job을 배포해야 하는데, 애플리케이션 모드는 job마다 별도의 클러스터가 필요해 전체 배포 시 배포 시간이 더 소요될 수 있습니다. 또한 프로젝트 초기 구축 시에는 배포마다 컨슈머 group.id가 별도로 부여되면 배포 타이밍에 downtime이 발생해 큰 이슈로 이어질 수도 있습니다.

세션 모드 선택으로 인한 트레이드오프도 존재했습니다. job manager를 재배포하거나 장애가 발생한 상황이라면 모든 job이 중단되었는데, 이 내용은 뒤의 트러블슈팅 과정에서 설명하겠습니다.

### Spring Framework 도입 필요성

세션 모드에서 Flink job을 구현해 보았을 때, 여기에 모든 기능을 구현하기에는 Spring 개발만 진행했던 경험상 불편한 점이 있었습니다.(이 부분도 트러블슈팅에서 자세히 설명하겠습니다.) 복제, 검증 기능을 먼저 개발해 보면서 **Flink에는 속도가 중요한 로직만 두자** 는 결론을 도출했고, 후술할 다양하고 복잡한 '복구' 로직은 별도 Spring 모듈로 격리하기로 결정했습니다.

## 주요 기능

ergate의 주요 기능은 복제, 검증, 복구의 3가지입니다.

### 복제

Source DB에서 변경이 발생하여 binlog로 기록되면, nbase-cdc가 해당 변경을 Kafka 레코드로 발행합니다. ergate의 Flink job인 jdbc-sink는 해당 **레코드를 읽어들여 Target DB로 반영** 합니다.

![](https://d2.naver.com/content/images/2025/11/3.png)

발행된 Kafka 레코드의 데이터의 예는 다음과 같습니다.

**Kafka 레코드의 예**

```json
{
    ...
    "payloads": [
        {
            "op": "update",
            "table": "table1",
            "old": {
                "primary_key": "pkvalue",
                "col1": "col1value",
                "col2": "col2value"
            },
            "new": {
                "primary_key": "pkvalue",
                "col1": "newcol1value",
                "col2": "newcol2value",
                "col3": "col3value",
            },
        },
        {
            "op": "insert",
            "table": "table2",
            "old": null,
            "new": {
                "primary_key": "pkvalue",
                "col1": "col1value",
                "col2": "col2value",
                "col3": "col3value",
            },
        },
    ]
}
```

#### 전용 칼럼 추가

ergate가 Target으로 데이터를 복제하는 시점에 전용 칼럼 2개를 추가로 반영하도록 구성했습니다. 이 칼럼들은 주로 모니터링에 사용됩니다.

| 칼럼명 | 용도 | 상세 |
| --- | --- | --- |
| ergate\_yn | 복제 주체 구분 | 0(mig-data)   1(ergate)   2(forceSync) |
| rpc\_time | 원 레코드가 Source에서 커밋된 시간 |  |

### 검증

**원 데이터와 복제한 데이터의 일치 여부를 확인** 하는 verifier라는 Flink job을 구현했습니다. verifier는 복제에서 사용하는 토픽을 바라보고 있으며 이 토픽을 **지연 컨슈밍** (2분)해 검증을 수행합니다. 검증에 실패하면 검증 실패 DLQ로 다시 발행하며, 별도의 Spring 컨슈머가 상태 DB에 기록합니다.

![](https://d2.naver.com/content/images/2025/11/4.png)

#### 지연 컨슈밍으로 인한 추가 동작

검증 시 Kafka 레코드의 데이터와 검증 시점 Target row를 비교하기 때문에, 지연 컨슈밍 시간 사이에 해당 row에 변경이 생기면 무조건 검증에 실패합니다. 따라서 레코드와의 검증이 1차로 실패하면, 검증 시점의 Source row를 추가로 조회해 해당 값과 Target row를 다시 비교하는 동작을 추가했습니다.

### 복구

검증 실패 건에 대해 복구 시점의 데이터를 재조회해 다시 검증하고, 실제로 불일치가 발생하면 Target DB에 업데이트합니다. 복구는 자동 및 수동으로 수행할 수 있습니다.

![](https://d2.naver.com/content/images/2025/11/5.png)

#### 기본 복구 흐름

1. 상태 DB에 검증 실패 row를 INSERT합니다.
2. 공통 복구 로직을 수행합니다.
3. 복구 완료된 건들을 다시 검증합니다.
	- 복구 완료 30분이 지난 시점에 실제 일치하는지 다시 확인합니다.
4. 복구 완료된 건들에 대해 상태 DB에 row DELETE를 수행합니다.

#### 순단 자동 복구

일시적인 오류로 복제에 실패하는 상황을 대비합니다. 검증 실패가 발견되면 5분 뒤 자동으로 복구를 수행합니다.

동일 row에 대해 연속 UPDATE가 발생하면 검증에 실패할 수 있습니다. 이 경우 5분이 지난 후 데이터를 재조회해 검증하므로, 실제 복구 수행은 없이 자연 해소를 기대할 수 없습니다.

#### 장애 자동 복구

순단이 지속되어 장애로 이어지는 상황을 대비합니다. 순단 복구를 먼저 시도했지만 복구되지 않은 row에 대해 배치로 재시도합니다.

#### 수동 복구

별도의 어드민 페이지를 구성해 실패한 레코드를 조회하고 API를 통해 복구를 수행합니다. 장애 자동 복구의 경우 배치이므로, 별도 범위를 지정해 수동 실행을 수행할 수도 있습니다.

## 개선 사항

ergate에서는 기존 mig-data 대비 다음과 같은 사항을 개선했습니다.

### 기능 개선

#### DDL 실행 순서 의존성 제거

앞에서 설명한 개선 필요 사항 중 기존 mig-data에서는 Source, Target의 칼럼 추가 순서가 중요하다는 제약 사항이 있었습니다. Source에 A 칼럼이 추가된 경우 Target으로 복제를 수행하는 시점에는 A 칼럼을 모르기 때문이었습니다. 그래서 이전에는 DDL 작업이 있는 경우 DBA가 칼럼 추가 순서에 주의해서 작업을 진행해야 했습니다.

DDL 작업은 보통 운영 영향도를 낮추기 위해 새벽에 수행합니다. 그리고 관련 데이터의 인입은 별도 소스 코드 배포 이후 진행되는 상황이었습니다. 결국, DDL 수행과 실제 데이터 인입 시점은 다르다는 결론을 낼 수 있었습니다.

그래서 ergate에서는 **칼럼을 캐싱해두는 전략** 을 사용했습니다. spring-jdbc의 SqlParameterSource와 캐싱된 스키마/쿼리를 이용해 PreparedStatement를 재사용하며, 복제 시점에 캐싱되어 있는 칼럼 데이터만 사용합니다(자세한 내용은 뒤에서 설명).

칼럼 추가 순서에 따른 동작은 다음과 같습니다.

- Source에 먼저 칼럼이 추가된 경우: 캐싱된 Target statement는 해당 칼럼을 알지 못하므로 무시하고, Target statement 갱신 후 데이터가 반영
- Target에 먼저 칼럼이 추가된 경우: Source에서 넘어온 데이터가 없으므로 null로 반영

다만 운영 시 하나의 예외 사항이 존재하는데, 바로 '칼럼 drop' 시점입니다. 앞에서 설명한 대로 statement를 캐싱해두고 재사용하는데, 칼럼이 drop되는 시점에 기존 statement를 사용하면 **쿼리 수행 시점에 알 수 없는 칼럼** 이기 때문에 오류가 발생합니다. 이때 개발자 레벨에서 다음과 같은 대응이 필요합니다.

- Flink job으로 주입되는 별도 복제 설정 'ignore-columns'를 미리 추가하고 반영해 둠
- statement 생성 시점에 해당 칼럼을 미리 제외 ![](https://d2.naver.com/content/images/2025/11/6-1.png)

#### 스키마 정보의 주기적인 조회 및 갱신

JDBC API에서는 스키마 정보를 제공하는 [DatabaseMetadata](https://docs.oracle.com/javase/8/docs/api/java/sql/DatabaseMetaData.html) 라는 클래스가 존재합니다. 해당 클래스로 런타임 호출 시점의 테이블 목록, 스키마(PK, 칼럼 등)을 가져올 수 있습니다. mig-data에서도 이 API를 이용하여 자체 스키마를 구성했고, ergate에서도 동일하게 이용했습니다.

**java.sql.Connection#getMetadata()**

```java
/**
  * Retrieves a {@code DatabaseMetaData} object that contains
  * metadata about the database to which this
  * {@code Connection} object represents a connection.
  * The metadata includes information about the database's
  * tables, its supported SQL grammar, its stored
  * procedures, the capabilities of this connection, and so on.
  *
  * @return a {@code DatabaseMetaData} object for this
  *         {@code Connection} object
  * @throws  SQLException if a database access error occurs
  * or this method is called on a closed connection
  */
DatabaseMetaData getMetaData() throws SQLException;
```

그렇지만 기존 서비스에서 사용하던 Oracle DB에서 예외가 있었습니다. 바로 스키마 상에 PK를 정의해 두지 않고 논리적으로 사용하는 PK가 따로 존재하는 상황이었습니다. 해당 예외를 위해 다음과 같이 복제 설정에 별도로 PK 목록을 기입해두어 사용했습니다.

![](https://d2.naver.com/content/images/2025/11/7-1.png)

이렇게 만든 스키마 정보를 Flink(복제/검증), Spring(복구) 모두에서 가지고 있어야 했으므로, 저희는 다음과 같이 구성했습니다.

- Spring: 실제 DB 조회 및 자체 정의 객체로 변환
- Flink: Spring으로 HTTP API 호출을 통해 조회

Flink의 경우 job의 병렬도(parallelism)가 높고 커넥션 공유가 어려워, DB보다 상대적으로 저렴한 HTTP를 이용했습니다. 또한 개별 단위마다 캐시를 적용해 커넥션 리소스를 절약하고 내결함성(fault tolerance)을 확보했습니다.

그리고 Flink job에서 런타임에 스키마 변경을 감지하면, 기존에 사용하던 PreparedStatement에 남아있는 데이터는 flush하고 새로운 메타데이터에 대한 PreparedStatement로 변경하는 동작을 구현해 두었습니다.

#### 일시 복제 중단 해소

ergate에서는 복제 단계에서 실패가 발생하더라도 해당 건은 무시하고 후속 데이터를 계속 복제하며, 실패 건은 **검증 단계에서 검출되어 복구** 하는 것을 의도했습니다. 물론 잘못 검출되는 경우도 발생할 수 있으므로 복구 단계에서는 앞서 기술한 대로 재검증을 수행합니다.

Oracle DB의 경우 read only (slave) DB를 사용해 검증하는데, 마스터와 슬레이브 사이의 차이로 인해 실패 건으로 잘못 검출될 수 있습니다. 따라서 복구 시에 검증할 데이터를 마스터에서 재조회하여 잘못 검출된 경우 정상 처리합니다.

판매자 DB의 경우 순단으로 인해 샤딩 키 조회에 실패해 복제에 실패할 수 있습니다. 이 경우에는 샤딩 키를 재조회해 복구합니다.

#### 다양한 데이터 복구 편의 기능 제공

앞에서 설명한 다수의 자동/수동 복구 흐름을 구성해, 이슈 발생 시에도 빠르게 복구할 수 있도록 접근성을 개선했습니다.

#### 복제 설정 개선

기존 mig-data 대비 개발 편의성을 위해 복제 설정도 개선했습니다. 먼저, mig-data에서는 2가지 주요 기능이 있었고 해당 기능은 ergate에서도 필요한 상황이었습니다.

- findckey: Target DB의 샤딩 키를 찾는 기능(예: 주문 DB에서 상품주문 테이블을 조회해 판매자 번호(샤딩 키) 목록을 가져와야 하는 경우)
- columnreplace: Target DB에만 존재하는 칼럼에 대한 데이터를 타 DB에서 조회 및 구성하여 채우는 기능

findckey를 기준으로 예시를 들면, 먼저 기존에는 조회하고자 하는 데이터에 대한 쿼리를 설정 파일에 직접 기입해 두었습니다. 그리고 이렇게 위와 기입된 쿼리는 동일 쿼리의 이전 실행 여부와 관계 없이 전부 실행이 되었습니다.

![](https://d2.naver.com/content/images/2025/11/8-1.png)

ergate에서는 다음과 같이 설정 파일을 간소화했습니다. 설정에는 enum 값만 선언하고, 쿼리와 로직을 Java 클래스로 옮겼습니다. 또한, 하나의 처리 단위(tx)에서 같은 PK에 대해 값을 구해 두었다면 추가 I/O가 일어나지 않도록 캐싱하는 로직도 추가했습니다.

![](https://d2.naver.com/content/images/2025/11/9-1.png)

### 성능 개선

#### Flink JdbcSink 확장

Flink의 기본 구현체인 [JdbcSink](https://nightlies.apache.org/flink/flink-docs-release-2.0/docs/connectors/datastream/jdbc/) 는 고정된 batchSize와 batchIntervalMs를 사용하고 있습니다.

- batchSize: 설정값 이상으로 데이터 인입 시 I/O
- batchIntervalMs: 설정한 값 주기마다 I/O

이 경우 '데이터량 증가 → executeBatch I/O blocking 증가 → 성능 저하'라는 흐름을 피할 수 없었습니다.

![](https://d2.naver.com/content/images/2025/11/10.png)

저희는 기본 구현을 확장해, **데이터 유동량에 따라 동적으로 값을 조정하는 DynamicBatchSize 개념** 을 추가로 구현했습니다.

![](https://d2.naver.com/content/images/2025/11/11.png)

데이터 유동량 증가 시 동적으로 설정값을 변경해 blocking 호출 수를 제어합니다. 이때, TCP 혼잡 제어 로직과 유사하게 이전 트래픽을 기반으로 다음과 같이 값을 제어합니다.

- 50~100ms 사이에 현재 할당량을 채웠으면 미조정
- 할당량을 채우는 데 100ms가 지났다면 할당량 감량
- 할당량을 채우는 데 50ms가 지나지 않았다면 할당량 증량

#### 비동기 검증

초기에는 검증을 동기로 수행해 병렬도를 높게 설정해야 했습니다. 그러나 검증 순서는 크게 중요하지 않다고 판단해, [AsyncDataStream](https://nightlies.apache.org/flink/flink-docs-release-2.0/docs/dev/datastream/operators/asyncio/) 을 이용해 병렬도를 낮게 설정해도 충분한 성능을 내도록 했습니다.

#### 1초 내 복제 보장

Flink JdbcSink에서 제공되는 batchIntervalMs 설정으로, 추가 구현 없이 목표를 달성할 수 있었습니다.

## 아키텍처 성능 검증

네이버페이 주문 서비스는 DB 간 복제 지연에 굉장히 민감한 시스템입니다. 그래서 ergate로 본격적으로 전환하기 전, **우리가 설계한 아키텍처 및 데이터 흐름이 문제없이 의도대로 동작하는지** 검증이 필요했습니다.

![](https://d2.naver.com/content/images/2025/11/12.png)

먼저 성능 부분부터 살펴보았습니다. 기존 Write(CUD) QPS 대비 10배 이상 처리하는 것이 목표였습니다.

### 테스트 환경 구축

기존 Source(주문) / Target(판매자) DB와 동일한 스키마의 논리 DB를 생성하고, 전용 nbase-cdc 도 신규로 구축했습니다. 추가로 [fixture-monkey](https://github.com/naver/fixture-monkey) 를 이용해 자체 테스트 데이터 생성 도구 banana를 만들어서 목표 QPS를 재현했습니다.

![](https://d2.naver.com/content/images/2025/11/13.png)

### 최초 테스트 결과

하나의 레코드를 처리하는 데 Source 커밋부터 Target 커밋까지의 **시간이 200ms나 소요** 되는 것을 확인했습니다. 병렬도를 높여 대응할 수도 있었지만 저희는 ' **DB 커넥션은 비싼 자원이다** ', ' **Flink task slot 또한 한정적이다** '라는 것을 전제로 개선 지점을 찾아보았습니다.

### 개선 지점 분석 및 해결 과정

원인을 분석하기 위해 개발 환경에서 flame graph 옵션을 켜서 전체 흐름을 확인했습니다.(다음은 실제 이슈 시점의 화면이 아니라 flame graph 옵션을 켠 경우 웹 UI에서 볼 수 있는 화면의 예입니다.)

![](https://d2.naver.com/content/images/2025/11/14.png)

발견 및 대응 시간 순서에 따라 살펴보겠습니다.

#### 1\. task 간 객체 직렬화 성능 이슈

A task에서 B task로 객체 이동 시 직렬화(serialize)/역직렬화(deserialize)에 소요되는 시간을 개선할 필요가 있었습니다.

- ✅ 해결: object reuse 옵션을 활성화해 같은 task manager 내에서 객체 이동 시에는 직렬화를 수행하지 않음
- 결과: 200ms → 130ms

setter 사용 시 동시성 이슈가 생길 수 있지만 저희 코드에는 해당 사례가 없었습니다.

#### 2\. 데이터 스큐(특정 task slot으로 몰림) 이슈

Kafka 레코드 키(구매자 번호)를 그대로 Flink 키로 사용해, Kafka 파티션 스큐가 Flink slot까지 이어지고 처리가 몰리는 문제가 있었습니다.

- ✅ 해결: 구매자 번호 + 테이블명으로 Flink 키를 구성해 스큐 분산
- 결과: 130ms → 70ms

![](https://d2.naver.com/content/images/2025/11/15.png)

#### 3\. DB I/O로 인한 성능 제한

I/O의 성능 자체는 제어할 수 없으므로 I/O의 횟수를 줄여야 했습니다.

- ✅ 해결: [Flink JdbcSink 확장](#flink-jdbcsink-확장) 으로 I/O 횟수 감소
- 결과: 70ms → 40ms

#### 4\. Flink 네트워크 버퍼 설정 해제

네트워크 버퍼를 사용하지 않으면 처리량이 줄어드는 대신 지연 시간(latency)을 줄일 수 있습니다.

- ✅ 해결: 네트워크 버퍼를 사용하지 않도록 설정(execution.buffer-timeout을 0으로 설정)
- 결과: I/O 지연 시간 소폭 감소

#### 5\. 검증 성능 개선

검증 시 복제와 동일하게 I/O가 발생하고 개별 객체의 비교 로직이 존재하므로 검증 성능을 개선할 필요가 있었습니다. 검증 순서는 중요하지 않으므로 검증을 동기로 수행할 필요가 없다고 판단했습니다.

- ✅ 해결: 검증 동작을 비동기로 변경

## 아키텍처 내결함성 검증

성능이 충분히 개선된 것을 확인한 후, 각 지점에서 장애가 발생했을 때 우리가 설계한 자동 복구가 정상적으로 동작하는지, 그리고 전체 동작에 이상이 없는지 확인하는 작업을 진행했습니다.

ergate는 크게 애플리케이션과 DB로 장애 지점을 나눌 수 있습니다.

### 애플리케이션 테스트

저희가 구현한 Flink, Spring 레벨의 각 지점마다 장애를 유발하고, 예상한 기대 동작과 실제 동작을 확인했습니다.

#### 1\. Flink job manager

- 장애: leader pod이 내려감
- 기대 동작
	1. follower가 새로운 leader로 승격
		2. 이전 leader에서 수행하고 있던 job을 전부 신규 leader가 재시작해 RUNNING 상태로 동작
- ✅ 정상 동작 확인: 체크포인트 유실 등의 이슈가 있었으나 스토리지 타입으로 S3 적용 후 해결됨

#### 2\. Flink task manager

- 장애: task를 수행하고 있는 pod이 내려감
- 기대 동작: 중지된 task가 다른 pod에 다시 배치되어 RUNNING 상태로 동작
- ✅ 정상 동작 확인

#### 3\. Spring 모듈 장애

- 장애: API를 제공해주는 Spring 모듈이 내려감
- 기대 동작
	- Flink job에서 Spring 모듈로 테이블 메타데이터 조회 호출 중에 Spring 모듈이 내려가더라도 Flink에서는 캐싱해 둔 메타데이터 정보를 사용
		- Spring은 복구를 담당하므로 메인 복제/검증 로직에는 영향이 없음
- ✅ 정상 동작 확인

위와 같이 전체 정상 동작을 확인했고 job manager HA 동작 관련 보완이 필요한 부분도 확인하여 대응했습니다.

### DB 모의 장애 테스트

다음으로 Source, Target DB가 내려간 경우를 확인해 보고자 했습니다. nBase-T 특성상 신규 구축이 쉽지 않아서 기존 개발 환경에서 사용하는 장비에 논리 DB를 추가한 형태였기 때문에, 다양한 부서에서 활용 중인 개발 물리 장비를 이 테스트를 위해 물리적으로 내릴 수는 없는 상황이었습니다.

그래서 DB Connection 코드를 확장하고 사내의 feature toggle([unleash](https://github.com/Unleash/unleash) 기반) 플랫폼을 활용해 **모의 장애 테스트를 수행** 했습니다. 다음은 저희가 추가한 코드의 일부입니다.

```java
public class BoomableNbaseConnection extends NbaseDynamicConnection {
 @Override
 public PreparedStatement prepareStatement(String sql, int autoGeneratedKeys) throws SQLException {
  mayBoom();
  return super.prepareStatement(sql, autoGeneratedKeys);
 }

 ...

 private void mayBoom() throws SQLException {
  if ((source && !FEATURE_TOGGLE.isEnabled(SOURCE_BOOM))
   || (!source && !FEATURE_TOGGLE.isEnabled(TARGET_BOOM))) {
   return;
  }
  try {
   Thread.sleep(3000);
  } catch (InterruptedException e) {
   Thread.currentThread().interrupt();
  }
  throw new SQLException("못 지나간다!");
 }
}
```

#### 1\. Source DB 장애

- 기대 동작
	- 샤딩 키 조회 실패 시: 복제 실패 → 전체 검증 실패 → ergate mySQL에 실패 상태 저장
		- Source 재조회 검증 실패 시: ergate mySQL에 실패 상태 저장
		- 장애 해소 시점: 데이터 복구 → 재검증 시 전체 일치
- ✅ 정상 동작 확인

#### 2\. Target DB 장애

- 기대 동작
	- 복제 실패 시: 전체 검증 실패 → ergate mySQL에 실패 상태 저장
		- 장애 해소 시점: 데이터 복구 → 재검증 시 전체 일치

그런데 검증 시점에 검증할 Target row를 가져오기 위해 Target DB에 커넥션을 맺으려고 시도할 때 오류가 발생했고, 신규 커넥션을 맺기 위해 대기하는 시간이 누적되면서 리소스가 소모되어 Flink 장애가 발생했습니다. Source DB 장애 테스트 시 이 문제가 발생하지 않은 것은, 검증 시 Kafka 레코드와 Target row가 일치하지 않는 경우에만 선택적으로 Source DB 커넥션을 맺었기 때문입니다.

이 이슈를 해결하기 위해 서킷 브레이커를 도입했습니다. DB 접근 오류 발생 시 검증 쿼리를 수행하고, 5회 이상 실패 시 서킷을 오픈합니다. 서킷 오픈 시에는 검증하지 않고 바로 DLQ로 전송합니다. 서킷 브레이커는 다음과 같이 구현했습니다.

```java
private final AtomicInteger consecutiveFailures = new AtomicInteger(0);
private final AtomicLong circuitOpenTime = new AtomicLong(0);

@Override
public RowVerificationResult verify(VerifySource source) {
 if (circuitOpened()) {
  return RowVerificationResult.circuitOpened(source, source.sourceData());
 }

 try {
  RowVerificationResult result = delegate.verify(source);
  consecutiveFailures.set(0); // Reset on success
  return result;
 } catch (DataAccessException exception) {
  // 해당 target ckey로 validation query 수행
  // 실패 시 target circuit 적립
  this.executeValidationQuery(source);
  return RowVerificationResult.unhandledException(source, source.sourceData(), exception);
 } catch (Exception exception) {
  return RowVerificationResult.unhandledException(source, source.sourceData(), exception);
 }
}

private boolean circuitOpened() {
 if (circuitOpenTime.get() == 0) {
  return false;
 }

 if (System.currentTimeMillis() - circuitOpenTime.get() >= openDurationMs) {
  log.warn("Circuit breaker timeout has been reached. Changing to half-open state.");
  circuitOpenTime.set(0);
  return false;
 }

 return true;
}

private void executeValidationQuery(VerifySource verifySource) {
 try {
  targetJdbcOperations.query(validationQuery, buildCkeyParameter(verifySource), rs -> null);
 } catch (DataAccessException ex) {
  log.error("Failed to validate DB operations", ex);
  if (consecutiveFailures.incrementAndGet() >= FAILURE_THRESHOLD) {
   circuitOpenTime.set(System.currentTimeMillis());
   log.warn("Circuit has been opened due to {} consecutive failures.", FAILURE_THRESHOLD);
  }
 }
}
```

## 전환 과정

기존 복제를 담당하던 mig-data를 어떻게 ergate로 전환했는지 과정을 살펴보겠습니다.

### 기본 전략

#### 복제 전략

복제 전략으로는 mig-data와 ergate가 각각 서로를 모르는 상태의 **중복 복제** 를 선택했습니다. 이는 mig-data에 중복 방어 로직을 추가하는 것이 기존 복제 동작에 어떤 영향을 줄지 모르고, 만약 이슈가 발생한다면 운영 환경에서 위험이 크다고 판단했기 때문입니다.

중복 복제로 인해 일시적으로 과거로 돌아갈 수는 있지만, 충분히 빠르기 때문에 사용자는 인지할 수 없고 최종적으로는 일치할 것이라고 판단했습니다.

#### 검증 전략

검증은 실제 데이터를 건드리지 않고, 자동 복구를 배포해두지 않으면 검출되더라도 문제가 없습니다. 따라서 **ergate 검증을 제일 먼저 배포** 하여 일정 기간동안 오검출, 과검출이 없는지 확인하는 과정을 가졌습니다.

그리고 평소 정상 복제 상황 하에서는 검증에서 검출되는 건이 없기 때문에, **만약을 위한 정답 선택지로 mig-data 검증을 유지** 하는 것이 좋다고 판단했습니다. 따라서 mig-data 검증의 종료는 제일 마지막으로 미루고, ergate 복제로 전환한 후에도 mig-data 검증을 일정 기간 유지했습니다.

#### 단계별 테이블 선별 및 순차 전환

복제 전략으로 중복 복제를 선택했기 때문에, 전체를 한 번에 전환하는 방식은 DB 리소스 사용량 증가의 위험이 있었습니다. 따라서 영향도가 낮은 테이블부터 시작해 차례로 투입하는 방식으로 전환을 진행했습니다.

1~3차로 대상 테이블을 분류해 순차적으로 전환했으며(예: 1차 5개, 2차 13개, 3차 잔여), 매 차수가 종료되는 시점에 mig-data 복제를 종료하고 ergate 단독 복제로 변경했습니다.

### 기존 복제 흐름

실제 전환으로 넘어가기 전에, 먼저 기존 mig-data의 복제 흐름부터 살펴보겠습니다. 기존에는 mig-data(비동기) + forceSync(동기) 복제가 수행되었습니다.

![](https://d2.naver.com/content/images/2025/11/16.png)

- mig-data Java 프로세스: Kafka 레코드를 컨슈밍 → Target에 복제
- forceSync([용어 설명](#용어-설명) 참고): API 기반 Source → Target에 수동 복제

복제가 양쪽에서 수행되면서 회귀 가능성은 존재했지만 다음과 같은 추가 장치가 있었습니다.

#### 과거 데이터로의 회귀 가능성 및 해결

먼저 forceSync의 동작 방식을 살펴보면 다음과 같습니다.

1. 서비스에서 사용 중인 '수정 시간' 칼럼을 비교해, Target에 최신 데이터가 복제되어 있는지 판단
2. 최신이 아니라면 현 시점 기준으로 Source SELECT → Target에 복제 수행

그런데 단기간에 A → B → C의 변경이 일어난 경우, 보통 forceSync의 복제가 동기로 더 빠르게 수행되기 때문에 다음과 같은 상황이 발생할 수 있습니다.

![](https://d2.naver.com/content/images/2025/11/17.png)

- forceSync: 최신 상태인 C로 반영
- mig-data: A → B → C 순서로 재반영

그 결과 **일시적으로 과거 데이터로 돌아갈 가능성** 이 있었습니다. 그래서 '복제 반영 시점'의 의미를 갖는 칼럼 sync\_seq를 추가해, 복제 쿼리에 다음과 같은 조건을 추가했습니다.

```sql
/* IS NULL 조건: 신규 추가한 칼럼이기 때문에 NULL인 경우에는 무조건 반영 */
/* >= 조건: 하위 참고 */
WHERE sync_seq IS NULL OR :commit_ts >= sync_seq
```

복제 시 sync\_seq 데이터(:commit\_ts)는 다음과 같습니다.

- forceSync: Source SELECT 시점 시간
- mig-data: Source 커밋 시간

`:commit\_ts >= sync\_seq` 는 반영할 데이터의 Source 커밋 시간이 Target 데이터의 Source 커밋 시간보다 과거라면 무시하라는 의미입니다.

여기서 조건이 `>` 가 아니라 `>=` 인 이유는 기존에 `ms` 를 절삭해 메시지를 발행하고 있었기 때문입니다. 단위인 ms를 변경하면 반영이 누락될 가능성이 있고, 메시지에 ms를 포함하도록 변경하면 mig-data의 동작을 예측하기 어렵습니다. 장애에 민감하기 때문에 유지하기로 결정했습니다.

### 전환 투입 - 동시 복제

앞서 말씀드렸듯이 mig-data와 ergate는 서로를 모르는 상태로 각각 복제를 수행하는 전략을 세웠습니다. 그래서 기존 복제 흐름에 ergate가 추가된 다음과 같은 형태로 투입을 시작했습니다.

![](https://d2.naver.com/content/images/2025/11/18.png)

이와 같은 흐름으로 1주일간 진행해 **데이터의 불일치 여부와 Flink 클러스터 모니터링** 을 수행했습니다.

추가로, 새롭게 참여한 ergate도 forceSync와의 관계는 mig-data에서와 동일하게 유지가 필요했습니다.

#### 과거 회귀 방지를 위한 별도 전용 칼럼 추가

![](https://d2.naver.com/content/images/2025/11/19.png)

ergate와 forceSync와의 회귀 방지를 위한 별도 전용 칼럼 'rpc\_time'을 추가했습니다. 로직은 mig-data와 동일하게 구성해 과거 회귀 방지를 달성했습니다.

### 최종 - 단독 복제

1주일간의 동시 복제를 진행한 후 mig-data 복제를 중단하여 다음 그림과 같이 ergate 단독 복제로 전환했습니다. 앞에서 설명드린 단계별 전환에서 매 단계마다 이 전환 과정을 반복했습니다.

![](https://d2.naver.com/content/images/2025/11/20.png)

## 트러블슈팅

ergate 프로젝트를 진행하면서 모든 것이 순탄할 수는 없었습니다. 결과로 넘어가기 전, Flink를 처음 사용하면서 겪었던 문제를 짚고 넘어가보겠습니다.

### job manager Metaspace OOM

이 문제는 저희가 세션 모드를 선택했기 때문에 발생했습니다. 먼저 동작 방식을 한 번 보겠습니다.

![](https://d2.naver.com/content/images/2025/11/21.png)

Flink 아키텍처(출처: [Flink Architecture](https://nightlies.apache.org/flink/flink-docs-release-2.0/docs/concepts/flink-architecture/))

#### 작성한 Flink job이 수행되는 방식

1. 작성한 Flink job(이하 user code)을 job manager로 제출(submit)
2. user code는 job manager에서 초기화된 후 직렬화되어 task manager로 전달
3. task manager가 받아서 user code 실제 수행

여기서 Flink JVM 클래스로더의 특수한 점을 발견했습니다. 사용자가 제출한 user code는 Flink에서 읽어들이고 관리할까요?

#### Flink 클래스 로딩 메커니즘 및 이슈

Flink의 클래스 로딩 메커니즘은 세션 모드 클러스터를 유지하면서 job/task manager 구동을 위한 Parent 클래스로더가 존재하고, 사용자가 제출한 user code는 Child 클래스로더가 읽어들이는 구조입니다.

![](https://d2.naver.com/content/images/2025/11/22.png)

- Parent 클래스로더: job/task manager 런타임
- Child 클래스로더: user code 로드. job이 종료되는 경우 본인이 소멸하면서 읽어들인 자원 해제

여기서 Child 클래스로더가 읽어들인 클래스에 대한 참조를 Parent가 보는 경우에 이슈가 발생했습니다. 예를 들어, Parent 클래스로더 어딘가에서 다음과 같은 코드를 참조한다고 가정하겠습니다.(예: Flink RestClient → Jackson ObjectMapper의 static Map)

```java
// user code에서 UserClass1 static field를 정의한 경우
private static final UserClass1 USER_CLASS = UserClass1.instanceOf()
```

Child 클래스로더의 소멸 시점에 Parent 클래스로더 어딘가에서 참조 중이기 때문에 소멸하지 못해, 자원을 해제할 수 없습니다. 그 결과, job이 여러 번 배포되는 과정에서 이 문제가 누적되어 OOM이 발생합니다.

#### 해결

여러 실험 결과, 'Parent에 없는 user code 클래스가 static field 타입으로 정의된 경우' 문제가 발생했습니다. 따라서 관련 라이브러리를 fat JAR로 만들어 Flink 클러스터 구동 시점에 포함시키거나, static 정의를 피해 코드를 수정하는 방식으로 해결했습니다.

- Flink 도커 이미지 빌드 시점에 필요 라이브러리 코드 포함
	- DB 드라이버 등 static resource를 관리하는 'ergate-flink-runtime' 저장소를 분리해 uber(fat) JAR 생성
		- 이미지 빌드 시 $FLINK\_HOME/lib 하위로 생성한 JAR 포함
- user code에서 static resource 사용 지양
	- [ArchUnit 테스트](https://d2.naver.com/helloworld/9222129) 를 추가해 기존/신규 코드 감시

ArchUnit 테스트 코드는 다음과 같습니다.

![](https://d2.naver.com/content/images/2025/11/23.png)

### job manager split brain

이 문제는 Kubernetes를 이용한 HA 구성 시 발생했습니다. 아무런 전조 증상 없이 갑자기 간헐적으로 job manager role change가 일어나고, 종국에는 split brain 이슈까지 발생했습니다.

좀 더 자세히 살펴보면, Kubernetes API 통신 간 leader 측의 네트워크 순단이 발생하는 찰나에 follower가 leader를 빼앗는 상황이 발생했습니다. 보통의 경우 기존 leader는 follower로 다시 내려가지만, 모종의 이유로 기존 leader가 지위를 내려놓지 못했습니다. 이 상황에서 task manager는 어떤 leader와 통신해야 하는지 혼란에 빠졌고, job도 다시 스케줄링되지 못해 복제가 멈췄습니다.

#### 해결

문제가 발생한 Kubernetes의 HA 관련 설정을 확인해 보겠습니다.

- lease-duration: leader로 인정되는 최대 시간
- renew-deadline: leader lease를 갱신해야 하는 최대 시간. 갱신 실패 시 리더 자진 퇴임
- retry-interval: lease 획득 또는 갱신 시도 주기

저희는 job manager 재배포 시 빠른 leader role change를 위해 초기에 위 값들을 각각 5s, 5s, 1s로 설정했습니다. 여러 사례를 찾아보고 AI 서비스의 도움을 받은 결과, lease-duration과 renew-deadline의 값이 같으면 이와 같은 이슈가 발생할 수 있다는 사실을 알아냈습니다.

네트워크 순단 가능성을 인정하고, 설정값을 각각 30s, 20s, 6s로 변경하자 더 이상 이슈가 발생하지 않았습니다.

## 결과

### 목표 전체 달성

올해 1월 말 프로젝트를 시작하면서 세웠던 모든 목표를 달성했습니다. 시작 당시 2명 모두 기존 업무를 겸하고 있었기에 본격적인 작업은 3월부터 진행했고, 3명이 된 시점은 5월부터였습니다. 1년 내내 수행해도 시간이 부족할 것이라고 생각했지만, 1차 목표인 판매자 DB 전환을 7월에 완료했습니다.

### 서비스 이슈 없는 전환 완료

![](https://d2.naver.com/content/images/2025/11/24.png)

전환 과정에서 데이터 관련 서비스 영향도 없었습니다. 위 이미지는 팀원 분께서 그 과정에서 재미로 만들어주신 이미지입니다.

잠깐의 해프닝 정도는 있었지만, 서비스에는 영향도가 거의 없는 수준으로, 제목과 같이 무중단, 무장애 선언을 할 수 있는 수준이었습니다. 단계를 나누어 DB 부하도 없었고 데이터 사고와 사용자 문의도 없었습니다.

### 기타

- forceSync 컴포넌트 페이드아웃: ergate만으로도 충분히 빠르고 안정적이라고 결론지어, 현재는 실제 동작을 비활성화했으며 최종적으로 내리는 단계를 밟고 있습니다.
- [ADR(Architecture Decision Record)](https://github.com/joelparkerhenderson/architecture-decision-record): 전체 아키텍처의 결정 과정을 ADR로 남겨두어, 이후 이 프로젝트를 담당하는 인원이 결정 과정과 근거를 참고할 수 있도록 했습니다.

## 마치며

지금까지 네이버페이 주문에서 DB 간 복제를 수행하는 도구인 ergate로의 전환 과정을 정리했습니다. 운영 중인 민감한 복제 도구를 이슈 없이 전환할 수 있었던 것에는, 7년이라는 장기간의 프로젝트를 진행하면서 쌓인 여러 노하우가 큰 역할을 했다고 생각합니다.

마치며 기존 복제 도구를 만들고 운영해주신 강철규 님께 감사 인사를 드립니다.

Tag

![](https://d2.naver.com/image/20251118/769219182626.jpg)

글쓴이

조찬형|NAVER Cloud WASL Tech

소개

네이버 내 여러 서비스들을 거치면서 경험을 쌓고 있습니다. 현재는 사우디 아라비아 프로젝트에 참여하고 있습니다.

![](https://d2.naver.com/image/20251118/097137840395.jpg)

글쓴이

이영대|NAVER Productivity Engineering

소개

산책과 리눅스를 좋아하고 성능을 개선하며 보람을 느끼는 개발자입니다. 현재 NAVER Pay 개선 프로젝트에 참여하고있습니다.

![](https://d2.naver.com/image/20251118/725472003214.jpg)

글쓴이

김동민|NAVER Productivity Engineering

소개

보드게임을 좋아하고 생산성에 관심이 많은 개발자입니다. 현재는 AI 를 많이 활용하려고 합니다.

관련글

- [![썸네일](https://d2.naver.com/content/images/2023/08/-----------2023-08-16-------11-26-57.png)
	분산디비지만 노출은 하고싶어 - mongo로 노출 전용 DB 만들기
	](https://d2.naver.com/helloworld/4381253)
- [![썸네일](https://d2.naver.com/content/images/2015/07/1255.PNG)
	데이터베이스 테스트 기법과 Coverage4iBatis
	](https://d2.naver.com/helloworld/1255)
- [![썸네일](https://d2.naver.com/content/images/2015/07/216593.PNG)
	글로벌 분산 데이터베이스 Spanner
	](https://d2.naver.com/helloworld/216593)
- [![썸네일](https://d2.naver.com/content/images/2024/03/helloworld_240306-1.png)
	일 3,000만 건의 네이버페이 주문 메시지를 처리하는 Kafka 시스템의 무중단 전환 사례
	](https://d2.naver.com/helloworld/9581727)

##### 댓글

1

- roeniss
	글의 짜임새가 너무 좋네요. 재미있게 잘 읽었습니다. 양질의 글 감사합니다.
	2025-11-29 07:12
	[**답글** 0](#)
	**공감/비공감** [공감 *1*](#) [비공감 *0*](#)
