---
title: "MySQL을 이용한 분산락으로 여러 서버에 걸친 동시성 관리 | 우아한형제들 기술블로그"
source: "https://techblog.woowahan.com/2631/"
author:
  - "[[권순규]]"
published: 2019-05-30
created: 2026-09-28
description: "안녕하세요. 비즈인프라개발팀 권순규입니다. 현재 광고시스템에서 사용하고 있는 MySQL을 이용한 분산락에 대해 설명드리고자 합니다. 분산락을 적용하게된 원인 현재 테이블은 아래 그림과 같이 User 테이블과 Card 테이블이 있고, User 테이블과 Card 테이블은 1 : N 의 구조로 생성 되어있습니다.(예제코드) 하지만 User 객체는 2개의 Card 만을 가질수 있도록 구현되어 있습니다. @Entity @Getter @NoArgsConstructor @ToString @Table(name = \"user\") @EqualsAndHashCode(onlyExplicitlyIncluded"
tags:
  - "clippings"
---

> [!summary]
> 우아한형제들 광고시스템에서 사용자당 카드 2장 제한이 동시 요청에 깨진 문제를, 별도 인프라 없이 MySQL USER-LEVEL LOCK(`GET_LOCK`/`RELEASE_LOCK`)으로 분산 락을 걸어 해결한 사례다. 관련 함수들의 반환값과 MySQL 5.7 전후 차이를 정리하고, `NamedParameterJdbcTemplate`으로 구현하면 쿼리마다 커넥션을 풀에 반납해 락 획득과 해제가 서로 다른 커넥션에서 실행되는 문제를 보여 준다. `@Transactional`로 묶으면 락용 커넥션 풀과 로직용 풀을 분리할 수 없어서, 최종적으로 `DataSource`에서 커넥션 하나를 직접 얻어 JDBC로 획득과 해제를 같은 커넥션에서 수행하도록 구현했다.

## MySQL을 이용한 분산락으로 여러 서버에 걸친 동시성 관리

2019\. 05. 30. 권순규

