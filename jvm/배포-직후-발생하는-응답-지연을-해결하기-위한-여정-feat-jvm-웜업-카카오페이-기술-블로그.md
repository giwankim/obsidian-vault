---
title: "배포 직후 발생하는 응답 지연을 해결하기 위한 여정 (feat. JVM 웜업) | 카카오페이 기술 블로그"
source: "https://tech.kakaopay.com/post/jvm-warm-up/"
author:
published: 2026-02-25
created: 2026-11-20
description: "굿딜 서비스를 운영하며 마주친 배포 직후 응답 지연 문제를 해결하기 위한 과정을 공유하고자 합니다."
tags:
  - "clippings"
---

> [!summary]
> Kakao Pay's GoodDeal team traces a recurring burst of HikariCP `Connection is not available` timeouts and slow responses right after every deploy. Tuning pool options (`connectionTimeout`, `maximumPoolSize`, `minimumIdle`) and changing the deployment strategy to reduce initial traffic did not fix it; server and HikariCP metrics eventually pointed to the JVM's lazy class loading, where first requests held connections while classes were still being loaded, exhausting the pool within seconds. Adding a warm-up step to the deployment pipeline that calls the core logic of the busiest APIs before real traffic arrives removed the delay, and the post closes with a look at class-loading logs and JIT tiered-compilation thresholds as the second goal of warm-up.

> 요약: 배포 직후 발생하는 DB Connection Timeout과 응답 지연 문제를 해결하기 위해, 단순한 설정 변경을 넘어 원인을 분석하고 **JVM 웜업(Warm-up)** 을 도입한 과정을 공유합니다. 배포 직후 성능 저하 문제를 어떻게 해결했는지, 그리고 고민 과정과 해결책은 무엇이었는지 함께 읽어보세요.

💡 **리뷰어 한줄평**

**rain.drop** 서비스가 성장하면 누구나 겪게 되는 문제예요. DB Connection Timeout 문제로부터 JVM 웜업 해결에 도달한 에덴의 생각 흐름을 같이 읽어보아요. 같은 문제를 겪고 계시거나 유사항 경험이 있으시다면 읽어보시길 추천드려요.

**wonny.p** 발생된 이슈에 대해서 점진적으로 원인 분석하고 가설을 검증해가는 과정을 매우 잘 표현한 글이에요. JVM 웜업 이란 주제를 넘어서 서비스 구현/운영 단계에서 발생된 문제 해결 전략 수립에 대해 어려움을 겪는 모든 담당자분들이 읽어 보시길 추천드려요.

## 시작하며

안녕하세요. 굿딜 서비스에서 서버 개발을 하고 있는 에덴이라고 합니다. 굿딜 서비스는 작년 2월에 오픈한 조건 없는 무제한 할인을 제공하는 카카오페이 결제 서비스 중 하나입니다.

