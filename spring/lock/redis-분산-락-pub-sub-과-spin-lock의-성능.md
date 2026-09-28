---
title: "Redis 분산 락 - Pub/Sub 과 Spin Lock의 성능"
source: "https://blog.naver.com/kwon37xi/223775157674"
author:
  - "[[권남]]"
published: 2025-02-26
created: 2026-09-28
description: "과거에는 분산 락(distributed lock)을 거의 사용하지 않았다. 아마도 대부분 단일 애플리케이션이었고(서..."
tags:
  - "clippings"
---

> [!summary]
> 권남(kwon37xi)이 Redis 분산 락의 Pub/Sub 방식과 Spin Lock 방식을 비교하며, 흔히 알려진 것과 달리 대부분의 경우 Spin Lock이 Redis 부하 면에서 훨씬 유리하다고 주장한다. Pub/Sub이 낫다는 근거는 락 경합이 오래 지속된다는 전제에 기대는데, 정상적인 애플리케이션이라면 경합이 거의 없어야 하고, 경합이 없을 때는 `SET NX EX`와 `GET`/`DEL`만 쓰는 Spin Lock이 Lua 스크립트와 publish가 따라붙는 Redisson Pub/Sub Lock보다 가볍다. Spin Lock으로 바꾼 뒤 Redis 부하가 약 90% 줄었다는 경험과 함께 락 획득 대기·락 유지 두 가지 타임아웃, 자기 값일 때만 지우는 원자적 해제, 구현체를 바꿔 가며 하는 성능 테스트, Redlock의 한계를 정리한다.

과거에는 분산 락(distributed lock)을 거의 사용하지 않았다. 아마도 대부분 단일 애플리케이션이었고(서버가 여러 대이더라도 보통 하나의 애플리케이션의 인스턴스들임) 단일 저장소에 의존했으므로 해당 단일 저장소(RDBMS)의 table/row lock 기능만으로 충분했으리라.

하지만 서비스 규모가 커지고 Microservices Architecture 가 많은 곳에서 사용되면서 분산 락의 필요가 많이 증가한 것 같다.

## 분산 락의 종류와 성능이 더 좋은 Spin Lock

그중에서 Redis 기반 분산 락이 성능도 좋고 구현도 편해서 아주 많이 사용되고 우리나라에 블로그 글 등으로 아주 많이 분산 락 구현하는 방법들이 나와 있는데, Redis 기반 분산 락 구현은 여러 가지 방법이 있다.

그중에서 가장 편하게 할 수 있는 게 Spin Lock 방식과 Pub/Sub Lock 방식이다. 이미 많은 좋은 글들이 이에 관해 잘 설명해 주고 있으므로 두 락 방식에 대해서 상세한 정보는 다른 글을 찾아보길 권한다.

국내에 나와 있는 대부분의 관련 글들이 Pub/Sub Lock 이 Spin Lock보다 성능이 좋다고 **추정** 하고 있어 보인다.

Spring Integration Redis Support 문서에서도 Pub/Sub Lock이 더 좋다고 얘기하고 있다.

하지만 "성능"이라는 말에는 약간 함정이 있다. Redis 의 성능인가? 애플리케이션의 성능인가? 나는 여기서는 주로 "Redis의 성능"에 초점을 맞추려고 한다. 다른 대부분의 글도 거기에 초점이 있기 때문이다.

**결론부터 말하자면 Spin Lock이 Pub/Sub Lock 보다 99.9%의 경우에 압도적으로 성능이 좋을** **가능성** **이 높다.**

"가능성"이라고 말했는데 성능 최적화는 애플리케이션의 특징에 따라 성능을 떨어뜨리기도 하기 때문이다. 물론 가끔은 Pub/Sub Lock 이 더 유리한 애플리케이션도 있겠지만 거의 대부분의 경우에는 Spin Lock의 성능이 훨씬 좋을 것으로 나는 생각한다.

그리고 실제로 내가 있었던 지난 팀에서 Spin Lock으로 변경한 뒤에 Redis의 부하가 거의 90% 정도 감소되었고 계속해서 Scale Up 하던 Redis 인스턴스를 Scale Down 할 수 있게 되었다.

## Spin Lock의 성능이 더 좋은 이유

Pub/Sub Lock의 성능이 더 좋다고 말하는 글들은 대부분 다음과 같은 근거를 든다(두 Lock 방식의 특징을 알아야만 이해할 수 있음).

