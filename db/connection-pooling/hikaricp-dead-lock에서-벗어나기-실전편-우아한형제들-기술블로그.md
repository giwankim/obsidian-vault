---
title: "HikariCP Dead lock에서 벗어나기 (실전편) | 우아한형제들 기술블로그"
source: "https://techblog.woowahan.com/2663/"
author:
  - "[[우아한형제들 기술블로그  |]]"
published: 2020-02-06
created: 2026-02-12
description: "1부 HikariCP Dead lock에서 벗어나기 (이론편)은 잘 보셨나요? 2부 HikariCP Dead lock에서 벗어나기 (실전편)에서는 실제 장애 사례를 기반으로 장애 원인을 설명하고 해결 사례를 공유하고자 합니다. 그럼 시작하도록 하겠습니다! 1부의 Dead lock 예시는 이해가 갔는데, 실제 상황은 뭐였나요? 사실, 예제가 실제 상황이었습니다. 장애 환경에 대한 Thread count와 maximum pool size의 조건은 아래와 같습니다 CPU Core :"
tags:
  - "clippings"
---
## HikariCP Dead lock에서 벗어나기 (실전편)

2020\. 02. 06.WoowaTech

[Infra](https://techblog.woowahan.com/?pcat=infra)

> 1부 HikariCP Dead lock에서 벗어나기 (이론편)은 잘 보셨나요?
>
> 2부 HikariCP Dead lock에서 벗어나기 (실전편)에서는 실제 장애 사례를 기반으로
> 장애 원인을 설명하고 해결 사례를 공유하고자 합니다.

그럼 시작하도록 하겠습니다!

## 1부의 Dead lock 예시는 이해가 갔는데, 실제 상황은 뭐였나요?

**사실, 예제가 실제 상황이었습니다.**

장애 환경에 대한 Thread count와 maximum pool size의 조건은 아래와 같습니다

- CPU Core: 4개
- Thread Count: 16개
- HikariCP MaximumPoolSize: 10개
- 하나의 Task에서 동시에 요구되는 Connection 갯수: 2개
	(처음엔 1개일거라 생각했지만, getConnection에 대한 디버깅을 해보니 2번의 getConnection 요청이 발생했습니다.)

실제 구현부의 간단한 코드입니다.

```java
@Entity
class Message {
  @Id
  @GeneratedValue(strategy = GenerationType.AUTO)
  private long id;
  private String title;
  private String contents;
}
```
```java
@Transactional
public Message save(final Message message) {
  return repository.save(message)
}
```

혹시 이 코드에서 왜 Connection이 2개나 필요한지 짐작이 되시나요?
코드만 보면 하나의 Connection으로 Insert가 잘 될 것 같습니다.
여태까지 그런줄 알았고 이번 장애가 아니었다면 몰랐을 것이었습니다.

## Into the unknown

## 범인은 바로 @GeneratedValue(strategy = GenerationType.AUTO)

JPA에서 DB Insert시, id 생성 방식을 결정하는 Annotation 입니다.
GenerationType이 AUTO이고, id 변수의 Type이 Long이기 때문에 내부적으로는 SequenceStyleGenerator 로 ID를 생성하게 됩니다.

기본적으로 Sequence를 기반으로 ID를 생성하는 Generator이지만
MySQL은 Sequence를 지원하지 않기 때문에 **hibernate\_sequence라는 테이블에 단일 Row를 사용** 하여 ID값을 생성합니다.
여기서 hibernate\_sequence 테이블을 조회, update를 하면서 Sub Transaction을 생성하여 실행하게 됩니다.

## ID 하나만 주세여

```java
select next_val as id_val from hibernate_sequence for update;
```

MySQL for update 쿼리는 조회한 row에 lock을 걸어 현재 트랜잭션이 끝나기 전까지
다른 session의 접근을 막습니다.

동시성 제어를 위해 이런 Query를 구성했다고 생각합니다. (ID 값이기 때문에 중복되면 안됨)

또한 별도 Sub Transaction을 구성한 이유도
만약 현재 사용 중인 상위 Transaction을 사용했다면,
상위 Transaction이 끝나기 전 까지 다른 thread에서 ID 채번을 할 수 없기 때문이라고 추측하고 있습니다.

## 코드를 직접 보여드리겠습니다.

아래 이미지의 라이브러리 버전은 다음과 같습니다.

- spring-data-jpa-2.2.1.RELEASE
- hibernate-core:5.4.8.Final

![SimpleJpaRepository.save](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/SimpleJpaRepository-save.png)

SimpleJpaRepository.save

![AbstractSaveEventListener.saveWithGeneratedId](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/AbstractSaveEventListener-saveWithGeneratedId.png)

AbstractSaveEventListener.saveWithGeneratedId

![SequenceStyleGenerator.generate](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/SequenceStyleGenerator-generate.png)

SequenceStyleGenerator.generate

![TableStructure.buildCallback](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/TableStructure-buildCallback.png)

TableStructure.buildCallback

![JdbcIsolationDelegate.delegateWork](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/JdbcIsolationDelegate-delegateWork.png)

JdbcIsolationDelegate.delegateWork

ID 채번을 위한 Query를 실행하는 과정에서
`Connection connection = jdbcConnectionAccess().obtainConnection();` 코드가 실행 되며
2번째 Connection을 가지고 오게 됩니다.

ID를 조회하고, update 하는 Transaction이 commit되면 Connection이 바로 Pool에 반납이 됩니다.

## 실제 운영환경에서는 어떤 일이 일어나고 있을까요?

일반적인 상황에서는 확률이 적었을 것입니다. Thread 전체가 동시에 일하지 않을 것이기 때문입니다.
하지만 문제는 Thread 전체가 일하는 부하상황에서 발생합니다.

![dead-lock-case](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/dead-lock-case.png)

부하 상황에서 16개의 Thread가 거의 동시에 HikariCP로부터 Connection을 얻어내
10개의 Thread만이 Connection을 가지고 Transaction을 시작했을 것입니다.
**하지만 ID 생성을 위한 Connection을 얻으려 하면, 현재 Pool에는 idle Connection이 없기 때문에 handOffQueue에서 10개의 Thread가 대기하고 있게 됩니다.**

Connection Timeout만큼의 시간이 흐르고.. 아까 전지적 개발자 시점에서 보았던 Thread-1의 명대사가 다시 떠오릅니다.

**\[Thread-1님\] 네 괜찮아요! (안 괜찮음) 저기서 30초만 기다려보고 없으면 Exception내면 되죠^^**

그렇게 SQLTransientConnectionException이 발생하고 Transaction이 rollback 되면서 다시 Connection이 Pool에 반납되고 handOffQueue에서 기다리는 다른 Thread에서 다시 Connection을 받아가기 시작합니다.

![dead-lock-case-lucky](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/dead-lock-case-lucky.png)

어쩌다 운이 좋은 Thread는 타이밍을 맞춰서 Id 채번을 위한 Connection을 받아낼 수도 있습니다.
(이 Case가 간헐적으로 어쩌다 성공하는 Case가 됩니다.)

이와 같은 경우를 HikariCP에서는 Dead lock 또는 Pool-locking이라는 용어를 사용하여 표현하고 있습니다.

## HikariCP Dead lock을 피하려면 어떻게 해야하나요?

이미 이 이슈는 HikariCP github에서도 issue로 등록되었고, HikariCP wiki에서 Dead lock을 해결하는 방법을 제시하고 있습니다.
(오 다행)

- Github: [https://github.com/brettwooldridge/HikariCP](https://github.com/brettwooldridge/HikariCP)
- issue: [https://github.com/brettwooldridge/HikariCP/issues/442#issuecomment-146096704](https://github.com/brettwooldridge/HikariCP/issues/442#issuecomment-146096704)
- wiki: [https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing)

## 마법의 공식

![magic-formula](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/magic-formula.png)

- *Tn*: 전체 Thread 갯수
- *Cm*: 하나의 Task에서 동시에 필요한 Connection 수

HikariCP wiki에서는 이 공식대로 Maximum pool size를 설정하면 Dead lock을 피할 수 있다고 합니다.

## 검증 들어갑니다

![check-formula](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/check-formula.png)

- 전체 Thread 갯수: 8개
- 하나의 Task에서 동시에 요구되는 Connection 갯수: 2개

![avoid-dead-lock](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/avoid-dead-lock.png)

8개의 Thread가 동시에 HikariCP에 Connection을 요청하고 8개의 Connection을 골고루 나눠 가졌습니다.
그럼에도 불구하고 1개의 Connection이 남아있습니다.
이 1개의 Connection이 Dead lock을 피할 수 있게 해주는 Key Connection이 됩니다.

위의 예시에서는 **Thread-2** 에서 먼저 ID 채번을 위한 Connection을 얻었습니다.
그렇게 되면 정상적으로 DB Insert가 이루어지고, idle Connection 2개가 Pool에 반납됩니다.

![avoid-dead-lock-2](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/avoid-dead-lock-2.png)

다음 Step으로 **Thread-2** 를 제외한 Thread는 handOffQueue에서 새로운 Connection을 얻기 위해 대기하다가
**Thread-2** 가 반납한 Connection을 받아가게 됩니다.
위의 예시에서는 **Thread-3**, **Thread-6** 에서 사이 좋게 나눠 가져갑니다.

위의 공식대로 pool size를 설정하니 Dead lock이 발생하지 않게되었습니다.

## 다시 공식을 봅시다.

![avoid-dead-lock-2](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/explain-formula.png)

## 이게 최선입니까?

위의 공식은 이론적으로 Dead lock을 피할 수 있는 최소한의 Pool size 입니다.
공식대로라면 Thread가 몇 개이든 동시에 필요한 Connection이 1개라면
Pool size가 1개인 Pool을 가지고도 모든 Request를 다 처리할 수 있을 것 입니다.

하지만 효율이 좋지 않겠죠.
어떤 Thread는 운이 없게 할당받지 못해서 30초 후에 SQLTransientConnectionException을 던질 수도 있습니다.
그렇기 때문에 최적의 Pool Size를 설정하기 위해서는 **Dead lock을 피할수 있는 pool 갯수 + a** 가 되어야 합니다.
이에 대한 방법으로는 성능 테스트를 수행하면서 최적의 Pool Size를 찾는 방법이 있을 것 같습니다.

## 장애의 후속 처리도 진행하였습니다.

장애에 대한 후속처리로 아래 2가지를 적용하였습니다.

- Dead lock을 회피할 수 있는 pool size 적용
- SequenceGenerator에 대한 Pooled-lotl optimizer 적용

## Dead lock을 회피할 수 있는 pool size 적용

![extended_formula](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/extended-formula.png)

위와 같은 pool size 공식을 기준으로 내부적으로 기본 공식을 확장하여 사용하고 있습니다

조금 더 성능 테스트를 진행해야 하겠지만 일단은 아래와 같이 설정하였습니다.

- thread count: 16
- simultaneous connection count: 2
- pool size: 16 \* ( 2 – 1 ) + (16 / 2) = 24

## SequenceGenerator에 대한 Pooled-lotl optimizer 적용

![SequenceStyleGenerator.generate](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/SequenceStyleGenerator-generate.png)

SequenceStyleGenerator.generate

위의 코드에서 확인했지만, SequenceStyleGenerator에는 몇가지 optimizer를 통해 ID를 채번할 수 있습니다.

## NoopOptimizer

Default Optimizer입니다. generate() 메서드 호출 시 마다 DB에 Query하여 ID를 채번합니다.
sequence값을 +1씩 update하여 사용합니다.

## HiLoOptimizer

![HiLoAlgorithm](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/HiLoAlgorithm.png)

"hilo" algorithm 을 적용한 Optimizer입니다.
내부적으로 hilo optimizer는 deprecated된 optimizer입니다.
`(increment * (조회한 Sequence -1) + 1) ~ (Hincrement * 조회한 Sequence)` 만큼의 범위를 사용 ID를 채번합니다.

## PooledOptimizer

![PooledOptimizer](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/PooledOptimizer.png)

NoopOptimizer와 다르게 한번에 incrementSize만큼 sequence를 업데이트하고
범위만큼 메모리에서 관리하는 방식입니다.
`(조회한 sequence - increment) ~ 조회한 sequence` 만큼의 범위를 DB를 Query하지 않고 메모리를 이용하여
채번할 수 있습니다.

ex) 현재 sequence가 1000이고 increment가 100인 경우, 900~999까지는 DB를 Query하지 않고 메모리에서 채번.
`update hibernate_sequence set next_val = next_val + 100 where next_val = 1000` 을 실행하여 미리 100만큼 업데이트 합니다.

## PooledLoOptimizer

![PooledLoOptimizer](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/PooledLoOptimizer.png)

PooledOptimizer와 동일하지만 조회해 온 sequence값을 Low값으로 하여 사용합니다.

ex) 현재 sequence가 1000이고 increment가 100인 경우, 1000~1099까지는 DB를 Query하지 않고 메모리에서 채번합니다.

## PooledLoThreadLocalOptimizer

PooledLoOptimizer를 Thread단위로 사용합니다.

ex) 현재 sequence가 1000이고 increment가 100인 경우,
thread-1에서는 1000~1099까지 범위를 사용.
thread-2에서는 1100~1199까지 범위를 사용
이 방식의 장점은 Thread 별로 ID 구간을 관리하므로 효율성 입장에서는 PooledLo보다 좋습니다.

