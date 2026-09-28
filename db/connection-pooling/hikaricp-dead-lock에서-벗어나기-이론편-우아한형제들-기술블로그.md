---
title: "HikariCP Dead lock에서 벗어나기 (이론편) | 우아한형제들 기술블로그"
source: "https://techblog.woowahan.com/2664/"
author:
  - "[[우아한형제들 DevRel]]"
published: 2020-02-06
created: 2026-09-28
description: "안녕하세요! 공통시스템개발팀에서 메세지 플랫폼 개발을 하고 있는 이재훈입니다. 메세지 플랫폼 운영 장애를 바탕으로 HikariCP에서 Dead lock이 발생할 수 있는 case와 Dead lock을 회피할 수 있는 maximum pool size를 구하는 방법을 공유하고자 합니다. 동일한 이슈를 해결하기 위해 고생하시는 분들께 도움이 되길 바라며 글을 작성하였습니다. 추가적으로 이 문제를 해결하면서 발견한 JPA / hibernate 관련 내용까지 추가하였습니다. 글이"
tags:
  - "clippings"
---

> [!summary]
> 메세지 플랫폼 장애를 계기로, 하나의 Task가 동시에 Connection 2개를 필요로 할 때 HikariCP maximum pool size가 스레드 수 대비 부족하면 스레드 간 Dead lock이 발생하는 원리를 설명한다. `ConcurrentBag.borrow()`/`requite()`를 통해 Connection을 빌리고(threadList → 전체 스캔 → handoffQueue 대기 30초) 반납하는 과정을 그림과 각본으로 풀어낸다. 2부(실전편)에서는 `@GeneratedValue(AUTO)` 사용 시 `save()` 한 번에 Connection이 몇 개 필요한지를 분석한다.

## HikariCP Dead lock에서 벗어나기 (이론편)

2020\. 02. 06. 이재훈