> **다른 스레드 등에서 Lock을 먼저 잡은 상태** 에서 Spin Lock 은 시간 단위로 대기하다가 **반복적** 으로 Redis에 Lock 획득 여부를 물어보면서 부하를 일으킨다. 하지만 Pub/Sub Lock 은 Lock 이 풀리면 락을 대기하는 쪽에 메시지를 한 번만 보내서 락을 넘겨주므로 Redis 호출이 적어서 성능이 더 좋다.

언뜻 보면 합당해 보이지만 사실 저 말 자체에 Spin Lock 이 더 성능이 좋은 이유가 내포되어 있다. 빨간색 글씨를 보면 이 추정은 한 가지를 전제한다. "다른 스레드가 Lock 을 먼저 잡은 상태를 장시간 유지할 경우" 즉, **"락 경합(Lock Contention) 이 발생하고 그것이 장시간 유지되면"이라는 전제** 이다.

우리가 만드는 애플리케이션은 사실 **락 경합이 0.1% 정도도 안 일어나야 한다**. 우리가 분산 락을 사용하는 이유는 허구한 날 락 경합이 발생하기 때문이 아니라 정말 어쩌다가 누군가가 실수로라도 동시 접근할까 봐 그 **"어쩌다가"** 를 위한 것이다.

우리가 만드는 애플리케이션이 (특히 실시간성으로 사용자 요청을 받는 API 서버의 경우) 허구헌날 락 경합이 발생한다면 이미 그 자체로 사용자들은 거의 사용이 불가능할 정도로 느리게 느껴질 것이다. Pub/Sub Lock 을 사용하면 어쩌면 이 상황에서 Redis의 성능은 (Spin Lock 보다는) 좋을지 모른다. 하지만 사용자가 사용이 불가능할 정도로 느린 애플리케이션 성능은 방치한 상태가 된다.

즉, 저 가정은 **Redis 성능만 고려했지 애플리케이션 성능에 대한 고려는 하지 않은 상황** 인 것이다.

이 경우에는 대기열 시스템이나, 순차 처리(FIFO)를 지원하는 Queue 방식 등 무언가 다른 아키텍처로 처리하게 변경하는 것이 사용성 측면에서 나아 보인다.

**따라서 Spin Lock의 문제로 지적되는 "장시간의 반복적인 Lock 획득 요청"은 사실상 문제 될 수준까지 발생하지 않을 가능성이 높고, 그렇게 되지 않도록 애플리케이션을 설계하는 것이 합당하다.**

## 경합이 적을 때의 Spin Lock 과 Pub/Sub Lock 성능

(Redisson의) Pub/Sub Lock 은 Lua Script 와 Publish/Subscribe 작업이 수반된다. 락 한 번 잡는데 매우 복잡한 명령이 전달되고 Redis CPU 연산이 증가하게 된다. 게다가 메시지 publish로 인해 상당한 Network Traffic까지 유발한다.

그에 반해 Spin Lock 은 아주 심플하게 SET NX EX 명령과 GET / DEL 정도만으로 구현이 가능하다. 트래픽도 아주 최소한으로만 발생한다.

락 경합이 없는 상태에서 Pub/Sub 과 Spin Lock 을 비교해 보면 Spin Lock의 부하가 현저히 낮을 수밖에 없다.

물론 Spin Lock 에는 한가지 단점이 있다. 락 경합이 발생했을 때, 매 spin 을 100ms 단위로 대기한다고 할 때,

1. 락 획득 여부 확인을 했는데 락이 점유된 상태라 대기(spin) 상태로 감
2. 대기 상태 시작 직후 1ms 만에 상대측에서 락을 풀어줌
3. 그래도 애플리케이션의 대기중인 스레드는 99ms 를 계속 더 대기해야했다가 락을 획득함

Pub/Sub은 락이 풀리자마자 message 를 publishing 하여 다른 쪽에 락을 가져가라고 신호를 준다. 하지만 Spin 방식은 그렇지 못하다.