## 저희는 PooledLoThreadLocalOptimizer를 사용했습니다.

작업 단위가 Thread단위로 분리되어 있고, 굳이 Linear한 ID를 생성할 필요가 없기 때문입니다.

아래처럼 코드를 구성하여 Optimizer를 적용하였습니다.

```java
@Entity
class Message {
  @Id
  @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "message-id-generator")
  @GenericGenerator(
    name = "message-id-generator",
    strategy = "sequence",
    parameters = [
      Parameter(name = SequenceStyleGenerator.SEQUENCE_PARAM, value = "hibernate_sequence"),
      Parameter(name = SequenceStyleGenerator.INCREMENT_PARAM, value = "1000"),
      Parameter(name = AvailableSettings.PREFERRED_POOLED_OPTIMIZER, value = "pooled-lotl")
    ]
  )
  private long id;
  private String title;
  private String contents;
}
```

이렇게 적용하니 Thread에서 ID 범위를 설정할 때만 hibernate\_sequence에 Query 하여
NoopOptimizer를 사용할 때 보다 Connection을 사용 횟수를 줄여 조금 더 효율적으로 Connection을 사용할 수 있게 되었습니다.

## 추가적으로..

## 왜 @GeneratedValue(strategy = GenerationType.AUTO)를 사용 했나요?

