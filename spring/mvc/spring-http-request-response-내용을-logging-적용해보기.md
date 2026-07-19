---
title: "[Spring] HTTP Request, Response 내용을 logging 적용해보기"
source: "https://beaniejoy.tistory.com/97"
author:
  - "[[beaniejoy]]"
published: 2023-05-17
created: 2026-07-19
description: "목표 - Spring Boot Application에서 HTTP Request, Response 내용에 대해서 logging을 적용해본다. 효과 - logging 적용을 통해 HTTP 요청마다 요청 전문과 응답 전문 내용 확인이 가능해진다. - logging을 통해 오류에 대한 디버깅과 원인 추적을 더욱 쉽고 빠르게 할 수 있다. 실무든 개인 프로젝트든 애플리케이션을 개발하거나 운용할 때 여러 에러를 마주하게 됩니다. 에러를 마주하게 되면 원인을 알아야 해결방법을 생각할 수 있기 때문에 에러 발생 원인을 찾는 것이 아주 중요합니다. 실제 업무하면서도 에러 발생 원인을 찾는데에 많은 시간을 할애하게 됩니다. 여러 단서들을 이곳 저곳에서 확인하고 원인을 추적해나가는데요. http request, respon.."
tags:
  - "clippings"
---

> [!summary]
> Korean tutorial on logging full HTTP request and response details (method, URI, client IP, headers, params, bodies, elapsed time) in a Spring Boot app for easier debugging. Implements a Kotlin `OncePerRequestFilter` using `ContentCachingRequestWrapper` and `ContentCachingResponseWrapper` so the bodies can be read without consuming the stream, and explains why a filter is preferred over an interceptor: it sees the rawest request first and the final response last.

글 작성자: beaniejoy

> 목표
> \- Spring Boot Application에서 HTTP Request, Response 내용에 대해서 logging을 적용해본다.
>
> 효과
> \- logging 적용을 통해 HTTP 요청마다 요청 전문과 응답 전문 내용 확인이 가능해진다.
> \- logging을 통해 오류에 대한 디버깅과 원인 추적을 더욱 쉽고 빠르게 할 수 있다.

실무든 개인 프로젝트든 애플리케이션을 개발하거나 운용할 때 여러 에러를 마주하게 됩니다. 에러를 마주하게 되면 원인을 알아야 해결방법을 생각할 수 있기 때문에 에러 발생 원인을 찾는 것이 아주 중요합니다.

실제 업무하면서도 에러 발생 원인을 찾는데에 많은 시간을 할애하게 됩니다. 여러 단서들을 이곳 저곳에서 확인하고 원인을 추적해나가는데요. http request, response 내용도 중요한 단서가 됩니다. 이번 게시글에서는 단서가 되는 request, response 내용이 무엇이 있는지, 그 내용들을 가지고 어떻게 logging을 적용할 것인지, 적용하는 데 있어서 필요한 설정이 무엇이 있을지에 대해서 정리해보고자 합니다.

## 📌 1. Logging할 내용 목록화하기

request, response 내용을 로깅할 때 어떤 것을 로그에 남길 것인지를 목록화하면 좋습니다.
웹서비스는 거의 HTTP 프로토콜로 움직이기 때문에 HTTP 프로토콜에서 중요한 요소들을 뽑아보았습니다.

- **request**
	\- **http method**: GET, POST, PUT, PATCH, DELETE 등...
	\- **request uri**: 요청 api에 대한 정보(ex. /api/cafes)
	\- **client ip**: 요청한 client의 ip 주소
	\- **headers**: 요청 내용에 포함된 http header 값들(ex. content-type:application/json)
	\- **request param**: 요청시 uri에 포함되어 있는 query string 내용
	\- **request body**: 요청 본문(body)에 해당하는 내용
- **response**
	\- **http status code**: http 응답에 대한 응답코드(200, 400, 401, 500 등...)
	\- **response body**: 응답 본문(body)에 해당하는 내용