[Infra](https://techblog.woowahan.com/?pcat=infra)

> 안녕하세요! 공통시스템개발팀에서 메세지 플랫폼 개발을 하고 있는 이재훈입니다.
>
> 메세지 플랫폼 운영 장애를 바탕으로 HikariCP에서 Dead lock이 발생할 수 있는 case와
> Dead lock을 회피할 수 있는 maximum pool size를 구하는 방법을 공유하고자 합니다.
> 동일한 이슈를 해결하기 위해 고생하시는 분들께 도움이 되길 바라며 글을 작성하였습니다.
>
> 추가적으로 이 문제를 해결하면서 발견한 JPA / hibernate 관련 내용까지 추가하였습니다.
> 글이 길어서 2편의 글로 나누어 업로드 하였습니다.

## 이 글의 예상독자

1. 아래와 같은 에러의 원인을 찾아 헤멘 개발자 **(이 에러가 발생한다면 이 글에서 설명하는 Case 일 수 있습니다.)**
	- o.h.engine.jdbc.spi.SqlExceptionHelper: SQL Error: 0, SQLState: null
		- o.h.engine.jdbc.spi.SqlExceptionHelper: hikari-pool-1 – Connection is not available, request timed out after 30000ms.
		- org.hibernate.exception.JDBCConnectionException: unable to obtain isolated JDBC connection
		- Could not open JPA EntityManager for transaction; nested exception is org.hibernate.exception.JDBCConnectionException: Unable to acquire JDBC Connection
2. HikariCP maximum pool size 설정할 때 "고려할게 있나?" "그냥 많이 만들어 두면 되는거 아니었어?" 라고 생각하셨던 분
	(저 또한 이랬습니다.)
3. Springboot2에서 @GeneratedValue를 사용하시는 분 (특히 GenerationType.SEQUENCE, AUTO를 쓰는 분)

## 무슨 내용인가요?

우아한형제들에서 사용하는 메세지 플랫폼 장애가 발생하였습니다.
장애의 원인을 분석 해보니 아래 3개 항목 간 상관관계가 있음을 발견하였습니다.

- HikariCP maximum pool size
- DB에 insert하고자 하는 전체 Thread Count
- 하나의 Task에서 **동시에** 필요한 Connection 수

위의 3개 항목 간의 상관관계를 정확히 알지 못해 HikariCP에서 Dead lock이 발생하였고,
Dead lock이 발생하는 case와 회피하는 방법을 공유하고자 합니다.

## 메세지 플랫폼 장애를 맞았습니다

장애가 발생한 구간의 간략한 Architecture 모식도입니다.

![메세지플랫폼 architecture](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/message-platform-architecture.png)

1. 전송할 메세지를 Message Queue에서 Consume합니다.
2. 메세지를 DB에 Insert 합니다.
3. 벤더사 Agent가 주기적으로 신규 메세지를 조회하면서, 벤더사 측으로 전송하게 됩니다.

## 그런데 말입니다.

![메세지플랫폼 architecture error](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/message-platform-architecture-error.png)

1. Application 로그에서 Connection timeout이 주기적으로 발생하였습니다.
2. 전송해야할 메세지가 Insert 실패, Rollback 로그가 다수 보였습니다.
3. 근데 이상하게도 간헐적으로 1~2건씩 어쩌다 성공해서 DB에 insert된 메세지가 보입니다.

## 처음엔 RDS 문제인 줄 알았지..

Application에서 계속 Connection timeout log만 떨어지니 처음엔 RDS 연결이 정상적이지 않다고 판단했습니다.

**근데**
**EC2에서도 mysql에 접속 잘되고…**
**local에서도 접속 잘되고…**
**쿼리도 잘 날아가고…**
**뭐지 왜 이상하게 쟤만 안되고..**.
**뭐지 카오스다…**

![chaos](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/chaos.png)

고ㅇ통 받는 공통시스템개발팀 익명의 개발자

일단 내부적으로 장애 상황을 해결하고 장애의 원인을 파헤쳐보기 시작했습니다.

## 범인은 이 안에 있을 것입니다.

## 장애의 단서부터 모아봤습니다.

1. 약 30초 주기로 발생하는 에러 로그
	```
	SQL Error: 0, SQLState: null
	HikariPool-1 - Connection is not available, request timed out after 30000ms.
	```
2. HikariCP HouseKeeper가 찍어주는 pool stats 로그
	```
	HikariPool-1 - Timeout failure stats (total=10, active=10, idle=0, waiting=16)
	```
3. Message Queue Consumer Thread 갯수 = **16개**
4. HikariCP maximum pool size 갯수 = **10개** (default로 사용하고 있었습니다.)
5. 장애 시간 대 네트워크 이슈 없음

## 결론부터 말씀드리자면

부하 상황에서 Thread간 Connection을 차지 하기 위한 Race Condition이 발생합니다.
메세지 1개를 저장하는데 한 Transaction에서 동시에 Connection 2개를 사용 하면서 HikariCP에 대한 Thread 간 Dead lock이 발생하게 되었습니다.

무슨 상황인지 감이 오시나요?
이 상황을 정확히 이해하기 위해선 HikariCP에서 Connection을 할당받고 반납하는 과정을 이해하셔야 합니다.

## HikariCP가 일하는 방식 (여기 일 잘한대서 구경왔어요)

SpringBoot 2.x가 출범하면서 HikariCP를 기본 JDBC Connection Pool로 사용할 수 있게 되었습니다.
HikariCP는 다른 Connection Pool에 비해 성능이 압도적이라고 합니다.
과연 내부에서는 어떻게 일하길래 (동작하길래?) 하고 살펴보았습니다.

## 하나의 쿼리가 실행되는 과정

실제 코드는 복잡하게 잘 구성되어 있지만 간략한 뼈대는 아래와 같을 것입니다.

```java
Connection connection = null;
PreparedStatement preparedStatement = null

try {
  connection = hikariDataSource.getConnection();
  preparedStatement = connection.preparedStatement(sql);
  preparedStatement.executeQuery();
} catch(Throwable e) {
  throw new RuntimeException(e);
} finally {
  if (preparedStatement != null) {
    preparedStatement.close();
  }
  if (connection != null) {
    connection.close(); // 여기서 connection pool에 반납됩니다.
  }
}
```

이제 `hikariDataSource.getConnection()` 부터 `connection.close()` 까지 내부 동작을 살펴 보겠습니다.

## 아래 내용을 보시기 전에..

HikariPool에서는 Connection 객체를 한번 wrapping한 PoolEntry라는 Type으로 내부적으로 Connection을 관리합니다.
아래 글에서는 이해를 편하게 하도록 **Connection** 이라는 용어로 언급하도록 하겠습니다.

## HikariCP에서 Connection을 리턴하는 방법

HikariPool에서 getConnection() 로직은 총 3단계를 통해 Connection을 리턴하고 있습니다.
(HikariCP에서 얼마나 성능을 올리기 위해 노력했는지 코드로 보입니다.)

HikariCP에서는 내부적으로 ConcurrentBag이라는 구조체를 이용해 Connection을 관리합니다.
`HikariPool.getConnection() -> ConcurrentBag.borrow()` 라는 메서드를 통해 사용 가능한(idle) Connection을
리턴하도록 되어있습니다.

전지적 개발자 시점으로 하나의 Thread가 Hikari Pool에 Connection을 요청하는 과정을 각본으로 만들어 보았습니다.
(개인적으로 유치하게 개발을 이해하면 이해도 잘되고 기억에도 오래 남는 것 같습니다.)

## Hikari님 Connection 하나만 주세요

![hikari-give-me-a-connection](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/hikari-give-me-a-connection.png)

**\[Thread-1님\]** 안녕하세요 Hikari님! Connection 하나만 주세요~
**\[Hikari님\]** 안녕하세요 Thread-1님! 저희 pool에서는 Connection을 주는 규칙이 있답니다. 확인해볼게요~
**\[Hikari님\]** 이전에 Thread-1님이 저희 pool에 방문한 내역 먼저 살펴볼게요!
**\[Hikari님\]** 오! 이전에 방문한 내역이 있으시네요~ 근데 그때 사용한 Connection은 다른 Thread 님이 사용 중(active) 이시네요~
다른 Thread님이 안 쓰셨으면 빠르게 이 Connection 먼저 드렸을 텐데 아쉽네요ㅠㅠ
**\[Thread-1님\]** 괜찮아요! Hikari님 다른 Connection 주세요~
**\[Hikari님\]** Pool 전체에서 사용 가능한(idle) Connection이 있는지 찾아볼께요~
**\[Hikari님\]** (Loop 돌면서 찾는중…)
**\[Hikari님\]** Thread-1님 지금 전체 Connection이 다 사용중이에요! ㅠㅠ
저기 handoffQueue 앞에 가서 좀 기다리셔야 할 것 같아요 ㅜㅜ
**\[Thread-1님\]** 네 괜찮아요! (안 괜찮음) 저기서 30초만 기다려보고 없으면 Exception내면 되죠^^
**(깨알 Tip. HikariCP default Connection timeout은 30초 입니다.)**
**\[Hikari님\]** 네 죄송합니다 Thread-1님. 다음에 또 다시 방문해주세요~
**\[Thread-1님\]** *(handoffQueue에서 다른 Thread가 쓰고 반납한 Connection을 얻었다!)*

혹시 잘 이해가 가셨을까요..?
이해가 아직 안되신 분들을 위한 Flow chart를 준비해보았습니다.

![getConnection-flow](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/getConnection-flow.png)

코드로 확인해보기 >> [ConcurrentBag.borrow()](https://techblog.woowahan.com/2664/%3Chttps://github.com/brettwooldridge/HikariCP/blob/dev/src/main/java/com/zaxxer/hikari/util/ConcurrentBag.java#L126%3E)

## Hikari님! Connection 다 썼어요

![hikari-requite-connection](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/hikari-requite-connection.png)

HikariCP에서 얻은 Connection은 (ProxyConnection) Connection.close()를 하게 되면 HikariPool에 반납이 됩니다.
(HikariPool에서 얻은 Connection은 `ProxyConnection` 타입입니다.)
정상적으로 transaction이 commit 되거나, 에러로 인해 rollback이 호출 되면 connection.close()가 호출되어
Connection을 Pool에 반납합니다.
getConnection과 마찬가지로 `connection.close() -> concurrentBag.requite()` 이 실행되며 Connection이 반납됩니다.

위와 같이 전지적 개발자 시점 각본을 짜보겠습니다.

**\[Thread-1님\]** Transaction내의 쿼리를 모두 수행하고 Commit이 되었어 이제 Connection을 반납해볼까?
**\[Thread-1님\]** *Thread-1님이 (ProxyConnection) connection.close()을 실행하였습니다.*
**\[Hikari님\]** 안녕하세요 Thread-1님! Connection 이용은 만족스러우셨나요? Connection 반납 절차 도와드리겠습니다.
**\[Hikari님\]** 일단 idle Connection으로 바꿀게요 (poolEntry.setState(STATE\_NOT\_IN\_USE))
**\[Hikari님\]** handOffQueue에서 Connection을 받길 원하는 다른 Thread님이 있나봐요~
**\[Hikari님\]** (handOffQueue에 Connection 삽입)
**\[Thread-2님\]** 나이스!! handOffQueue에 Connection 하나 떨어졌다~
**\[Hikari님\]** Thread-1님 고생하셨습니다~ 이번에 사용한 Connection 정보 등록해 드릴께요~!

다음에 빠르게 이용하실 수 있으실거에요
**\[Thread-1님\]** 감사합니다! Hikari님 또 Connection 받으러 올께요~

혹시 잘 이해가 가셨을까요..?
이해가 아직 안되신 분들을 위한 Flow chart를 준비해보았습니다.

![getConnection-flow](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/close-flow.png)

코드로 확인해보기 >> [ConcurrentBag.requite()](https://github.com/brettwooldridge/HikariCP/blob/dev/src/main/java/com/zaxxer/hikari/util/ConcurrentBag.java#L181)

## HikariCP에서 Dead lock이 발생하는 Case

Message Queue의 consumer thread 갯수보다 HikariCP의 maximum pool size를 충분하게 설정하지 못해 Dead lock이 발생하여 이번 장애로 이어지게 되었습니다.
도데체 무슨 관계가 있다고 Dead lock이 발생했을까요?
간단한 예시를 통해 알아보도록 하겠습니다.

Thread count와 maximum pool size의 조건은 아래와 같습니다.

- Thread Count: 1개
- HikariCP Maximum pool size: 1개
- 하나의 Task에서 동시에 요구되는 Connection 갯수: **2개!!**

조금은 감이 오시나요?
그림으로 살펴보도록 하겠습니다.

![dead-lock-thread-flow](https://techblog.woowahan.com/wp-content/uploads/img/2020-02-06/dead-lock-thread-flow.png)

1. Thread가 Repository.save(entity) 라는 insert query를 실행하기 위해 Transaction을 시작합니다.
2. Root Transaction용 Connection을 하나 가져옵니다. **(PoolStats: total=1, active=1, idle=0, waiting=0)**
3. Transaction을 시작하였고 Repository.save를 하기 위해 Connection이 하나 더 필요하다고 **가정** 해보겠습니다.
4. Thread-1은 Hikari Pool에 Connection을 요청합니다.
	1. 위의 3단계 절차대로, 현재 자기 Thread의 방문내역을 살펴봅니다.
		아직 방문내역이 등록된 게 없습니다.
		2. 전체 Hikari Pool에서 idle상태의 Connection을 스캔합니다.
		Pool Size는 1개이고 1개 있던 Connection은 Thread-1에서 이미 사용중입니다.
		3. 마지막으로 **handOffQueue에서 누군가 반납한 Connection이 있길 기대하며 30초 동안 기다립니다.**
		하나 있던 Connection을 자기 자신이 사용하고 있기 때문에 자기 자신이 반납하지 않는 이상 사용할 Connection이 없습니다.
		**(PoolStats: total=1, active=1, idle=0, waiting=1)**
		4. 결국 30초가 지나고 Connection Timeout이 발생하고
		`hikari-pool-1 - Connection is not available, request timed out after 30000ms.` 에러 발생
5. SQLTransientConnectionException으로 인해 **Sub Transaction이 Rollback 됩니다.**
6. Sub Transaction의 Rollback으로 인해 Root Transaction이 rollbackOnly = true가 되며 Root Transaction이 롤백 됩니다. JpaTransactionManager를 사용한다고 가정하겠습니다.
	([우아한형제들 기술블로그 – 응? 이게 왜 롤백되는거지?](http://woowabros.github.io/experience/2019/01/29/exception-in-transaction.html) 참고)
7. Rollback 됨과 동시에 Root Transaction용 Connection은 다시 Pool에 반납됩니다.
	**(PoolStats: total=1, active=0, idle=1, waiting=0)**

이렇게 Thread내에서 하나의 Task에 수행하는데 필요한 Connection갯수가 모자라게 되면
**Dead Lock 상태에 빠져 Insert Query를 실행할 수 없게 됩니다.**

## 1부를 마치며

1부에서는 제가 겪은 장애와 HikariCP의 동작 원리를 살펴보았습니다.
2부인 실전편에서는 실제 장애의 원인을 분석하고 개선한 사례를 공유하려고 합니다.

## 2부 예고

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

`repository.save()` 을 수행하는데 Connection이 몇 개 필요할까요?
궁금하면 다음 글로 이동~
[HikariCP Dead lock에서 벗어나기 (실전편)](http://woowabros.github.io/experience/2020/02/06/hikaricp-avoid-dead-lock-2.html)