사실 GenerationType.IDENTITY를 사용하고, MySQL id column에 `auto_increment` 를 적용하면
1개의 Connection 으로도 insert 할 수 있습니다.
하지만 저희는 auto\_increment를 사용하지 말아야 할 이유가 있었습니다.
메세지 플랫폼에서 사용하는 메세지 발송 Table은 데이터의 삽입/삭제가 빈번하게 일어납니다.
그런데 RDS Restart 시, auto\_increment의 index가 변경될 가능성이 있습니다.
(RDS Restart 시, Table의 Last ID 기준으로 auto\_increment index가 조정됩니다.)

외부 벤더사와의 연동을 하다보니 이전에 사용한 ID를 다시 사용하면 안되는 벤더사 측 이슈가 있기 때문에,
중복되지 않고, ID 대역을 언제든지 조작할 수 있도록 SEQUENCE로 사용하도록 의사 결정 하였습니다.

## GenerationType.AUTO인데 SEQUENCE로 동작하나요?

주의!
SpringBoot 버전에 따라 GenerationType.AUTO 일 때 결정되는 ID Generator가 다릅니다.

SpringBoot 2로 버전이 올라가면서 hibernate.id.new\_generator\_mappings default 속성 값이 변경되었습니다.

- Springboot 1.5.x: hibernate.id.new\_generator\_mappings 속성값이 false
- Springboot 2.x.x: hibernate.id.new\_generator\_mappings 속성값이 true

