---
title: "AI 시대, JPA의 복잡성 대신 본질에 집중하기"
source: "https://brunch.co.kr/@cleancode/95"
author:
  - "[[백명석]]"
published: 2025-12-21
created: 2026-07-20
description: "spring-data-jpa vs spring-data-jdbc | 들어가며  JPA와 Hibernate는 10년 넘게 Java 영속성의 표준이었다. 처음 배울 때는 “마법” 같았다. 객체만 수정하면 알아서 DB에 반영되고, 지연 로딩으로 성능도 최적화된다고 했다.  하지만 실무에서 JPA를 쓰면서 의문이 생기기 시작했다.  세션, 영속성 콘텍스트, 엔티티 생명주기… 내부 동작을 제대로 이해하지 못해 예상치 못한 버그를 만"
tags:
  - "clippings"
---

> [!summary]
> Argues that JPA/Hibernate is overkill for most modern Spring Boot microservices, citing dirty checking surprises, lazy loading pitfalls, bloated aggregates, and domain logic coupled to persistence. Recommends Spring Data JDBC for its explicit, predictable save-what-you-see model that enforces aggregate root boundaries. Frames the choice in AI-era terms: JPA is accidental complexity that AI already knows well, so developers should invest their time in domain modeling — the essential complexity AI cannot learn.

