---
title: "지연이체 서비스 개발기: 은행 점검 시간 끝나면 송금해 드릴게요! (feat. 발표 후기) | 카카오페이 기술 블로그"
source: "https://tech.kakaopay.com/post/ifkakao2024-delayed-transfer/"
author:
published: 2024-12-10
created: 2026-06-26
description: "Kafka 기반 지연이체 서비스를 재설계하고 개발한 경험과 if(kakao) 발표 소감을 공유합니다."
tags:
  - "clippings"
---

> [!summary]
> 카카오페이 송금 개발자가 RabbitMQ 지연 큐 기반 지연이체 서비스를 Kafka 기반으로 재설계한 경험을 정리한다. 중복 송금 방지(DELAY 상태 체킹, 유저락, userId를 Record Key로 활용해 같은 사용자 건을 같은 Consumer로 라우팅)와 성능 최적화(Consumer·파티션 수 조정, Batch Read 20건, 멀티스레드 10개)를 통해 은행 공통 점검 시간 송금 실행 시간을 68분에서 8분으로 약 8배 단축했다. if(kakao) 발표 준비 회고도 함께 담겨 있다.

> 요약: 카카오페이 서버 개발자 엘모는 if(kakaoAI)2024에서 지연이체 서비스를 Kafka 기반으로 재설계한 경험을 발표하고, 이를 기술 블로그에 정리했습니다. RabbitMQ에서 Kafka로의 전환 과정에서 아키텍처 설계, 중복 방지, 성능 최적화 등의 문제를 해결하며 처리 속도를 8배 이상 개선한 방법을 공유합니다. 인생 마일스톤의 한 지점이었던 if(kakao) 발표 준비 과정까지 함께 확인할 수 있습니다.

💡 **리뷰어 한줄평**

**peter.mj** 아키텍처를 설계하며 한 번쯤 고민해 볼 만한 포인트들이 잘 정리되어 있는 글입니다. 기존 서비스의 아키텍처를 바꾸거나 새로운 아키텍처를 설계하시는 분들이 이 글을 읽는다면 혹시 놓치고 지나칠뻔한 부분들을 다시 한번 꼼꼼하게 생각해 볼 기회도 가질 수 있게 될 것 같아요.

**piglet.xd** 점진적으로 아키텍처를 확장하고, 개선하는 과정 속의 고민들이 잘 녹여있는 글입니다. if(kakao) 발표 영상과 기술 블로그 글을 통해서 엘모가 어떤 문제를 고민했으며, 이를 어떻게 해결했는지 같이 구경해 보아요!

## 시작하며

