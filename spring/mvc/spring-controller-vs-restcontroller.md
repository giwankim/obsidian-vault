---
title: "Spring @Controller vs @RestController"
source: "https://dev-letter.kr/posts/spring-controller-vs-rest-controller"
author:
  - "[[강민혁]]"
published: 2026-03-05
created: 2026-07-12
description: "두 어노테이션의 차이를 시각적으로 비교하고, 언제 어떤 것을 써야 하는지 알아봅니다."
tags:
  - "clippings"
---

> [!summary]
> 면접 대비용으로 @Controller와 @RestController의 차이를 정리한 글. @Controller는 뷰 이름을 반환해 ViewResolver가 HTML을 렌더링하고, @RestController(@Controller + @ResponseBody)는 객체를 반환하면 HttpMessageConverter(Jackson)가 JSON으로 직렬화한다. 선택 기준은 클라이언트 유형 — SSR 웹에는 @Controller, 모바일·SPA 대상 REST API에는 @RestController를 사용한다.

## @Controller와 @RestController의 차이에 대해서 설명해주세요

요청부터 응답까지 두 컨트롤러의 처리 흐름 차이, JSON 직렬화 과정, 언제 어떤 것을 선택해야 하는지. 면접에서 자주 묻는 핵심 개념을 인터랙티브 시각화로 완벽히 준비합니다.

2026년 3월 5일 · 약 8분 읽기

Q. "@Controller와 @RestController의 차이를 설명하고, 각각 어떤 상황에서 사용하는지 말씀해주세요."

예상 꼬리질문

- 1\. @Controller와 @RestController의 요청 처리 흐름이 어떻게 다른가요?
- 2\. @RestController = @Controller + @ResponseBody라고 하는데 정확히 어떤 의미인가요?
- 3\. Java 객체가 JSON으로 변환되는 과정을 설명해주세요
- 4\. 두 컨트롤러의 장단점과 언제 어떤 것을 선택해야 하나요?

답변 가이드

"@Controller는 **View(HTML)를 반환** 하고, @RestController는 **데이터(JSON)를 반환** 합니다. @RestController는 @Controller + @ResponseBody의 합성 어노테이션으로, 모든 메서드에 자동으로 @ResponseBody가 적용됩니다."

"요청 처리 흐름에서 핵심 차이는 **ViewResolver를 거치느냐, HttpMessageConverter를 거치느냐** 입니다. @Controller는 뷰 이름(String)을 반환하면 ViewResolver가 템플릿을 찾아 HTML을 렌더링합니다. @RestController는 객체를 반환하면 Jackson이 JSON으로 직렬화합니다."

"선택 기준은 **클라이언트 유형** 입니다. SSR 웹 애플리케이션(Thymeleaf 등)에는 @Controller, 모바일 앱·SPA와 통신하는 REST API 서버에는 @RestController를 사용합니다."

Spring Framework를 학습하다 보면 `@Controller` 와 `@RestController` 라는 두 어노테이션을 만나게 됩니다. 둘 다 HTTP 요청을 처리하지만, **어떤 방식으로 응답을 반환하는지** 에 따라 큰 차이가 있습니다.

이 아티클에서는 요청 처리 흐름의 차이부터 JSON 직렬화 과정, 상황에 따른 선택 기준까지 시각화로 명확히 이해합니다.

---

## 1\. 기본 아키텍처 — 요청에서 응답까지

꼬리질문: "@Controller와 @RestController의 요청 처리 흐름이 어떻게 다른가요?"

HTTP 요청이 Spring 애플리케이션에 도달한 후 응답으로 변환되는 과정은 처음에는 같지만, **ViewResolver를 거치느냐, HttpMessageConverter를 거치느냐** 에서 완전히 다른 길로 나뉩니다.

**@Controller** 는 뷰 이름을 반환하면 ViewResolver가 Thymeleaf·JSP 템플릿을 찾아 HTML을 서버에서 렌더링합니다. **@RestController** 는 객체를 반환하면 HttpMessageConverter(Jackson)가 JSON으로 직렬화해 클라이언트에 전송합니다.

탭을 전환하며 두 컨트롤러의 흐름 차이를 확인해 보세요.