- **elasped time**: 요청 ~ 응답 처리하는데 걸린 시간
```kotlin
data class HttpLogMessage(

    val httpMethod: String,

    val requestUri: String,

    val httpStatus: HttpStatus,

    val clientIp: String,

    val elapsedTime: Double,

    val headers: String?,

    val requestParam: String?,

    val requestBody: String?,

    val responseBody: String?,

) {

//...

}
```

로깅의 대상이 되는 http 프로토콜 관련 정보들을 Spring Application에 사용하기 위해 위와 같이 하나의 클래스로 정의하는 것이 좋은 것 같습니다. (이부분은 아래에서 다시 언급하도록 하겠습니다.)

## 📌 2. Filter 구성하기

본격적으로 logging 처리할 Filter를 구성해보려고 합니다.
그 전에 왜 Filter에서 구현하려고 하는지에 대해서 나름의 이유를 정리해보았습니다.

### 🔖 2-1. Filter에서 구현하는 이유

항상 개발할 때는 어떤 방식으로 구현할 것인지에 대한 **선택과 이유가 명확하면 좋습니다.**
logging을 구현하기 위해서 생각해볼 수 있는 구간이 filter와 interceptor가 있을 것 같은데요. 이 중 filter를 선택했습니다. 이유는 대부분의 프로젝트에서 filter로 logging을 처리하고 있기 때문입니다라고 하면 사실 공부하는 입장에서 별로 좋지 않은 접근이라고 생각합니다. 다른 사람들의 코드를 그냥 무지성으로 따라한 느낌이 강하기 때문이죠.

