---
title: "Kotlin으로 Spring AOP 극복하기! | 카카오페이 기술 블로그"
source: "https://tech.kakaopay.com/post/overcome-spring-aop-with-kotlin/"
author:
published: 2023-08-16
created: 2026-09-28
description: "Kotlin의 문법적 기능을 사용해서 Spring AOP 아쉬운 점을 극복한 경험을 공유합니다."
tags:
  - "clippings"
---

> [!summary]
> 카카오페이 해외결제서비스파티의 경험담으로, Spring AOP의 세 가지 아쉬운 점(어노테이션·Advice·Pointcut을 모두 작성해야 하는 번거로움, 프록시 구조 탓에 내부 함수 호출에는 적용되지 않는 한계, Pointcut 표현식과 SpEL 키처럼 컴파일 시점에 검증되지 않는 런타임 오류 가능성)을 짚는다. Kotlin의 후행 람다로 부가 기능을 고차 함수로 감싸는 'KotlinAOP' 방식을 제안하고, `@Transactional`을 붙인 `TxAdvice` 빈을 companion object로 노출한 `Tx.run {}`과 `@Cacheable`을 감싼 `CacheUser.cache(...) {}`로 내부 호출 문제와 캐시 키 검증 문제를 해결한다. 여러 타입을 반환할 때 쓰는 중위 함수 `and`와 구조 분해 선언, Advice가 JoinPoint로 인자를 넘기는 Reverse Argument 팁도 다룬다.

## 시작하며

안녕하세요! 해외결제서비스파티에서 서버개발 업무를 맡고 있는 포도입니다.

제가 소속된 해외결제서비스파티에서는 Kotlin + Spring Framework (코프링) 조합을 기술 스펙으로 사용하고 있습니다. Kotlin은 JVM (Java Virtual Machine) 위에서 동작하여 Java와 상호 운용 가능하며, 상대적으로 좀 더 간결한 코드로 생산성을 올리고 Null Safe와 같은 안전한 코드를 작성할 수 있습니다. 따라서 Java 기반의 웹 애플리케이션 프레임워크인 Spring Framework와도 궁합이 잘 맞으며, Spring Framework에서도 지속적으로 Kotlin 언어를 지원하고 있습니다.

이번 포스팅에서는 프로젝트에서 코프링 기술 스펙을 사용하면서, Kotlin 문법을 사용하여 Spring AOP의 아쉬운 점을 극복한 방법을 공유해 보겠습니다.

## 내용에 앞서

본격적인 내용에 앞서 AOP와 Kotlin에 대해 간단히 설명해 드리려고 합니다.

### AOP (Aspect Oriented Programming)

