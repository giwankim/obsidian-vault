---
title: "게임 서버 시스템을 위한 HikariCP 옵션 및 권장 설정"
source: "https://netmarble.engineering/hikaricp-options-optimization-for-game-server/"
author:
  - "[[박정욱]]"
published: 2022-11-09
created: 2026-02-12
description: "HikariCP는 특별히 옵션을 튜닝하지 않더라도 대부분의 개발 및 배포에서 충분한 성능으로 동작합니다. 하지만 게임 서버 시스템을 위한 JDBC와 Timeout 이해하기에서 이야기한 것처럼 WAS 시스템을 위한 HikariCP 권장 설정을 게임 서버 시스템에 그대로 적용... - HikariCP, JDBC, Timeout, TPM실, 게임 서버, 기술분석팀"
tags:
  - "clippings"
---
안녕하세요, 넷마블 TPM실 기술분석팀 박정욱입니다.

HikariCP는 특별히 옵션을 튜닝하지 않더라도 대부분의 개발 및 배포에서 충분한 성능으로 동작합니다.

하지만 [게임 서버 시스템을 위한 JDBC와 Timeout 이해하기](https://netmarble.engineering/jdbc-timeout-for-game-server/) 에서 이야기한 것처럼 WAS 시스템을 위한 HikariCP 권장 설정을 게임 서버 시스템에 그대로 적용할 경우 순간적으로 응답 속도가 떨어지거나 예상치 못한 장애가 발생하는 상황을 겪을 수 있습니다. 이는 게임 서버 시스템이 추구하는 바가 WAS 시스템과 다르기 때문입니다. 즉, 고성능 게임 서버를 위해서는 HikariCP의 설정이 게임 서버 시스템에 맞도록 설정되는 것이 중요합니다.

따라서 본 글에서는 반드시 설정되어야 하거나 고성능 게임 서버를 위해서 튜닝이 필요한 옵션에 대해서 살펴보겠습니다. 본 글에서 다루지 않는 옵션에 대해서는 공식 사이트의 [Configuration](https://github.com/brettwooldridge/HikariCP#gear-configuration-knobs-baby) 을 참고하기 바랍니다.

## dataSourceClassName

HikariCP는 DataSource를 자체적으로 구현한 구현체인 com.zaxxer.hikari.util.DriverDataSource를 기반으로 커넥션 풀을 제공할 뿐만 아니라, DBMS 벤더에서 제공하는 DataSource 구현체를 기반으로도 커넥션 풀을 제공합니다.

dataSourceClassName 옵션은 DBMS 벤더에서 제공하는 DataSource 구현체를 기반으로 커넥션 풀을 사용하고자 하는 경우에 설정하는 옵션입니다. dataSourceClassName 옵션에 적용 가능한 DataSource 구현체 클래스 목록은 공식 사이트의 [Popular DataSource Class Names](https://github.com/brettwooldridge/HikariCP#popular-datasource-class-names) 를 참고하기 바랍니다.

> **주의**: MySQL에서 제공하는 DataSource 구현체의 경우 Network Timeout(Connection Timeout과 Socket Timeout)이 정상적으로 설정되지 않기 때문에 **MySQL을 사용할 경우에는 jdbcUrl 옵션을 사용해야 합니다.**

## jdbcUrl & driverClassName

jdbcUrl 옵션은 com.zaxxer.hikari.util.DriverDataSource를 기반으로 커넥션 풀을 사용하고자 하는 경우에 설정하는 옵션입니다. jdbcUrl 옵션에 적용 가능한 URL 형식 및 연결 속성은 DBMS 벤더별로 다르기 때문에 아래 링크를 참고하기 바랍니다.

- MySQL Connector/J
	- [URL Format](https://dev.mysql.com/doc/connector-j/8.0/en/connector-j-reference-jdbc-url-format.html)
	- [Connection Properties](https://dev.mysql.com/doc/connector-j/8.0/en/connector-j-reference-configuration-properties.html)
- JDBC Driver for SQL Server
	- [URL Format](https://learn.microsoft.com/ko-kr/sql/connect/jdbc/building-the-connection-url?view=sql-server-ver16)
	- [Connection Properties](https://learn.microsoft.com/ko-kr/sql/connect/jdbc/setting-the-connection-properties?view=sql-server-ver16)
- PostgreSQL JDBC Driver
	- [URL Format](https://jdbc.postgresql.org/documentation/use/#connecting-to-the-database)
	- [Connection Properties](https://jdbc.postgresql.org/documentation/use/#connection-parameters)
- Oracle JDBC Driver
	- [URL Format](https://docs.oracle.com/cd/F49540_01/DOC/java.815/a64685/basic1.htm#1006213)
	- [Connection Properties](https://docs.oracle.com/en/database/oracle/oracle-database/21/jajdb/oracle/jdbc/OracleConnection.html)

> **참고**: dataSourceClassName 옵션과 jdbcUrl 옵션을 모두 설정한 경우, HikariCP 내부 구현의 우선순위로 인해 dataSourceClassName 옵션이 적용됩니다.

driverClassName 옵션은 DB와 물리적으로 연결을 맺는 JDBC Driver의 구현체 클래스 이름을 지정하는 옵션입니다. 일부 오래된 JDBC Driver 구현체를 사용할 경우 반드시 driverClassName 옵션을 설정해 줘야 하기 때문에 **driverClassName 옵션은 jdbcUrl 옵션과 함께 항상 명시적으로 설정하기를 권장합니다.**

driverClassName 옵션에 적용 가능한 대표적인 JDBC Driver 구현체들은 다음과 같습니다.

| JDBC Driver Vendor | JDBC Driver Class (Implementation) |
| --- | --- |
| MySQL Connector/J | com.mysql.cj.jdbc.Driver |
| JDBC Driver for SQL Server | com.microsoft.sqlserver.jdbc.SQLServerDriver |
| PostgreSQL JDBC Driver | org.postgresql.Driver |
| Oracle JDBC Driver | oracle.jdbc.driver.OracleDriver |

driverClassName 옵션에 적용 가능한 대표적인 JDBC Driver 구현체별 구현 클래스

## username & password

username, password 옵션은 DB 연결 시 인증에 사용될 사용자 이름, 암호를 지정하는 옵션입니다.

> **참고**: dataSourceProperties를 통해서 사용자 이름, 암호를 설정하는 경우 사용자 이름은 user 속성, 암호는 password 속성을 사용해야 합니다.

## autoCommit

autoCommit 옵션은 풀(Pool)에서 관리하는 커넥션의 기본 Auto-commit 동작을 지정하는 옵션입니다.

대다수의 DBMS는 Auto-commit 트랜잭션 모드와 명시적 트랜잭션 모드를 제공합니다. 하지만 JDBC Driver는 Auto-commit 모드를 통해서 Auto-commit 트랜잭션과 명시적 트랜잭션을 지원합니다. JDBC Driver는 SQL 문 실행 시 Auto-commit 모드가 true면 SQL 문을 Auto-commit 트랜잭션 모드로 실행하고, false면 SQL 문을 명시적 트랜잭션 모드로 실행합니다.

즉, JDBC Driver는 명시적 트랜잭션을 시작하기 위한 BeginTransaction 등의 API를 제공하지 않습니다. 따라서 애플리케이션에서 명시적 트랜잭션을 구현하기 위해서는 Connection.setAutoCommit(false) API를 호출하여 트랜잭션을 시작하고, Connection.commit() API를 호출하여 트랜잭션을 반영해야 합니다.

이러한 이유로 DBMS에서 제공되는 트랜잭션 모드와 동작적으로 일치할 수 있도록 **autoCommit 옵션은 true로 설정하기를 권장합니다** (기본값은 true입니다)**.**

만약 HikariCP의 autoCommit 옵션을 상황과 목적에 맞춰서 true 또는 false를 설정하여 성능을 최적화하고 싶다면 다음을 참고하기 바랍니다.

> 애플리케이션에서 대다수의 비즈니스 로직이 단일 SQL 문(또는 Rollback이 필요 없는 복합 SQL 문)으로 구성된다면 SQL 문의 실행 로직을 구현할 때마다 Connection.setAutoCommit(true) API를 호출하는 것은 비효율적입니다. 이럴 경우 커넥션의 기본 Auto-commit 동작을 true로 변경하여 단일 SQL 문(또는 Rollback이 필요 없는 복합 SQL 문)의 실행 로직을 구현할 때는 Connection.setAutoCommit(true) API를 호출하지 않도록 합니다. 애플리케이션에서 명시적 트랜잭션을 구현할 때만 Connection.setAutoCommit(false) API를 명시적으로 호출하도록 하는 것이 효율적입니다.
>
> 반대로 애플리케이션에서 대다수의 비즈니스 로직이 복합 SQL 문으로 구성된다면 명시적 트랜잭션을 구현할 때마다 Connection.setAutoCommit(false) API를 호출하는 것은 비효율적입니다. 이럴 경우 커넥션의 기본 Auto-commit 동작을 false로 변경하여 명시적 트랜잭션을 구현할 때는 Connection.setAutoCommit(false) API를 호출하지 않도록 합니다. 애플리케이션에서 단일 SQL 문(또는 Rollback이 필요 없는 복합 SQL 문)의 실행 로직을 구현할 때만 Connection.setAutoCommit(true) API를 명시적으로 호출하도록 하는 것이 효율적입니다.

그리고 Auto-commit 모드에서 가장 중요하게 고려해야 하는 부분은 Connection.setAutoCommit() API 호출 최적화입니다. 왜냐하면 다수의 JDBC Driver 구현체들이 Connection.setAutoCommit() API가 호출될 때마다 Auto-commit 설정 쿼리를 DB로 전송하고, DB가 해당 쿼리를 실행하기 때문입니다. 만약 Connection.setAutoCommit() API가 필요 이상으로 많이 호출이 된다면 불필요한 네트워크 트래픽 발생과 DB 부하로 인해 응답 지연이 발생할 수 있습니다. 따라서 **Connection.setAutoCommit() API는 필요한 상황에서만 호출될 수 있도록 최적화하기를 권장합니다.**

대표적인 JDBC Driver 구현체들에서 전송되는 Auto-commit 설정 쿼리들은 다음과 같습니다.

| JDBC Driver Vendor | setAutoCommit(true) | setAutoCommit(false) |
| --- | --- | --- |
| MySQL Connector/J | SET autocommit=1 | SET autocommit=0 |
| JDBC Driver for SQL Server | set implicit\_transactions off | set implicit\_transactions on |
| PostgreSQL JDBC Driver |  | BEGIN (*deferred*) |
| Oracle JDBC Driver |  | BEGIN (*deferred*) |

대표적인 JDBC Driver 구현체들에서 전송되는 Auto-commit 설정 쿼리

> PostgreSQL JDBC Driver는 Connection.setAutoCommit(false) API가 호출되면 그 즉시 BEGIN 문을 DB로 전송하지 않습니다. PostgreSQL JDBC Driver는 Statement.executeQuery() 등의 쿼리 API가 처음으로 호출될 때 BEGIN 문을 DB로 전송합니다. Oracle JDBC Driver도 동일하게 동작합니다.

## maximumPoolSize & minimumIdle

maximumPoolSize, minimumIdle 옵션은 풀(Pool)의 최대 크기, 최소 크기를 지정하는 옵션입니다.

> minimumIdle 값은 풀에서 유지될 최소 유휴(Idle) 연결 수를 나타내나 의미상 풀의 최소 크기와 같습니다.

WAS 시스템의 경우 일반적으로 컴퓨터 자원을 효율적으로 관리하기 위하여 커넥션 풀의 유휴 연결 수를 minimumIdle 값만큼 제한하게 됩니다. 하지만 게임 서버 시스템의 경우 이런 제한을 하지 않는 것이 좋습니다. 왜냐하면 커넥션 풀의 유휴 연결이 부족하여 새로운 연결을 맺을 경우 연결을 맺는 데 소요되는 시간만큼 응답 지연이 발생하고, 이러한 응답 지연은 게임의 특성상 유저에게 좋지 않은 경험을 유발할 수 있기 때문입니다.

위의 이유를 포함한 다양한 이유로 응답 속도가 중요하고 민감한 게임 서버 시스템은 유휴 상태 없이 항상 활성(Busy) 상태로 동작하는 시스템으로 간주되어야 합니다. 따라서 커넥션 풀의 유휴 연결 수 제한 기능이 동작하지 않도록 **maximumPoolSize, minimumIdle 옵션은 동일한 값으로 설정하기를 권장합니다.**

다음으로 풀 크기를 산정해야 합니다. HikariCP의 커넥션 풀 크기를 산정할 때는 애플리케이션의 최대 스레드 수를 산정한 후 Pool-locking 현상으로 인한 교착 상태의 발생 가능성 유무를 고려해야 합니다.

> **참고**: Pool-locking 현상이란 하나의 스레드에서 커넥션을 획득한 후 중첩해서 추가적인 커넥션을 획득하고자 할 때 풀이 고갈된 상태여서 커넥션을 획득하지 못하고 대기하는 현상을 말합니다. 더 자세한 사항은 공식 사이트의 [About Pool Sizing](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing#pool-lockin) 을 참고하기 바랍니다.

Pool-locking 현상을 방지하기 위한 공식은 다음과 같습니다.

$pool\,size = T_n \times (C_m - 1) + 1$

- $T_n$ : 최대 스레드 수
- $C_m$ : 단일 스레드에서 점유되는(held) 최대 동시 연결(Connection) 수

> 다음과 같은 공식도 있으니 참고하기를 바랍니다.
>
> $pool\,size = T_n \times (C_m - 1) + \cfrac{T_n}{2}$
>
> **출처**: https://techblog.woowahan.com/2663/

하지만 게임 서버 시스템의 경우 하나의 스레드에서 중첩해서 여러 개의 커넥션을 사용하는 경우가 드뭅니다. 따라서 Pool-locking 현상이 발생하지 않음을 가정하고, DB의 리소스 사용량 및 DB당 연결되는 게임 서버의 수를 고려하여 풀 크기를 산정하는 것이 일반적입니다. **풀 크기를 산정할 때는 성능 테스트를 수행하는 것을 권장하며, 성능 테스트 시작을 위한 초기 풀의 크기는 CPU 코어 수만큼을 권장합니다.**

성능 테스트 시 풀 크기 산정 전략은 다음을 참고하기 바랍니다.

- 테스트 기준
	- DB의 리소스 사용량 임계치: CPU 60%
- 풀 크기 산정
	- HikariCP의 IdleConnections 수치가 크다면 풀 크기를 축소
	- HikariCP의 PendingConnections 수치가 크다면 풀 크기를 증가
	- DB의 리소스 사용률이 임계치보다 크다면 풀 크기를 축소
		- 또는 DB에 연결되는 게임 서버의 수를 축소

## connectionTestQuery

connectionTestQuery 옵션은 풀에서 커넥션을 가져올 때, HikariCP가 커넥션을 반환하기 전에 DB와의 물리적인 연결이 아직 살아있는지를 확인하는 헬스 체크 용도로 사용되는 쿼리 문을 지정하는 옵션입니다.

JDBC v4.0 스펙을 충족하는 JDBC Driver 구현체를 사용하는 경우, HikariCP는 Connection.isValid() API를 이용하여 더 작은 네트워크 트래픽으로 헬스 체크 수행합니다. 대표적인 JDBC Driver 구현체들은 모두 JDBC v4.0 스펙을 충족하고 있으므로 **connectionTestQuery 옵션은 아무것도 지정하지 않는 것을 권장합니다** (기본값은 null입니다)**.**

## validationTimeout

validationTimeout 옵션은 풀에서 커넥션을 가져올 때, HikariCP가 커넥션을 반환하기 전에 DB와의 물리적인 연결이 아직 살아있는지를 확인하는 헬스 체크에 소요되는 시간의 임계치를 지정하는 옵션입니다. 즉, Connection.isValid() 또는 connectionTestQuery를 수행하는 데 소요되는 최대 시간을 지정하는 옵션입니다.

> 만약 connectionInitSql 옵션을 설정하였다면 connectionInitSql을 실행할 때도 validationTimeout 값이 적용됩니다.

validationTimeout은 DB와 물리적인 연결이 맺어진 후 헬스 체크에 적용되는 옵션이기 때문에 이 옵션 값을 산정할 때는 criticalRTT 값과 minRTO 값을 고려해야 합니다.

criticalRTT 값은 TCP 패킷 왕복 시간의 임계치로써, 일반적인 인터넷 패킷의 왕복 속도가 1ms/100km임을 감안한다면 지구의 반대편까지 패킷이 오고 가는 데는 이론상 대략 200ms 정도의 시간이 소요되기 때문에 이를 criticalRTT 값으로 삼을 수 있습니다. 일반적으로 게임 서버와 DB를 20000km 정도의 거리를 두고 호스팅하는 경우는 드물기 때문에 200ms라는 값은 적당한 수치라고 할 수 있으며, 만약 게임 서버와 DB가 호스팅되는 거리가 매우 멀다면 criticalRTT 값을 200ms 값보다 크게 정할 수도 있습니다.

minRTO 값은 [게임 서버 시스템을 위한 JDBC와 Timeout 이해하기](https://netmarble.engineering/jdbc-timeout-for-game-server/) 의 [TCP 재전송](https://netmarble.engineering/jdbc-timeout-for-game-server/#TCP) 섹션을 참고하기를 바라며, 대다수의 Java 서버가 Linux에서 호스팅되는 관계로 200ms를 기준값으로 합니다.

위와 같은 기준값을 바탕으로 **validationTimeout 값은 500ms로 설정하는 것을 권장합니다.**

> **validationTimeout 계산에 사용된 공식**
>
> $validationTimeout = criticalRTT + minRTO + \alpha$

## connectionTimeout

connectionTimeout 옵션은 풀에서 커넥션을 가져올 때 이용 가능한 커넥션을 기다리는 최대 대기시간을 지정하는 옵션입니다.

이 옵션의 시간 값은 DB와의 물리적인 연결을 맺는 데 소요되는 시간의 임계치를 의미하는 것이 아니라, 풀에서 커넥션을 가져오는 데 소요되는 시간의 임계치를 의미합니다. 즉, 풀이 고갈되어서 이용 가능한 커넥션이 없을 때 다른 스레드에서 점유 중인 커넥션이 풀로 반환되어서 이용 가능해질 때까지 대기하는 시간을 의미합니다. 또한 커넥션을 반환하기 전에 물리적인 연결에 대한 헬스 체크에 소요되는 시간(validationTimeout)도 포함됩니다.

> 이 시간 값에는 백그라운드에서 새로운 커넥션이 생성되는 것을 대기하는 시간도 포함되나, 게임 서버 시스템의 특성상 고정된 풀 크기를 사용하기 때문에 해당 내용은 설명에서 제외하였습니다.

따라서 connectionTimeout 값을 산정할 때는 JDBC Statement Timeout 값과 validationTimeout 값을 고려해야 합니다. JDBC Statement Timeout 값은 하단의 [JDBC Statement Timeout](https://netmarble.engineering/hikaricp-options-optimization-for-game-server/#JDBC_Statement_Timeout) 섹션을 참고하기 바랍니다.

각 섹션에서 산정된 기준값을 바탕으로 **connectionTimeout 값은 2000ms로 설정하는 것을 권장합니다.** 이 시간 값은 재시도 1회가 포함된 수치입니다. 그리고 만약 해당 시간 동안 커넥션을 반환하지 못하는 경우 Timeout Exception(SQLTransientConnectionException)이 발생됩니다.

> **connectionTimeout 계산에 사용된 공식**
>
> $connectionTimeout = statementTimeout + validationTimeout + \alpha$

## maxLifetime & idleTimeout & keepaliveTime

maxLifetime 옵션은 풀에서 관리되는 커넥션의 최대 생명 주기를 지정하는 옵션이고, idleTimeout 옵션은 풀에서 유휴 상태로 대기 중인 커넥션이 종료(Close)될 때까지의 대기 시간을 지정하는 옵션입니다.

게임 서버 시스템은 항상 활성 상태로 동작하는 시스템으로 간주되어야 하기 때문에 **maxLifetime, idleTimeout 옵션은 0ms(Infinite Lifetime)로 설정하기를 권장합니다.**

keepaliveTime 옵션은 DB가 유휴 연결 시간제한에 맞춰서 유휴 연결을 강제로 종료시키지 않도록 하기 위해서 HikariCP가 DB로 헬스 체크를 보내는 주기를 지정하는 옵션입니다. JDBC v4.0 스펙을 충족하는 JDBC Driver 구현체를 사용하는 경우 HikariCP는 Connection.isValid() API를 이용해서 헬스 체크를 수행하고, 그렇지 않다면 connectionTestQuery를 DB로 전송하여 헬스 체크를 수행합니다. 이 옵션은 HikariCP v4.0 이상 버전부터 지원됩니다.

마찬가지 이유로 게임 서버 시스템은 항상 활성 상태로 동작하는 시스템으로 간주되어야 하기 때문에 **keepaliveTime 옵션은 설정 가능한 최솟값인 30000ms로 설정하기를 권장합니다.**

## JDBC Statement Timeout

Statement Timeout 옵션은 HikariCP가 제공하는 옵션이 아니라 JDBC Driver가 제공하는 옵션입니다. HikariCP는 DataSource의 구현체이기 때문에 JDBC Driver의 Timeout 관련 옵션들도 반드시 고려되고 설정되어야 하는 옵션입니다.

[게임 서버 시스템을 위한 JDBC와 Timeout 이해하기](https://netmarble.engineering/jdbc-timeout-for-game-server/) 의 [Statement Timeout과 Socket Timeout](https://netmarble.engineering/jdbc-timeout-for-game-server/#Statement_Timeout_Socket_Timeout) 섹션에서 설명한 것처럼 Statement Timeout의 용도는 DB에서 수행되는 SQL 문 한 개의 수행 시간을 제한하는 것입니다. SQL 문의 실행 시간을 제한해야 하는 이유는 SQL 문의 실행 시간이 길어져서 DB의 응답 지연이 발생할 경우, 게임 서버의 스레드 고갈 또는 커넥션 풀 고갈 등으로 인해서 요청 처리가 보류(Pending)되고 응답 지연 장애가 발생할 수 있기 때문입니다. 뿐만 아니라 게임 서버 시스템의 특성상 하나의 서버는 다른 서버들과 유기적으로 연결되는 경우가 많기 때문에 한 서버에서만 응답 지연 장애가 발생하더라도 다른 서버들로 장애가 전파되어 전체 게임 서버 시스템의 응답 지연 장애가 유발될 수 있습니다. 따라서 **Statement Timeout 옵션은 반드시 설정하기를 권장합니다.**

Statement Timeout 값을 산정할 때는 criticalRTT 값, minRTO 값 그리고 슬로 쿼리 임계 시간 값을 고려해야 합니다.

게임의 장르에 따라서 DB의 쿼리 실행 시간은 수 또는 수십 ms 이내가 되는 것이 좋습니다. 하지만 예상치 못한 상황에서는 DB에서 슬로 쿼리가 발생할 수 있기 때문에 위에서 설명한 이유를 바탕으로 쿼리 실행 시간을 제한하는 것이 좋습니다. 쿼리 실행 시간을 제한하기 위한 기준값인 슬로 쿼리 임계 시간 값은 게임 장르에 따라서 200~1000ms를 기본으로 하는 것이 좋습니다.

위와 같은 기준값을 바탕으로 **Statement Timeout 값은 1000ms로 설정하는 것을 권장합니다.**

> **Statement Timeout 계산에 사용된 공식**
>
> $statementTimeout = criticalRTT + minRTO + avgSlowQueryTime + \alpha$
>
> ㆍ $avgSlowQueryTime$ : 슬로 쿼리 임계 시간 평균값(500ms)

## JDBC Connection Timeout & Read Timeout

Connection Timeout, Read Timeout 옵션은 HikariCP가 제공하는 옵션이 아니라 TCP 소켓이 제공하는 옵션입니다. Connection Timeout, Read Timeout에 대한 자세한 설명은 [게임 서버 시스템을 위한 JDBC와 Timeout 이해하기](https://netmarble.engineering/jdbc-timeout-for-game-server/) 의 [Timeout 이해하기](https://netmarble.engineering/jdbc-timeout-for-game-server/#Timeout) 섹션을 참고하기를 바라며, 여기서는 권장 설정값에 대해서만 다루도록 하겠습니다.

Connection Timeout 값은 criticalRTT 값, initialRTO 값 그리고 Fast Failover를 고려하여 **3000ms로 설정하는 것을 권장합니다.** 만약 DB 연결 시 IP 대신 HostName을 사용한다면 DNS Lookup Time도 고려하여 13000ms로 설정하는 것을 권장합니다. 이 시간 값은 TCP 3-Way Handshake 과정에서 패킷 손실에 대한 재전송 시도가 1회 포함된 수치입니다.

> **Connection Timeout 계산에 사용된 공식**
>
> $Connection\,Timeout = criticalRTT + initialRTO + \alpha$

Read Timeout 값을 산정할 때는 criticalRTT 값, minRTO 값 그리고 허용 쿼리 임계 시간 값을 고려해야 합니다.

게임 서버 시스템에서 쿼리 실행 시간은 [JDBC Statement Timeout](https://netmarble.engineering/hikaricp-options-optimization-for-game-server/#JDBC_Statement_Timeout) 섹션에서 설명한 것처럼 최악의 경우에도 1000ms를 넘지 않도록 하는 것이 일반적입니다. 하지만 배치 작업 등과 같이 실행 시간이 긴 경우에는 쿼리 실행 시간이 1000ms를 넘게 됩니다. 만약 배치 작업에 3000ms가 소요되는데 Read Timeout 값을 2000ms로 설정했다고 가정한다면, 배치 작업이 끝나기도 전에 Timeout Exception이 발생하여 물리적인 연결이 끊어지고 실행 중인 쿼리가 취소되어서 배치 작업이 정상적으로 완료되지 않게 됩니다.

이러한 이유로 허용 쿼리 임계 시간 값을 정할 때는 예상되는 최대 쿼리 실행 시간을 기준으로 하는 것을 권장합니다. 만약 배치 작업 등과 같이 실행 시간이 긴 쿼리가 없다면 10000ms 이내의 값을 기본으로 하는 것이 좋습니다.

위와 같은 기준값을 바탕으로 Read Timeout 값은 **10000ms로 설정하는 것을 권장합니다.**

> **Read Timeout 계산에 사용된 공식**
>
> $Read\,Timeout = criticalRTT + minRTO + allowedQueryTime + \alpha$
>
> ㆍ $allowedQueryTime$ : 허용 쿼리 임계 시간 기본값(< 10000ms)

Connection Timeout, Read Timeout 값을 설정할 때 dataSourceClassName 옵션을 설정한 경우에는 dataSourceProperties를 이용해서 값을 지정해야 하고, jdbcUrl 옵션을 설정한 경우는 URL 형식에 맞춰서 값을 지정해 줘야 합니다. 대표적인 JDBC Driver 구현체들에서 Connection Timeout, Read Timeout 옵션을 적용하기 위한 속성들은 다음과 같습니다.

| JDBC Driver Vendor | Connection Timeout | Read Timeout |
| --- | --- | --- |
| MySQL Connector/J | connectionTimeout | socketTimeout |
| JDBC Driver for SQL Server | loginTimeout | socketTimeout |
| PostgreSQL JDBC Driver | connectTimeout | socketTimeout |
| Oracle JDBC Driver | oracle.net.CONNECT\_TIMEOUT | oracle.jdbc.ReadTimeout |

대표적인 JDBC 구현체별 Connection Timeout, Read Timeout 옵션을 적용하기 위한 속성

## 권장 설정 요약

지금까지 여러 가지 HikariCP 옵션과 권장 설정을 살펴봤습니다. 이러한 옵션별 권장 설정을 다음과 같은 표로 정리해보았습니다.

| 옵션 | 권장 설정 |
| --- | --- |
| dataSourceClassName | [dataSourceClassName](https://netmarble.engineering/hikaricp-options-optimization-for-game-server/#dataSourceClassName) 섹션 참고 |
| jdbcUrl | [jdbcUrl & driverClassName](https://netmarble.engineering/hikaricp-options-optimization-for-game-server/#jdbcUrl_driverClassName) 섹션 참고 |
| driverClassName | [jdbcUrl & driverClassName](https://netmarble.engineering/hikaricp-options-optimization-for-game-server/#jdbcUrl_driverClassName) 섹션 참고 |
| transactionIsolation | DBA와 상의하여 결정 |
| username | DB 사용자 계정 이름 |
| password | DB 사용자 계정 암호 |
| autoCommit | true (명시적으로 설정하는 것을 권장) |
| maximumPoolSize | [maximumPoolSize & minimumIdle](https://netmarble.engineering/hikaricp-options-optimization-for-game-server/#maximumPoolSize_minimumIdle) 섹션 참고 |
| minimumIdle | maximumPoolSize 값과 동일하게 설정 |
| connectionTestQuery | null (기본값: null) |
| validationTimeout | 500ms |
| connectionTimeout | 2000ms |
| maxLifetime | 0ms |
| idleTimeout | 0ms |
| keepaliveTime | 30000ms (HikariCP v4.0 이상 부터 지원) |
| JDBC Statement Timeout | 1000ms |
| JDBC Connection Timeout | 3000ms |
| JDBC Read Timeout | 10000ms |

게임 서버 시스템을 위한 HikariCP 옵션 및 권장 설정 요약

여기에서 소개된 권장 설정은 권장일 뿐 절대적인 것이 아닙니다. 따라서 게임의 장르, 상황 및 목적에 맞춰서 HikariCP를 튜닝하면서 본 글을 참고 정도만 해도 무방합니다.

| | | | |