실제로 대부분의 logging 처리를 filter에서 구현하고 있고 저희 실무에서조차 filter에서 구현하고 있습니다. 왜 그런지에 대해서 생각해보면 이유를 filter와 interceptor의 구조 차이에서 찾아볼 수 있을 것 같습니다.
[https://www.baeldung.com/spring-mvc-handlerinterceptor-vs-filter](https://www.baeldung.com/spring-mvc-handlerinterceptor-vs-filter)

(구글링을 조금만 해봐도 filter와 interceptor의 차이에 대해서 설명한 글들이 많습니다. 먼저 차이점에 대해서 찾아보시고 이 글을 이어가시면 좋을 것 같습니다.)

제가 생각한 logging을 filter에서 구현하는 이유는 다음과 같습니다.

- **Filter 단계에서 가장 먼저 request 내용을 받고, response 내보낼 때 가장 마지막에서 처리**

request, response logging은 client에서 보낸 요청과 client로 보낼 응답 내용을 날 것(?) 그 자체로 확인하는 것이 좋기 때문에 client 요청 이후 가장 먼저 받아볼 수 있는 구간에서 request 내용을 logging하는 것이 좋고, client에 최종 응답을 보내기 직전인 구간에서 response 내용을 logging 하는 것이 좋다고 생각했습니다.

- **Filter 단계에서는 요청, 응답 header의 조작이 가능합니다.**

Filter 단계에서는 request, response header에 대한 내용들을 충분히 조작할 수 있습니다. logging의 목적은 client의 요청내용과 최종 응답내용에 대해서 그 자체로 확인하고자 하는 것입니다. 그렇기 때문에 interceptor보다 Filter에서 처리함으로써 client로부터 온 request header 그대로를 확인해볼 수 있고 client에 최종 응답을 보내기 직전에 최종 response 내용을 확인할 수 있습니다. (물론 LoggingFilter에 대해서 우선순위를 최상위로 설정해야할 것입니다. 이부분도 아래 코드 구현부분에서 살펴보겠습니다.)

### 🔖 2-2. 기본적인 Logging Filter 구현

```kotlin
@Component

class ReqResLoggingFilter : OncePerRequestFilter() {

    private val log = KotlinLogging.logger {}



    override fun doFilterInternal(

        request: HttpServletRequest,

        response: HttpServletResponse,

        filterChain: FilterChain,

    ) {

        val cachingRequestWrapper = ContentCachingRequestWrapper(request)

        val cachingResponseWrapper = ContentCachingResponseWrapper(response)



        val startTime = System.currentTimeMillis()

        filterChain.doFilter(cachingRequestWrapper, cachingResponseWrapper)

        val end = System.currentTimeMillis()



        try {

            log.info {

                HttpLogMessage.createInstance(

                    requestWrapper = cachingRequestWrapper,

                    responseWrapper = cachingResponseWrapper,

                    elapsedTime = (end - startTime) / 1000.0

                ).toPrettierLog()

            }



            cachingResponseWrapper.copyBodyToResponse()

        } catch (e: Exception) {

            log.error(e) { "[${this::class.simpleName}] Logging 실패" }

        }

    }

}
```

Spring Boot에서 Filter를 적용하는 방법에는 여러가지가 있는데요. Filter도 Spring Bean 등록을 통해 적용이 가능해지면서 저도 Bean 등록 방식으로 구현했습니다.

- **OncePerRequestFilter**

**OncePerRequestFilter** 를 구현했는데요. 이부분에 대한 설명도 상당히 길어지기 때문에 왜 이 Filter를 구현했는지 찾아보시면 좋을 것 같습니다. forwarding 등 여러 이유들로 하나의 요청에 Filter가 불필요하게 두 번 호출되는 경우가 존재하는데요. 이러한 중복 호출을 방지하고자 사용되는 Filter가 **OncePerRequestFilter** 라고 할 수 있습니다.
(이와 관련된 내용을 따로 정리했던 글이 있는데요. 참고하시면 될 것 같습니다. [OncePerRequestFilter 관련 이전 글 내용](https://beaniejoy.tistory.com/96))

[

\[Spring\] Filter 중복 호출되는 경우와 OncePerRequestFilter를 통한 처리

목표 - 하나의 request에서 Filter의 중복 호출되는 사례들을 알아보자 - OncePerRequestFilter를 사용함으로써 Filter 중복 호출 방지 Spring Boot를 사용해 web application을 개발하다보면 Filter를 구현해서 적용

beaniejoy.tistory.com

](https://beaniejoy.tistory.com/96)
- **CotentCachingRequestWrapper, **CotentCachingResponseWrapper****

또 주목할 것이 **CotentCachingRequestWrapper**, **CotentCachingResponseWrapper** 내용입니다. Logging Filter에서 Request, Response 데이터 내용을 확인해야 하는데요. 데이터 확인을 위해 Stream에서 데이터 read 과정을 거치게 되는데 이 때 Stream은 한 번 데이터를 읽으면 다시 해당 데이터를 읽을 수 없게 됩니다. **쉽게 말해서 한 번 읽은 데이터에 대해서 재사용이 불가능하다는 것입니다.

**InputStream으로 설명을 드리자면 read, write에 대한 pointer가 존재하는데 데이터의 끝자락(End Of File, EOF)에 도달하면 더이상 해당 Stream 내용을 읽을 수 없게 됩니다.
(이부분에 대해서 설명한 글이 있는데요. 영어로 되어있긴 하지만 한 번 읽어보시면 좋을 것 같습니다. [https://www.programmersought.com/article/80902025083/](https://www.programmersought.com/article/80902025083/))

[

How to reuse inputStream? - Programmer Sought

Quote: Do the project when it came before a question is read from the network to upload pictures to oss, but also to cut and compress images, which have to use to upload and crop images to inputStream, but also because they can not duplicate read inputstre

www.programmersought.com

](https://www.programmersought.com/article/80902025083/)

request logging을 위해 request 내부의 Stream에서 데이터를 읽는 순간 실제 request 내용 가지고 처리를 해야하는 Controller단에서 request 데이터를 가져올 수 없게 됩니다. response도 마찬가지로 client에 보낼 최종 응답 데이터를 보낼 수 없게 됩니다.

이를 해결하기 위해 나온 것이 **CotentCachingRequestWrapper**, **CotentCachingResponseWrapper** 입니다. Stream에서 데이터를 읽을 때 내부에서 해당 데이터들을 임시 저장(caching 처리)해놓았다가 실제 request, response 데이터를 가져올 때 caching해두었던 데이터들을 반환해주는 처리를 알아서 해줍니다.

response는 **copyBodyToResponse** 를 최종적으로 호출해야하는데요. 해당 메소드를 호출함으로써 실제 response에 caching 해두었던 데이터들을 담아 보내게 됩니다.

- **실제 logging 처리**
```kotlin
// Logging Filter

try {

    log.info {

        HttpLogMessage.createInstance(

            requestWrapper = cachingRequestWrapper,

            responseWrapper = cachingResponseWrapper,

            elapsedTime = (end - startTime) / 1000.0

        ).toPrettierLog()

    }



    cachingResponseWrapper.copyBodyToResponse()

} catch (e: Exception) {

    log.error(e) { "[${this::class.simpleName}] Logging 실패" }

}



// HttpLogMessage

data class HttpLogMessage(

    //...

) {

    companion object {

        fun createInstance(

            requestWrapper: ContentCachingRequestWrapper,

            responseWrapper: ContentCachingResponseWrapper,

            elapsedTime: Double

        ): HttpLogMessage {

            return HttpLogMessage(

                httpMethod = requestWrapper.method,

                requestUri = requestWrapper.requestURI,

                httpStatus = HttpStatus.valueOf(responseWrapper.status),

                clientIp = requestWrapper.getClientIp(),

                elapsedTime = elapsedTime,

                headers = requestWrapper.getRequestHeaders(),

                requestParam = requestWrapper.getRequestParams(),

                requestBody = requestWrapper.getRequestBody(),

                responseBody = responseWrapper.getResponseBody(),

            )

        }

    }



    // 이부분은 각자 취향대로 포멧 정하는 것으로,,,

    fun toPrettierLog(): String {

        return """

        |

        |[REQUEST] ${this.httpMethod} ${this.requestUri} ${this.httpStatus} (${this.elapsedTime})

        |>> CLIENT_IP: ${this.clientIp}

        |>> HEADERS: ${this.headers}

        |>> REQUEST_PARAM: ${this.requestParam}

        |>> REQUEST_BODY: ${this.requestBody}

        |>> RESPONSE_BODY: ${this.responseBody}

        """.trimMargin()

    }

}
```

실제 Logging 처리를 위한 코드를 가져왔습니다. INFO 레벨로 처리하였고 logging할 내용을 만들어내는 코드는 **HttpLogMessage** 클래스에서 담당하도록 했습니다. logging 내용을 만들어내는 부분은 구현하는 개발자 마음이기 때문에 원하는 방식으로 적용하면 됩니다.

LoggingFilter 클래스를 **@Component** 로 bean 등록을 했고 Spring Boot에서 따로 설정하지 않아도 알아서 Filter로 등록을 해줄 것입니다. 바로 애플리케이션을 실행해서 설정한 로그들을 확인해보면 다음과 같습니다.

![](https://blog.kakaocdn.net/dna/N3TZt/btsgcpRjFJN/AAAAAAAAAAAAAAAAAAAAAE-VeR5lYWnHyM1VkewSXRlOvUsIp_11tD22fC2uHi-F/img.png?credential=yqXZFxpELC7KVnFOS48ylbz2pIh7yKj8&expires=1785509999&allow_ip=&allow_referer=&signature=MOPMOwEe%2FpeIgPR57S3ug990i5U%3D)

## 📌 3. Request 식별자 및 logging format 설정하기

지금까지 각 요청마다 HTTP 내용을 로그로 기록하는 작업을 진행했습니다. 여기서 살짝 부족한 부분이 있는데요, 각 request를 구별지을 수 있는 식별자가 없습니다.

각 request에 대한 식별자(**request\_id**)가 필요한 이유는 여러가지가 있겠지만 멀티쓰레드 환경에서 여러 request들을 구분지을 수 있기 때문입니다. 멀티쓰레드 환경에서 Spring Boot는 각 request들에 쓰레드를 할당하고 이들을 동시에 처리하게 됩니다. 사실 말은 동시처리지만 OS단에서의 context switching 기법에 의해 여러 쓰레드들을 번갈아가면서 처리를 하게 됩니다.

이렇게 되면 여러 요청들이 동시에 들어왔을 때 번갈아가며 요청들을 처리하기 때문에 로그들이 섞여서 출력이 되는 경우가 대부분입니다. 각 로그들이 어떤 request에 의해 발생된 것인지 구분하기 위해 request 식별자를 사용하는 것입니다.

그리고 추가로 키바나 같은 로그 관리 툴에서 로그를 추적할 때 검색조건으로 자주 사용됩니다. 실무에서도 에러에 대한 원인을 분석할 때, 에러가 발생한 request\_id를 가지고 키바나에서 로그데이터를 검색을 하곤합니다.

이번에는 지금까지 설정한 내용을 기반으로 request 식별자를 적용하고 logback 설정파일을 통해 logging format을 따로 설정해보겠습니다.

### 🔖 3-1. Request 식별자 설정

```kotlin
// ReqResLoggingFilter

class ReqResLoggingFilter : OncePerRequestFilter() {

    private val log = KotlinLogging.logger {}



    companion object {

        const val REQUEST_ID = "request_id"

    }



    override fun doFilterInternal(

        request: HttpServletRequest,

        response: HttpServletResponse,

        filterChain: FilterChain,

    ) {

        //...



        val requestId = UUID.randomUUID().toString().substring(0, 8)



        MDC.put(REQUEST_ID, requestId)



        //...



        try {

            //...

        } catch (e: Exception) {

            log.error(e) { "[${this::class.simpleName}] Logging 실패" }

        }



        MDC.remove(REQUEST_ID)

    }

}
```

식별자는 여러 방법으로 적용할 수 있습니다. 구글링했을 때 가장 많이 검색되는 **UUID** 를 가지고 random 값을 생성해서 적용했습니다.

여기서 MDC를 이용했는데요. 이와 관련된 자세한 설명은 제가 참고했던 링크로 보시면 될 것 같습니다.
([Improved Java Logging with Mapped Diagnostic Context (MDC)](https://www.baeldung.com/mdc-in-log4j-2-logback))
핵심은 MDC는 내부에서 ThreadLocal 방식으로 동작하고 logback appender에서 접근가능하다는 것입니다.
ThreadLocal은 각 쓰레드별로 관리되는 임시저장소 같은 것이라서 request\_id와 같은 쓰레드별로 관리되어야 하는 데이터에 적격입니다.

**logback appender** 내용은 다음으로 넘어가서 보겠습니다.

### 🔖 3-2. logback 설정파일 적용

resources 디렉토리 안에 **logback-spring.xml** 파일을 생성해보겠습니다.

```xml
<?xml version="1.0" encoding="UTF-8"?>

<configuration>

    <include resource="org/springframework/boot/logging/logback/defaults.xml"/>

    <include resource="org/springframework/boot/logging/logback/console-appender.xml"/>



    <!-- Pattern -->

    <property name="LOG_PATTERN" value="%d{yyyy-MM-dd HH:mm:ss.SSS} %clr(%5level) [%15.15t] [%X{request_id}] %clr(%-40.40logger{39}){cyan} : %m%n%wEx"/>

    <!-- Request Thread Console Appender -->

    <appender name="THREAD_CONSOLE" class="ch.qos.logback.core.ConsoleAppender">

        <encoder class="ch.qos.logback.classic.encoder.PatternLayoutEncoder">

            <pattern>${LOG_PATTERN}</pattern>

        </encoder>

    </appender>

</configuration>
```

custom한 logging format을 적용하기 위해 logback 설정파일을 통해 appender를 추가해줍니다. appender는 logback 구성요소중 하나인데요. logging 대상들을 어디에 쓸 것인지(파일, 콘솔 등등), 어떤 포멧을 적용할지 등을 설정할 수 있습니다.

custom appender를 하나 추가했고 name을 **THREAD\_CONSOLE** 로 하였습니다.

여기서 주목할 점은 **LOG\_PATTERN** 인데요. 여기에 **request\_id** 를 사용하고 있습니다. 위에서 MDC 사용 이유 중 하나가 logback appender에서 접근가능하다는 특성이 있다고 설명했는데요. 이러한 특징이 여기서 빛을 발한다고 볼 수 있습니다.

별개로 **\<include>** 로 추가 적용한 내용이 있는데요. Spring Boot에서 기본적으로 포함되어 있는 logback 관련 기본 appender를 가져오기 위한 설정내용입니다.

```xml
<!-- org/springframework/boot/logging/logback/console-appender.xml -->

<included>

    <appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">

        <encoder>

            <pattern>${CONSOLE_LOG_PATTERN}</pattern>

            <charset>${CONSOLE_LOG_CHARSET}</charset>

        </encoder>

    </appender>

</included>
```

기본적으로 포함하고 있는 **ConsoleAppender** 를 가져왔습니다.

```xml
<springProfile name="local">

    <logger additivity="false" level="INFO" name="io.beaniejoy.dongnecafe">

        <appender-ref ref="THREAD_CONSOLE"/>

    </logger>



    <!-- Bootstrap class file -->

    <logger additivity="false" level="INFO" name="io.beaniejoy.dongnecafe.DongneServiceApiApplicationKt">

        <appender-ref ref="CONSOLE"/>

    </logger>



    <root level="INFO">

        <appender-ref ref="CONSOLE"/>

    </root>

</springProfile>
```

**\<springProfile>** 를 통해 특정 profile에서 appender를 적용할 수 있는데요. 저는 일단 local 환경에서만 테스트를 할 것이기에 local profile로 설정했습니다.

제 개인 프로젝트 기본 패키지가 **io.beaniejoy.dongnecafe** 이기에 해당 패키지에 custom appender(**THREAD\_CONSOLE**)을 등록했습니다. 한 가지 유의해야할 사항은 Bootstrap class file도 제가 지정한 custom appender로 적용이 된다는 점입니다. 그래서 따로 Bootstrap class file에 대해서는 기본 **CONSOLE** appender를 적용했습니다.

그 외에 나머지 부분(\<root>)에 대해서도 기본 **CONSOLE** appender를 적용했습니다.

여기까지 완료되면 웬만한 Logging Filter 관련 설정이 마무리됩니다.

## 📌 4. Filter 순서 조정

마지막으로 고려해야할 것이 있는데요. Filter의 순서를 조정해야 합니다.
프로젝트를 개발하다보면 LoggingFilter 뿐만 아니라 Security Filter 같은 여러 Filter들을 같이 적용해 사용하게 됩니다. 지금까지 Logging Filter 관련 설정한 내용들을 가지고 Security Filter가 같이 적용이 된 상황에서 request를 요청해보면 어떻게 될까요.

![](https://blog.kakaocdn.net/dna/cwj1L4/btsgex2jAgc/AAAAAAAAAAAAAAAAAAAAABsHqdKNfLKlbwmmWt0s3o1zWQ9ZmQ10uN5CLbrVt0h0/img.png?credential=yqXZFxpELC7KVnFOS48ylbz2pIh7yKj8&expires=1785509999&allow_ip=&allow_referer=&signature=0vWFwc8zodc%2BDVTEBENV8JNT7jA%3D)

위 사진과 같이 Spring Security에 적용된 Filter에 대해서는 request\_id 값이 로그에 제대로 적용이 안 된 것을 확인 할 수 있습니다.
왜 그럴까요.

![](https://blog.kakaocdn.net/dna/bFL4zZ/btsgbJJJygW/AAAAAAAAAAAAAAAAAAAAAE-1SkDd91Zau5WiyXOnlBxG2YDuAYpjJdmYtT3oXftu/img.png?credential=yqXZFxpELC7KVnFOS48ylbz2pIh7yKj8&expires=1785509999&allow_ip=&allow_referer=&signature=FWoRExVw0n69biHVK2WlLpBP4kQ%3D)

Spring Security Filter의 기본 순서값은 -100입니다. 다시 말하면 Spring Security에 적용된 Filter들은 기본적으로 모든 Filter보다 선행한다는 것입니다.

Logging Filter보다도 먼저 Security 관련 Filter들이 동작하기 때문에 MDC에 request\_id 값을 저장하기 전이라서 아무런 값이 없는 상태입니다. Security Filter도 MDC에 저장한 request\_id 값에 접근하기 위해서 Filter의 순서 조정이 필요해보입니다.

```
@Component

@Order(Ordered.HIGHEST_PRECEDENCE)

class ReqResLoggingFilter : OncePerRequestFilter() {

//...

}
```

Spring에서 제공해주는 Order 어노테이션을 이용해서 LoggingFilter를 최상위 우선순위로 설정해줍니다.

```yaml
spring:

  security:

    filter:

    order: 10 # for logging filter
```

application.yml 파일에서 spring security에 대한 filter 순서값을 대략 10으로 설정해줍니다.
이렇게 되면 LoggingFilter가 가장 먼저 동작하게 되고 MDC에 저장된 request\_id 값을 이후에 Spring Security 관련 Filter에서도 접근할 수 있게 됩니다.

## 📌 5. 결과

애플리케이션 최초 실행시 bootstrap class file(여기서는 DongneServiceApiApplicationKt)에 대해서는 기본 Console appender가 적용이 된 것을 확인할 수 있습니다.

![](https://blog.kakaocdn.net/dna/d7HRlr/btsgcrCwXix/AAAAAAAAAAAAAAAAAAAAAE51rlhmtTYO0_2KmTSTc3yqx44Mw0auuMw25t3YB5Vx/img.png?credential=yqXZFxpELC7KVnFOS48ylbz2pIh7yKj8&expires=1785509999&allow_ip=&allow_referer=&signature=4vEgt3NpYQydSEPpNnqyJ%2BTRiQ8%3D)

![](https://blog.kakaocdn.net/dna/c5mc2C/btsgaL2lNAy/AAAAAAAAAAAAAAAAAAAAAKEdKgSDuSJiRq9d7dtLmOAqbgh6dWOIIRcEEb3rDXgY/img.png?credential=yqXZFxpELC7KVnFOS48ylbz2pIh7yKj8&expires=1785509999&allow_ip=&allow_referer=&signature=Ajmmt8uDlaQge8UdtwgFFvZ%2BvJs%3D)

Spring Security에 등록된 Filter에도 request\_id가 잘 나오고 있고, LoggingFilter에서의 로그도 request\_id와 함께 제가 지정한 로그 형식대로 잘 출력된 것을 볼 수 있습니다.

**LoggingFilter 작성시 고려사항**

- 로그로 기록할 HTTP 프로토콜 내용 추리기
- 구현할 Filter 내용 설정
	\- OncePerRequestFilter 사용 이유
	\- CotentCachingRequestWrapper, CotentCachingResponseWrapper 등 내용 고려
	\- request\_id 식별자 값 적용
- logback 설정파일 적용
	\- logback-spring.xml 파일 생성
	\- custom appender, 기본 logback console appender 등 원하는 appender 적용
- LoggingFilter에 대한 최상위 순서로 조정
	\- 여러 Filter들이 존재하기 때문에 logging filter 순서를 고려해야함

이정도일 것 같네요:)

> 틀린 내용이 있을 수 있습니다. 건강한 피드백 언제나 환영합니다!

[이 글은 (새창열림) 본 저작자 표시, 비영리, 변경 금지 규칙 하에 배포할 수 있습니다. 자세한 내용은 Creative Commons 라이선스를 확인하세요.](https://creativecommons.org/licenses/by-nc-nd/4.0/deed.ko)

#### 'Spring' 카테고리의 다른 글

| [Spring Boot + kotlin 프로젝트에 ktlint 적용하기 (Multi module 통합 관리하기)](https://beaniejoy.tistory.com/108) (0) | 2024.01.18 |
| --- | --- |
| [\[Vault\] Spring Boot에 vault secret 정보를 적용해보자](https://beaniejoy.tistory.com/102) (0) | 2023.09.05 |
| [\[Spring\] Filter 중복 호출되는 경우와 OncePerRequestFilter를 통한 처리](https://beaniejoy.tistory.com/96) (0) | 2023.05.07 |
| [\[Spring\] 설정파일과 Bean 사이의 순환참조(circular references) 이슈 및 해결](https://beaniejoy.tistory.com/85) (0) | 2022.10.31 |
| [\[Spring Core #2\] 스프링 컨테이너와 스프링 빈 (스프링 핵심 원리 강의정리)](https://beaniejoy.tistory.com/82) (0) | 2022.07.12 |