이 99ms가 정말로 본인 시스템에 치명적이라면 spin 마다의 대기시간을 조금 줄여주는 방법도 있겠다. 어쨌든 이것도 경합이 많이 발생해야만 부차적으로 문제가 되는 것이다. Spring Integration Redis Support 문서를 보면 이 문제를 다소 중요하게 생각하고 Pub/Sub 을 권하는 것으로 보인다. [https://docs.spring.io/spring-integration/reference/redis.html#redis-lock-registry](https://docs.spring.io/spring-integration/reference/redis.html#redis-lock-registry)

아래에서 다시 말하겠지만 Redisson 문서에서는 경합과 무관하게 Pub/Sub Lock의 구조상 CPU/네트워크 대역폭 부하 발생 문제가 있음을 밝히고 있다.

## 분산 락과 두 가지 Timeout

Lock 을 구현할 때는 2 종류의 Timeout 을 필수적으로 염두에 둬야만 한다.

- Lock 획득 대기(wait) timeout: lock 을 다른 쪽에서 잡고 있을 때 얼마나 대기할 것인가. 해당 대기 시간 이후에는 오류를 발생시키고 요청을 종료해버리는 게 낫다. 이걸 구현하지 않으면 Lock 획득 때문에 무한 대기 상태에 빠질 수 있다.
- Lock 유지 timeout: lock 을 잡은 상황에서 최대한 유지할 수 있는 시간. 이 시간이 지나면 다른 쪽에서 lock 을 획득해 갈 수 있어야 한다. 이걸 구현하지 않으면 어떤 스레드가 락을 잡은 상태에서 죽어버리면 다른 쪽에서 해당 키에 대한 락을 결코 획득할 수 없는 상황이 된다.

## Spin Lock 구현 시 주의점

- 바로 위에서 말한 두 종류의 timeout 을 철저하게 구현해야 한다.
- Lock 획득 대기 timeout
	- Lock 획득에 실패해서 대기(spin) 하는 횟수와 대기 시간을 계산하여 사용자가 설정한 Lock 획득 대기 timeout 보다 오랫동안 대기하는 일이 없게 구현한다.
		- 이 시간이 넘어가면 바로 오류를 내버린다.
- 각 Spin 의 대기시간을 설정 가능하게: 사용자가 적절한 값을 테스트하고 선택할 수 있게 해준다.
- Lock 유지 timeout
	- 과거에는 SETNX([https://redis.io/docs/latest/commands/setnx/](https://redis.io/docs/latest/commands/setnx/)) 명령을 사용해서 구현하다 보니 Lock 유지 timeout 구현이 힘들었으나 현재는 SET 명령으로 NX, EX 옵션([https://redis.io/docs/latest/commands/set/](https://redis.io/docs/latest/commands/set/))이 추가되면서 손쉽게 가능해졌다.
		- Lock 을 놓을 때 이미 timeout으로 다른 쪽에서 해당 Lock을 가져갔을 수 있으므로 해당 키의 값으로 자기 스레드의 정보를 넣어두고 그 값이 동일할 때만 해당 키를 삭제하게 구현해야 한다. 안 그러면 남의 Lock을 해제해버리는 문제가 발생할 수 있다. 원자적으로 구현하면 더 좋다(lua script 등으로).

## Pub/Sub Lock 을 사용하고자 한다면

- 본인의 애플리케이션이 정말로 Pub/Sub 이 더 유리한 상황인지 성능 테스트를 권한다.
- Pub/Sub Lock이라도 구현체마다 성능이 다를 수 있다.
- 어차피 Lock 관련 코드를 인터페이스화해서 구현체를 Pub/Sub 과 Spin 중에 하나로 갈아끼우기 쉽게 만들 수 있으므로 구현체를 바꿔가며 실제 자기 애플리케이션 상황에 맞는 부하를 줘서 테스트해야 한다.
- 의미 없는 과도한 락 경합 상태로 테스트해서는 안 된다. 잘못된 결과가 도출된다.
- 성능 테스트 과정에서 Network Traffic 도 살펴본다.
	- 이게 Pub/Sub Lock 구현에 따라 다를 것 같기는 하지만 Lock의 key를 기준으로 대기하는 subscriber 에만 메시지를 쏘면 별로 부하가 없을 것 같은데, 이상하게도 우리가 사용하던 Redisson 구현체는 락 경합이 별로 없는 상태에서도 메시지 publish를 과도하게 해서 Network Traffic이 폭증하는 현상이 발견되었다.
- Connection 개수를 확인한다. Network Traffic 폭증의 원인이 과도한 커넥션 개수와 그에 대한 전체 message publish 때문인 것으로 **추정** 했다.
	- 어차피 우리는 Pub/Sub으로 돌아갈 생각이 없었기 때문에 세세하게 더 테스트해 보지는 않았다.

Redisson 문서에서도 Pub/Sub Lock 이 CPU 폭증과 트래픽 유발 문제가 있음을 고지하고 있다. [https://redisson.org/docs/data-and-services/locks-and-synchronizers/#spin-lock](https://redisson.org/docs/data-and-services/locks-and-synchronizers/#spin-lock)

> Thousands or more locks acquired/released per short time interval may cause reaching of network throughput limit and Redis or Valkey CPU overload because of pubsub usage in Lock object. This occurs due to nature of pubsub - messages are distributed to all nodes in cluster.
>
> 짧은 시간 동안 수 천 혹은 그 이상의 Lock 획득/반환이 일어날 경우 (Redisson의) Lock 객체가 사용하는 Pub/Sub 방식으로 인해서 네트워크 대역폭 제한에 걸릴 수 있고 Redis 혹은 Valkey의 CPU 부하가 발생할 수 있다. 이는 메시지가 클러스터의 모든 노드로 발송되는 Pub/Sub의 특성에서 기인한다.
>
> https://redisson.org/docs/data-and-services/locks-and-synchronizers/#spin-lock 2025/02

여기서 "클러스터의 모든 노드"라는 것이 Redis 클러스터를 의미하는 것인지 Redis에 접속한 애플리케이션(의 커넥션)들을 의미하는 것인지 다소 불분명한데 우리 시스템에 일어났던 트래픽 폭증 사건으로 보건대 모든 애플리케이션 커넥션인 것으로 **추정** 된다. 그런데 그게 아니더라도 문제는 문제다.

이 말을 보면 Pub/Sub Lock 은 락 **경합 여부와 무관** 하게 매우 많은 락 획득/반환 요청만으로도 성능 저하(CPU도 그렇지만 트래픽도)가 심하게 발생함을 알 수 있다.

## Redlock

- Pub/Sub Lock과 Spin Lock 둘 다 Single Redis 인스턴스 기반이다. 이 말은 해당 서버가 죽으면 fail over 가 일어나면서 Lock 유실이 발생할 수도 있다는 의미이다.
- 그래서 Redis 문서에서는 Redlock이라는 다중 Redis 인스턴스 기반의 Lock 구현을 권장하는 것으로 보인다.
- [https://redis.io/docs/latest/develop/use/patterns/distributed-locks/](https://redis.io/docs/latest/develop/use/patterns/distributed-locks/)
- 이 경우 여러 Redis 인스턴스를 관리해야 하므로 비용 증가/관리 부담이 발생한다.
- 여러 가지 글들을 참고하건대 Redlock 도 완전무결하지는 않아 보인다.
- Redisson의 경우 Redlock 구현체는 deprecated 돼 있고 RLock 과 FencedLock 을 더 추천하고 있는데 이에 대해서는 더 살펴봐야겠다.
- 아무튼 엄청나게 정합성이 중요한 상황이 아니라면 Spin Lock으로 충분하지 않을까 싶고, 정합성이 매우 중요하다면 차라리 ZooKeeper 등의 더 나은 대안을 생각해보는 것이 좋을 듯 하다.

## 정리

- 최적화는 비용이 든다. 내가 한 최적화로 인한 비용이 실제 부하의 임계점을 넘어서는 효과를 발휘하는지 측정해야 한다.
- 대부분의 경우에는 Spin Lock의 성능이 더 좋고 락 경합이 허구헌날 발생할 때만 pub/sub 이 더 좋을 가능성이 조금은 있을 수 있다. 하지만 이 경우조차도 대부분은 Spin Lock의 성능이 더 좋을 것으로 추정된다. 즉, 성능 때문에 Pub/Sub 을 선택할 이유는 없어 보인다. 다른 이유(안정성 / Spin 대기를 참아줄 수 없다! 등)가 있으면 모를까.
- Redisson의 Lock 구현체들은 JVM의 Full GC 상황까지 대응하고 있는 것으로 보인다. 좀 더 확인 필요.
- 이 글에서 많은 부분에 "추정/가능성"된다고 썼음을 명심하길... 결국 나도 해본 적 없으니 본인 시스템에 직접 테스트해 보라는 의미이다.