[Backend](https://techblog.woowahan.com/?pcat=backend)

> 안녕하세요. 비즈인프라개발팀 권순규입니다.
> 현재 광고시스템에서 사용하고 있는 MySQL을 이용한 분산락에 대해 설명드리고자 합니다.

## 분산락을 적용하게된 원인

현재 테이블은 아래 그림과 같이 User 테이블과 Card 테이블이 있고, User 테이블과 Card 테이블은 1: N 의 구조로 생성 되어있습니다.([예제코드](https://github.com/woowabros/mysql_user_level_lock_demo))
![관계도](https://techblog.woowahan.com/wp-content/uploads/img/2019-05-30/erd.png)

하지만 [User](https://github.com/woowabros/mysql_user_level_lock_demo/tree/master/src/main/java/woowa/demo/model/User.java) 객체는 2개의 [Card](https://github.com/woowabros/mysql_user_level_lock_demo/tree/master/src/main/java/woowa/demo/model/Card.java) 만을 가질수 있도록 구현되어 있습니다.

```java
@Entity
@Getter
@NoArgsConstructor
@ToString
@Table(name = "user")
@EqualsAndHashCode(onlyExplicitlyIncluded = true)
public class User {

    private static final int MAXIMUM_CARD_COUNT = 2;

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id", nullable = false)
    @EqualsAndHashCode.Include
    private Long id;

    @Column(name = "name", nullable = false)
    private String name;

    @OneToMany(mappedBy = "user",cascade = )
    private Set<Card> cards = new HashSet<>();

    public User(String name) {
        this.name = name;
    }

    public void addCard(Card card) {
        if (isMaxCardCount()) {
            throw new IllegalStateException("최대 수량을 초과하였습니다. 최대수량 : "+ MAXIMUM_CARD_COUNT +", 현재 크기 : "+getCardCount());
        }
        card.setUser(this);
        this.cards.add(card);
    }

    private boolean isMaxCardCount() {
        return getCardCount() >= MAXIMUM_CARD_COUNT;
    }

    public int getCardCount() {
        return this.cards.size();
    }

}
```

[SingleThreadRequest.java](https://github.com/woowabros/mysql_user_level_lock_demo/tree/master/src/main/java/woowa/demo/test/SingleThreadRequest.java) 를 실행하여 Card 생성을 한건씩 요청했을 때는 아래와 같이 2개 이상 생성 할 수 없었습니다.

- 요청 로그
	!\[한건씩 요청\](/wp-content/uploads/img/2019-05-30/한건씩 호출.png)
- 요청 결과 Card 테이블
	!\[한건씩 결과\](/wp-content/uploads/img/2019-05-30/한건씩 결과.png)

[MultiThreadRequest.java](https://github.com/woowabros/mysql_user_level_lock_demo/tree/master/src/main/java/woowa/demo/test/MultiThreadRequest.java) 를 실행하여 Card 생성을 동시에 20건 요청했을때는 아래와 같이 정상적으로 요청이 수행된 것 처럼 응답을 내려줍니다.

- 요청 로그
	!\[동시 요청\](/wp-content/uploads/img/2019-05-30/동시 호출.png)

하지만 Card 테이블에는 하나의 User당 2개의 Card 라는 제약사항을 어기고 아래와 같이 20개의 Card가 하나의 User 에게 생성되어 있습니다.

- 요청 결과 Card 테이블
	!\[동시 결과\](/wp-content/uploads/img/2019-05-30/동시 결과.png)

위와 같이 동시에 데이터 생성이 요청되게 되면 데이터 생성에 대한 제약사항이 무시되게 되었기에 데이터를 생성하는 부분에 분산락을 적용하게 되었습니다.

## 왜 MySQL 을 이용하여 분산락을 구현하였나?

구글에 분산락 구현에 대해 검색해보면 ZooKeeper, Redis 등을 이용하여 구현한 예제가 다수 검색이 됩니다.
ZooKeeper, Redis 등을 이용하여 분산락을 구현하는 것도 좋지만 ZooKeeper, Redis 등을 이용하여 분산락을 구현하게 되면 인프라 구축에 대한 비용이 발생할 뿐만 아니라 인프라 구축 후 유지보수에 대한 비용 또한 발생하게 됩니다.
하지만, MySQL은 프로젝트 초기부터 RDBMS로 사용해오고 있었기때문에 인프라 구축 및 유지보수에 대한 추가 비용이 들지 않았고, 분산락의 사용량이 추가적인 비용을 들일만큼 많지않았기 때문에 MySQL 을 이용하게 되었습니다.
또한, MySQL에서 제공하는 USER-LEVEL LOCK 은 LOCK 에 이름을 지정할 수 있기 때문에 LOCK 의 이름을 이용하여 어플리케이션단에서 제어가 가능하다는 점도 분산락의 구현에 MySQL 을 이용하는 이유가 되었습니다.

## MySQL USER-LEVEL LOCK 관련 함수

- GET\_LOCK(str,timeout)
	- 입력받은 이름(str) 으로 timeout 초 동안 잠금 획득을 시도합니다. timeout 에 음수를 입력하면 잠금을 획득할 때까지 무한대로 대기하게 됩니다.
		- 한 session에서 잠금을 유지하고 있는동안에는 다른 session에서 동일한 이름의 잠금을 획득 할 수 없습니다.
		- GET\_LOCK() 을 이용하여 획득한 잠금은 Transaction 이 commit 되거나 rollback 되어도 해제되지 않습니다.
		- GET\_LOCK() 의 결과값은 1, 0, null 을 반환합니다.
		- sql
		!\[get\_lock sql\](/wp-content/uploads/img/2019-05-30/get\_lock sql.png)
		- 1: 잠금을 획득하는데 성공하였을때
		!\[get\_lock 성공\](/wp-content/uploads/img/2019-05-30/get\_lock 성공.png)
		- 0: timeout 초 동안 잠금 획득에 실패했을때
		!\[get\_lock 실패\](/wp-content/uploads/img/2019-05-30/get\_lock 실패.png)
		- null: 잠금획득 중 에러가 발생했을때.(ex: Out Of Memory, 현재 스레드가 강제로 종료되었을때)
		- MySQL 5.7 이상 버전과 5.7 미만 버전의 차이
	| 5.7 미만 | 5.7 이상 |
	| --- | --- |
	| 동시에 하나의 잠금만 획득 가능 | 동시에 여러개 잠금 획득 가능 |
	| 잠금 이름 글자수 무제한 | 잠금 이름 글자수 60자로 제한 |
	- MySQL 5.7 이전 버전에서 GET\_LOCK() 을 이용하여 동시에 여러개의 잠금을 획득하게 되면, 이전에 획득했던 잠금이 해제되게 됩니다.
		- 동시에 잠금을 획득하기위해 대기할 때 대기 순서는 보장되지 않습니다.
- RELEASE\_LOCK(str)
	- 입력받은 이름(str) 의 잠금을 해제합니다.
		- RELEASE\_LOCK() 의 결과값은 1, 0, null 을 반환합니다.
		- sql
		!\[release\_lock sql\](/wp-content/uploads/img/2019-05-30/release\_lock sql.png)
		- 1: 잠금을 성공적으로 해제했을때
		!\[release\_lock 성공\](/wp-content/uploads/img/2019-05-30/release\_lock 성공.png)
		- 0: 잠금이 해제되지는 않았지만, 현재 쓰레드에서 획득한 잠금이 아닌경우
		!\[release\_lock 실패\](/wp-content/uploads/img/2019-05-30/release\_lock 실패.png)
		- null: 잠금이 존재하지 않을때
- RELEASE\_ALL\_LOCKS()
	- 현재 세션에서 유지되고 있는 모든 잠금을 해제하고 해제한 잠금 갯수를 반환합니다.
- IS\_FREE\_LOCK(str)
	- 입력한 이름(str)에 해당하는 잠금이 획득 가능한지 확인합니다.
		- 결과 값으로 1, 0, null 을 반환합니다.
		- 1: 입력한 이름의 잠금이 없을때
		- 0: 입력한 이름의 잠금이 있을때
		- null: 에러발생시(ex: 잘못된 인자)
- IS\_USED\_LOCK(str)
	- 입력한 이름(str)의 잠금이 사용중인지 확인합니다.
		- 입력받은 이름의 잠금이 존재하면 connection id 를 반환하고, 없으면 null 을 반환합니다.

## 분산락 구현

MySQL에서 제공하는 함수 중에서 `GET_LOCK()` 과 `RELEASE_LOCK()` 을 이용하여 분산락을 구현하였습니다.
`executeWithLock()` 한번의 호출로 Lock 을 얻고, Lock 을 푸는 작업을 하기 위해 비즈니스 로직은 `Supplier` 인터페이스를 이용한 콜백으로 수행되도록 구현하였습니다.
`GET_LOCK()` 과 `RELEASE_LOCK()` 을 사용하기 위해서는 쿼리를 이용하여 호출해야 했기 때문에 처음에는 `NamedJdbcTemplate` 이용하여 아래와 같이 구현하였습니다.
Lock 을 얻는 부분이 로직을 수행하는 부분에 영향을 주는것을 방지하기 위해 Lock 을 얻는부분에서 사용하는 ConnectionPool 과 로직을 수행하는 부분에서 사용하는 ConnectionPool 을 분리하여 설정하였고, 각각 다른 ConnectionPool 을 사용해야 하므로 `excuteWithLock()` 에 `@Transactional` 을 붙이지 않았습니다.

- [UserLevelLockWithJdbcTemplate.java](https://github.com/woowabros/mysql_user_level_lock_demo/tree/master/src/main/java/woowa/demo/lock/UserLevelLockWithJdbcTemplate.java)
	```java
	public class UserLevelLockWithJdbcTemplate {
	private static final String GET_LOCK = "SELECT GET_LOCK(:userLockName, :timeoutSeconds)";
	private static final String RELEASE_LOCK = "SELECT RELEASE_LOCK(:userLockName)";
	private static final String EXCEPTION_MESSAGE = "LOCK 을 수행하는 중에 오류가 발생하였습니다.";
	private final NamedParameterJdbcTemplate jdbcTemplate;
	public UserLevelLockWithJdbcTemplate(NamedParameterJdbcTemplate jdbcTemplate) {
	    this.jdbcTemplate = jdbcTemplate;
	}
	public <T> T executeWithLock(String userLockName,
	                             int timeoutSeconds,
	                             Supplier<T> supplier) {
	    try {
	        getLock(userLockName, timeoutSeconds);
	        return supplier.get();
	    } finally {
	        releaseLock(userLockName);
	    }
	}
	private void getLock(String userLockName,
	                     int timeoutSeconds) {
	    Map<String, Object> params = new HashMap<>();
	    params.put("userLockName", userLockName);
	    params.put("timeoutSeconds", timeoutSeconds);
	    log.info("GetLock!! userLockName ], timeoutSeconds ]", userLockName, timeoutSeconds);
	    Integer result = jdbcTemplate.queryForObject(GET_LOCK, params, Integer.class);
	    checkResult(result, userLockName, "GetLock");
	}
	private void releaseLock(String userLockName) {
	    Map<String, Object> params = new HashMap<>();
	    params.put("userLockName", userLockName);
	    log.info("ReleaseLock!! userLockName ]", userLockName);
	    Integer result = jdbcTemplate.queryForObject(RELEASE_LOCK, params, Integer.class);
	    checkResult(result, userLockName, "ReleaseLock");
	}
	private void checkResult(Integer result,
	                         String userLockName,
	                         String type) {
	    if (result == null) {
	        log.error("USER LEVEL LOCK 쿼리 결과 값이 없습니다. type = [], userLockName ]", type, userLockName);
	        throw new RuntimeException(EXCEPTION_MESSAGE);
	    }
	    if (result != 1) {
	        log.error("USER LEVEL LOCK 쿼리 결과 값이 1이 아닙니다. type = [], result ] userLockName ]", type, result, userLockName);
	        throw new RuntimeException(EXCEPTION_MESSAGE);
	    }
	}
	}
	```
	아래의 [WithJdbcTemplateRequest.java](https://github.com/woowabros/mysql_user_level_lock_demo/tree/master/src/main/java/woowa/demo/test/WithJdbcTemplateRequest.java) 를 실행하여 `UserLevelLockWithJdbcTemplate` 를 사용하는 API 호출 결과를 보면 에러 메시지만 봐서는 잘 동작하는것 같이 보여집니다.
	하지만 JdbcTemplate 의 특성상 `GET_LOCK()` 을 수행하는 쿼리가 실행 되고 트랜잭션이 종료되게 되면 pool 에서 얻어온 Connection을 반환하게 됩니다. 그래서 `RELEASE_LOCK()` 을 실행할 때는 `GET_LOCK()` 을 실행할때와 다른 Connection 을 얻어오는 경우가 발생하게 되어 획득한 LOCK 을 반환하지 못하는 경우가 발생하게 됩니다.
	더 나아가 동시에 동일한 Lock 이름으로 요청한 다른 스레드에서 `GET_LOCK()` 에서 반환했던 Connection 을 획득하여 락을 풀어버릴 위험도 존재합니다.
- 요청 로그
	!\[jdbcTemplate 호출\](/wp-content/uploads/img/2019-05-30/jdbcTemplate 호출.png)
- 요청 결과
	!\[jdbcTemplate 결과\](/wp-content/uploads/img/2019-05-30/jdbcTemplate 결과.png)
	`GET_LOCK()` 수행 후에 반환된 Connection 을 다른 스레드에서 `GET_LOCK()` 을 수행할때 재사용하게 되어 동일 Connection 에서 Lock을 획득하게 되었고, 로직은 정상적으로 수행되어 User 당 2개의 Card 라는 제약사항이 지켜지지 않은 상황이 연출되었습니다.
	하지만, `RELEASE_LOCK()` 을 수행할 때는 `GET_LOCK()` 에서 사용했던 Connection이 아닌 다른 Connection을 얻어와서 Lock 을 반환하는데는 실패하게 되었습니다.
- Connection 로그
	!\[jdbcTemplate 커넥션\](/wp-content/uploads/img/2019-05-30/jdbcTemplate 커넥션.png)

위의 상황을 해결하기 위해 `@Transactional` 을 `executeWithLock()` 에 선언하여 Lock 을 얻어오는 부분과 로직을 수행하는 부분을 하나의 트랜잭션으로 묶는 방법도 있습니다.
[UserLevelLockWithJdbcTemplate.java](https://github.com/woowabros/mysql_user_level_lock_demo/tree/master/src/main/java/woowa/demo/lock/UserLevelLockWithJdbcTemplate.java) 에 선언되어있는 `@Transactional` 의 주석을 풀고 [WithJdbcTemplateRequest.java](https://github.com/woowabros/mysql_user_level_lock_demo/tree/master/src/main/java/woowa/demo/test/WithJdbcTemplateRequest.java) 를 실행하게 되면 아래와 같이 하나의 User 당 Card 2개라는 제약사항이 지켜지는 것을 확인 할 수 있습니다.

- 요청 로그
	!\[트랜잭션 호출\](/wp-content/uploads/img/2019-05-30/트랜잭션 호출.png)
- 요청 결과
	!\[트랜잭션 결과\](/wp-content/uploads/img/2019-05-30/트랜잭션 결과.png)

Lock 을 얻어오는 부분과 로직을 수행하는 부분을 `@Transactional` 을 통해 하나의 트랜잭션으로 묶게 되면 Lock 을 얻어오는 부분과 로직을 수행하는 부분이 동일한 ConnectionPool 을 사용하게 되어 Lock을 얻어오는 부분이 로직을 수행하는 부분에 영향을 줄 수 있기에, 결국 JdbcTemplate 의 사용을 포기하고 최종적으로는 DataSource 를 주입받아 JDBC 를 이용하여 직접 구현하였습니다.
DataSource 를 주입받아 JDBC 를 이용하여 직접 구현하였기에 Connection 을 직접 관리 할 수 있어서 GET\_LOCK() 과 REALSE\_LOCK() 모두 동일한 Connection 을 사용할 수 있었고, 획득한 LOCK 을 정상적으로 반환할 수 있게되었습니다.

- [UserLevelLockFinal.java](https://github.com/woowabros/mysql_user_level_lock_demo/tree/master/src/main/java/woowa/demo/lock/UserLevelLockFinal.java)
	```java
	public class UserLevelLockFinal {
	private static final String GET_LOCK = "SELECT GET_LOCK(?, ?)";
	private static final String RELEASE_LOCK = "SELECT RELEASE_LOCK(?)";
	private static final String EXCEPTION_MESSAGE = "LOCK 을 수행하는 중에 오류가 발생하였습니다.";
	private final DataSource dataSource;
	public UserLevelLockFinal(DataSource dataSource) {
	    this.dataSource = dataSource;
	}
	public <T> T executeWithLock(String userLockName,
	                             int timeoutSeconds,
	                             Supplier<T> supplier) {
	    try (Connection connection = dataSource.getConnection()) {
	        try {
	            log.info("start getLock=[], timeoutSeconds ], connection=[]", userLockName, timeoutSeconds, connection);
	            getLock(connection, userLockName, timeoutSeconds);
	            log.info("success getLock=[], timeoutSeconds ], connection=[]", userLockName, timeoutSeconds, connection);
	            return supplier.get();
	        } finally {
	            log.info("start releaseLock=[], connection=[]", userLockName, connection);
	            releaseLock(connection, userLockName);
	            log.info("success releaseLock=[], connection=[]", userLockName, connection);
	        }
	    } catch (SQLException | RuntimeException e) {
	        throw new RuntimeException(e.getMessage(), e);
	    }
	}
	private void getLock(Connection connection,
	                     String userLockName,
	                     int timeoutseconds) throws SQLException {
	    try (PreparedStatement preparedStatement = connection.prepareStatement(GET_LOCK)) {
	        preparedStatement.setString(1, userLockName);
	        preparedStatement.setInt(2, timeoutseconds);
	        checkResultSet(userLockName, preparedStatement, "GetLock_");
	    }
	}
	private void releaseLock(Connection connection,
	                         String userLockName) throws SQLException {
	    try (PreparedStatement preparedStatement = connection.prepareStatement(RELEASE_LOCK)) {
	        preparedStatement.setString(1, userLockName);
	        checkResultSet(userLockName, preparedStatement, "ReleaseLock_");
	    }
	}
	private void checkResultSet(String userLockName,
	                            PreparedStatement preparedStatement,
	                            String type) throws SQLException {
	    try (ResultSet resultSet = preparedStatement.executeQuery()) {
	        if (!resultSet.next()) {
	            log.error("USER LEVEL LOCK 쿼리 결과 값이 없습니다. type = [], userLockName ], connection=[]", type, userLockName, preparedStatement.getConnection());
	            throw new RuntimeException(EXCEPTION_MESSAGE);
	        }
	        int result = resultSet.getInt(1);
	        if (result != 1) {
	            log.error("USER LEVEL LOCK 쿼리 결과 값이 1이 아닙니다. type = [], result ] userLockName ], connection=[]", type, result, userLockName, preparedStatement.getConnection());
	            throw new RuntimeException(EXCEPTION_MESSAGE);
	        }
	    }
	}
	}
	```
	[FinalRequest.java](https://github.com/woowabros/mysql_user_level_lock_demo/tree/master/src/main/java/woowa/demo/test/FinalRequest.java) 를 실행하여 `UserLevelLockFinal` 을 사용하는 API 를 호출하게 되면 아래와 같이 하나의 User 당 2개의 Card 라는 제약사항이 지켜지는 것을 확인 할 수 있습니다.
- 요청 로그
	!\[최종 호출\](/wp-content/uploads/img/2019-05-30/최종 호출.png)
- 요청 결과
	!\[최종 결과\](/wp-content/uploads/img/2019-05-30/최종 결과.png)