매거진 [지속 가능한 소프트웨어 개발하기](https://brunch.co.kr/magazine/sustainable-sw)

spring-data-jpa vs spring-data-jdbc

by

## 들어가며

JPA와 Hibernate는 10년 넘게 Java 영속성의 표준이었다. 처음 배울 때는 “마법” 같았다. 객체만 수정하면 알아서 DB에 반영되고, 지연 로딩으로 성능도 최적화된다고 했다.

하지만 실무에서 JPA를 쓰면서 의문이 생기기 시작했다.

**세션, 영속성 콘텍스트, 엔티티 생명주기… 내부 동작을 제대로 이해하지 못해 예상치 못한 버그** 를 만나고, **디버깅에 시간** 을 쏟았다. "정말 이 복잡한 ORM이 필요할까?"라는 의문이 들었다.

더 큰 문제는 **JPA의 연관관계 기능이 너무 좋다** 는 것이었다. @OneToMany, @ManyToMany로 쉽게 관계를 맺다 보니 **Aggregate가 점점 비대해졌다**. **마치 모놀리식 애플리케이션이 제어되지 않은 환경에서 커지면서 제어 불가능한 상태에 빠지는 것처럼**, 아주 사소한 일을 할 때도 거대한 객체 그래프를 로딩하고 저장해야 하는 상황이 됐다.

2025년 현재, 80%의 현대 Spring Boot 애플리케이션—특히 도메인이 작고 경계가 명확한 마이크로서비스—에서 **JPA는 과잉(overkill)** 이다. 칼싸움에 탱크를 가져오는 것과 같다.

## JPA의 "마법"이 가져오는 문제들

### 더티 체킹의 함정

[https://gist.github.com/msbaek/f81488307c0346e338f5c7b71b8b77f4](https://gist.github.com/msbaek/f81488307c0346e338f5c7b71b8b77f4)

**@Transactional**

편리해 보이지만 문제가 있다. SQL이 정확히 언제 실행되는지 예측하기 어렵고, **의도치 않은 엔티티를 실수로 수정** 할 수 있다. 디버깅할 때 머리가 아프다.

### Lazy Loading 지옥

트랜잭션 밖에서 getter를 호출하면? LazyInitializationException. 한 번쯤 겪어봤을 것이다. N+1 문제는 또 어떤가. getter를 호출하는 것만으로

> User → Order → Product → Category

를 **순회할 수 있다**. 멋져 보이지만 **거대하고 보이지 않는 SQL 쿼리들이 생성** 된다.

### Aggregate가 비대해지는 경향

Vaughn Vernon이 분석한 금융 시스템 사례를 보면, **전체 Aggregate 중 70%는 root entity와 value object만** 으로 이뤄졌고, 나머지 **30%도 2-3개의 entity로 충분** 했다.

하지만 JPA를 쓰면서 1:N, N:M 관계를 남용하게 되고, **Aggregate가 필요 이상으로 커진다**. 이렇게 편하게 사용한다면 모놀리식 애플리케이션이 개발은 쉽지만 향후 **변경 비용이 커지는 것과 비슷한 문제** 를 겪게 된다.

### 도메인 로직이 JPA에 종속되는 문제

가장 안타까운 문제가 있다. spring-data-jpa의 JpaRepository를 도메인 로직에서 직접 사용하는 코드를 자주 본다.

위와 같이 JPA Repository(OrderRepository)를 직접 사용하면 여러 문제가 생긴다.

첫째, **테스트할 때 DB 없이는 실행도 안 된다**. TDD로 개발하며 빠른 설계 피드백을 받고 싶어도 매번 DB를 띄워야 한다. 테스트가 느려지고, 피드백 루프가 길어지고, 결국 테스트를 덜 작성하게 된다.

둘째, **도메인 로직이 기술적 세부사항에 오염** 된다(**상위 수준 정책이 하위 수준 상세함에 의존하는 DIP 위반 문제 발생**). 비즈니스 규칙을 표현해야 할 도메인 계층에 JPA 애노테이션, 프락시 객체, 영속성 콘텍스트 같은 기술적 개념이 스며든다. 도메인 모델의 순수성이 깨진다.

셋째, **향후 변경이 어려워진다**. 나중에 JPA가 아닌 다른 영속성 기술(예: Spring Data JDBC, MongoDB)로 바꾸고 싶어도, 도메인 로직 전체를 수정해야 한다.

해결책은 간단하다. 순수한 Repository 인터페이스를 정의하고, JpaRepository는 그 구현체로 뒤에 숨기면 된다. 그러면 테스트 시 InMemoryRepository로 쉽게 대체할 수 있다.

[https://gist.github.com/msbaek/99b46c40ecad6fbb7294f2c3ef0a2c9a](https://gist.github.com/msbaek/99b46c40ecad6fbb7294f2c3ef0a2c9a)

테스트 환경에서는 사용하는 다음과 같은 **InMemory Fake는 AI를 이용하면 수초면 구현이 가능** 한데, **테스트를 할 때는 매우 막강** 하다.

[https://gist.github.com/msbaek/79daa3c01487485d0a91291531cf6f72](https://gist.github.com/msbaek/79daa3c01487485d0a91291531cf6f72)

그런데 **JPA 책이나 강의에서는 이런 부분을 구체적으로 언급하는 것을 거의 보지 못했다**. spring-data-jpa 사용법은 열심히 가르치지만, 도메인 로직을 JPA로부터 분리하는 원칙은 다루지 않는다. 결국 개발자들이 잘못된 관행을 배우게 된다.

## Spring Data JDBC: 단순함의 귀환

Spring Data JDBC의 철학은 단순하다.

> “엔티티를 로드하려면, 로드하라. 저장하려면, save()를 호출하라.”

**세션도 없고, 더티 체킹도 없고, 지연 로딩 프락시도 없다. WYSIWYG(What You See Is What You Get) 방식** 이다.

[https://gist.github.com/msbaek/be34a512e4b2361f39d087b5f05e0cd1](https://gist.github.com/msbaek/be34a512e4b2361f39d087b5f05e0cd1)

**읽기 쉽고, 디버깅하기 쉽고, 명백하다. save()를 호출하지 않으면 아무 일도 일어나지 않는다.**

또한 Spring Data JDBC는 **Aggregate Root를 존중하도록 강제** 한다. **Repository는 오직 Aggregate Root만을 위한 것** 이다. 이 제약이 오히려 더 좋고 깔끔한 설계를 만든다.

## AI 시대, 우리가 진짜 집중해야 할 것

여기서 한 가지 질문을 던지고 싶다.

**JPA를 정말 제대로 이해한다면 위의 문제들은 오히려 장점이 될 수도 있다**. 하지만 우리가 정말 제대로 알아야 하는 것이 JPA일까?

JPA는 **우발적 복잡성(Accidental Complexity)의** 영역이다. 반면 우리 회사의 비즈니스 로직, 도메인 지식은 **본질적 복잡성(Essential Complexity)이다.**

그리고 중요한 포인트가 있다.

**JPA 같은 우발적 복잡성은 공개된 자료가 많아서 AI가 잘 배울 수 있다**. Stack Overflow, 공식 문서, 수많은 튜토리얼… AI는 이미 이 영역을 잘 알고 있다.

하지만 **우리 회사의 핵심 도메인 지식은 공개되지 않기 때문에 AI가 배울 수 없는 영역이다.**

**AI가 잘할 수 없는 것을 잘하는 사람** 이 앞으로 더 높은 가치를 인정받을 것이다. JPA 튜닝에 시간을 쓸 것인가, 도메인 모델링에 시간을 쓸 것인가?

## 결론: 본질에 집중하라

물론 **JPA가 여전히 적합한 경우도 있다**. 변경할 수 없는 복잡한 레거시 스키마, 세밀한 캐싱 최적화가 필요한 읽기 중심 모놀리스, 복잡한 객체 그래프가 필요한 경우다.

하지만 **대부분의 현대 마이크로서비스 환경에서는 Spring Data JDBC가 더 적합** 하다. 시작 시간이 빠르고, 메모리 사용량이 적으며, LazyInitializationException에 방해받지 않는 수면을 취할 수 있다.

개발을 할 때 중요한 것은 **나의 의도를 동료들이 이해할 수 있도록 하는 코드의 가독성** 과 **향후 변경 비용을 낮추는 좋은 설계** 를 하는 것이다. 이를 위해서는 기술 스택 선택도 중요하지만, 도메인 전문성, 설계 역량 등이 더 중요하다.

암묵적 "마법"을 버리고, 명시적 제어와 예측 가능한 SQL을 선택하자. 그리고 아낀 시간으로 정말 중요한 것—우리 비즈니스 도메인—에 집중하자.

## 참고한 글

\- [Spring Data JDBC vs. JPA: Why Simplicity is Winning Over Hibernate Complexity in 2025](https://medium.com/@mesfandiari77/spring-data-jdbc-vs-jpa-why-simplicity-is-winning-over-hibernate-complexity-in-2025-59eba2661cb0)

\- ["Implementing Domain-Driven Design",](https://product.kyobobook.co.kr/detail/S000000935852) [Vaughn Vernon](https://product.kyobobook.co.kr/detail/S000000935852)

\- ["Migrating from JPA to Spring Data JDBC" (Spring IO 2024), Jens Schauder](https://www.youtube.com/watch?v=WYa9n0F4CRM&list=WL&index=42)

**keyword**

**이 글이 좋았다면
로 특별한 마음을 표현해 보세요.**[**오늘만 무료**](https://brunch.co.kr/@@8UrD/653)

 [![오늘만 무료 슬롯](https://img1.kakaocdn.net/thumb/C720x360.fwebp/?fname=http://t1.kakaocdn.net/brunch/service/user/8UrD/image/sQJAbi8kSVogHWwIDfm-qyfu6fM) brunch membership

청춘은 왜 파리에서 작가가 되었을까

by마테호른](https://brunch.co.kr/@@8UrD/653)

[매거진의 이전글 **개발 리더로서 나의 역할**](https://brunch.co.kr/@cleancode/94)