> Default value for `hibernate.id.new_generator_mappings` setting changed to true for 5.0. See `org.hibernate.cfg.AvailableSettings#USE_NEW_ID_GENERATOR_MAPPINGS` javadocs.

또한 Id Generator에 대해 hibernate 공식 문서에서는 아래와 같이 설명하고 있습니다.

> This is the default strategy since Hibernate 5.0. For older versions,
> this strategy is enabled through the hibernate.id.new\_generator\_mappings
> configuration property. When using this strategy, AUTO always resolves
> to SequenceStyleGenerator. If the underlying database supports
> sequences, then a SEQUENCE generator is used. Otherwise, a TABLE
> generator is going to be used instead.

위의 내용 + 실제 코드를 기반으로 작성한 Flow chart입니다.

![determine-generator](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/determine-generator.png)

먼저 `hibernate.id.new_generator_mappings=false` 인 경우입니다.

![determine-native-1](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/determine-native-1.png)

DefaultIdentifierGeneratorFactory.getIdentifierGeneratorClass

strategy가 `native` 인 경우 사용하는 Dialect에 의해 Generator가 결정됩니다.

![determine-native-2](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/determine-native-2.png)

Dialect.getNativeIdentifierGeneratorStrategy

Dialect에서 supportsIdentityColumns()가 `true` 인 경우 IdentityGenerator를 사용하게 됩니다.
`false` 인 경우 SequenceStyleGenerator를 사용하게 됩니다.