![AOP](https://tech.kakaopay.com/_astro/aop.CWENl699_Z19QW7z.webp)

AOP

AOP는 로깅, 트랜잭션과 같은 부가적인 기능의 모듈화로 재사용하여 생산성을 개선하는 프로그래밍 기법인데요. 대표적으로 AOP 예시인 `@Transactional` 을 살펴보면 쉽게 이해할 수 있습니다. 다음과 같이 `@Transactional` 어노테이션이 명시된 함수는 호출하기 전후로 트랜잭션 시작과 종료 로직이 삽입됩니다.

```kotlin
class UserService{

    @Transactional
    fun singUp(){
    // 트랜잭션 시작 로직이 자동으로 호출됨
    ..
    ..
    // 트랜잭션 종료 로직이 자동으로 호출됨
    }
}
```

따라서 대상이 되는 함수는 트랜잭션을 위한 로직을 작성할 필요가 없어집니다. 트랜잭션 로직을 모듈화하여, `@Transactional` 어노테이션을 명시하는 것만으로도 트랜잭션 로직을 재사용할 수 있도록 한 것입니다. 위 예시와 같이, AOP는 코드 중복을 방지하고 재사용하여 생산성을 개선하는 코드를 작성할 수 있도록 하는 프로그래밍 기법입니다.

트랜잭션 로직과 같이 삽입되는 로직을 `Advice`, 그리고 로직이 삽입될 함수를 `JoinPoint` 라고 정의하는데요. 앞으로의 설명에서도 이 용어가 계속 등장하니 꼭 기억해 두시기 바랍니다.

### Kotlin Functional Programing - Trailing Lambdas

Kotlin은 객체지향언어이며 함수형 프로그래밍 언어입니다. 여기서 Kotlin 함수형 프로그래밍 문법 중 하나인 `Trailing Lambdas(후행 람다)` 라는 재미있는 문법을 소개하겠습니다.

이 문법은 마지막에 오는 함수 형태의 인자를 람다식으로 변환하여 넘겨줍니다. 다음은 함수를 인자로 넘겨주는 호출인데요.

```kotlin
val result = delegate({1+3})
```

`Trailing Lambdas` 문법을 사용하면, 다음과 같은 표현식으로 변경할 수 있는데, 인자로 전달한 `{1 + 3}` 함수를 람다 형식으로 작성하여 간결한 코드를 작성 할 수 있습니다.

```kotlin
val result = delegate {1 + 3}
```

## Spring AOP의 아쉬운 점

AOP에 대한 간단한 리마인드와 Kotlin의 Trailing Lambdas에 대한 문법 소개는 이 정도로 마무리하고, 이제 개인적으로 느낀 Spring AOP의 아쉬운 점 3가지를 공유하도록 하겠습니다.

### 첫 번째. 구현의 번거로움

AOP는 반복되는 공통 로직을 재사용함으로써 생산성을 늘릴 수 있습니다. 여러 군데 반복되는 로직이 있다면, 생산성을 위해 AOP를 적용하고 싶은 욕구가 생기는데요. 하지만 Spring AOP는 구현하기에 다소 번거롭게 느껴질 때가 있습니다. 예시를 하나 들어보겠습니다. 명시적인 가독성을 위해서 어노테이션을 정의하여 대상을 명시하는 AOP 구현 방식을 선호하는데요. 함수의 실행 시간을 로깅하는 AOP를 구현하면 다음과 같습니다. 먼저 AOP가 적용될 함수임을 명시하기 위한 어노테이션을 정의합니다.

```kotlin
@Target(AnnotationTarget.FUNCTION)
@Retention(AnnotationRetention.RUNTIME)
annotation class LoggingStopWatch
```

그리고 어노테이션이 명시된 곳에 삽입될 `Advice` 를 정의한 클래스를 구현합니다.

```kotlin
@Aspect
@Component
class LoggingStopWatchAdvice {

   companion object {
       val logger: Logger = LoggerFactory.getLogger(this::class.java)
   }

   @Around("@annotation(com.example.springaop.aspect.LoggingStopWatch)")
   fun atTarget(joinPoint: ProceedingJoinPoint, name: String): Any? {
       val startAt = LocalDateTime.now()
       logger.info("Start At : $startAt")

       val proceed = joinPoint.proceed()

       val endAt = LocalDateTime.now()

       logger.info("End At : $startAt")
       logger.info("Logic Duration : ${Duration.between(startAt, endAt).toMillis()}ms")

       return proceed
   }
}
```

그리고 필요한 함수에 다음과 같이 사용하면, 구현한 AOP가 적용될 것입니다.

```kotlin
@Service
class UserService{

   @LoggingStopWatch
   fun signUp(){
       // ..Business Logic..
   }
}
```

위의 코드를 복기하면 어노테이션을 정의한 후 `Advice 클래스` 를 정의하였고, 과정에서 `Pointcut 표현식` 이라는 익숙하지 않은 문법도 사용하였습니다. 그리고 Pointcut 표현식으로 작성한 AOP가 실제로 잘 적용되었는지 가시적으로 확인도 필요할 것입니다. 이렇게 AOP 코드를 작성하다 보면 생각보다 번거롭게 느껴질 때가 있습니다. 많은 곳에 AOP를 적용할 것이 아니라면, 중복코드를 작성하는 게 오히려 생산성이 더 좋을지도 모르겠다는 의구심이 듭니다. 선뜻 AOP 적용에 손이 안 가게 되어, 생산성이 좋아질 수 있는 코드도 그렇지 않은 방식을 선호하게 되는 것입니다.

### 두 번째. 내부함수 호출 적용 불가

우선 Spring AOP가 어떤 방식으로 동작하는지 이해가 필요할 것 같습니다. Spring AOP는 Proxy 기반으로 동작하는데, `JDK Dynamic Proxy` 또는 `CGLib Proxy` 를 사용하여 동작합니다. 우선 두 방식의 차이점 배제하더라도, 두 방식 모두 클래스 내부 함수를 호출했을 때 내부 함수에는 AOP가 적용되지 않습니다. 다음 코드 예제를 보면, `ClientCode` 는 `userService.signUp()` 함수를 호출하고, 이어서 클래스 내부 함수인 `saveUserData()` 함수를 호출합니다.

```kotlin
@Component
class ClientCode(
   val userService: UserService
){
   fun main(){
       userService.signUp(User("podo"))
   }
}
```
```kotlin
@Service
class UserService(
   val userRepository: UserRepository
){

   @LoggingStopWatch
   fun signUp(user: User){
       this.saveUserData(user)
   }

   @LoggingStopWatch
   private fun saveUserData(user: User){
       userRepository.save(user)
   }
}
```

코드 실행 결과를 확인해 보면 `saveUserData()` 는 AOP 적용을 명시했지만, 삽입되어야 할 로직인 실행 시간 로깅이 발생하지 않았습니다. 의도와 다르게 AOP가 내부 함수 호출로 인하여 적용되지 않은 것인데요. 이 현상은 프록시의 한계점으로 인해 발생한 것입니다.

`UserService` 의 경우, 런타임에는 프록시로 감싸져 있는데요. 실제 흐름은 다음 다이어그램과 같이 동작하게 됩니다.

![UserServiceProxy 동작 흐름](https://tech.kakaopay.com/_astro/user-service-proxy.Cujv4XYA_Z1ORrEq.webp)

UserServiceProxy 동작 흐름

`ClientCode` 의 함수 호출은 프록시의 `signUp()` 함수를 호출하게 되고, 프록시는 `LoggingStopWatch` 로직 수행 중에 `UserService` 의 `signUp()` 함수를 호출합니다. 이어서 호출된 `signUp()` 함수는 클래스 내부에서 `saveUserData()` 함수를 호출합니다.

문제는 내부 함수 호출이 `this` 를 참조하고 있기 때문에 프록시를 거치지 않게 되는 데에 있습니다. 즉, AOP가 적용되지 않는 것을 의미합니다. 결국 AOP 동작 방식인 프록시를 사용하는 방법은 클래스 내부 함수 호출에 AOP가 적용될 수 없는 한계점을 갖습니다. 하지만 내부 함수 호출 시 AOP를 적용해야 하는 요구사항이 발생할 수 있습니다. 예를 들어, 외부로부터 특정 데이터를 IO로 가져온 후 데이터베이스에 적재하는 로직의 함수 등을 예시로 들 수 있을 것 같습니다.

```kotlin
@Service
class UserSyncService(
   private val userStoreRestClient : UserStoreRestClient
){
   @Transactional
   fun syncUsers(){
       val users = userStoreRestClient.requestGetAllUsers() // Long Time IO..

       // .. TX update users..
       // .. TX insert users..
   }
}
```

위 코드에서는 `@Transactional` 어노테이션을 명시하여 함수의 실행 과정에서 트랜잭션이 적용될 것입니다. 하지만 함수 내에서 외부와의 IO가 오랜 시간을 소모한다면, 중요한 자원인 트랜잭션 시간 비용이 늘어나는 문제가 발생합니다. 따라서 다음과 같은 코드를 생각할 수 있습니다.

```kotlin
@Service
class UserSyncService(
   private val userStoreRestClient : UserStoreRestClient
){

   fun syncUsers(){
       val users = userStoreRestClient.requestGetAllUsers() // Long Time IO..
       this.upsertBulkUsers(users)
   }

   @Transactional
   private fun upsertBulkUsers(user: List<User>){
       // .. TX update users..
       // .. TX insert users..
   }

}
```

트랜잭션이 필요한 로직을 별도의 함수로 정의하여, 로직의 일부만 트랜잭션 AOP가 적용되도록 의도한 것입니다. 하지만 안타깝게도 위의 설명한 프록시의 한계점으로 `upsertBulkUsers()` 함수는 트랜잭션 AOP가 적용되지 않을 것입니다.

이때 간단한 해결책으로 클래스를 분리하여, 내부 함수 호출을 우회함으로써 프록시의 한계점을 극복하는 방식을 채택할 수 있습니다.

```kotlin
@Service
class UserSyncService(
   private val userStoreRestClient : UserStoreRestClient,
   private val userSyncTxService : UserSyncTxService
){
   fun syncUsers(){
       val users = userStoreRestClient.requestGetAllUsers() // Long Time IO..
       userSyncTxService.upsertBulkUsers(users)
   }
}
```
```kotlin
@Service
class UserSyncTxService{
   @Transactional
   fun upsertBulkUsers(user: List<User>){
       // .. TX update users..
       // .. TX insert users..
   }
}
```

내부 함수 호출을 막기 위해 클래스를 분리하는 방식은, 의도한 대로 AOP가 적용될 것입니다. 하지만 AOP 적용을 위해 오히려 서비스 레이어는 단계가 증가하여 코드 복잡도가 증가하게 됩니다. 또한 클래스를 분리하는 과정에서 생산성 낭비는 AOP의 장점을 희석하게 됩니다. 결과적으로 AOP의 한계점을 우회하기 위해, AOP 장점을 희석하는 코드를 작성한 것입니다.

### 세번째. 런타임 예외 발생 가능성

Spring AOP는 런타임 예외가 발생할 가능성을 제공하는데요. 런타임 예외가 발생할 가능성을 예시 별로 살펴보겠습니다.

**Advice에서 JoinPoint를 지목하는 방식**

먼저 Advice에서 JoinPoint를 지목하는 방식을 살펴보겠습니다.

```kotlin
@Aspect
@Component
class LogingStopWatchAdvice {

   @Around("execution(* com.example.springaop.service.*Service.*(..))")
   fun aroundTarget(joinPoint: ProceedingJoinPoint): Any? {

       // ..
   }

}
```

위 코드는 Advice 클래스입니다. 그리고 `@Around` 어노테이션을 사용하여, AOP를 적용할 대상을 명시하였습니다. `@Around` 어노테이션을 살펴보면, AOP를 적용할 함수를 `Pointcut 표현식` 으로 작성했는데요. 해석해 보면, ‘ `com.example.springaop.service` 패키지에 `Service` 로 끝나는 클래스의 모든 함수에 적용해라’ 입니다. 표현식을 작성하는 것도 번거로운 일이지만, 문제는 이 표현식이 의도한 대상에 적용되는지 컴파일 단계에서 검증되지 않는 점입니다.

만약 표현식으로 정의된 대상의 패키지나 클래스명을 변경한다면 AOP가 적용되지 않는 상황이 발생합니다. 하지만 컴파일 예외는 발생하지 않고, 결국 이를 인지하는 순간은 런타임 예외가 발생할 때일 것입니다. 비즈니스로직 변경도 아닌, 패키지나 클래스명 변경이 의도하지 않은 서비스 장애로 이어질 가능성을 제공하는 것입니다.

**Advice에서 JoinPoint의 인자를 꺼내오는 방식**

다음으로 Advice에서 JoinPoint의 인자를 꺼내오는 방식입니다. 때로는 Advice에서 JoinPoint의 인자를 필요로 하는 요구사항이 있습니다. 문제는 JoinPoint의 인자를 가져올 수 있는 인터페이스를 지원하고 있지만, 인자를 식별할 수 없이 단순히 `Array<Any>` 타입으로 가져오게 되는 것입니다.

```kotlin
@Around("@annotation(com.example.springaop.aspect.LoggingStopWatch)")
fun aroundTarget(joinPoint: ProceedingJoinPoint): Any? {
   val arguments : Array<Any> = joinPoint.args
   //..
}
```

즉, Advice에서 인자를 필요하기에 JoinPoint의 인자 타입과 순서를 의도적으로 맞추어 작성해야 합니다. 물론 다른 방식으로 인자명으로 JoinPoint의 인자 값을 가져오는 방식도 있습니다. 하지만 이 또한 JoinPoint 함수의 인자명을 의도적으로 맞추어서 코드를 작성해야 합니다. 이런 코드 안에서 룰을 지켜가며 작성하더라도, JoinPoint의 인자명이나 순서가 변경되는 순간 런타임 시 예외가 발생할 것입니다. 위 예시를 살펴보았듯이, Advice에서 JoinPoint의 인자를 꺼내오기 위해서는 런타임 예외가 발생할 가능성이 다분하고, 꽤나 위험한 코드를 작성해야 할 부담이 있습니다.

**@Cacheable 어노테이션에 key를 주입하는 방식**

비슷한 맥락으로 `@Cacheable` 어노테이션도 살펴보겠습니다. Spring에서 지원하는 `@Cacheable` 어노테이션도 AOP를 기반으로 동작합니다. `@Cacheable` 어노테이션을 함수에 명시함으로써, 함수의 반환값을 캐싱하고 동일한 키로 요청이 온다면 캐시를 반환하는 AOP가 적용됩니다.

```kotlin
@Service
class CalculateService {

   @Cacheable(cacheNames = ["plus"], key = "#x+ ' ' +#y")
   fun plus(x: Int, y: Int): Int {
       return x + y
   }
}
```

문제가 될 수 있는 지점은 `@Cachable` 어노테이션의 `key` 를 주입하는 방식입니다. 캐시의 키는 변하는 값으로, 즉 변수여야 합니다. 하지만 `@Cachable` 에 `key` 인자에 변수를 부여할 수가 없습니다. 따라서 `key` 인자는 `Spring Expression Language(SpEL)` 표현식을 지원하고 있습니다. SpEL 표현식을 사용해서 JoinPoint 함수의 인자를 사용하여 캐시의 키로 주입하도록 하는 것입니다.

```kotlin
@Cacheable(cacheNames = ["plus"], key = "#x + '::' + #y" ) // JoinPoint 인자 x,y 로 key를 생성
fun plus(x: Int, y: Int): Int {
   return x + y
}
```
```kotlin
plus(1, 1) // 캐시의 키는 '1::1'
```

문제는 표현식과 JoinPoint 인자명이 불일치하더라도 컴파일 예외가 발생하지 않는다는 것입니다. 예를 들면 다음과 같은 코드입니다.

```kotlin
@Cacheable(cacheNames = ["plus"], key = "#x + '::' + #y")
fun plus(a: Int, b: Int): Int {
   return a + b
}
```

표현식에서는 JoinPoint의 인자 `x`, `y` 를 찾아 `key` 를 생성합니다. 하지만 이를 인지하지 못하고 JoinPoint 함수의 인자를 `a`, `b` 로 변경한 것입니다. 이럴 경우 캐시의 키는 `null::null` 로 들어가게 될 것입니다. 캐싱의 키가 모두 동일해지고, 함수의 반환값이 모두 동일한 버그가 발생할 것입니다. 그리고 이 버그는 컴파일에서 검증되지 않고 런타임에서 버그가 발생할 것입니다. `@Cacheable` 어노테이션에 `key` 를 주입하는 방식이 런타임 예외가 발생할 가능성을 제공하는 것입니다. 위의 세 가지 예시에서 봤듯이, Spring AOP는 런타임 예외가 발생 가능한 코드를 작성해야 하는 위험을 수반할 때가 있습니다. 따라서 이런 요소들을 모두 빌드 과정에서 검증하는 추가 코드를 작성해야 합니다. 그렇게 되면 AOP가 가진 장점인 생산성을 희석하게 될 것입니다.

## Overcome, With Kotlin + Spring Context

제가 개인적으로 Spring AOP에서 아쉽다고 느꼈던 점을 복기하면 다음과 같습니다.

- Spring AOP는 작성하기가 다소 번거롭습니다.
- Spring AOP는 내부 함수 호출 시 적용되지 않습니다.
- Spring AOP는 런타임 예외를 발생시킬 가능성을 제공합니다.

그럼, Kotlin을 사용하여 Spring AOP의 아쉬웠던 점을 극복하는 방법을 공유하겠습니다.

### 간단한 구현 With Trailing Lambdas

벌써 눈치채셨을지 모르겠지만, `Trailing Lambdas` 문법을 사용하면 정말 간단하게 AOP를 구현할 수 있습니다. 앞서 Spring AOP로 구현한 `LoggingStopWatch` 를 `Trailing Lambdas` 문법을 사용하여 구현하면 다음과 같습니다.

```kotlin
fun <T> loggingStopWatch(function: () -> T): T {
   val startAt = LocalDateTime.now()
   logger.info("Start At : $startAt")

   val result = function.invoke()

   val endAt = LocalDateTime.now()

   logger.info("End At : $endAt")
   logger.info("Logic Duration : ${Duration.between(startAt, endAt).toMillis()}ms")

   return result
}
```

그리고 다음과 같이 대상이 되는 함수에 사용할 수 있습니다.

```kotlin
@Service
class UserService{

   fun signUp() = loggingStopWatch{
       // .. Business Logic..
   }
}
```

기존에 Spring AOP를 구현하기 위해서는 어노테이션 클래스, Advice 클래스, 그리고 익숙하지 않은 Pointcut 표현식을 작성해야 했습니다. 하지만 `Trailing Lambdas` 문법을 사용 시, 함수 하나만 작성하면 AOP와 동일한 동작이 가능합니다. 이 포스팅에서는 이와 같은 구현 방식을 쉽게 설명하기 위해 공식적인 명칭은 아니지만, 간단히 `KotlinAOP` 라고 부르도록 하겠습니다. KotlinAOP는 함수의 정의로 이루어지기 때문에, 전역적으로 사용한다면 Util성 클래스 또는 패키지 레벨에 함수로 정의해서 사용할 수 있습니다. 한 클래스 내에서만 사용하고 싶다면 내부 함수로 구현하여, 생산성과 응집도를 높이는 코드 작성도 가능할 것입니다.

### 클래스 내부 함수 호출 by KotlinAOP

Spring AOP는 동작방식인 프록시의 한계점으로 인해 클래스 내부 함수 호출 시 AOP가 적용되지 않았습니다. KotlinAOP는 Spring AOP와 달리, 함수형 프로그래밍 기법을 사용하기 때문에 내부 함수 호출 또한 AOP가 동작하도록 극복할 수 있습니다.

```kotlin
@Service
class UserService(
   val userRepository: UserRepository
) {

   fun signUp(name: String, user: User){
       this.saveUserData(user, )
   }

   private fun saveUserData(user: User) = loggingStopWatch{
       // ...
   }
}
```

`saveUserData()` 함수는 클래스 내부에서 호출되었지만, KotlinAOP가 적용되어 실행 시간 로그가 남을 것입니다. 같은 맥락으로 `private`, `protect` 접근 지정자 함수도 KotlinAOP는 동작합니다. KotlinAOP는 함수 하나의 정의로 쉽게 구현할 수 있으며, 클래스 내부 함수 호출 또한 AOP를 적용할 수 있도록 극복이 가능합니다.

### @Transactional 극복해보기

경험상 내부 함수 호출의 AOP가 적용되기를 희망할 때는 `@Transactional` 어노테이션을 사용할 때입니다. 이를 KotlinAOP로 극복하고 싶지만, Spring Context에 엮여있는 트랜잭션 로직을 분석하여 KotlinAOP로 모두 구현하기에는 무리가 있었습니다. 따라서 `@Transactional` 어노테이션의 트랜잭션 로직을 그대로 사용하면서, KotlinAOP의 장점을 살린 방식을 고민했습니다. 그리고 다음과 같은 방식으로 극복할 수 있다는 사실을 알아냈습니다. 먼저 `TxAdvice` 클래스를 Spring Bean으로 정의하였습니다.

```kotlin
@Component
class TxAdvice {

    @Transactional
    fun <T> run(function: () -> T): T {
        contract {
            callsInPlace(function, kotlin.contracts.InvocationKind.EXACTLY_ONCE)
        }
        return function.run()
    }
}
```

`run()` 함수는 함수를 인자로 받아, 호출만 해주는 함수인데요. `@Transactional` 어노테이션을 명시하여 트랜잭션 로직이 삽입되도록 AOP를 적용하였습니다. 그리고 필요한 곳에 `TxAdvice Bean` 을 의존하여 다음과 같이 사용하면, 내부 함수 호출 시에도 트랜잭션이 동작하는 것입니다.

```kotlin
@Service
class UserService(
   val txAdvice: Tx.TxAdvice,
   val userRepository: UserRepository
) {

   val logger: Logger = LoggerFactory.getLogger(this::class.java)

   fun signUp(userInsert: UserInsert) {
       logger.info("signUp() 시작")
       // Business Logic..
       this.saveUserData(userInsert.toEntity())
       logger.info("signUp() 종료")
   }

   private fun saveUserData(user: User) = txAdvice.run {
       logger.info("saveUserData() 시작")
       userRepository.save(user)
       logger.info("saveUserData() 종료")
   }

}
```
![TxAdvice Transaction 로그](https://tech.kakaopay.com/_astro/tx-advice-log.BBVw3R41_Ew9e6.webp)

TxAdvice Transaction 로그

로그를 확인해 보면, 내부 함수로 호출된 `saveUserData()` 함수의 시작과 종료 시에 트랜잭션이 시작되고 종료되는 것을 확인할 수 있습니다. `@Transactional` 어노테이션을 명시한 것과 동일한 트랜잭션 로직이 삽입된 것입니다.

KotlinAOP의 장점을 사용하면서, Spring이 기존에 구현한 트랜잭션 로직을 그대로 사용할 수 있습니다. 하지만 트랜잭션이 필요할 때마다, `TxAdvice Bean` 과 의존관계를 맺기는 번거로운 일입니다. 따라서 `run()` 함수를 전역적으로 사용하기 위해, 추가로 다음과 같은 `Tx` 클래스를 Spring Bean으로 정의하였습니다.

```kotlin
@Component
class Tx(
   _txAdvice: TxAdvice,
) {

   init {
       Tx.txAdvice = _txAdvice
   }

   companion object {
       private lateinit var txAdvice: TxAdvice

       fun <T> run(function: () -> T): T {
           return txAdvice.run(function)
       }
   }
}
```

`Tx` 클래스는 초기화하면서 private 전역 변수인 `txAdvice` 에, `TxAdvice Bean` 을 할당합니다. 초기화 과정에서 `TxAdvice Bean` 이 존재하지 않는다면, Null Safe한 `_txAdvice` 변수로 인하여 빌드 진행 시 예외가 발생할 것입니다. 따라서 초기화에 대한 검증은 빌드 과정에서 자연스럽게 진행될 것입니다.

동일한 인터페이스인 `run()` 함수는 전역 함수로 정의했습니다. `run()` 전역 함수는 인자로 함수를 전달받아 `txAdvice` 변수의 `run()` 함수로 책임을 위임하게 됩니다. 두 클래스를 하나로 결합하여, 최종적으로는 다음과 같은 모습으로 완성됩니다.

```kotlin
@Component
class Tx(
   _txAdvice: TxAdvice,
) {

   init {
       txAdvice = _txAdvice
   }

   companion object {
       private lateinit var txAdvice: TxAdvice

       fun <T> run(function: () -> T): T {
           return txAdvice.run(function)
       }
   }

   @Component
   class TxAdvice {

       @Transactional
       fun <T> run(function: () -> T): T {
           return function.run()
       }
   }
}
```

이제 `TxAdvice Bean` 에 의존없이 전역적으로 트랜잭션을 사용할 수 있을 것입니다. `@Transactional` 을 사용하던 방식과 동일한 수준의 적용 방식으로, 내부 함수를 호출할 수 있습니다.

```kotlin
@Service
class UserService(
   val userRepository: UserRepository
) {

   val logger: Logger = LoggerFactory.getLogger(this::class.java)

   fun signUp(userInsert: UserInsert) {
       logger.info("signUp() 시작")

       logger.info("saveUserData() 시작")
       this.saveUserData(userInsert.toEntity())
       logger.info("saveUserData() 종료")

       logger.info("signUp() 종료")
   }

   private fun saveUserData(user: User) = Tx.run {
       userRepository.save(user)
   }

}
```
![Tx Transaction 로그](https://tech.kakaopay.com/_astro/tx-advice-log-2.qnhtwhuP_2r2OdA.webp)

Tx Transaction 로그

KotlinAOP에는 재밌는 점이 있는데, 만약 다음과 같이 내부 함수를 두 번 호출한다면 트랜잭션이 두 번 진행된다는 점을 발견할 수 있습니다.

```kotlin
fun signUp(userInsert: UserInsert) {
   logger.info("signUp() 시작")

   logger.info("saveUserData() -1 시작")
   this.saveUserData(userInsert.toEntity())
   logger.info("saveUserData() - 1 종료")

   logger.info("saveUserData() - 2 시작")
   this.saveUserData(userInsert.toEntity())
   logger.info("saveUserData() - 2 종료")

   logger.info("signUp() 종료")
}
```
![두 번의 Tx Transaction 로그](https://tech.kakaopay.com/_astro/tx-advice-log-3.GHtEQhYZ_1R0ih1.webp)

두 번의 Tx Transaction 로그

이제 하나의 함수에서 여러 내부 함수를 호출하여, 트랜잭션을 분리하여 트랜잭션 로직으로 다룰 수 있는 것입니다. 또한 KotlinAOP는 꼭 함수를 정의하는 코드와 같이 작성할 필요는 없습니다. 다음과 같이 하나의 함수 안에서 KotlinAOP 코드를 작성하여 트랜잭션을 분리하여 사용할 수도 있습니다.

```kotlin
@Service
class UserService(
   val userRepository: UserRepository
) {

   fun signUp(userInsert: UserInsert) {
       Tx.run { this.saveUserData(userInsert.toEntity()) }
       Tx.run { this.saveUserData(userInsert.toEntity()) }
   }

   private fun saveUserData(user: User) {
       userRepository.save(user)
   }

}
```

이렇게 Spring AOP 로직을 KotlinAOP와 함께 엮어서 사용하는 방법을 적용한다면, 간단한 방법으로 AOP를 적용하면서, 클래스 내부 함수 호출 또는 함수 내에서 자유롭게 AOP를 사용할 수 있습니다.

#### KotlinAOP 트랜잭션 톺아보기

KotlinAOP를 적용하여 트랜잭션을 사용하다 보니, 좀 더 활용하면 더 재밌는 코드를 작성할 수 있었습니다. 예를 들어, `Tx` 클래스의 함수를 `@Transactional` 어노테이션의 속성을 구분하여 다양하게 정의하여 사용하는 것입니다.

```kotlin
Tx.writeble {} // @Transactional
Tx.readable {} // @Transactional(readOnly=true)
Tx.withSecureDB{} // @Transactional(transactionManager = "SecureDBTransactionManager")
```

위와 같이 함수 네이밍으로 구분하여 트랜잭션을 명확히 사용한다면, 코드 가독성 관점에서도 읽기 좋은 코드를 작성할 수 있습니다.

KotlinAOP는 내부 함수 호출로 트랜잭션을 다루게 될 수 있다 보니, 다음과 같이 난감한 코드가 발생하기도 했는데요. KotlinAOP에서 내부 함수 호출을 사용하여 여러 타입의 데이터를 한번에 반환하기 번거로운 코드가 발생하는 것입니다.

```kotlin
fun example(){
   val datas : Map<String, Any> = Tx.readable {
       val users = userRepository.findByIds(userIds)
       val payments = paymentRepository.findByIds(paymentIds)
       val roles = roleRepository.findByIds(roleIDs)

       // 타입이 다른 결과값을 반환하기 위해서, Map<String,Any>를 사용, 결국 타입을 분실
       return@readble mapOf<String,Any>("users" to users, "payments" to payments, "roles" to roles
   }
}
```

그렇다고 위 코드와 같이 `Map<String, Any>` 를 사용하여 반환한다면, 타입을 잃어버리는 상황이 발생합니다. 이렇다 보니 타입을 유지하기 위해 매번 DTO를 정의해서 반환해야 하지만, 그 또한 번거로운 일이 아닐 수 없습니다. 여러 방법을 고민해 보고, `Kotlin의 중위함수(Infinx Function)` 그리고 `구조분해 선언(Destructuring Declaration)` 문법을 사용하면 이를 간단한 모습으로 해결할 수 있었습니다.

다음은 `DynamicPair.kt` 파일에 제네릭 클래스와 중위 함수를 정의한 예시입니다.

```kotlin
data class Fourth<out A, out B, out C, out D>(
   val first: A,
   val second: B,
   val third: C,
   val fourth: D,
)

data class Fifth<out A, out B, out C, out D, out E>(
   val first: A,
   val second: B,
   val third: C,
   val fourth: D,
   val fifth: E,
)

infix fun <A, B> A.and(value: B) = Pair(this, value)
infix fun <A, B, C> Pair<A, B>.and(value: C) = Triple(this.first, this.second, value)
infix fun <A, B, C, D> Triple<A, B, C>.and(value: D) = Fourth(this.first, this.second, this.third, value)
infix fun <A, B, C, D, E> Fourth<A, B, C, D>.and(value: E) = Fifth(this.first, this.second, this.third, this.fourth, value)
```

`Pair<A,B>`, `Triple<A,B,C>` 에 이어서 `Fifth<A,B,C,D,E>` 까지 최대 5개의 제네릭 타입 프로퍼티를 가지는 DTO를 정의하였습니다. 그리고 이를 체이닝하여 생성할 수 있는 `and` 라는 중위함수를 정의하였습니다. 그 결과 다음과 같이 구조분해 선언을 하여 함께 사용할 수 있습니다.

```kotlin
fun example(){
   val (users, payments, roles) = Tx.readable {
       val users = userRepository.findByIds(userIds)
       val payments = paymentRepository.findByIds(paymentIds)
       val roles = roleRepository.findByIds(roleIds)

       return@readble users and payments and roles // Triple<User, Department, Role>
   }
}
```

이렇게 중위함수와 구조분해 선언을 같이 사용한다면, 여러 타입의 데이터 반환을 번거로움 없이 읽기 쉬운 코드로 풀어 나갈 수 있습니다.

### @Cacheable 극복해보기

`@Cachable` 어노테이션을 사용한 AOP의 아쉬운 점은 `key` 인자를 SpEL 표현식을 사용하여 정의하는 것입니다. 이는 표현식에서 참조하는 인자명과 JoinPoint의 인자명과 불일치한다면, 컴파일에서 검증이 되지 않고 런타임 예외 혹은 버그가 발생합니다. 그리고 이를 KotlinAOP로 극복할 수 있습니다.

KotlinAOP의 `Trailing Lambdas` 문법을 다시 복기해 보면, ‘마지막의 오는 함수 인자의 표현식을 람다로 바꿀 수 있는 문법’ 입니다. 즉, 이 말은 인자가 함수 하나여야 한다는 것은 아닙니다. KotlinAOP는 함수뿐만 아니라 인자를 여러 개 받을 수 있습니다. 그래서 KotlinAOP를 `@Cachable` AOP와 혼합하여 사용한다면 다음과 같은 코드로 작성이 가능합니다.

```kotlin
@Service
class UserService(
   val userRepository: UserRepository
) {

   fun findById(userId: Long): UserRead = CacheUser.cache("UserRead", "userId:${userId}") { // 캐시 AOP 적용
       val user = userRepository.findById(userId).orElseThrow { throw Exception("User Not Found :${userId}") }
       return@cache UserRead(user)
   }

   fun updateUser(userId: Long, userUpdate: UserUpdate) = CacheUser.evict("UserRead", "userId:${userId}") { // 캐시 삭제 AOP 적용
       // Update User ..
   }

}
```

KotlinAOP로 구현한 `CacheUser.cache()` 함수의 사용 방식을 보면, 선행 인자로 캐시의 키를 주입하고 마지막 인자인 함수 인자를 람다로 작성하였습니다. `Trailing Lambdas` 문법을 사용하면서, 캐시의 키도 정의 할 수 있도록 인터페이스를 구현한 것입니다. 따라서 JoinPoint의 인자를 변경하더라도 컴파일 에러가 발생하여 검증 가능한 안전한 코드가 될 것입니다.

`CacheUser` 클래스의 내부를 자세히 살펴보면 `@Transactional` 과 동일한 방식을 사용하였습니다.

```kotlin
@Component
class CacheUser(
   _advice: CacheUserAdvice,
) {

   init {
       advice = _advice
   }

   companion object {
       private lateinit var advice: CacheUserAdvice
       private const val TOKEN = "::"

       // 가변인자를 사용하여, 여러개의 Any 타입의 keys 인자를 받음
       fun <T> cache(vararg keys: Any, function: () -> T): T {
           return advice.cache(generateKey(keys), function)
       }

       fun <T> evict(vararg keys: Any, function: () -> T): T {
           return advice.evict(generateKey(keys), function)
       }

       // 일관된 룰로 키 생성
       private fun generateKey(keys: Array<out Any>) = keys.joinToString(TOKEN)

   }

   @Component
   class CacheUserAdvice {
       companion object {
           private const val CACHE_NAME = "User"
       }

       @Cacheable(value = [CACHE_NAME], key = "#key")
       fun <T> cache(key: String, function: () -> T): T {
           return function.invoke()
       }

       @CacheEvcit(value = [CACHE_NAME], key = "#key")
       fun <T> evict(key: String, function: () -> T): T {
           return function.invoke()
       }
   }
}
```

`CacheUser.cache()` 함수의 `keys` 가변 인자를 사용하여 내부에서는 일관된 캐시키 생성 룰로 `key` 변수를 생성하였습니다. 그리고 Spring AOP가 적용된 `CacheUserAdvice` 클래스의 함수를 호출하면서 생성한 `key` 변수를 인자로 전달합니다. `CacheUserAdvice` 클래스의 함수는 외부로부터 정의된 key를 일관되게 전달받기 때문에, SpEL 표현식과의 인자명 불일치에 대한 런타임 예외를 예방할 수 있는 코드가 될 것입니다. 이처럼 KotlinAOP를 사용하여 Spring AOP 캐시 로직과 조합하여 사용한다면, 기존에 `@Cacheable` 어노테이션이 가지는 아쉬움을 극복할 수 있습니다.

마지막으로 SpringAOP의 Advice에서 JoinPoint의 인자를 `Array<Any>` 로 꺼내오는 방법도 개선할 수 있을 것입니다. Advice에서 JoinPoint의 인자를 꺼내오는 방식 아니라, 반대로 `cache()` 함수와 같이 JoinPoint에서 필요한 인자를 Advice에 전달하는 방식으로 변경할 수 있는 것입니다. 이는 좀 더 명확한 방식으로 필요한 인자를 Advice로 전달하여, 런타임 예외가 발생할 가능성을 예방할 수 있습니다.

#### KotlinAOP 캐시 톺아보기

지금까지의 예시는 SpringAOP의 로직을 그대로 가져와서 KotlinAOP에 적용하는 방식이었습니다. 하지만 이 방식은 활용 방안의 예시 하나일 뿐입니다. 캐시를 사용하기 위해서 `@Cachable` 어노테이션의 캐시 로직을 그대로 사용하지 않고, 새롭게 구현하여 캐싱하는 KotlinAOP를 작성하는 방법도 있을 것입니다. 다음 예시는 KotlinAOP를 사용하여, 레디스에 적재하는 캐싱 로직의 코드를 소개하려고 합니다. 먼저 다음과 같은 `CacheAspect` 클래스를 Spring Bean으로 등록하였습니다.

```kotlin
@Component
class CacheAspect(
   _redisTemplate: RedisTemplate,
) {

   init {
       CacheAspect.redisTemplate = _redisTemplate
   }

   companion object {
       lateinit var redisTemplate: RedisTemplate
           private set
   }
}
```

초기화 과정에서 전역 변수 `redisTemplate에` `RedisTemplate Bean` 을 할당합니다. 전역 변수인 `redisTemplate` 은 접근 지정자를 private로 제한하였는데요. Kotlin의 private 접근 지정자는 Java와 달리 클래스 내뿐만 아니라 동일 파일 안에서도 접근할 수 있습니다. 따라서 동일 파일 내에서 `redisTemplate` 에 접근 가능한 것은, 패키지 레벨 함수에서도 접근 가능하다는 것을 의미합니다.

`CacheAspect` 클래스가 작성된 파일에 다음과 같이 `cache()` 패키지 레벨 함수를 정의하였습니다.

```kotlin
fun <T> cache(ttl: Long, vararg key: String, function: () -> T): T {
   val redisTemplate = CacheAspect.redisTemplate
   val cached = redisTemplate.get(key)

   if (cached != null) {
       return cached as T
   }

   val result = function.invoke()

   if (result != null) {
       redisTemplate.put(key, result, ttl)
   }

   return result
}

@Component
class CacheAspect{
   //..
   //..
}
```

`cache()` 함수는 `CacheAspect.redisTemplate` 변수에 접근이 가능하기 때문에, `CacheAspect.redisTemplate` 을 사용하여 캐싱 로직을 구현하였습니다. 패키지 레벨의 함수는 전역 함수와 동일하게, 인스턴스 생성없이 사용할 수 있습니다. 그러므로, 다음과 같이 KotlinAOP를 사용하여 레디스에 적재하는 캐시 로직을 사용할 수 있을 것입니다.

```kotlin
import com.example.springaop.aspect.cache // 패키지 레벨 함수 Import

@Service
class UserService(
   val userRepository: UserRepository
) {

   fun findById(userId: Long): UserRead = cache(60000, "UserRead", "userId:${userId}") { // 캐시 AOP
       val user = userRepository.findById(userId).orElseThrow { throw Exception("User Not Found :${userId}") }
       return@cache UserRead(user)
   }

}
```

위와 같이 캐싱 로직을 구현한 것을 보여드린 것은 하나의 예시일 뿐입니다.

보여드린 예시와 같이, 필요하다면 KorlinAOP를 Spring Context 위에서의 구현 로직을 작성하는 것도 가능할 것입니다. 비즈니스 요구사항에 따라서 기존에 SpringAOP의 로직을 활용하는 방법, 또 새로운 로직을 구현하는 방법 모두 어렵지 않게 작성하실 수 있을 것입니다.

### 추가 활용 Tip - Reverse Argument

마지막으로 재밌는 팁 하나를 공유해 드리겠습니다. KotlinAOP는 함수형 프로그래밍 문법을 사용한 동작 방법으로, 함수를 인자로 전달하여 호출하는 방식으로 동작합니다. 따라서 위의 예시들을 보면 Advice에 `function : () -> T` 형태의 함수 인자를 전달하였습니다.

```kotlin
fun <T> logging(function: () -> T) : T
```

하지만 인자로 전달하는 함수를 단순히 T를 반환하는 함수가 아닌 인자를 가지는 함수를 전달할 수도 있습니다.

```kotlin
fun <T> logging(function: (MutableMap<String, Any>) -> T): T // function에 인자 추가
```

이 방식을 사용하면 오히려 KotlinAOP의 Advice에서 인자로 받은 함수를 호출할 때 인자를 넣어주고 호출해야 합니다. 즉, Advice에서 JoinPoint에 인자를 전달해 줄 수 있는 인터페이스가 제공되는 것입니다.

```kotlin
fun <T> logging(function: MutableMap<String,Any> -> T): T {
   val logData = mutableMapOf<String, Any>()
   logData["startAt"] = LocalDateTime.now()

   val result = function.invoke(logData) // logData 변수를 넘겨줌

   logger.info(logData)
   return result
}
```

그러면 JoinPoint에서는 다음과 같이 구현하게 되는데요.

```kotlin
@Service
class UserService{

   fun signUp() = logging { logData ->
       //..
       logData.put("userId", userId)
       //..
   }
}
```

위의 예시를 보면 JoinPoint에서 `logData` 라는 인자를 받아서 비즈니스 로직을 작성하면서 로그에 남기고 싶은 값들을 넣어 주게 됩니다. 그리고 함수 종료 후에, 비즈니스 로직 과정에서 추가한 로그 데이터를 같이 남길 것입니다. 이렇듯 Spring AOP에서 지원하지 않는, 반대로 Advice에서 JoinPoint로 인자를 전달하는 방식의 인터페이스를 사용할 수 있습니다. 이 인터페이스를 사용하면 Advice에서 정의한 일부 값을 JoinPoint 비즈니스 로직 과정에서 활용할 수 있을 것입니다.

## 마치며

KotlinAOP 라는 명칭의 구현 방식은, 실제로 진행해왔던 프로젝트에서 잘 활용하고 있습니다. 트랜잭션과 캐시가 대표적으로 많이 사용하고 있는데요. 이 외에도 예외 스킵, 인증 체크 등 필요한 로직에 따라서 작은 범위안에서 또는 넓은 범위안에서 정의하여 사용하고 있습니다.

돌이켜보면 코프링으로 프로젝트를 진행하면서 처음에는 익숙하지 않았지만, Kotlin이 가지는 문법적 특성을 이용해서 재밌는 코드를 작성할 수 있었습니다. 본 포스팅에 소개된 내용 외에도 Kotlin의 새로운 활용 방식이 있다면, 다음 포스팅에도 알차게 내용을 준비해 보겠습니다. 본 포스팅에 내용이 작성하시는 코드에 조금이나마 도움이 되었기를 희망합니다. 읽어주셔서 감사합니다. 😊
