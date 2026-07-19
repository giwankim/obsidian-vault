---
title: "직렬화,역직렬화 in Spring"
source: "https://velog.io/@supernovamk/%EC%A7%81%EB%A0%AC%ED%99%94%EC%97%AD%EC%A7%81%EB%A0%AC%ED%99%94-in-Spring"
author:
published:
created: 2026-07-19
description: "직렬화,역직렬화가 처음인 당신을 위하여"
tags:
  - "clippings"
---

> [!summary]
> Explains how Spring handles JSON serialization and deserialization behind `@RequestBody`/`@ResponseBody` via the `HttpMessageConverter` chain, with `MappingJackson2HttpMessageConverter` and its internal `ObjectMapper` doing the actual work. Covers the Jackson conditions for it to function: a default constructor plus setters (or reflection) for deserialization, and getters following Java Bean naming for serialization. Warns that any method starting with `get` is treated as a property, so unintended values can leak into the serialized JSON.

![thumbnail](https://velog.velcdn.com/images/gwk/profile/3f7c8383-982b-4ed4-85d2-d644e0b576c6/image.webp)

## 서론 🚀

우아한테크코스에서는 각자 하나의 주제를 가지고 발표를 하는 테코톡을 한다. 발표를 준비하기 전에 어떤 주제를 선정할지 고민을 하였다.

주제를 선정하는 당시의 나는 `@ResponseBody`, `@RequestBody` 에 대해서 학습하고 있었을 때인데, 이때 직렬화와 역직렬화라는 개념을 처음 알게 되었고 이 부분이 신기하여 주제를 선정하게 되었다.

직렬화 부분을 처음에는 간단하다고 생각하고 준비했는데, 직렬화의 역사는 너무 길었다. 처음에는 자바의 직렬화 부분을 먼저 준비하였는데, 자바의 직렬화만 이야기해도 10분을 넘기게 되어 빼게 되었다.

## 직렬화, 역직렬화 in Spring 🌱

![](https://velog.velcdn.com/images/supernovamk/post/21597b32-4772-446a-9632-e05e528b37c9/image.jpg)

## 직렬화란?

먼저 간단하게 직렬화와 역직렬화가 무엇인지 설명해보자면, **직렬화** 란 Java 객체를 `JSON`, `XML`, 혹은 `바이트 배열` 과 같이 저장하거나 전송할 수 있는 상태로 변환하는 과정이다. 이 과정을 통해 객체를 파일로 저장하거나 네트워크를 통해 전달할 수 있게 된다.

## 역직렬화란?

**역직렬화** 는 이와 반대의 과정으로, 직렬화된 데이터를 다시 Java 객체로 복원하는 것이다. 예를 들어 `JSON` 형식의 요청 본문을 컨트롤러에서 `User` 객체로 변환하는 것이 역직렬화이다.

## 그렇다면 우리는 왜 직렬화와 역직렬화를 사용하는 것일까?

![](https://velog.velcdn.com/images/supernovamk/post/ccfde205-7792-4088-b35a-e8d3cd4a07bf/image.jpg)

우리가 실제로 사용하는 `user` 객체는 `JVM` 의 힙 메모리에 존재한다. 이 객체는 메모리 주소를 기준으로 관리되기 때문에 외부 시스템이 직접적으로 이해할 수 없다. 따라서 외부 시스템도 이해할 수 있도록 `user` 객체를 `문자열` 혹은 `바이트` 형태로 바꿔주는 작업이 필요하다.
![](https://velog.velcdn.com/images/supernovamk/post/4b7051c8-d03a-4d79-a451-44db62880722/image.jpg)
Spring에서는 이 과정을 직접 처리하지 않고도 `@RequestBody` 와 `@ResponseBody` 어노테이션을 통해 비교적 간단하게 사용할 수 있다.

예를 들어, `@RequestBody` 는 `HTTP` 요청의 본문을 `Java` 객체로 변환해야 할 때 사용하고, `@ResponseBody` 는 그 반대로 `Java` 객체를 `HTTP` 응답 본문으로 직렬화할 때 사용한다.

## HttpMessageConverter

![](https://velog.velcdn.com/images/supernovamk/post/4202e646-e1bc-4cb0-9f3c-db5f5fcbc70c/image.jpg)
이때 직렬화와 역직렬화를 실제로 수행하는 핵심 컴포넌트가 `HttpMessageConverter` 이다. 이 인터페이스는 요청/응답 데이터를 객체로 변환하거나 객체를 응답 데이터로 변환할 수 있는 기능을 제공한다.

주요 메서드는 다음과 같다:

- `canRead()` / `canWrite()`: 특정 클래스와 `MediaType` (예: `application/json`)에 대해 읽기/쓰기 가능한지 boolean 값으로 반환한다.
- `read()` / `write()`: 실제로 객체를 읽거나 쓰는 동작을 수행한다.

![](https://velog.velcdn.com/images/supernovamk/post/98d273c0-0779-4e6b-99e5-6d0f2c30567d/image.jpg)
Spring에서는 다양한 구현체를 등록해 두고, 요청이 올 때마다 우선순위에 따라 `canRead()` / `canWrite()` 여부를 체크한 뒤, 가능한 구현체를 선택하여 사용한다.

만약 직렬화와 역직렬화를 실행하게 된다면 우선순위대로 messageConverter를 내려오게 되면서 canRead()를 확인하며 true가 된다면 해당 구현체를 사용하게 된다.

현재 Spring에서 기본적으로 `JSON` 을 처리하는 구현체는 `MappingJackson2HttpMessageConverter` 이다. 만약 다른 구현체를 사용하고 싶다면 우선순위를 조정하여 앞에 등록하면 된다.

## MappingJackons2HttpMessageConveter

![](https://velog.velcdn.com/images/supernovamk/post/59a1bc2b-db9d-4201-b484-1f7bd8420ae4/image.jpg)

이번에 더 알아볼 `MappingJackson2HttpMessageConverter` 는 Spring에서 Json을 직렬화 역직렬화 할 때 기본으로 사용하는 Jackson에서 제공한 converter이다.

MappingJackson2HttpMessageConver의 상속 구조를 따라가다 보면 httpMessageConvter를 구현하고 있다는 점을 확인할 수 있다.

![](https://velog.velcdn.com/images/supernovamk/post/e091e0b1-16f8-4c45-b0c6-bdd061da06ae/image.jpg)
`MappingJackson2HttpMessageConverter` 는 내부적으로 `ObjectMapper` 를 사용하여 `JSON` ↔ `Java` 객체 간 변환을 수행한다.

해당 객체는 Spring에 등록되어 있어서 우리가 직접 @AutoWired를 통해서 확인 할 수 있다. 따라서 등록되어 있는 `ObjectMapper` 를 설정할 수 도 있다.

보이는 것 과 같이 생성자에서 `ObjectMapper` 를 직접 주입받고 있는 것을 확인 할 수 있다.

![](https://velog.velcdn.com/images/supernovamk/post/a684a480-be05-4798-83f1-739692cbbec9/image.jpg)
실제로 `canRean()` 구현 안에서도 `ObjectMapper` 를 사용하고 있는 점을 확인할 수 있다.

## Jackson 직렬화,역직렬화 조건

여기까지 간단하게 `MappingJackson2HttpMessageConverter` 를 알아보았으나 이를 사용하기 위한 몇가지 조건이 있다.

## 역직렬화 조건

먼저 역직렬화를 하기 위한 몇가지 조건을 살펴보자.

![](https://velog.velcdn.com/images/supernovamk/post/82a809a7-71dc-44a4-af36-b685826c7c12/image.jpg)

- 클래스의 필드가 public이라면 문제없이 값을 주입할 수 있다.

![](https://velog.velcdn.com/images/supernovamk/post/9554489f-e6c5-481d-9e22-7e6c5a5eed02/image.jpg)

- 하지만 일반적으로는 필드를 private으로 선언하기 때문에, 이 경우 Jackson은 기본 생성자로 객체를 만든 뒤, setter 메서드를 통해 값을 주입한다.
- 이때 저 기본생성자의 `public` 을 `private` 으로 변경해보았는데 잘 작동하는 점이 신기하였다. 작동하는 이유는 시간이 남는다면 추가할 예정이다.아마 리플렉션을 사용하는 것 같다.

![](https://velog.velcdn.com/images/supernovamk/post/9f32070b-1e4b-4ebc-8097-5fd6b1a0fd36/image.jpg)

- 만약 `setter` 가 없어도, `Reflection` 을 통해 `private` 필드에 직접 값을 주입할 수 있다.

## 직렬화 조건

다음으로 직렬화의 조건을 살펴보자.

- 직렬화할 때도 필드가 `public` 이라면 바로 JSON으로 변환된다.

![](https://velog.velcdn.com/images/supernovamk/post/abd39aec-a607-434e-b0d4-7a5edff6418d/image.jpg)

- `private` 으로 설정되어 있다면 `getter` 의 역할이 중요해진다.
- `getter` 를 사용하여 프로퍼티를 찾아 직렬화 하게 된다.

![](https://velog.velcdn.com/images/supernovamk/post/f145b8bf-f903-44d4-9ea7-eba7092a2f88/image.jpg)

- `get` 뒤의 단어 첫 글자를 소문자로 바꾼 후 에 이를 프로퍼티 이름으로 사용하여 직렬화 하게 된다.
- 여기서 사용하는 방식은 사실 Java Bean 규칙을 따르는 것이다. 궁금하다면 더 찾아보길 바란다.

![](https://velog.velcdn.com/images/supernovamk/post/c9eff9f3-903e-4a7b-ac25-523fd3854ca2/image.jpg)

- 더 자세히 본다면 필드가 없다 하더라도 return 값을 직렬화 하고 있는 점을 확인 할 수 있다.
	![](https://velog.velcdn.com/images/supernovamk/post/d13bf674-af9d-48b2-993f-2fb6249bc997/image.jpg)
	🤔
- 만약 개발자가 별 생각 없이 직렬화 하는 객체에 get이라는 이름으로 시작하는 메서드를 사용한다면 그대로 해당 `return 값` 을 직렬화를 하게 된다. 즉 의도치 않은 직렬화가 생길 수 있다는 점이다.
- 반대로 말하면 필드에 있는 값만 직렬화 할 수 있는 것이 아닌 개발자가 원하는 만큼 직렬화 할 수 있다.

여기까지 몇가지 조건을 살펴보았다.

---

### 궁금증 🤔

근데 한가지 의문이 들었다. 역직렬화 할 때 setter가 없다 하더라도 리플렉션을 사용하여 Jackson은 값을 가져와 역직렬화 해준다.

하지만 직렬화의 경우에는 getter가 없으면 필드의 값을 리플렉션을 사용하지 않고 오류가 발생한다.

왜 이 부분에 예외를 두었는지를 고민해보았다.고민과 검색 끝에 몇가지 내가 내린 결론을 써보자면

1. 요즘 개발에서는 불변성을 중요시 여겨 setter가 없는 객체가 많다. 즉 setter가 없을 수 있다는 점을 고려하여 리플렉션을 허용한다.
2. 자바의 철학인 자바 Bean 규칙에 따라 프로퍼티 이름은 get뒤의 이름을 사용한다는 점을 지킨다. 필드의 접근에 관해서는 getter/setter를 통해서만 접근한다.
3. 역직렬화를 하는 과정보다는 직렬화를 하는 과정이 더 엄격해야한다고 생각이 든다. 역직렬화 과정에서는 어떻게든 데이터 매핑을 찾아 시도할 수 있겠지만, 직렬화를 보내는 데이터는 무결성이 보장되어야한다고 생각든다.

하지만 지나가던 크루인 머랭이 3번 생각에 대해 질문을 주었다. 클라이언트에게 직렬화 해주었을 때 만약 직렬화가 잘못되었다면 클라이언트 측에서 정보를 확인 할 수 없게 된다. 하지만 역직렬화의 문제의 경우는 서버측에 장애가 생길 수 있다는 점을 이야기 했다.

이 이야기에서도 나는 굳이 더 안전하게 다뤄야하는 것을 정해보자면 직렬화가 더 중요하다고 생각든다. 직렬화가 잘못되었다면 역직렬화 역시 문제가 생길 수 밖에 없기 때문이다. 네트워크 전송의 시작점이 직렬화이기 때문이다. 오히려 서버의 장애가 생긴다는 것은 우리가 해결할 수 있는 문제이지 않을까 싶다.

- Json 직렬화,역직렬화 에서의 경우이다. byte\[\]의 직렬화 역직렬화에서는 역직렬화의 보안은 매우 중요하게 다뤄지고 있다.

---

### 위의 조건들이 아니어도 되는데?

처음에 이 조건들을 직접 확인 해보기 위해서 따라 해보았는데 찾아본 내용들과 많이 다른 경우가 있었다. 기본 생성자가 없는 경우에도 잘 작동이 되자 예제를 만들 수 없었다.

알고보니 나의 Intellij에서 컴파일의 설정이 `-parameters` 가 켜져 있어서 런타임에도 클래스 정보를 Jackson에서 알 수 있었다. 보통 개발 환경에서 build를 Gradle로 하게 된다면 자동으로 켜지게 되는데 꺼져있는 경우를 고려하고 공부하는 것이 다양한 상황을 맞이할 때 더 좋을 것 같다는 생각이 들었다.

## Jackson 어노테이션 활용

이제는 이 직렬화를 하는 과정에서 더 잘 사용할 수 있는 몇가지 어노테이션을 소개해보고자 한다.

### @JsonIgnore

#### \- 직렬화/역직렬화 대상에서 제외시켜,보안이나 불필요한 데이터 전송을 막을 수 있다.

![](https://velog.velcdn.com/images/supernovamk/post/cf8f8c59-b2e0-4505-a2fc-a6738f31775e/image.jpg)

이 사진은 앞에서 소개한 의도치 않은 직렬화가 생기는 상황이다.
![](https://velog.velcdn.com/images/supernovamk/post/b4809f1e-d069-43b7-b974-7ffbe7cb030a/image.jpg)

이때 메서드 위에 `@JsonIgnore` 라는 어노테이션을 붙여주게 된다면 해당 메서드는 직렬화 되는 과정에서 제외된다.

![](https://velog.velcdn.com/images/supernovamk/post/37fe7eb3-9e00-4cc2-8b19-2cbb360a4879/image.jpg)

메서드 뿐만 아니라 필드에서도 사용할 수 있는데 해당 필드를 return 하더라도 직렬화 되지 않는 것을 볼 수 있다.

### @JsonCreator & @JsonProperty

![](https://velog.velcdn.com/images/supernovamk/post/9af45fe1-755b-4888-a008-f10fcfa517bd/image.jpg)

다음으로 알아볼 어노테이션은 `@JsonCreator` 와 `@JsonProperty` 이다.

앞선 조건에서 역직렬화 과정에서 기본생성자가 있어야 한다고 말했다. 하지만 해당 어노테이션을 사용한다면 기본 생성자 대신 해당 메서드를 통해 역직렬화 할 수 있다.

따라서 기본 생성자가 없어도 된다. 이때 인자가 2개 이상이 된다면 `@JsonProperty` 를 명시해주어야한다. Json의 키 이름과 생성자의 파라미터를 매핑 해줌으로써 역직렬화를 구체적으로 알려주는 것이다.

![](https://velog.velcdn.com/images/supernovamk/post/9ce0cb70-6d7c-4138-b9a8-d1f517ec8d4b/image.jpg)

`@JsonProperty` 역시 필드에도 사용이 가능한데 이 경우에는 `getter` 가 생략되어도 직렬화가 가능해진다.

또한 ()안에 프로퍼티 이름을 설정 해 줄 수도 있다.

## 마무리하며 🥭

이번 포스팅에서는 직렬화와 역직렬화에 대해 간단히 알아보았다. 그 중에서도 `JSON` 을 사용하는 방식, 특히 Spring에서 기본으로 사용하는 Jackson 기반의 `MappingJackson2HttpMessageConverter` 를 중심으로 설명하였다.

물론 `JSON` 을 다루는 라이브러리는 Jackson 외에도 `Gson`, `FastJson`, `Protobuf` 등 다양한 방식이 존재하고, `application/xml`, `text/csv` 같은 다른 미디어 타입도 처리해야 하는 상황이 생길 수 있다.

따라서 특정 라이브러리 하나를 깊게 파는 것보다는, Spring에서의 전체적인 직렬화 흐름과 **어노테이션 중심의 유연한 사용법** 을 익히는 것이 실제 서비스 개발에서는 더 유용하지 않을까 생각해보게 되었다.

[![profile](https://velog.velcdn.com/images/supernovamk/profile/0b66a513-7538-440c-87a5-a36a7fc532cc/image.JPG)](https://velog.io/@supernovamk/posts)

[슬링민키](https://velog.io/@supernovamk/posts)

하루하루는 성실하게 인생 전체는 되는대로

#### 2개의 댓글

직렬화에 대해서 잘 모르고 넘겼었는데, 포스팅 해주셔서 감사합니다!

1개의 답글

관심 있을 만한 포스트

#### [Spring에서의 직렬화](https://velog.io/@hgo641/Spring%EC%97%90%EC%84%9C%EC%9D%98-%EC%A7%81%EB%A0%AC%ED%99%94JSON-parse-error-%ED%95%84%EB%93%9C%EA%B0%80-%ED%95%98%EB%82%98%EB%B0%96%EC%97%90-%EC%97%86%EB%8A%94-DTO)

Spring은 ObjectMapper라는 클래스를 사용해 Json값을 Spring의 자바 객체로 변환한다. spring-boot-starter-web을 gradle에 의존성으로 추가하면 jackson이라는 라이브러리도 함께 가져오는데, jackson안에 ObjectMa...

2023년 5월 21일·0개의 댓글

[by **hongo**](https://velog.io/@hgo641/posts)

3

[![](https://velog.velcdn.com/images/invidam/post/819ddc8c-f5ef-402d-b37a-516d3e7bf97f/image.png)](https://velog.io/@invidam/how-deserialize-date-in-spring)

#### [스프링은 날짜를 어떻게 역직렬화할까? (@DateTimeFormat, @JsonFormat)](https://velog.io/@invidam/how-deserialize-date-in-spring)

스터디에서 코드리뷰를 하던 중, {date: "2023-12-12"} 꼴을 로 변환하는 방법에 대해 인원마다 차이가 있는 걸 발견했습니다.어느 인원은 @DateTimeFormat을 작성해주었으나, 저는 해당 어노테이션 없이도 변환이 잘 이루어졌습니다.향로님의 정리 글를...

2023년 12월 8일·1개의 댓글

[by **Hansu Park**](https://velog.io/@invidam/posts)

5

#### [\[SpringBoot\] Kotlin 환경에서 JSON 직렬화/역직렬화](https://velog.io/@tkppp-dev/SpringBoot-Kotlin-%ED%99%98%EA%B2%BD%EC%97%90%EC%84%9C-JSON-%EC%A7%81%EB%A0%AC%ED%99%94%EC%97%AD%EC%A7%81%EB%A0%AC%ED%99%94)

SpringBoot + Kotlin 에서 JSON 직렬화 및 역직렬화 정리

2022년 6월 6일·1개의 댓글

[by **tkppp**](https://velog.io/@tkppp-dev/posts)

1

[![](https://velog.velcdn.com/images/junho5336/post/0d51a746-4973-45e9-a951-ee051fda2401/image.png)](https://velog.io/@junho5336/SpringBoot%EB%8A%94-%EC%96%B4%EB%96%BB%EA%B2%8C-Json-%EB%8D%B0%EC%9D%B4%ED%84%B0%EB%A5%BC-%EB%B0%9B%EC%95%84%EC%98%AC-%EC%88%98-%EC%9E%88%EC%9D%84%EA%B9%8C)

#### [SpringBoot는 어떻게 Json 데이터를 받아올 수 있을까?](https://velog.io/@junho5336/SpringBoot%EB%8A%94-%EC%96%B4%EB%96%BB%EA%B2%8C-Json-%EB%8D%B0%EC%9D%B4%ED%84%B0%EB%A5%BC-%EB%B0%9B%EC%95%84%EC%98%AC-%EC%88%98-%EC%9E%88%EC%9D%84%EA%B9%8C)

부제: ObjectMapper에 대해 알아보자

2023년 4월 23일·2개의 댓글

[by **주노**](https://velog.io/@junho5336/posts)

7

[![](https://velog.velcdn.com/images/park2348190/post/8876ae3e-1f7a-49de-bd16-d659c5b91225/image.png)](https://velog.io/@park2348190/Jackson-ObjectMapper%EC%97%90%EC%84%9C-%EA%B8%B0%EB%B3%B8-%EC%83%9D%EC%84%B1%EC%9E%90-%EC%97%86%EC%9D%B4-Deserialization-%ED%95%98%EA%B8%B0)

#### [Jackson ObjectMapper에서 기본 생성자 없이 Deserialization 하기](https://velog.io/@park2348190/Jackson-ObjectMapper%EC%97%90%EC%84%9C-%EA%B8%B0%EB%B3%B8-%EC%83%9D%EC%84%B1%EC%9E%90-%EC%97%86%EC%9D%B4-Deserialization-%ED%95%98%EA%B8%B0)

본 내용은 Spring Boot 2.x의 Jackson을 기반으로 작성하였다.나는 API 응답 클래스를 getter 메서드와 final 필드의 조합으로 작성하는 편이다.이 경우 한 번 생성한 응답이 중간에 실수로라도 변경될 일이 없고 어떤 데이터를 표현한다는 목적 자체...

2022년 1월 2일·2개의 댓글

[by **하루히즘**](https://velog.io/@park2348190/posts)

13

[![](https://velog.velcdn.com/images/kimdy0915/post/6eaee9a1-b0f1-436c-b54f-4e3f2c28888e/image.png)](https://velog.io/@kimdy0915/NoArgsConstructor-Getter-%EC%96%B8%EC%A0%9C-%EC%99%9C-%EC%82%AC%EC%9A%A9%ED%95%A0%EA%B9%8C)

#### [@NoArgsConstructor, @Getter 언제, 왜 사용할까?](https://velog.io/@kimdy0915/NoArgsConstructor-Getter-%EC%96%B8%EC%A0%9C-%EC%99%9C-%EC%82%AC%EC%9A%A9%ED%95%A0%EA%B9%8C)

스프링부트로 게시판 만들기를 진행하면서 lombok 어노테이션을 자주 사용하곤 했다.주로 Entity 클래스와 DTO 클래스에 @NoArgsConstructor, @Getter 를 붙여 사용했는데, 이 어노테이션을 언제, 왜 사용하는지에 대해 공부해보았다. 파라미터가...

2023년 2월 15일·0개의 댓글

[by **Doyeon**](https://velog.io/@kimdy0915/posts)

1

#### [직렬화 & 역직렬화 ( JS )](https://velog.io/@youngminss/WEB-%EC%A7%81%EB%A0%AC%ED%99%94-%EC%97%AD%EC%A7%81%EB%A0%AC%ED%99%94-JS)

이전 포스팅에서 Serialize(직렬화) & Deserialize(역직렬화) 에 대한 개요 느낌의 내용을 알아봤다.이번 포스팅은 이러한 방식의 데이터 포맷방식 중, 가장 대표적인 JSON 에 대해서 알아본다.JSON(JavaScript Object Notation)자...

2021년 5월 24일·1개의 댓글

[by **위영민(Victor)**](https://velog.io/@youngminss/posts)

5

[![](https://velog.velcdn.com/images/bagt/post/4e6600b7-1269-4b8c-b36c-e19b2c5d2a61/image.png)](https://velog.io/@bagt/Redis-%EC%97%AD%EC%A7%81%EB%A0%AC%ED%99%94-%EC%82%BD%EC%A7%88%EA%B8%B0-feat.-RedisSerializer)

#### [Spring Redis 역직렬화 삽질기 (feat. RedisSerializer)](https://velog.io/@bagt/Redis-%EC%97%AD%EC%A7%81%EB%A0%AC%ED%99%94-%EC%82%BD%EC%A7%88%EA%B8%B0-feat.-RedisSerializer)

redis에 객체(dto)를 저장할 때 serializer를 통해 직렬화해주어야 한다.이 때, 선택할 수 있는 여러가지 직렬화 방법이 존재한다.Class Type을 지정해야 하며, redis에 객체를 저장할 때 class 값 대신 Classy Type 값을 JSON 형...

2023년 2월 21일·2개의 댓글

[by **bagt13**](https://velog.io/@bagt/posts)

19

[![](https://velog.velcdn.com/images/sago_mungcci/post/9a78a1ee-4bd0-4438-86d0-2c7ed6d7c066/image.png)](https://velog.io/@sago_mungcci/redis-%EB%A9%94%EC%8B%9C%EC%A7%80-%EC%A7%81%EB%A0%AC%ED%99%94-%EB%B0%8F-%EC%97%AD%EC%A7%81%EB%A0%AC%ED%99%94-%EB%AC%B8%EC%A0%9C)

#### [redis 메시지 직렬화 및 역직렬화 문제(2)](https://velog.io/@sago_mungcci/redis-%EB%A9%94%EC%8B%9C%EC%A7%80-%EC%A7%81%EB%A0%AC%ED%99%94-%EB%B0%8F-%EC%97%AD%EC%A7%81%EB%A0%AC%ED%99%94-%EB%AC%B8%EC%A0%9C)

문제채팅메시지를 레디스에 저장시 저장이 안되고 아래와 같은 오류가 발생채팅메시지를 Redis에 저장 시 저장이 안되는 오류 발생오류내용: org.springframework.data.redis.serializer.SerializationException: Cannot...

2022년 10월 6일·0개의 댓글

[by **SaGo\_MunGcci**](https://velog.io/@sago_mungcci/posts)

2

[![](https://velog.velcdn.com/images/semi-cloud/post/97b5fbb8-3860-4a2d-9c06-df5216b3c4f6/image.png)](https://velog.io/@semi-cloud/%EC%8A%A4%ED%94%84%EB%A7%81-%EC%BA%90%EC%8B%9C-%EC%A0%81%EC%9A%A9-%EA%B3%BC%EC%A0%95%EC%97%90%EC%84%9C%EC%9D%98-%EC%82%BD%EC%A7%88%EA%B8%B0)

#### [\[Spring Boot\] @Cacheable 동작 과정과 Redis 직렬화 방식에 대해 알아보자](https://velog.io/@semi-cloud/%EC%8A%A4%ED%94%84%EB%A7%81-%EC%BA%90%EC%8B%9C-%EC%A0%81%EC%9A%A9-%EA%B3%BC%EC%A0%95%EC%97%90%EC%84%9C%EC%9D%98-%EC%82%BD%EC%A7%88%EA%B8%B0)

☁️ Redis를 사용한 이유? \`Redis\` 나 \`Memcached\` 를 사용하는 방법은 글로벌 캐싱 전략이다.

2023년 9월 10일·0개의 댓글

[by **Loopy**](https://velog.io/@semi-cloud/posts)

1

[![](https://velog.velcdn.com/images/gongmeda/post/a43d0fd1-d7b8-4870-847c-ff7afd3dadc6/image.png)](https://velog.io/@gongmeda/Java-Record-%ED%86%BA%EC%95%84%EB%B3%B4%EA%B8%B0-Spring-%EC%97%90%EC%84%9C%EC%9D%98-Record-%EC%82%AC%EC%9A%A9-%EC%82%AC%EB%A1%80%EC%99%80-%ED%95%A8%EA%BB%98)

#### [Java Record - Spring에서의 사용 사례와 함께](https://velog.io/@gongmeda/Java-Record-%ED%86%BA%EC%95%84%EB%B3%B4%EA%B8%B0-Spring-%EC%97%90%EC%84%9C%EC%9D%98-Record-%EC%82%AC%EC%9A%A9-%EC%82%AC%EB%A1%80%EC%99%80-%ED%95%A8%EA%BB%98)

Java Record와 Spring에서의 사용 방식에 대해 알아봅니다.

2023년 11월 8일·0개의 댓글

#### [@JsonIgnore, @JsonIgnoreProperties, @JsonIgnoreType차이점](https://velog.io/@hth9876/JsonIgnorePropertiesignoreUnknown-true)

json 데이터를 받아와서 객체로 맵핑할 때 클래스에 선언되지 않은 프로퍼티가 json에 있으면 오류 발생 (json 구성 = 클래스 구성)이럴 때 예외 발생시키지 말고 무시출처: https://darksilber.tistory.com/280 IT 개발 / 게...

2022년 1월 14일·0개의 댓글

[![Powered by GraphCDN, the GraphQL CDN](https://i.imgur.com/BMhDSUt.png)](https://graphcdn.io/?ref=powered-by)