이번엔 `hibernate.id.new_generator_mappings=true` 인 경우입니다.

![buildDatabaseStructure](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/buildDatabaseStructure.png)

SequenceStyleGenerator.buildDatabaseStructure

Dialect에서 Sequence기능 제공 여부에 따라 내부적으로 사용하는 DatabaseStructure가 결정됩니다.

![isPhysicalSequence](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/isPhysicalSequence.png)

SequenceStyleGenerator.isPhysicalSequence

- Sequence기능을 지원하는 경우 SequenceStructure를 사용
- Sequence기능을 지원하지 않는 경우 TableStructure를 사용합니다.

위에서 결정된 DatabaseStructure는 아래 코드에서 사용됩니다.

![SequenceStyleGenerator.generate](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/SequenceStyleGenerator-generate.png)

SequenceStyleGenerator.generate

## 내 코드에서 Dead lock 발생 가능성을 체크해 보아요

1. **HikariCP의 Maximum Pool Size을 1로 설정한 다음 1건씩 Query를 실행해 봅니다.**
	만약 정상적으로 실행되지 않고, connection timeout과 같은 에러가 발생한다면 Dead lock 발생 가능성이 있는 코드입니다.
2. **Nested Transaction을 사용하지 않는다.** 보이지 않는 dead lock을 유발할 수 있습니다.

## 마무리

정말 찾아내기 어려운 문제였던 만큼 이번 기회를 통해 배운 것들이 많은 것 같습니다.
서비스인프라실에서는 위와 같은 이슈를 분석하고 좋은 개선점이 있는지 항상 고민하고 있습니다.
다음에도 좋은 기술 블로그로 찾아오도록 하겠습니다.

더불어 같이 HikariCP 코드까지 분석하면서 밤늦게까지 고생해주신 공통시스템개발팀 팀원 분들께 감사 인사드립니다.
처음 써보는 기술블로그이기에 설명이 어눌하거나 부족한 부분이 많습니다(ㅠㅠ) 양해 부탁드리겠습니다.

긴 글 읽어주셔서 감사합니다.

저희와 같이 기술적인 문제를 해결하고 고민하고 성장하고 싶은 욕구가 있으신 분들은
언제든지 공통시스템개발팀에 지원 부탁드리겠습니다.
**\[공통기술부문\] 공통시스템 개발자 모집** ([지원서 GoGo](https://www.woowahan.com/#/recruit/tech))

## 참고

- \[About Pool Sizing\] – [https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing)
- \[Down the Rabbit Hole\] – [https://github.com/brettwooldridge/HikariCP/wiki/Down-the-Rabbit-Hole](https://github.com/brettwooldridge/HikariCP/wiki/Down-the-Rabbit-Hole)
- [https://github.com/brettwooldridge/HikariCP](https://github.com/brettwooldridge/HikariCP)
- [우아한형제들 기술블로그 – 응? 이게 왜 롤백되는 거지?](http://woowabros.github.io/experience/2019/01/29/exception-in-transaction.html)
- \[Hibernate pooled and pooled-lo identifier generators\] – [https://vladmihalcea.com/hibernate-hidden-gem-the-pooled-lo-optimizer/](https://vladmihalcea.com/hibernate-hidden-gem-the-pooled-lo-optimizer/)
- [https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-2.0-Migration-Guide#id-generator](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-2.0-Migration-Guide#id-generator)
- [https://docs.jboss.org/hibernate/orm/5.2/userguide/html\_single/Hibernate\_User\_Guide.html#identifiers-generators-auto](https://docs.jboss.org/hibernate/orm/5.2/userguide/html_single/Hibernate_User_Guide.html#identifiers-generators-auto)