![다양한 혜택을 제공하는 굿딜 서비스](https://tech.kakaopay.com/_astro/image1_gooddeal_home.v7gcFQ2v_Z1g82df.webp)

다양한 혜택을 제공하는 굿딜 서비스

특히 굿딜만의 시그니처 프로모션인 `타임어택`을 통해 파격적인 할인율을 제공하며 성장하고 있습니다.

![작년 10월에 진행했던 굿딜 타임어택](https://tech.kakaopay.com/_astro/time_attack.DiYYP6gb_dUvIR.webp)

작년 10월에 진행했던 굿딜 타임어택

서비스 오픈 후 많은 분들이 사용해 주시면서 트래픽이 꾸준히 늘어났고, 저희 팀은 서비스 안정성과 성능을 높이기 위해 여러 가지 개선 작업을 진행했습니다.

서비스 진입을 위한 노출되는 영역이 증가함에 따라 조회 쿼리를 유발하는 트래픽이 많이 늘어났고, 배포 직후 인입되는 요청들이 `DB Connection Timeout`과 함께 초기 응답 지연이 발생하기 시작했습니다. 운영 배포 시마다 반복된 `배포 직후 발생하는 초기 응답 지연 문제`를 해결하기 위한 여정을 소개하려 합니다.

해당 이슈의 결론부터 말씀드리면, 애플리케이션이 구동되는 시점에 **JVM 웜업** 을 적용하여 문제를 해결할 수 있었습니다.

HikariCP 커넥션 타임아웃과 JVM 웜업과 무슨 상관관계가 있는지 궁금하시지 않나요?

이 글을 통해서

1. 말로만 듣던 웜업을 왜 해야 하는지
2. 굿딜 서비스에서 발생한 해당 이슈와 어떤 연관관계가 있어서 웜업을 적용 후 해결했는지

예상치 못한 병목 구간을 발견하고 진짜 원인을 찾기 위한 과정을 생생하게 담아보았습니다. 또한, 서비스를 운영하면서 겪을 수 있는 트러블 슈팅 경험이 궁금하신 분들도 한번 읽어보시면 좋을 것 같습니다.

## 첫 에러 발생

오픈 초기에는 서비스 트래픽이 그렇게 많지 않았고 개발팀은 평상시처럼 신규 피쳐 개발 후 운영 배포를 진행했습니다.

그리고 어느 날, 배포 직후 요청에 대한 응답 속도가 평소와 달리 오래 걸리기 시작하더니 처음 발생하는 에러로그들이 올라오기 시작했습니다.

![갑자기 발생하는 ConnectionTimeout 에러](https://tech.kakaopay.com/_astro/image2_error_log.CHpxE5Uk_Z2kfKd2.webp)

갑자기 발생하는 ConnectionTimeout 에러

```plaintext
JDBCConnectionException (Unable to acquire JDBC Connection [HikariPool-1 - Connection is not available, request timed out after 10007ms.] [n/a]) from org.hibernate.exception.internal.SQLExceptionTypeDelegate in convert at line 49
```

### 갑작스러운 Connection Timeout의 등장

해당 로그를 살펴보니 HikariCP에서 커넥션 요청 시 발생하는 타임아웃이었습니다. 실제로 발생하는 위치는 `getConnection()` 이었으며 전체 코드는 다음과 같습니다.

```java
HikariPool.java

 /**
 * Get a connection from the pool, or timeout after the specified number of milliseconds.
 *
 * @param hardTimeout the maximum time to wait for a connection from the pool
 * @return a java.sql.Connection instance
 * @throws SQLException thrown if a timeout occurs trying to obtain a connection
 */
public Connection getConnection(final long hardTimeout) throws SQLException
{
   suspendResumeLock.acquire();
   final var startTime = currentTime();

   try {
      var timeout = hardTimeout;
      do {
         var poolEntry = connectionBag.borrow(timeout, MILLISECONDS);
         if (poolEntry == null) {
            break; // We timed out... break and throw exception
         }

         final var now = currentTime();
         if (poolEntry.isMarkedEvicted() || (elapsedMillis(poolEntry.lastAccessed, now) > aliveBypassWindowMs && isConnectionDead(poolEntry.connection))) {
            closeConnection(poolEntry, poolEntry.isMarkedEvicted() ? EVICTED_CONNECTION_MESSAGE : DEAD_CONNECTION_MESSAGE);
            timeout = hardTimeout - elapsedMillis(startTime);
         }
         else {
            metricsTracker.recordBorrowStats(poolEntry, startTime);
            return poolEntry.createProxyConnection(leakTaskFactory.schedule(poolEntry));
         }
      } while (timeout > 0L);

      metricsTracker.recordBorrowTimeoutStats(startTime);
      throw createTimeoutException(startTime);
   }
   catch (InterruptedException e) {
      Thread.currentThread().interrupt();
      throw new SQLException(poolName + " - Interrupted during connection acquisition", e);
   }
   finally {
      suspendResumeLock.release();
   }
}
```

그리고 TimeoutException을 발생시키는 메서드는 `throw createTimeoutException(startTime)`이었고, 전체 코드는 다음과 같습니다.

```java
/**
    * Create a timeout exception (specifically, {@link SQLTransientConnectionException}) to be thrown, because a
    * timeout occurred when trying to acquire a Connection from the pool.  If there was an underlying cause for the
    * timeout, e.g. a SQLException thrown by the driver while trying to create a new Connection, then use the
    * SQL State from that exception as our own and additionally set that exception as the "next" SQLException inside
    * of our exception.
    *
    * As a side-effect, log the timeout failure at DEBUG, and record the timeout failure in the metrics tracker.
    *
    * @param startTime the start time (timestamp) of the acquisition attempt
    * @return a SQLException to be thrown from {@link #getConnection()}
    */
   private SQLException createTimeoutException(long startTime)
   {
      logPoolState("Timeout failure ");
      metricsTracker.recordConnectionTimeout();

      String sqlState = null;
      final var originalException = getLastConnectionFailure();
      if (originalException instanceof SQLException) {
         sqlState = ((SQLException) originalException).getSQLState();
      }
      final var connectionException = new SQLTransientConnectionException(poolName + " - Connection is not available, request timed out after " + elapsedMillis(startTime) + "ms.", sqlState, originalException);
      if (originalException instanceof SQLException) {
         connectionException.setNextException((SQLException) originalException);
      }

      return connectionException;
   }
```

HikariCP의 getConnection 메서드 내부를 간략히 살펴보면,

1. `connectionBag.borrow(...)`를 통해 커넥션을 빌려오려 시도합니다.
2. 만약 설정된 connectionTimeout 시간 안에 커넥션을 얻지 못하면
3. `createTimeoutException` 메서드를 호출해 우리가 로그에서 봤던 바로 그 예외를 발생시킵니다.

즉, 사용자의 요청을 받은 스레드가 커넥션 풀에서 커넥션을 획득하려 시도하지만, 우리가 설정한 타임아웃만큼 대기하다가 획득 실패 후 타임아웃이 발생하는 것입니다.

해당 에러를 인지한 후, 첫 번째로 접근한 포인트는 HikariCP 옵션을 바꿔보는 것이었습니다.

1. 커넥션 획득에 실패하여 connectionTimeout 에러가 발생했고
2. 굿딜 서버에 유입되는 트래픽이 초기 오픈했을 때보다 증가했지만
3. 그에 반해 yml에 설정하는 spring.datasource.hikari 옵션을 우리 서비스에 맞게 맞춤 설정하지 않고 사용하고 있었기 때문입니다.

당시 팀의 생각은 다음과 같았습니다.

> 커넥션 풀이 부족한 건가? 커넥션에 여유가 생기면 획득하려 대기하는 시간도 없어질 테니 자연스럽게 초기 응답 속도 지연도 해결되지 않을까?

## #1 커넥션 풀 에러 로그 원인 해결을 위한 HikariCP 커넥션 옵션 수정

### 우리 시스템의 특성을 고려한 옵션 변경

다음과 같이 3개의 hikariCP 옵션에 대해 알아보고 가장 큰 의심 포인트였던 커넥션 풀 사이즈에 대한 검토를 진행했습니다.

1. connectionTimeout
2. maximumPoolSize
3. minimumIdle

#### connectionTimeout

```plaintext
This property controls the maximum number of milliseconds that a client (that's you) will wait for a connection from the pool.
If this time is exceeded without a connection becoming available, a SQLException will be thrown.
Lowest acceptable connection timeout is 250 ms. Default: 30000 (30 seconds)
```

`커넥션 풀에서 커넥션을 얻기 위해 대기하는 최대 시간`을 의미합니다. 해당 시점에 적용된 커넥션 타임아웃은 10s였습니다.

- 위 에러 로그에서도 최대 10000ms까지 대기하다가 예외가 발생하는 것을 확인할 수 있었습니다.

#### maximumPoolSize

```plaintext
This property controls the maximum size that the pool is allowed to reach, including both idle and in-use connections.
Basically this value will determine the maximum number of actual connections to the database backend.
A reasonable value for this is best determined by your execution environment.
When the pool reaches this size, and no idle connections are available, calls to getConnection() will block for up to connectionTimeout milliseconds before timing out.
Please read about pool sizing. Default: 10
```

`커넥션 풀의 최대 커넥션 개수`를 의미합니다.

해당 시점에 적용된 `maximumPoolSize`는 처음 프로젝트 세팅 시 설정되어 있던 30개가 적용되어 있었습니다. 또한, `connectionTimeout`이 발생했던 순간을 hikariCP 메트릭으로 확인해 본 결과, 30개 connection 모두 `Active` 상태인 점을 확인할 수 있었습니다.

배포 직후 최대 개수만큼 모든 커넥션이 사용되어 idle한 Connection 부족 현상을 막아보고자 최대 개수를 50개로 늘리기로 합니다.

늘렸음에도 불구하고, 만약 해당 현상이 반복된다면 단순히 커넥션 풀 사이즈 부족으로 인해 발생한 문제가 아닐 것이라 생각했습니다.

> 1. 팀에서 운영하고 있는 데이터베이스 서버와 커넥션을 맺는 서버는 해당 서버뿐만 아니라 다른 애플리케이션 서버들이 존재했습니다.
> 	모든 서버의 커넥션 풀 사이즈와 각 서버의 레플리카 개수, 배포 시 일시적으로 증가하는 수 등을 고려하여 `(운영하고 있는 애플리케이션 서버 x 각 서버 당 최대 레플리카 수 x 서버 당 점유하는 커넥션 개수 < 사용하고 있는 MySQL의 max_connections)`와 같이 데이터베이스 서버의 최대 커넥션 수를 넘지 않도록 계산하는 과정을 진행했습니다.

> 2. [HikariCP wiki](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing) 를 확인하면, `커넥션 풀 사이즈 계산`에 대한 팁을 확인할 수 있습니다.
> 	해당 공식을 통해 대략적으로 계산해 보면, 커넥션 풀이 남아야 정상이기도 하고 평상시에도 훨씬 적은 커넥션으로도 운영이 가능했지만 풀 사이즈를 증가해도 해당 현상이 반복되는지 확인을 위해 증설했습니다. 커넥션 풀 사이즈가 문제의 핵심 해결 요소라면 각 시스템의 워크로드를 분석해서 풀 사이즈를 계산해 보시는 것도 좋은 방법입니다.

#### minimumIdle

```plaintext
This property controls the minimum number of idle connections that HikariCP tries to maintain in the pool.
If the idle connections dip below this value and total connections in the pool are less than maximumPoolSize, HikariCP will make a best effort to add additional connections quickly and efficiently.
However, for maximum performance and responsiveness to spike demands, we recommend not setting this value and instead allowing HikariCP to act as a fixed size connection pool.
Default: same as maximumPoolSize
```

`HikariCP가 최소로 유지하려 하는 idle 상태의 커넥션 개수`입니다.

평소에는 최대 개수 모두 사용하지 않고 일정 개수의 커넥션으로도 충분히 요청을 처리하고 있었기에, 혹시 커넥션 풀이 안정화되지 않은 상태에서 요청이 들어옴에 따라 커넥션 부족 문제로 타임아웃이 발생하지 않을까 생각하여 최소 개수를 보장하려고 설정한 옵션입니다.

> 당시 의도는 minimumIdle을 통해 `최소로 필요한 유휴 커넥션의 개수`를 보장하려 했습니다. 하지만 [HikariCP 문서](https://github.com/brettwooldridge/HikariCP) 에서 알 수 있듯이, **default는 maximumPoolSize와 동일하며 오히려 설정하지 않는 것** 을 권장합니다.
> `minimumIdle`을 `maximumPoolSize`보다 작게 설정하면, **유휴 커넥션이 `minimumIdle`보다 적어질 때마다 풀이 동적으로 새 커넥션을 맺게 됩니다.** 이 과정에서 오버헤드가 발생하여 오히려 성능에 좋지 않은 영향을 줄 수 있습니다.
> 따라서 이런 이유로 현재 저희 애플리케이션 설정에서도 **해당 옵션을 제거** 하고, `maximumPoolSize`와 동일하게 유지하여 fixed size connection pool처럼 동작하도록 사용하고 있습니다.

최종적으로 적용한 설정 파일은 다음과 같습니다.

```yml
spring:
  datasource:
    hikari:
    ... 생략
      connection-timeout: 10000
      maximum-pool-size: 50
      minimum-idle: 20
```

#### HikariCP 옵션 변경 후 결과 확인

1. 해결되지 않는 타임아웃 에러
![10s 이후 올라오는 에러 알림](https://tech.kakaopay.com/_astro/image5_error_log.DVZj3T3o_Zxhr8F.webp)

10s 이후 올라오는 에러 알림

여전히 10초 내에 커넥션을 획득하지 못하고 타임아웃이 발생하기 시작했습니다.

2. 모니터링 지표
![여전히 발생하는 응답 지연](https://tech.kakaopay.com/_astro/image6_matrix.HU0X0ZuP_OWwMT.webp)

여전히 발생하는 응답 지연

배포 직후 새롭게 생성된 파드에 트래픽이 인입되는 순간 기존과 동일하게 응답 지연이 발생했습니다.

3. 그라파나에서 살펴본 connection 관련 지표
![증가하는 active 커넥션 개수](https://tech.kakaopay.com/_astro/image_grafana_connection_active.EWNP1pan_Z2eF16R.webp)

증가하는 active 커넥션 개수

기존과 동일하게 최대 개수까지 모든 커넥션이 사용되었다가, 지연이 잠잠해진 이후엔 사용되는 커넥션 수가 일정 개수로 유지되는 현상이 반복되었습니다. `minimumIdle`을 20으로 세팅했지만, 유휴 커넥션의 개수가 부족해짐에 따라 요청 처리 도중에 최대 개수까지 실시간으로 커넥션을 맺는 현상도 발견할 수 있었습니다. (위 `minimumIdle`에 대한 설명과 동일하게 동작함을 볼 수 있었습니다.)

### 커넥션 타임아웃은 커넥션 문제가 아닐 수도 있다.

처음엔 커넥션 타임아웃 에러 발생으로 커넥션 관련 옵션을 수정해 봤지만 배포 직후 발생하는 지연 현상은 해결하지 못했습니다.

옵션 변경에 대한 결과를 정리해 보면 다음과 같습니다.

1. **배포 직후 모든 커넥션이 사용 상태** 가 된다. 이후 지연이 안정된 후엔 최대 개수보다 적은 개수로도 지연 없이 충분히 트래픽을 받아낸다.
2. 원활히 획득, 반환이 되지 않으니 **다음 요청이 커넥션 획득을 대기하다가 타임아웃이 발생하고 전체적인 응답 속도가 지연된다.**
3. 왜 배포 직후에만 원활하게 커넥션 풀링이 되지 않는가?

여기까지 읽었을 때 여러분들의 생각은 어떤가요? 감을 잡으신 분들도 있고 아직 아리송하신 분들도 있으실 것 같습니다.

커넥션 풀 사이즈를 30개에서 50개로 늘렸음에도 여전히 최대 개수까지 모두 사용되는 패턴이 반복되었습니다. 만약 단순히 커넥션이 부족한 상황이었다면, 풀 사이즈를 늘렸을 때 사용률이 낮아져야 한다고 생각합니다.

하지만 우리의 상황은 달랐습니다.

1. 30개를 설정하면 30개 모두 사용
2. 50개로 늘리면 50개 모두 사용
3. 하지만 안정화 이후에는 20개 정도만으로도 충분

이를 통해 **커넥션 자체가 부족한 게 아니다** 는 의미로 해석했습니다.

> 커넥션이라는 리소스 자체 문제가 아니라, 생성된 직후 아직 모든 준비가 되지 않은 초기 파드로 들어오는 트래픽 유입량이 문제는 아닐까?
> 초기 인입되는 트래픽 양을 줄여보고 결과를 분석해 보자

이건 단순한 커넥션 풀 이슈가 아닌 내부의 다른 원인이 있을 것이라 생각했고, 트래픽 유입량에 대한 테스트를 해보기로 합니다.

## #2 트래픽 양이 문제일까? 배포 전략 변경을 통한 해결 시도

서비스 오픈 초기에 트래픽이 많지 않았을 때는 해당 문제가 발생하지 않았습니다. 하지만 서비스의 성장과 함께 늘어나는 트래픽에 의해 이 에러가 발생하기 시작했습니다. 즉, 배포 직후 애플리케이션에 쏟아지는 트래픽이 너무 많은 건 아닌가라는 생각이 들었습니다.

기존에 팀에서 사용하고 있던 `롤링 업데이트 배포 방식`은 기존 파드가 받고 있던 일정량의 트래픽을 새로운 파드가 그대로 받게 됩니다.

해당 배포 방식 대신 `블루/그린 배포 방식`을 고도화하여, 새로운 파드 그룹에 트래픽을 30s 간격으로 20%씩 점진적으로 흘려보낼 수 있도록 했습니다.

물론 트래픽의 양을 의도적으로 줄이는 것은 근본적인 해결책이 되진 않을 것이라 예상했습니다. 하지만 배포 직후의 파드에 `일종의 적응 기간`을 주는 것과 같이 트래픽을 일정 비율로 조금씩 흘려보내면 배포 직후 내부에서 어떤 준비를 할 시간을 주고, 문제 현상이 해결되지 않을까?라는 막연한 기대감이기도 했습니다.

새롭게 블루, 그린을 이용한 점진적 배포의 결과는 다음과 같습니다.

![지연이 어느 정도 해소된 것처럼 보였다](https://tech.kakaopay.com/_astro/image8_bluegreen2.9bNqOkEO_ZCRQ7a.webp)

지연이 어느 정도 해소된 것처럼 보였다

기둥이 세워지긴 했지만 그럴듯하게 해결된 것처럼 보였습니다.

우선 배포 시마다 타임아웃 에러가 발생하는 현상은 임시방편으로 해결했으나, 근본적인 원인이 아니었기에 지속적으로 모니터링하며 분석하기로 합니다.

### 이후 다시 발생하는 문제

얼마 지나지 않아 서비스의 성장에 따라 20%씩 흘려보내는 트래픽 자체가 커졌고, 배포 직후의 기둥이 점점 길어지며 재발하기 시작했습니다. 커넥션 타임아웃이 발생할 정도의 지연이 생기진 않았지만, 해당 현상이 발생하는 건 시간문제라고 생각했습니다.

![다시 발생하는 응답 지연](https://tech.kakaopay.com/_astro/image9_delay_bluegreen2.DLnKjc1o_Z1kUGfN.webp)

다시 발생하는 응답 지연

결국 예상한 대로 초기 트래픽을 의도적으로 줄이는 것은 근본적인 해결책이 되지 못했습니다.

그러나 이 배포 전략 변경으로, `일정 수준 이상의 트래픽이 들어오는 구간부터 슬슬 처리량 저하가 발생한다는 것`을 확실히 알게 되었습니다.

### 트래픽 변경 결과 분석을 통한 문제 재정의

처음에 커넥션 풀 관련 옵션 변경 후 정리한 내용에 덧붙이면 다음과 같습니다.

1. **배포 직후 모든 커넥션이 사용 상태** 가 된다. 이후 지연이 안정된 후엔 최대 개수보다 적은 개수로도 지연 없이 충분히 트래픽을 받아낸다.
2. 원활히 획득, 반환이 되지 않으니 **다음 요청이 커넥션 획득을 대기하다가 타임아웃이 발생하고 전체적인 응답 속도가 지연된다.**

위에서 언급했었던 궁금증에 새로운 궁금증이 추가되었습니다.

1. **일정 수준 이상의 트래픽** 이 들어오면 점점 버티지 못하고 응답 속도가 저하되기 시작한다.
2. 그렇다면 버티지 못하는 `병목 지점`은 어디인가?
3. 어떤 성능이 저하됨으로써 커넥션 사용이 밀리고 최종적으로 타임아웃 내에 획득하지 못하는 요청들이 발생하는가?

이제 `커넥션 리소스도, 트래픽`도 이 현상의 근본적인 원인은 아니라는 것을 확인했으니 `응답속도를 저하시키는 병목`을 찾아내기로 방향을 바꿨습니다.

커넥션 관련 에러 로그나 트래픽 인입량 등 여러 단서들이 보여주는 현상에만 집중하지 않고, 좀 더 전체적으로 살펴보기 시작했습니다. 특히 병목을 발생시킬 수 있는 구간별을 확인하기 위해, 본격적으로 관련된 서버 메트릭을 분석하기로 합니다.

## #3 전체적인 서버 메트릭 분석을 통한 “진짜” 병목 구간 찾아보기

### CPU와 메모리 메트릭의 변화

**1\. CPU Usage**

![트래픽이 인입되기 전 증가하는 CPU Usage](https://tech.kakaopay.com/_astro/cpu.C4omOyiJ_Z2sj2xD.webp)

트래픽이 인입되기 전 증가하는 CPU Usage

**2\. Young GC 그래프**

![메모리 사용량 증가에 따른 Young GC](https://tech.kakaopay.com/_astro/young_gc.vnugnRPm_6xj2l.webp)

메모리 사용량 증가에 따른 Young GC

단순히 서버가 가동되면서 여러 가지 일을 하니까 많이 쓰이지 않을까? 하고 넘겼던 메트릭을 다시 살펴보았습니다. 당연하겠지만 배포 직후, CPU 사용량과 메모리 사용량이 증가함을 확인할 수 있었습니다.

### Actuator가 제공하는 HikariCP 메트릭

해당 메트릭을 그라파나 대시보드에서 살펴봤을 때, `배포 직후에만 Connection usage time과 acquire time이 증가하는 구체적인 단서`를 얻을 수 있었습니다.

**1\. 커넥션 사용 시간**

- 배포 직후 지표
	![최대 1~1.5s까지 사용](https://tech.kakaopay.com/_astro/table_before_connection_usage.Dav_Q_Eo_1E2fJs.webp)
	최대 1~1.5s까지 사용
- 평소 안정적인 지표
	![최대 3ms내로 사용](https://tech.kakaopay.com/_astro/table_after_connection_usage.C-_rm7OB_ZARl7Q.webp)
	최대 3ms내로 사용

**2\. 커넥션 획득 시간**

- 배포 직후 지표
	![최대 타임아웃인 10s까지 획득 대기](https://tech.kakaopay.com/_astro/table_before_connection_acquire.3-68FEgQ_1I9Onb.webp)
	최대 타임아웃인 10s까지 획득 대기
- 평소 안정적인 지표
	![최대 1ms 내로 획득](https://tech.kakaopay.com/_astro/table_after_connection_acquire.Cquo8hj7_RvD2o.webp)
	최대 1ms 내로 획득
1. `평소 커넥션 사용 시간 (Connection Usage Time)`은 5ms 이하였지만, 직후의 평균 사용 시간은 1s를 넘어갔고
2. `평소 커넥션 획득 시간 (Connection Acquire Time)` 역시 평균 1ms 이하였지만 5s~10s사이인 것을 확인할 수 있었습니다.

데이터베이스 쿼리 응답 시간은 평소와 동일했으므로, 이는 구체적인 근거를 제시했습니다.

> **커넥션을 획득한 후, 데이터베이스 작업 외에 애플리케이션 내부에서 무언가 무거운 작업을 하고 있다.**

무엇이 커넥션 사용 시간을 증가시켰는지 의문을 가졌습니다.

### 메트릭 분석을 통한 인사이트

이제까지의 과정 및 의문점을 정리해 보면 다음과 같습니다.

1. 커넥션 사이즈를 늘려보기도 하고, 타임아웃을 조절해보기도 했지만 원인 및 해결책이 되지 못했다.
2. 초기 트래픽을 의도적으로 줄이는 것도 임시방편에 불과했다.
3. 그라파나에서 HikariCP 메트릭을 살펴보면, 배포 직후에만 connection usage time과 connection acquire time이 늘어났고 전체적인 서버의 처리량 저하로 이어졌다.
4. **이 모든 현상은 배포 직후에만 발생한다.** 그리고 배포 직후에 서버 메트릭을 살펴보면 cpu와 memory의 사용량이 높아진다.

평소에는 5ms 이내에 커넥션을 사용하고 반환하던 애플리케이션이, 배포 직후에만 초 단위로 걸리는 이유는 무엇일까요?

네트워크 I/O 포함한 데이터베이스 쿼리 응답 시간은 변함이 없었기에, **커넥션을 점유하고 있는 동안 동작하는 추가적인 작업은 무엇인가** 는 결론에 도달했습니다.

> 평소에는 거뜬히 처리하던 서버가 `왜 배포 직후에는 처리량이 저하되는가`
> 도대체 `배포 직후의 우리 애플리케이션 내부에서는 무슨 일이 벌어지길래 CPU 사용량 및 GC가 활발해지면서 커넥션 점유 시간이 길어지는가`?

## #4 배포 직후 무슨 일이 일어나는가?

외부 요인이 아닌, 애플리케이션 동작 내부를 살펴보기로 합니다. 그중, 우리가 작성한 코드가 실행되는 공간인 자바 가상 머신 (JVM)에서 구동 직후에 무슨 일이 일어나는지부터 확인했습니다.

굿딜 서버는 JVM 기반 언어인 코틀린으로 개발되었습니다. 코틀린 언어 역시, 코틀린 컴파일러에 의해 자바 바이트코드로 컴파일되고 이후 자바 언어와 동일하게 동작되기 때문에 자바 언어 기준으로 설명해 보겠습니다.

### JVM의 동작 방식에 대해서

JVM 기반 애플리케이션을 개발하거나 공부한 경험이 있으시면, 한 번씩 다 들어보셨을 내용입니다.

![자바 언어의 컴파일 및 실행 과정](https://tech.kakaopay.com/_astro/java_compile.Do0-B1_H_17vvMd.webp)

자바 언어의 컴파일 및 실행 과정

애플리케이션이 가동 시 우리가 작성한.java 파일이 javac 컴파일러에 의해 jvm이 읽을 수 있는.class 바이트코드 컴파일됩니다. 이후 클래스 로딩 과정에서 필요한.class 파일이 로딩 -> 링킹 -> 초기화의 과정을 거쳐 메서드 영역에 저장되고 실행 엔진에 의해 인터프리터 방식으로 진행될 경우 명령어를 하나씩 읽고 해석하며 실행됩니다.

그리고 **이 과정은 모두 애플리케이션이 시작할 때 진행됩니다.** 이렇게 `런타임에 동적 로딩과 동적 링킹`되어 실제 구현 클래스 결정을 실행될 때까지 미룸에 따라, 높은 확장성과 유연성을 가져갈 수 있는 특징이 있기도 합니다.

### 원인은 동적 로딩?

방금 언급한 `동적 로딩으로 인해서 클래스 로딩은 실제 해당 클래스가 사용되기 전까지 로딩되지 않는 지연 로딩`으로 동작합니다. 즉, 애플리케이션이 실행되면서 **실제로 해당 클래스가 최초로 사용되는 시점에 해당 클래스가 JVM에 로딩** 되는 것입니다.

그리고 이 동적 로딩의 과정으로 인해서, `사용자의 요청이 들어온 직후에` 로딩되지 않은 클래스들의 **추가 로딩 과정** 이 시작됩니다.

#### 성능 저하 원인

우리가 찾는 병목 지점은 `초기 성능 저하의 원인을 유발하는 지연 로딩 과정`이라고 판단했습니다. 배포 직후의 요청이 느릴 수밖에 없는 이유는

- 애플리케이션이 요청을 처리하는 동시에 백그라운드에서 수많은 클래스를 로딩하는 작업을 동시에 하고 있었기 때문입니다.
![](https://tech.kakaopay.com/_astro/before_warmup.pHKyLl7j_14XRh1.webp)

따라서 사용자의 요청이 들어오기 전에, 우리가 미리 필요한 클래스들을 로딩을 해주는 **JVM 웜업 작업** 을 진행해 보기로 합니다.

웜업을 적용하며 기대했던 점은 다음과 같았습니다.

1. 실제 요청이 들어오기 전 미리 로딩을 모두 해두면 위에서 언급했던 “왜 배포 직후에만 지연이 일어나는가?”에서의 `배포 직후`라는 요인을 없앨 수 있을 것이다.
2. 그렇다면 로딩이 완료된 서버는 `평상시처럼 트래픽을 거뜬히 받아내는 서버의 퍼포먼스`를 보여줄 것이다.
3. 지표 또한 애플리케이션 실행 후 웜업 시에 일시적으로 급증했다가 평소와 같은 안정적인 그래프를 그릴 것이다.

## JVM 웜업 적용해보기

### 우리 서비스에서의 웜업

현재 굿딜 서비스에서는 클래스 로딩 웜업 정도로도 충분히 효과가 있을 것이라 예상되어 `가장 호출량이 많은 API의 핵심 로직을 의도적으로 호출시켜주도록 웜업`을 적용했습니다.

### 웜업이 적용된 배포 파이프라인

![startUpProbe를 추가한 파이프라인](https://tech.kakaopay.com/_astro/deploy_pipeline.PiL9Jy89_qj2nv.webp)

startUpProbe를 추가한 파이프라인

현재 팀에서 적용 중인 K8s 기반 배포 파이프라인에서는 `liveness probe`와 `readiness probe`를 체크 후, 서버에서 `200 ok 응답 시` 유저 트래픽이 인입되기 시작했습니다.

따라서 `startUpProbe` 단계를 추가하여 `웜업 완료 여부`를 체크하도록 함으로써, 애플리케이션의 웜업이 완료된 후 유저 트래픽이 들어올 수 있도록 했습니다.

startupProbe 단계에서 웜업이 모두 완료될 때까지 liveness probe와 readiness probe는 비활성화되며 모든 단계가 완료된 이후에 트래픽이 들어옴으로써 안정적으로 웜업이 동작하도록 적용했습니다.

> [kubernetes probe](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/) 관련하여 간단히 설명하면 다음과 같습니다.
> **Startup Probe**: 컨테이너 내 애플리케이션이 완전히 기동되었는지 확인하여 성공 전까진 다른 모든 프로브를 비활성화하여 불필요한 재시작을 방지합니다.
> **Liveness Probe**: 컨테이너가 살아서 정상 동작 중인지 확인하며, 주기적으로 호출 후 응답이 없으면 재시작됩니다.
> **Readiness Probe**: 컨테이너가 실제 유저 트래픽을 받을 준비가 되었는지 확인하며, 실패 시 서버 LB 그룹에서 제외될 수 있습니다.

### 웜업을 적용해 보기

애플리케이션이 실행된 후, 웜업 코드를 실행하기 위해 ApplicationRunner를 사용했습니다. ApplicationRunner는 스프링 애플리케이션이 구동된 후 실행되어야 하는 빈을 정의할 수 있는 인터페이스이고, 해당 인터페이스를 구현하여 웜업 로직을 작성했습니다.

그리고 startupProbe 단계에서 호출될 `GET /api/warmup API`를 신규 개발하여 웜업 완료 여부 플래그를 반환하도록 했습니다.

```kotlin
/**
 * 실제 웜업이 동작하는 ApplicationRunner 구현 클래스
 */

@Component
class WarmupApplicationRunner(
    private val repeatCount: Int,
    private val brandService: BrandService
): ApplicationRunner {

    private var isCompleted = false

    override fun run(args: ApplicationArguments) {

            log.info { "WarmUpApplicationRunner Start - repeatCount : $repeatCount" }

            for (i in 0 until repeatCount) {

               /**
               * 웜업하고자 하는 로직을 실행합니다.
               * 배포 직후 가장 많이 호출되는 로직을 사용자의 요청이 들어오기 전 미리 호출하여 준비해 둡니다.
               */
               brandService.findActiveBrandList();
               brandService.findRecommendBrandList();
            }

            this.isCompleted = true

            log.info { "WarmUpApplicationRunner End" }
        }

    fun isCompleted(): Boolean {
        return isCompleted
    }
}
```

웜업의 대상은 애플리케이션이 가동 후 실제 트래픽이 인입되기 전, `성능 향상을 위해 혹은 비교적 오래 걸리는 무거운 작업을 미리 준비해 두는 것` 모두 해당된다고 생각합니다.

- 위에서 언급한 클래스 로딩이 될 수 있고, 실제 요청이 호출되고 나서야 커넥션을 맺는 client일 경우 ping을 날림으로써 미리 커넥션을 맺어둘 수도 있습니다. (ex HTTP Client의 connection pool, Redis client 등)

굿딜의 웜업은 배포 직후 쏟아지는 트래픽 중 비율을 가장 많이 차지하는 굿딜의 전체 브랜드 조회 로직 및 추천 브랜드 조회 로직을 호출했습니다. 해당 로직은 캐싱되는 로직은 없었고, 단순히 DB에 쿼리 조회 후 데이터를 조합하여 응답하는 로직이었습니다.

### 적용 후

웜업을 적용한 후 그래프입니다.

![평평해진 그래프](https://tech.kakaopay.com/_astro/image13_after_warmup.Bp4KxkNE_Z2f37ek.webp)

평평해진 그래프

배포 직후 사용자의 요청이 들어와도 초기 지연 없이 응답하는 것을 확인할 수 있었습니다. 이슈가 발생할 때보다 트래픽이 더 늘어났음에도 불구하고 더 안정적이었습니다.

또한, 위에서 언급했던 메트릭들도 이상이 없는지 확인해 봤습니다.

**1\. connection usage time**

![배포 직후 Connection Usage Time](https://tech.kakaopay.com/_astro/image10_connection_usage_time.BdukKURq_ZfLQSg.webp)

배포 직후 Connection Usage Time

웜업 코드가 동작하는 타이밍에 커넥션 usage time을 확인할 수 있었고, 실제 유저의 요청이 들어오는 경우엔 2ms 내에서 안정적으로 유지했습니다.

**2\. connection acquire time**

![배포 직후 Connection Acquire Time](https://tech.kakaopay.com/_astro/image11_connection_acquire_time.DQLZ9RuD_1oggYA.webp)

배포 직후 Connection Acquire Time

usage time과 마찬가지로, connection pooling의 병목이 사라졌기에 원활히 획득하는 것을 볼 수 있었습니다.

**3\. HikariCP connection pool**

![](https://tech.kakaopay.com/_astro/image12_connection_metric-1.BLjXuaqz_1LyJW9.webp)

커넥션 개수는 max로 고정이었지만 커넥션들의 상태가 active하지 않고 사용량이 원활한 것을 볼 수 있었습니다.

**4\. response time**

![](https://tech.kakaopay.com/_astro/image14_after_warmup_response.DtVumsCH_ZBdDj7.webp)

api 응답 속도 역시 평소와 같이 안정적으로 받아내고 있었습니다.

### 모든 현상이 해석 가능해진 확실한 원인

#### 왜 커넥션 풀타임아웃 에러였을까?

우리가 기대했던 것은 사용자 요청 처리를 빠르고 원활하게 응답하는 것이었지만

1. 실제로 내부에서는 요청 처리뿐만 아니라 `클래스 로딩을 위해 추가적인 작업`이 필요했고
2. `커넥션을 점유한 상태`로 해당 과정들이 진행되며 최종적으로 예상치 못한 connection timeout이 발생한 것이었습니다.

#### 왜 배포 직후에만 응답 지연 현상이 발생했을까?

배포 직후에만 응답에 지연이 발생했는지 설명이 가능했습니다.

1. 평소에 5ms 안으로 커넥션을 사용 후 반환하는 경우, 외부 요인 고려하지 않은 단순 계산 시 하나의 커넥션이 초당 대략 150~200개의 요청을 거뜬하게 받아낼 수 있습니다.
2. 하지만 `커넥션 사용의 병목`이 생겨 시간이 조금만 늘어나도 `처리량이 급격하게 떨어지며` 수초 안에 커넥션이 모두 고갈되며 `이후 요청들이 대기`하기 시작했던 것입니다.

## 웜업에 대한 추가적인 궁금증

웜업을 통해 해당 이슈를 해결했지만 `실제로 어떤 클래스들이 지연 로딩되며 지연을 일으켰을까?` 라는 궁금증이 남아있었고, 실제로 클래스 로딩 과정을 볼 수 있는지 방법을 찾아봤습니다.

### 클래스 로딩 로그 확인

웜업의 필요성을 어렴풋이 이해했을 때는 개발자가 직접 작성한 클래스들을 제외하고, 서버 시작을 위한 프레임워크 레벨의 클래스들만 사용될 테니 로딩된다고 생각했습니다. 그리고 그 클래스들이 모두 웜업 대상이라고 생각했고, 웜업을 어느 범위까지 해줘야 할지 고민이 들기도 했습니다.

하지만 스프링의 동작 방식을 생각해 보면, `@Component 어노테이션을 붙인 클래스들은 모두 스프링의 빈 컨테이너에서 싱글톤 인스턴스화되어 관리`가 됩니다. 즉, 해당 클래스들은 모두 최초 요청이 들어오기 전에 참조가 되므로 웜업 대상이 아니라고 판단했습니다.

그러면 **어떤 클래스는 로딩이 되고, 어떤 클래스가 지연 로딩됨에 따라 우리 애플리케이션의 초기 성능을 저하시키는 걸까요?**

웜업을 적용하기 전, 어떤 클래스들을 웜업해줘야 하는지 직접 로그로 확인해 보기로 합니다.

```plaintext
-Xlog:class+load=info:file=classloading.log
```

위 VM 옵션을 통해 발생하는 클래스 로딩 로그를 살펴봤습니다.

클래스 로딩되는 전 과정이 파일에 남다 보니, 엄청나게 많은 라인의 로그가 찍혀서 살펴보던 중 흐름을 파악할 수 있는 클래스들을 위주로 정리해 보았습니다. (하위 패키지명이나 source는 제거했습니다.)

#### 1\. 애플리케이션 스타트 후 기본으로 로딩되는 클래스들

0 ~ 26s동안 실행될 때 로그에 가장 먼저 찍힌 건, `JVM 실행에 필수적인 핵심 Java 클래스들이 부트스트랩 클래스 로더에 의해 로딩되는 것`을 확인할 수 있었습니다. 우리가 너무나 잘 아는 Object 클래스부터 String, ClassLoader, Exception 등 최상위 클래스들이 보입니다.

```plaintext
[0.028s][info][class,load] java.lang.Object source: shared objects file
[0.029s][info][class,load] java.io.Serializable source: shared objects file
...
[0.029s][info][class,load] java.lang.String source: shared objects file
...
[0.029s][info][class,load] java.lang.Class source: shared objects file
[0.029s][info][class,load] java.lang.ClassLoader source: shared objects file
[0.029s][info][class,load] java.lang.System source: shared objects file
[0.029s][info][class,load] java.lang.Throwable source: shared objects file
[0.029s][info][class,load] java.lang.Error source: shared objects file
...
[0.029s][info][class,load] java.lang.Exception source: shared objects file
[0.029s][info][class,load] java.lang.RuntimeException source: shared objects file

....
```

이후 애플리케이션 콘텍스트 초기화를 위해 main 메서드가 실행되고, 뒤이어 초기화하기 위한 클래스들이 로딩되는 것을 확인할 수 있었습니다. xxxApplication.run()을 기점으로 수많은 스프링 관련 클래스 및 내장 웹 서버인 톰캣 관련 클래스를 살펴볼 수 있었습니다.

```plaintext
[0.728s][info][class,load] org.springframework.boot.SpringApplication source:

[0.737s][info][class,load] org.springframework.context.ApplicationContext source:

[0.839s][info][class,load] com.kakaopay.xxx.yyy.CustomApplication source:

[0.840s][info][class,load] org.springframework.boot.ApplicationContextFactory source:
[0.840s][info][class,load] org.springframework.boot.DefaultApplicationContextFactory source:
[0.840s][info][class,load] org.springframework.context.Lifecycle source:
[0.840s][info][class,load] org.springframework.context.ConfigurableApplicationContext source:

[0.854s][info][class,load] jakarta.servlet.http.HttpServlet source:
[0.854s][info][class,load] org.springframework.web.servlet.HttpServletBean source:
[0.854s][info][class,load] org.springframework.web.servlet.FrameworkServlet source:
[0.854s][info][class,load] org.springframework.web.servlet.DispatcherServlet source:

[1.768s][info][class,load] org.springframework.web.context.support.GenericWebApplicationContext source:
[1.768s][info][class,load] org.springframework.boot.web.servlet.context.ServletWebServerApplicationContext source:
[1.768s][info][class,load] org.springframework.boot.web.servlet.context.AnnotationConfigServletWebServerApplicationContext source:

[7.135s][info][class,load] org.apache.catalina.startup.Tomcat source:
```

또한 이 시점에 `개발자가 작성한 Controller, Service, Configuration, repository, client 등 클래스들이 빈으로 등록되기 위해 모두 초기화되는 것`을 확인할 수 있었습니다. 빈으로 등록되지 않고 순수 코틀린으로 작성된 util 클래스 중 한 번도 호출되지 않은 클래스들은 로딩이 되지 않는 것을 볼 수 있었습니다.

```plaintext
[7.152s][info][class,load] com.kakaopay.xxx.yyy.service.CustomService source:
[7.160s][info][class,load] com.kakaopay.xxx.yyy.controller.CustomController source:
[7.161s][info][class,load] com.kakaopay.xxx.yyy.logger.CustomLogger source:
[7.162s][info][class,load] com.kakaopay.xxx.yyy.config.CustomConfig source:
[7.162s][info][class,load] com.kakaopay.xxx.yyy.config.CustomConfig source:
[7.232s][info][class,load] com.kakaopay.xxx.yyy.client.CustomClient source:
```

#### 2\. /api/ping 호출

39 ~ 40s는 http 요청만을 위해 /api/ping을 호출한 후의 로그입니다.

이 시점에 로딩되는 클래스들부터는 모두 `외부 요청이 들어온 이후에 초기화되는 클래스`라고 판단할 수 있었습니다. 실제 운영 배포 파이프라인 내부 k8s probe 단계에서 호출되는 ping api였기에 웜업을 적용하기 전에도 여기까지는 로딩이 되었을 것이라고 추측합니다.

Tomcat 웹 서버의 요청 처리를 위한 coyote, catalina 관련 나머지 클래스들을 볼 수 있었고

```plaintext
[39.685s][info][class,load] org.apache.tomcat.util.net.SocketBufferHandler source:
[39.696s][info][class,load] org.apache.coyote.http11.Http11Processor source:
[39.697s][info][class,load] org.apache.coyote.InputBuffer source:
[39.697s][info][class,load] org.apache.coyote.OutputBuffer source:
[39.728s][info][class,load] org.apache.catalina.connector.InputBuffer source:
```

Spring의 HTTP 요청 / 응답 처리를 위한 클래스들도 요청 후 로딩되는 것을 확인할 수 있었습니다.

```plaintext
[40.147s][info][class,load] org.springframework.web.context.request.ServletWebRequest source:
```

#### 3\. 실제 서비스에서 사용되는 api 호출

58s부터는 실제 사용자의 요청이 들어오듯이, 유저의 요청으로 호출되는 api의 실행 결과입니다. 즉, **실제로 유저의 요청 이후 지연 로딩되는 웜업의 원인이 되는 클래스들** 이라고 볼 수 있습니다.

`사용자 요청을 처리하기 위한 jackson, spring web 관련 클래스와 개발자가 작성한 custom util 클래스`도 이제야 로딩이 되는 걸 확인할 수 있었습니다. 그리고 실제 데이터베이스에 쿼리를 날리기 위한 `JPA, jdbc, QueryDSL, Spring Data JPA, Transaction 관련 나머지 클래스`도 초기화되었습니다.

이 로그들은 테스트 환경이었지만 약 59s부터 62~63s까지 찍혔으니 수 초가 걸리는 작업이었습니다.

```plaintext
[58.894s][info][class,load] com.fasterxml.jackson.databind.deser.std.BaseNodeDeserializer source:

[58.948s][info][class,load] org.springframework.web.bind.annotation.PathVariable source:
[58.948s][info][class,load] org.springframework.web.bind.annotation.MatrixVariable source:
[58.948s][info][class,load] org.springframework.web.bind.annotation.RequestBody source:
[58.949s][info][class,load] org.springframework.web.bind.annotation.RequestHeader source:
[58.949s][info][class,load] org.springframework.http.RequestEntity source:

[59.004s][info][class,load] com.kakaopay.xxx.model.CustomRequestHeader source:

[59.023s][info][class,load] org.springframework.transaction.interceptor.TransactionInterceptor$1 source:
[59.027s][info][class,load] org.springframework.orm.jpa.EntityManagerHolder source:
[59.041s][info][class,load] org.springframework.jdbc.datasource.DataSourceUtils source:
[59.119s][info][class,load] org.springframework.data.jpa.repository.EntityGraph source:
[59.135s][info][class,load] com.querydsl.core.JoinExpression source:
[59.141s][info][class,load] com.querydsl.core.group.GroupBy source:
```

결국, 실제 HTTP 요청을 처리하고 DB와 통신하는 데 필요한 수많은 라이브러리 클래스들은 첫 요청이 들어왔을 때 비로소 로딩되고 있었습니다.

이렇게 로그를 통해, **실제로 첫 요청 후 클래스들이 늦게 로딩이 됨으로써 초기 처리량에 영향을 끼치는 근본 원인임을 확인할 수 있었습니다**.

1. 커넥션 획득 후, orm 및 쿼리 관련된 클래스들이 `커넥션을 점유한 상태로 로딩되면서 사용 시간이 길어졌을 것이고`
2. 커넥션을 빠르게 사용하고 반환하며 풀 내의 리소스가 순환이 되어야 했지만 `요청 당 커넥션 사용 시간을 평소보다 훨씬 많이 쓰면서 모든 커넥션은 고갈이 되었던 것입니다.`
3. 이후 사용자의 요청을 받은 스레드들은 커넥션 풀에 커넥션 획득을 호출했지만, 사용 가능한 커넥션이 없으므로 대기하다 `타임아웃 에러`가 발생한 것입니다.

### (참고) 웜업을 적용하는 두 가지 목표

JVM 웜업의 목표는 크게 두 가지가 있다고 생각합니다.

1. 위에서 언급한 **아직 로딩되지 않은 클래스들을 의도적으로 로딩시키는 것** 혹은 **외부 커넥션 등 부가적인 작업을 미리 해두는 것**
2. JVM 기반 애플리케이션의 실행 성능 향상을 위한 **JIT 컴파일링**

저희 팀은 1번 목표에 집중하여 웜업을 적용했고, 초기 지연을 해결하는 데 충분한 효과를 볼 수 있었습니다.

다만, 더 높은 성능이 필요한 환경을 위해 `두 번째 목표인 JIT(Just-In-Time) 컴파일러`에 대해서도 간략히 덧붙여 봅니다.

JVM은 우리가 작성한 자바 코드가 컴파일러에 의해 바이트 코드로 컴파일되는데 이 바이트 코드는 JVM이 해석할 수 있는 플랫폼 중립 바이트 코드입니다. 즉, JVM이 읽을 수 있는 바이트 코드가 런타임 시 인터프리터가 한 줄씩 읽어 해석하고 실행되는 구조입니다.

만약 `훨씬 더 큰 규모의 트래픽과 빠른 응답속도`가 요구된다면, JIT 컴파일러를 통해 바이트 코드를 아예 네이티브 기계어로 컴파일하여 애플리케이션 성능이 더욱 향상할 수 있습니다. 이때 JIT 컴파일러는 `런타임에 자주 호출되는 메서드(Hot Spot)`를 식별하여, `Code Cache라는 메모리 영역`에 네이티브 기계어를 저장합니다. 우리가 흔히 사용하는 JVM을 HotSpot VM이라고 불리는 이유기도 합니다.

이 컴파일 과정은 여러 단계 (Level 0~4의 Tiered Compilation)로 이루어지며, 특정 메서드의 호출 횟수나 루프 반복 횟수가 내부적으로 설정한 임계값 (Threshold)를 넘을 때마다 더 높은 수준의 최적화가 적용됩니다.

```plaintext
java -XX:+PrintFlagsFinal -version | grep Threshold

     intx Tier2BackEdgeThreshold                   = 0                                         {product} {default}
     intx Tier2CompileThreshold                    = 0                                         {product} {default}
     intx Tier3BackEdgeThreshold                   = 60000                                     {product} {default}
     intx Tier3CompileThreshold                    = 2000                                      {product} {default}
     intx Tier3InvocationThreshold                 = 200                                       {product} {default}
     intx Tier3MinInvocationThreshold              = 100                                       {product} {default}
     intx Tier4BackEdgeThreshold                   = 40000                                     {product} {default}
     intx Tier4CompileThreshold                    = 15000                                     {product} {default}
     intx Tier4InvocationThreshold                 = 5000                                      {product} {default}
     intx Tier4MinInvocationThreshold              = 600                                       {product} {default}
```

위 명령어를 통해 사용하고 있는 JVM의 Threshold를 확인해 볼 수 있으며, 그중 Tier CompileThreshold라는 이름을 가진 변수를 통해 임계값을 확인할 수 있습니다.

따라서 `이번 이슈를 위해 적용한 단순히 몇 번의 웜업 반복`만으로는 배포 직후에 가장 높은 수준의 최적화 (Level 4)까지 도달하기 어려웠을 것이지만 클래스 로딩을 유도하는 것만으로도 배포 지연을 막을 수 있었습니다. (이후 일정 시간 실제 유저 트래픽을 받으며 자연스럽게 최적화 임계치를 넘어서게 된 애플리케이션은 모든 최적화가 완료된 상태에 도달했을 것이라 예상합니다.)

단순한 응답 지연을 넘어 더 많은 성능 향상이 필요하시다면 이 임계값을 고려한 충분한 반복 횟수의 웜업을 수행하거나, 아예 빌드 시점에 네이티브 코드로 미리 컴파일하는 GraalVM Native Image 같은 AOT(Ahead Of Time) 기술도 고려해 볼 수 있습니다.

## 마치며

이미 서비스 운영 경험이 있으신 분들은 배포 이후 초기 응답 지연에 대한 해결책으로 바로 JVM 웜업을 떠올리셨을 수도 있습니다. 지금 돌이켜보면 당연한 해결책이었을지 몰라도, 당시에는 `HikariCP 커넥션 타임아웃 에러 로그에서부터 JVM 웜업`이라는 해결 방안을 도출해 내기까지 많은 시행착오를 겪었던 것 같습니다.

이 글을 작성하며 이전 타임라인을 정리해 보니 그때 이렇게 접근했으면 더 좋았겠구나 라는 포인트들이 보이기도 합니다. 저 역시 평소에 웜업이라는 키워드를 들어보긴 했지만, 처음 이슈 발생 시에는 Connection Pool 에러 로그에 꽂혀서, 근본적인 원인을 파악하지 못하고 주변만 계속 확인했던 것 같습니다. 발생한 에러 로그는 문제에 대한 원인이 아니고, 증상일 뿐이었습니다.

지금 새로운 이슈를 겪는다면 어떤 메트릭이 이 이슈와 관련 있는가, 서버가 말해주는 지표 기반으로 상황을 조금 더 넓게 판단하고 논리적으로 접근할 것 같습니다.

서비스가 점점 성장하는 가운데, 만약 배포 시에 응답이 지연 현상이 생기기 시작한다면 웜업을 한번 고려해 보시는 것도 좋을 것 같습니다.

긴 글 읽어주셔서 감사합니다.

![eden.bk](https://tech.kakaopay.com/_astro/eden.bk.C33XOWzI_26RteR.webp)

**eden.bk**

카카오페이 굿딜 서비스를 개발하고 있는 에덴입니다. 유저들에게 더 나은 혜택을 제공하기 위해 노력하고 있습니다.