🔗 if(kakao) 발표 영상 보러 가기: [지연이체 서비스 개발기: 은행 점검 시간 끝나면 송금해 드릴게요!](https://youtu.be/LECTNX8WDHo?si=XxDmUo9I5ScOlPO8)

안녕하세요! 카카오페이 송금 서비스를 개발하는 서버 개발자 엘모입니다.

이번 if(kakaoAI)2024 발표에서 ‘지연이체 서비스 개발기: 은행 점검 시간 끝나면 송금해 드릴게요!’ 주제로 카카오페이 지연이체 서비스를 Kafka 기반으로 재설계하고 개발한 경험을 공유드렸습니다.

이번 기술 블로그 콘텐츠에서는 발표 준비 비하인드를 시작으로 지연이체 서비스 아키텍처와 Kafka 기반 아키텍처 설계 시 고려사항에 대해 전달하고자 합니다. 개발자 컨퍼런스 발표를 준비하고 있거나 아키텍처에 관심 있는 분들이라면 영상에 이어 이번 콘텐츠도 읽어 보세요!

### if(kakao) 발표 왜 했니?

개발 시작한 지 얼마 안 되었을 때쯤, if(kakao)dev 2019 컨퍼런스를 보며 ‘저기서 발표할 수 있는 개발자가 되어야겠다.’ 마음먹었습니다. 제 개발자 인생 마일스톤의 한 지점이었습니다. 그리고 5년 뒤 if(kakaoAI)2024에서 발표할 수 있는 기회가 찾아왔습니다! 사실 정말 할 수 있을까, 해도 되는 것일까 많은 고민이 되었지만, 할 거면 빨리 하라는 조언 덕분에 일단 한 번 해보기로 했습니다.

발표자 선정 이후 이제 무엇을 발표해야 하는가가 고민이었습니다. 작년에 지연이체 서비스를 개발하면서 서버 개발자로서 많이 배울 수 있었기에 이 경험을 공유하고자 했습니다.

### 험난한 if(kakao) 발표 준비

본격적으로 발표 준비를 시작하면서, 예상보다 많은 과정들이 필요함을 알게 되었습니다. 그중 발표를 처음 듣는 분들에게 어떻게 하면 발표 내용을 잘 전달할 수 있을지 많은 고민이 필요했습니다. 전체적인 발표 내용 흐름 구성에 어려움이 있었지만, 스토리를 다듬을수록 전달력이 높아지는 것을 느낄 수 있었습니다. 그리고 매 리허설마다 피드백들이 쏟아졌지만 피가 되고 살이 되는 조언들이었기에 최대한 수용하며 내용을 발전시켜 나갔습니다.

![진짜최종의최종의최종의최종.jpg](https://tech.kakaopay.com/_astro/many_versions.CSNk6Jxl_nWooF.webp)

진짜최종의최종의최종의최종.jpg

발표 자료 및 내용 관련해서 받은 피드백들은 다음과 같습니다. 전체 스토리부터 특정 표현, 중간 랩업 장표 추가 등 여러 피드백을 수용해 발표 내용을 더욱 탄탄하게 했습니다.

```plaintext
• 프로세스 부분 장표 쪼개기
• 망했다, 찔렀다 같은 워딩 수정하면 좋을 것 같아요
• 앞부분 재설계 언급이 없다 보니 레거시 down 내용이 갑자기 왜 나왔나 싶네요
• 성능 개선 과정이 언급되어야 할 것 같네요
• 중간 랩업 장표가 있는 게 좋을 것 같아요
등등
```

발표 내용뿐 아니라 발표 스킬 관련해서도 스피치 강사님에게 많은 조언을 받았는데요. 기억에 남는 피드백에는 이런 것들이 있었네요.

```kotlin
• 전체적으로 더 강약 살리기
• 자연스럽게 내 입에 맞는 말로 스크립트 수정하기
• 시선과 표정 굳어있음
• 말하면서 손목 흔들지 말기
• 음성이 불안하니 가르쳐준 목소리 훈련하기
• 마이크 대고 말할 때 쩝쩝거리지 말기
등등
```

발표 준비 과정에서 스스로 인지하지 못했던 부분들을 알게 되었고, 이를 개선해 발표 전달력을 높이고자 했습니다.

신청 당시 생각했던 것과는 달리, if(kakao) 발표자가 되어 4개월 동안의 준비 과정이 쉽지만은 않았습니다. 일정은 타이트하고 현업도 병행해야 했지만, 주변 동료 분들의 많은 피드백과 응원 덕분에 무사히 발표를 마칠 수 있었습니다.

### 이번 포스팅에서는!

if(kakao) 발표에서는 지연이체 서비스 아키텍처 설계부터 릴리즈하며 마주한 문제와 해결 에피소드까지 전해드렸는데요. 이번 포스팅에서는 발표 내용 중 아키텍처에 좀 더 집중해서 정리하고 다뤄보고자 합니다.

지금부터는 지연이체 서비스의 아키텍처와 Kafka 기반 아키텍처 설계 시 고려해야 할 점들에 대해 알려드리겠습니다. 아직 영상을 보지 못하셨다면 [영상](https://youtu.be/LECTNX8WDHo?si=XxDmUo9I5ScOlPO8) 먼저 보고 오시길 추천드립니다.

## 카카오페이 지연이체 서비스

### 지연이체 서비스 소개

![](https://tech.kakaopay.com/_astro/introduce.D5pmrBkz_ZaVWss.webp)

혹시 위 화면들 보신적 있나요? 늦은 밤 송금 시도를 하면 ‘은행 점검 시간이에요.’ 화면이 뜨는데요. 여기서 송금 예약하기를 누르면 지연이체 송금이 등록되고, 은행 점검 시간이 끝나면 자동으로 송금이 실행됩니다. 이처럼 **카카오페이 지연이체 서비스** 는 **은행 점검 시간 종료 후, 송금해 주는 서비스** 입니다.

### RabbitMQ 기반 아키텍처

기존 지연이체 서비스는 RabbitMQ를 사용하여 지연 큐 기반으로 작동하고 있었습니다.

![](https://tech.kakaopay.com/_astro/rabbit_arch.Cc-8GzKw_M2Kyk.webp)

위 아키텍처를 구체적으로 설명하면, 다음과 같은 순서로 작동합니다.

클라이언트가 지연이체 등록 요청
→ API 서버에서 은행펌을 요청하여 은행 점검 완료 시간을 조회
→ DB에 송금 정보 저장
→ 점검 완료 시간을 고려하여, x분 뒤 송금 실행할지 계산 후, x값과 함께 송금 건 지연 큐로 발행
→ x분이 지나면, 해당 송금 건 실행 큐로 이동
→ Consumer에서 해당 송금 건 Consume 하여 송금 실행

### 지연이체 서비스에 찾아온 위기

위 프로세스로 동작하는 RabbitMQ 아키텍처 기반의 지연이체 서비스에 위기가 찾아왔습니다.

사내 공용 표준 메시지 큐를 Kafka로 정했고, Kafka만 운영할 것이라는 사내 공지가 떴기 때문입니다. RabbitMQ 운영을 중단하면 지연이체 서비스도 같이 중단될 위기에 처했습니다. 하지만 지연이체 서비스는 내리면 안 되므로 재설계를 피할 수 없게 되었습니다.

## New 아키텍처를 찾아서

지금부터는 지연이체 서비스의 새로운 아키텍처를 찾아가는 과정을 설명하겠습니다.

### 1단계) 핵심 기능 구현한 아키텍처

지연이체 서비스의 핵심 기능은 은행 점검 시간 종료 후, 자동으로 송금해주는 것이었습니다. 참고로 우리나라에는 다양한 은행들이 있는데요. 은행 점검 시간이 공통인 경우도 있었지만, 조금씩 다른 경우도 꽤 많습니다. 이러한 경우에도 은행 점검 시간이 종료되면, 자동으로 송금해 주어야 했습니다.

- 지연이체 등록 API 개발
	먼저, 지연이체 등록 API를 개발했습니다.
![](https://tech.kakaopay.com/_astro/delay_register_api.BAbHHeyN_Z10id0C.webp)

사용자에게 ‘지연이체 등록할까요?’ 안내 화면이 뜨고 사용자가 버튼을 누르면, API 서버로 지연이체 등록 요청이 갑니다. API 서버에서는 은행펌을 요청하여 점검 완료 시간을 조회 후, DB에 송금 정보와 송금 실행 예정 시간을 DELAY 상태로 저장하게 됩니다.

- 지연이체 실행 스케줄러 개발
![](https://tech.kakaopay.com/_astro/delay_execute_simple.DYv3i6Jr_h324S.webp)

지연이체 실행 단계에서는 스케줄러가 5분마다 돌면서, 상태가 DELAY이면서 송금 실행 예정 시간에 도달한 것들을 읽어와 내부 서버에 송금 실행을 요청하는 방식으로 구현하였습니다.

- 문제점
	5분마다 도는 스케줄러가 한 번에 수천 건 이상의 송금건을 읽어서 송금을 실행해야 했습니다. 하지만 단 5분 안에 수천 건의 송금을 완료하는 것은 지금 구조에서는 불가능하기 때문에 문제가 생길 수밖에 없었습니다.

### 2단계) 여러 대의 스케줄러 기반 아키텍처

두 번째 단계로 그렇다면 ‘스케줄러를 늘려볼까?’ 생각해 보았습니다. 여러 대의 스케줄러를 두어서 수 천 건의 송금 실행을 나눠서 처리하는 방식입니다.

![](https://tech.kakaopay.com/_astro/multiple_schedules.tSySujod_oKhxh.webp)

- 문제점
	여러 대의 스케줄러를 두게 된다면 겹치지 않게 송금 건들을 읽어와야 하므로 복잡한 분기를 피할 수 없을 것이고, 인프라적으로도 용이해 보이지 않았습니다. 게다가 여러 대의 스케줄러가 한 번에 송금 실행 요청을 한다면 송금 실행 서버에도 부담을 줄 것으로 보였습니다.

### 최종 단계) Kafka 기반 아키텍처

1~2단계를 거쳐 최종적으로 메시지 큐를 두기로 했고 사내 공용 메시지 큐인 Kafka를 사용하여 Kafka 기반 아키텍처를 설계했습니다.

![](https://tech.kakaopay.com/_astro/kafka_arch.BfSZS2-0_Z1ID7QA.webp)

Kafka 기반 지연이체 실행 아키텍처를 설명하자면, 스케줄러가 5분마다 돌면서 송금 실행할 건들을 읽고 Kafka에 Produce까지 합니다. 그러면 Consumer가 송금 건을 Consume 하여 내부 서버에 송금 실행을 요청합니다. 여기서 토픽은 transfer-delay 토픽만 간단하게 두었고 사내 초기 설정에 따라 파티션은 3개, Consumer는 2대로 두었습니다.

하지만 다음과 같은 이슈들에 대해 고민해야 했습니다.

- 토픽에 같은 송금 건이 쌓인다면?
	혹시라도 토픽에 같은 송금 건이 쌓인다면 같은 송금 건이 중복으로 실행될 수 있었습니다. 이를 방지하기 위해 우선은 가장 기본적인 상태 체킹 로직을 추가했습니다. 이미 송금 실행이 시작되어 DELAY 상태가 아니라면 Skip 되도록 처리했습니다. 추후에는 스케줄러에서 PREPARATION 상태로 변경 후 Kafka로 Produce 하여 다음 스케줄러에서 돌 때 다시 읽히지 않도록해서 애초에 토픽에 같은 송금 건이 쌓이지 않도록 했습니다.
- Consumer에서 동시에 같은 송금 건을 Consume 한다면?
	희박한 확률이기는 하지만 Consumer 2대에서 같은 송금 건을 동시에 읽고 송금을 실행한다면, 여전히 중복 송금이 발생될 수 있었습니다. Consumer 동시 소비로 인한 중복 송금을 방지하고자, 송금을 실행하고 상태를 변경하는 부분에 유저락을 잡아주었습니다. 혹여라도 동시에 같은 송금 건을 실행하려 해도 유저락이 잡혀있기 때문에 다른 한 건은 송금이 실행되지 않도록 했습니다.
- 유저락으로 인해, 송금 실패가 늘어난다면?
	지연이체 서비스 특성상 한 사용자는 여러 건의 지연이체를 등록할 수 있었습니다. 그렇다 보니 한 사용자의 여러 송금 건이 여러 Consumer에서 동시에 Consume 된다면, 유저락으로 인해 한 건만 송금이 실행되고 나머지 건들은 실패날 수밖에 없는 상황이었습니다.
![](https://tech.kakaopay.com/_astro/user_lock_fail.P8XkTKVJ_19APEn.webp)

그래서 같은 사용자의 송금 건들은 같은 Consumer에서 처리되도록 했습니다. 같은 사용자의 송금 건들은 한 Consumer에서 소비되도록 하여 순차적으로 모든 송금 건들을 성공적으로 실행시켜 주기로 했습니다.

![](https://tech.kakaopay.com/_astro/user_same_consumer.CuPn4X31_Z2uRQ8E.webp)

- 어떻게 같은 Consumer로 보낼까?
	스케줄러에서 Kafka로 Produce 할 때, Record Key 값에 userId를 넣어주었습니다. 동일한 사용자의 송금 건들은 같은 파티션으로 가도록 하여, 같은 Consumer에서 순차적으로 처리될 수 있도록 했습니다.
![](https://tech.kakaopay.com/_astro/record_key.DvhPlYfb_ZqeoTA.webp)

## 최최종 단계) 실행 속도 부스트업!

아키텍처는 어느 정도 완성이 되었지만, 은행 공통점검 시간에 등록된 송금 건 실행이 오래 걸리는 성능적인 이슈가 있었습니다. 그래서 송금 실행 속도를 높이기 위해 다음 사항들을 적용했습니다.

### 적절한 Consumer, 파티션 수 설정

기존 파티션 개수 3개에 맞춰서 Consumer를 2대에서 3대로 늘렸습니다. 주의할 점은 여기서 Consumer 대수를 더 늘려도, 토픽 파티션이 3개로 설정되어 있었기 때문에 3대 초과된 Consumer들은 놀고 있게 된다는 점입니다. 파티션 개수를 설정할 때는 파티션은 한 번 늘리면 다시 줄이기 힘들다는 점을 염두해야 합니다. 한 번 늘린 파티션 수를 줄이려 하면 InvalidPartitionsException이 발생하기 때문입니다.

### 다건으로 메시지 Consume 하기

Consumer에서 Batch Read로 설정하여, 메시지를 한 번에 다건으로 Consume 하도록 했습니다. 한 번에 얼마나 Consume 할지 정하는 값은 송금 실행 내부 서버 부담과 목표 송금 실행 시간을 고려하여 20으로 설정했습니다.

### Multi Thread 적용

하지만 다건으로 Consume 해서 한건 한건씩 처리하면 실행속도가 달라지지 않을 것이므로, 멀티스레드를 적용하여 송금이 실행되도록 했습니다. 여기서 스레드 수는 몇 개로 해야 하는가에 대해서는 목표 실행 시간과 송금 실행 서버 부담을 고려하여 10개로 설정했습니다.

### Consumer Code

```kotlin
private val forkJoinPool: ForkJoinPool = ForkJoinPool(10)

@KafkaListener(
  topics = ["transfer-delay"],
  containerFactory = "batchKafkaListenerContainerFactory",
  groupId = "kafka-consumer",
  properties = [
    "max.poll.records:20"
  ]
)
fun listen(
    @Headers headers: MessageHeaders, @Payload delayMessages: List<TransferDelayMessage>
): ConsumerResult {
    return try {
        val groupedMessages = delayMessages.groupBy { it.userId }

        forkJoinPool.submit {
            groupedMessages.values.parallelStream().forEach { messages -> delaySend(headers, messages) }
        }.join()

        ConsumerResult.success()
    } catch (ex: Exception) {
        log.error { "[ForkJoinPool Exception]. error:$ex" }
        ConsumerResult.fail()
    }
}
```
```kotlin
@Configuration
class KafkaConsumerConfig(
    private val kafkaConsumerProperty: KafkaConsumerProperty
) {
    @Bean
    fun batchKafkaListenerContainerFactory(): ConcurrentKafkaListenerContainerFactory<String, Any> {
      val containerFactory = ConcurrentKafkaListenerContainerFactory<String, Any>()
      containerFactory.consumerFactory = DefaultKafkaConsumerFactory(kafkaConsumerProperty.properties)
      containerFactory.isBatchListener = true
      containerFactory.containerProperties.ackMode = ContainerProperties.AckMode.BATCH
      containerFactory.setMessageConverter(BatchMessagingMessageConverter(StringJsonMessageConverter(objectMapper)))
      return containerFactory
    }

    @Component
    @ConfigurationProperties("money-kafka.consumer")
    class KafkaConsumerProperty(val properties: Map<String, String>)
}
```

### 개선 전후 지연이체 송금 실행 시간 비교

- 은행 공통 점검 시간 등록된 송금 건들 기준

|  | 개선 전 | 개선 후 |
| --- | --- | --- |
| Consumer 대수 | 2 | 3 |
| Read Records 수 | 1 | 20 |
| Thread 수 | 1 | 10 |
| 1분 당 처리 건수 | 91건 | 728건 |
| 실행 시간 | 68분 | 8분 |

최종적으로 Consumer 대수를 2대 => 3대로, Read Records 수를 1개 => 20개로, 스레드 수를 1개 => 10개로 개선한 결과, 1분당 처리량은 800% 증가했고 실행 속도는 8배 가량 빨라졌습니다.

## 마치며

지연이체 서비스를 개발하고 if(kakao) 발표를 준비하면서 느낀 점들을 정리하며 글을 마쳐보려 합니다.

아키텍처 설계 시 기능 구현이 다가 아니라 고려해야 할 것이 많다는 점입니다. 중복 발생 위험, 동시에 발생할 수 있는 상황들, 적절한 락 사용과 다른 서버에 미치는 영향 등을 고려해야 합니다.

서비스 특성을 고려하여 트래픽 대비를 해야 하고, 성능 개선 시 단순히 숫자만 올리는 게 능사가 아니라는 것을 알게 되었습니다. 정말 의미가 있는 설정일지, 그로 인한 영향은 없을지 고려해야 합니다.

완성도 있는 발표를 위해 예상보다 많은 준비 과정이 필요함을 느꼈고, 개발 내용을 잘 전달할 수 있는 여러 방법들에 대해 알 수 있는 기회였습니다. 기술전략팀을 포함하여 많은 분들의 조언들을 받으며 큰 성장을 할 수 있었답니다!

긴 글 읽어주셔서 감사합니다. 😀 [if(kakao) 발표 영상](https://youtu.be/LECTNX8WDHo?si=XxDmUo9I5ScOlPO8) 에 더 많은 내용이 담겨있으니 관심 있으시면 봐보시길 바랍니다~!