1

#### HTTP Request

클라이언트의 HTTP 요청 수신

↓

2

#### DispatcherServlet

Spring의 중앙 요청 처리 서블릿

↓

3

#### @Controller

MVC 컨트롤러 메서드 실행

↓

4

#### Model 생성

데이터를 Model에 저장

↓

5

#### View 이름 반환

String으로 뷰 이름 반환

↓

6

#### ViewResolver

뷰 객체를 찾음

↓

7

#### View 렌더링

JSP, Thymeleaf 등으로 HTML 생성

↓

8

#### HTTP Response

완성된 HTML을 응답으로 전송

↓

9

#### Client (렌더됨)

클라이언트가 이미 렌더링된 HTML 수신

진행률: 1/911%

전통적 MVC 방식: 서버에서 HTML을 완전히 렌더링하여 전송합니다. 초기 로딩은 빠르지만 서버 부하가 높습니다.

## 2\. 구현 방식의 차이 — 코드로 비교해보기

꼬리질문: "@RestController = @Controller + @ResponseBody라고 하는데 정확히 어떤 의미인가요?"

같은 기능을 구현하더라도 두 방식의 코드는 다릅니다. 핵심 차이는 **반환 타입** 과 **@ResponseBody 자동 적용 여부** 입니다.

@Controller는 메서드에서 뷰 이름(String)을 반환하고 Model 객체로 데이터를 전달합니다. @RestController는 메서드에서 데이터 객체를 직접 반환하며, Spring이 자동으로 JSON으로 변환합니다.

코드를 나란히 비교해보세요.

언어: java

### @Controller (전통적 MVC)

1 `@Controller`

2 `@RequestMapping("/products")`

3 `public class ProductController {`

4

5 `    @Autowired`

6 `    private ProductService productService;`

7

8 `    @GetMapping`

9 `    public String listProducts(Model model) {`

10 `        List<Product> products = productService.findAll();`

11 `        model.addAttribute("products", products);`

12 `        return "product/list";  // ← 뷰 이름 반환`

13 `    }`

14

15 `    @GetMapping("/{id}")`

16 `    public String getProduct(@PathVariable Long id,`

17 `                            Model model) {`

18 `        Product product = productService.findById(id);`

19 `        model.addAttribute("product", product);`

20 `        return "product/detail";  // ← 뷰 이름 반환`

21 `    }`

22 `}`

### @RestController (REST API)

1 `@RestController`

2 `@RequestMapping("/api/products")`

3 `public class ProductRestController {`

4

5 `    @Autowired`

6 `    private ProductService productService;`

7

8 `    @GetMapping`

9 `    public List<Product> listProducts() {`

10 `        return productService.findAll();  // ← 데이터 객체 반환`

11 `    }`

12

13 `    @GetMapping("/{id}")`

14 `    public Product getProduct(@PathVariable Long id) {`

15 `        return productService.findById(id);  // ← 데이터 객체 반환`

16 `    }`

17

18 `    @PostMapping`

19 `    public ResponseEntity<Product> createProduct(`

20 `                            @RequestBody Product product) {`

21 `        Product created = productService.save(product);`

22 `        return ResponseEntity.status(HttpStatus.CREATED)`

23 `                            .body(created);`

24 `    }`

25 `}`

#### 주요 차이점

라인 1: Controller 애노테이션 차이

Controller:`@Controller`

RestController:`@RestController`

라인 9: 반환 타입 차이: String vs Object

Controller:`String listProducts(Model model)`

RestController:`List<Product> listProducts()`

라인 12: Model 사용 vs 직접 반환

Controller:`model.addAttribute("products", products)`

RestController:`return productService.findAll()`

라인 14: 뷰 이름 vs 데이터 객체

Controller:`return "product/list"`

RestController:`return productService.findById(id)`

## 3\. JSON 변환 과정 — 직렬화 이해하기

꼬리질문: "Java 객체가 JSON으로 변환되는 과정을 설명해주세요"

@RestController가 Java 객체를 JSON으로 변환하는 과정은 **Jackson 라이브러리** 가 자동으로 처리합니다. Spring Boot는 Jackson을 기본으로 포함하고 있습니다.

개발자는 그냥 객체를 반환하면 됩니다. Spring이 Jackson을 사용하여 객체를 JSON으로 변환하고 HTTP 응답으로 전송하는 전 과정을 처리합니다.

직렬화 단계를 순서대로 확인해 보세요.

### 단계 1/4: Java 객체 (Product)

RestController가 반환하는 POJO (Plain Old Java Object)

```
new Product() {
  id: 1,
  name: "Spring Boot",
  price: 29.99,
  inStock: true
}
```

메서드에서 반환된 순수 Java 객체입니다. 필드와 Getter/Setter로 구성되어 있습니다.

진행 상황1/4

1

2

3

4

💡 팁: 각 단계 표시(원)를 클릭하면 해당 단계로 바로 이동할 수 있습니다.

## 4\. 전체 특성 비교 — 언제 무엇을 선택할까

꼬리질문: "두 컨트롤러의 장단점과 언제 어떤 것을 선택해야 하나요?"

선택 기준은 **클라이언트 유형, SEO 필요성, 확장성** 입니다. SSR(서버 렌더링) 웹에는 @Controller, REST API 서버에는 @RestController를 사용합니다.

**@Controller의 장점** 은 SEO 최적화, 초기 페이지 로딩 속도입니다. 단점은 서버 부하가 높고 다양한 클라이언트 지원이 어렵습니다. **@RestController의 장점** 은 낮은 서버 부하, 다양한 클라이언트 지원, 높은 확장성입니다.

모든 항목을 한눈에 비교해 보세요.

필터:

표시 중: 10개 항목

| 항목↑ | @Controller↕ | @RestController↕ |
| --- | --- | --- |
| SEO 친화성 | `높음` | `낮음 (별도 처리 필요)` |
| 기본 애노테이션 | `@Controller` | `@RestController` |
| 네트워크 대역폭 | `높음 (전체 HTML)` | `낮음 (필요한 데이터만)` |
| 다양한 클라이언트 지원 | `낮음` | `높음` |
| 마이크로서비스 적합성 | `낮음` | `높음` |
| 반환 타입 | `String, ModelAndView` | `객체 (자동 직렬화)` |
| 뷰 렌더링 위치 | `서버에서 수행` | `클라이언트에서 수행 (또는 없음)` |
| 서버 부하 | `높음 (뷰 렌더링)` | `낮음 (데이터 전송만)` |
| 응답 형식 | `HTML (text/html)` | `JSON (application/json)` |
| 초기 로딩 속도 | `빠름 (렌더링 완료됨)` | `느림 (클라이언트 렌더링 필요)` |

#### 항목별 상세 설명

💡 팁: 열 헤더를 클릭하여 정렬 순서를 변경할 수 있습니다.

서버 부하 (낮을수록 좋음)

확장성

나쁨좋음

좋음나쁨

C

R

#### @Controller

확장성: 30/100

서버 부하 (낮을수록 좋음): 80/100

#### @RestController

확장성: 95/100

서버 부하 (낮을수록 좋음): 20/100

#### 범례

**C** = @Controller

**R** = @RestController

좌상단: 낮은 확장성, 높은 SEO 친화성 (Controller 유리)

우하단: 높은 확장성, 낮은 SEO (RestController 유리)

💡 팁: 축을 변경하면 다양한 관점에서 두 방식을 비교할 수 있습니다. 버블 위에 마우스를 올려 상세 수치를 확인하세요.

---

## 면접 체크리스트

이 항목들을 자신 있게 설명할 수 있다면 컨트롤러 질문은 준비 완료입니다.

- \- **핵심 차이**: @Controller는 View(HTML) 반환, @RestController는 데이터(JSON) 반환
- \- **합성 관계**: @RestController = @Controller + @ResponseBody — 모든 메서드에 자동 적용
- \- **처리 흐름**: @Controller → ViewResolver → HTML, @RestController → HttpMessageConverter → JSON
- \- **직렬화**: Jackson 라이브러리가 Java 객체를 자동으로 JSON으로 변환
- \- **선택 기준**: SSR 웹 → @Controller, REST API(모바일·SPA) → @RestController
