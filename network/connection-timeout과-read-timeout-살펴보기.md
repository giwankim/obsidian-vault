---
title: "Connection Timeout과 Read Timeout 살펴보기"
source: "https://alden-kang.tistory.com/20"
author:
  - "[[Aaron's papa]]"
published: 2021-10-07
created: 2026-07-19
description: "오늘은 타임아웃 계의 양대 산맥 Connection Timeout과 Read Timeout에 대해 이야기 해 보려고 합니다. 두 타임아웃의 의미에 대해 살펴보며 적정한 값을 찾는 방법에 대해서 살펴 보겠습니다. Connection Timeout과 Read Timeout의 의미 먼저 Connection Timeout은 종단 간 연결하는데 소요되는 최대 시간을 의미 합니다. 이 시간을 넘기게 되면 연결 할 수 없는 것으로 판단하고 에러가 발생 합니다. Connection 이라는 단어가 의미하는 것처럼 종단 간 연결에 사용되는 타임아웃 입니다. 그리고 이 때의 연결이란 우리가 잘 알고 있는 TCP 3 way handshake를 통해 TCP 연결이 생성되는 것을 의미 합니다. Read Timeout은 연결된 종.."
tags:
  - "clippings"
---

> [!summary]
> Korean article explaining connection timeout (time to complete the TCP 3-way handshake) versus read timeout (time to receive data on an established connection) and how to derive sensible values from TCP retransmission behavior. A lost SYN or SYN+ACK is retried after InitRTO (hardcoded to 1s on Linux, doubling on each retry), while later packets use an RTT-based RTO with a 200ms floor. Using the criterion "tolerate exactly one packet loss," the author recommends roughly 3s for connection timeout and 1s for read timeout, with read timeout also accounting for RTT plus server processing time.

오늘은 타임아웃 계의 양대 산맥 Connection Timeout과 Read Timeout에 대해 이야기 해 보려고 합니다. 두 타임아웃의 의미에 대해 살펴보며 적정한 값을 찾는 방법에 대해서 살펴 보겠습니다.

---

## Connection Timeout과 Read Timeout의 의미

먼저 Connection Timeout은 종단 간 연결하는데 소요되는 최대 시간을 의미 합니다. 이 시간을 넘기게 되면 연결 할 수 없는 것으로 판단하고 에러가 발생 합니다. Connection 이라는 단어가 의미하는 것처럼 종단 간 연결에 사용되는 타임아웃 입니다. 그리고 이 때의 연결이란 우리가 잘 알고 있는 TCP 3 way handshake를 통해 TCP 연결이 생성되는 것을 의미 합니다.

Read Timeout은 연결된 종단 간에 데이터를 주고 받을 때 소요되는 최대 시간을 의미 합니다. 이 시간을 넘기게 되면 데이터를 받을 수 없는 것으로 판단하고 에러가 발생 합니다. Read 라는 단어가 의미하는 것처럼 연결되어 있는 종단 간 데이터를 주고 받을 때 사용되는 타임아웃 입니다.

Rest API 클라이언트의 경우라면 TCP 통신 과정에서 Connection Timeout과 Read Timeout이 적용되는 구간은 아래 그림과 같습니다.

![](https://blog.kakaocdn.net/dna/bcAkGh/btrgGsmGvaY/AAAAAAAAAAAAAAAAAAAAAKhHAUHcmHIx_vS1g_1lS2fCUaOEnsCVvNTxLqgaiuI_/img.png?credential=yqXZFxpELC7KVnFOS48ylbz2pIh7yKj8&expires=1785509999&allow_ip=&allow_referer=&signature=jyrshq1eKMG%2BCVkOMoMGpvvtTc0%3D)

TCP 통신 과정으로 살펴본 각 타임아웃의 적용 구간

여기까지는 대부분 알고 있는 두 타임아웃의 의미인데요, 그렇다면 두 타임아웃의 값은 어떻게 설정하는 것이 좋을까요?

---

## 타임아웃 설정을 위한 기준 정하기

타임아웃 값을 설정하기에 앞서 기준을 정해야 합니다. 그리고 그 기준은 아래 두 가지 조건을 만족 시키도록 설정 될 수 있습니다.

- 네트워크 상에서 패킷 유실은 꼭 장애 상황이 아니라도 언제든 발생할 수 있다.
- 네트워크 상에서 문제가 발생했다면 가능한 빨리 인지해야 한다.

위 두 가지 조건을 바탕으로 적당한 값을 찾아야 합니다.

> 패킷 유실은 꼭 장애 상황이 아니라도 발생할 수 있습니다.

요즘에는 기술이 좋아져서 비교적 덜 하겠지만 패킷 유실이라는 것은 언제든 발생할 수 있다는 것을 유념해 두어야 합니다. 네트워크는 항상 100% 완벽하게 동작하지 않기 때문에 이를 고려해야 합니다. 또한 실제로 네트워크 장애가 발생 했다면 가급적 빨리 발견해서 필요한 조치를 할 수 있어야 합니다. 만약 타임아웃 값을 너무 짧게 둔다면 간헐적으로 발생할 수 있는 패킷 유실에 대해 너무 민감하게 반응하게 되고, 타임아웃 값을 너무 길게 준다면 네트워크 장애를 발견하는데 긴 시간이 소요되게 됩니다. 그렇다면 어떤 값이 가장 좋을까요? 제가 생각하는 위의 두 가지 조건을 만족하는 기준은 아래와 같습니다.

> 한 번의 패킷 유실 정도는 재전송을 통해 해결 할 수 있는 수준의 타임아웃

이에 대해서는 사람들마다 기준이 다르겠지만 어쨋든 중요한 건 기준을 세우고 그에 맞는 타임아웃 값을 설정하는 게 중요하다는 것 입니다. 그럼 위와 같은 기준을 바탕으로 하면 두 타임아웃 값을 어떻게 설정하는 게 좋을까요? 먼저 Connection Timeout에 대해 생각해 보겠습니다.

---

## Connection Timeout 값 설정하기

Connection Timeout은 TCP 3 way handshake시 발생할 수 있는 연결 지연이기 때문에 연결을 맺는 과정에서 발생할 수 있는 패킷 유실에 대해 생각해 봐야 합니다. 고려해 볼 수 있는 경우의 수는 세 가지 입니다. SYN 패킷이 유실 되었을 때, SYN + ACK 패킷이 유실 되었을 때, 그리고 마지막 ACK 패킷이 유실 되었을 때 입니다. 이들을 하나씩 살펴 보겠습니다.

먼저 SYN 패킷이 유실 되었을 때 입니다.

![](https://blog.kakaocdn.net/dna/SxVoZ/btrgOuj5dEh/AAAAAAAAAAAAAAAAAAAAABhcslvQO40CZRigfNapPaWIAfHPNTyCWvE0kHJI8EaQ/img.png?credential=yqXZFxpELC7KVnFOS48ylbz2pIh7yKj8&expires=1785509999&allow_ip=&allow_referer=&signature=smxZmOlUOL%2BIyT2T77nt3ve5gxs%3D)

A가 B와 연결을 맺기 위해 보낸 SYN 패킷이 유실 되었다고 가정해 보겠습니다. A는 B로부터 SYN+ACK를 받을 준비를 하고 있는데 SYN 패킷이 유실되어 B에게 도착하지 않았기 때문에 B는 SYN+ACK를 보낼 수 없습니다. 따라서 A는 자신이 보낸 SYN 패킷이 유실되었다고 판단하고 다시 보내게 됩니다. 그리고 이 때 사용되는 재전송을 판단하기 위한 타임아웃을 InitRTO 라고 부릅니다. 패킷의 유실 여부를 판단하는 타임아웃 값을 RTO라고 부르는 데 RTO는 두 종단 간의 RTT (Rount Trip Time)을 기준으로 생성 됩니다. 즉 패킷이 두 종단 간을 흘러가는 데 필요한 최소한의 물리적인 시간이 필요하기 때문에 그 값을 기반으로 RTO를 계산해 냅니다. 두 종간 간에 패킷이 흐르는 데 100ms가 필요하다면, 보내는데 100ms 받는데 100ms 합쳐서 최소한 200ms 가 소요되기 때문에 200ms 이상은 기다려야 패킷이 유실되었는지 여부를 알 수 있습니다. 하지만 방금 본 예제처럼 연결을 최초에 맺는 경우에는 종단 간 RTT 값을 알 수 없기 때문에 무조건 이만큼은 기다려보자 라는 설정 값이 필요하고 이 값이 바로 InitRTO 입니다. 그리고 이 값은 리눅스 상에서는 1초로 하드코딩 되어 있습니다. 따라서 SYN 패킷이 한 번 유실된다면 최소한 연결을 맺는데 1초 이상의 시간이 소요 됩니다.

> InitRTO와 RTO 그리고 RTT의 관계는 제가 예전에 쓴 글인 [https://brunch.co.kr/@alden/15](https://brunch.co.kr/@alden/15) 을 참고 하시기 바랍니다.

다음으로 SYN+ACK이 유실 되었을 때를 생각해 보겠습니다.

![](https://blog.kakaocdn.net/dna/xtX4S/btrgMsmwrF6/AAAAAAAAAAAAAAAAAAAAAEtlr3o0NN5V21R7wrqmvWxtwv12jqKZhigu-Us-1DOL/img.png?credential=yqXZFxpELC7KVnFOS48ylbz2pIh7yKj8&expires=1785509999&allow_ip=&allow_referer=&signature=9pP2g3FhAWpOwYhgscGcJVkmD9c%3D)

이 경우도 SYN이 유실되었을 때와 동일한 시나리오로 흘러 갑니다. SYN 패킷이 B에게 정상적으로 도착했고, 이에 따라 B가 A에게 SYN+ACK 패킷을 전달 했지만 중간에서 SYN+ACK 패킷이 유실 되었습니다. SYN+ACK 패킷이 유실 되었음을 알 수 없는 A는 당연히 SYN이 유실 되었다고 판단하고 1초 후에 다시 한 번 SYN을 보내게 됩니다. 그래서 원인은 다르지만 실질적으로 동작하는 방식은 SYN 패킷이 유실 되었을 때랑 동일 합니다.

그럼 마지막으로 ACK 패킷이 유실되었을 때를 생각해 보겠습니다.

![](https://blog.kakaocdn.net/dna/brcMRP/btrgFTedP3L/AAAAAAAAAAAAAAAAAAAAANVBLpqwisq8PHjNBRAO2iODM0joQ28Wp_YgtTO1bzyW/img.png?credential=yqXZFxpELC7KVnFOS48ylbz2pIh7yKj8&expires=1785509999&allow_ip=&allow_referer=&signature=utY2S1wjyLfhLo%2FCHVyk4mFOTWU%3D)

ACK 패킷 유실의 경우는 앞의 두 경우와는 조금 다른데 왜냐하면 SYN과 SYN+ACK 패킷을 서로 주고 받으면서 A와 B는 이제 둘 사이의 RTT를 알게 되었습니다. ACK 패킷 부터는 InitRTO의 적용을 받지 않고 RTT를 기반으로 계산된 RTO의 적용을 받습니다. 그리고 RTO의 기본값은 RTT를 기반으로 계산된 복잡한 값 혹은 이 값이 200 ms 보다 작다면 200 ms가 적용 됩니다. 따라서 ACK의 유실에 의한 재전송은 최소 200 ms 가 소요 됩니다. 대부분의 경우 1초를 넘기지는 않을 겁니다.

이렇게 Connection Timeout이 발생할 수 있는 세 가지 경우에 대해서 살펴 봤는데요, 그래서 어떤 값으로 설정하면 좋을 것인가가 남았습니다. **아마 다들 의견이 다르겠지만 제가 생각하는 이상적인 값은 3초 입니다.** 왜나하면 세 경우에서 발생하는 패킷 유실의 경우 최대 1초 정도의 소요 시간이 발생 하기 때문입니다. 한 번의 패킷 유실로 인해 발생할 수 있는 지연 시간은 1초 이상이기 때문에 최소 1초 보다는 커야 한 번의 패킷 유실 정도는 무시하고 넘어가게 됩니다. 하지만 두 번 이상 패킷 유실이 발생한다면, 이 때는 네트워크 상에 이슈가 있을지도 모른다는 생각을 해 봐야 합니다. 연속해서 두 번 이상 패킷 유실이 발생한다면 확실히 이상이 있을 수 있기 때문 입니다. 특히 InitRTO의 경우 2의 제곱값으로 값이 커지기 때문에 최초의 유실에 대해서는 1초를 기다리지만 두 번째 유실은 2초를 기다리게 됩니다. 즉 두 번 이상의 패킷 유실이 발생한다면 3초 이상의 지연 시간이 발생하기 때문에 Connection Timeout이 3초라면 최소한 패킷 유실이 두 번 이상 발생 했을 수 있다는 이야기가 됩니다. 그리고 이렇게 두 번 이상의 패킷 유실이 발생 했다면 네트워크에 이슈가 있지 않은지 살펴봐야 할 필요가 있습니다.

![](https://blog.kakaocdn.net/dna/VPnU6/btrgIOXuoDu/AAAAAAAAAAAAAAAAAAAAAOAywG_y7Rqp_Pv1WEJ76N1lmw4yQ_VHdO_uUaWYnaGt/img.png?credential=yqXZFxpELC7KVnFOS48ylbz2pIh7yKj8&expires=1785509999&allow_ip=&allow_referer=&signature=G7y4LmA1jsJqX1SlJ1uuZIyNutY%3D)

물론 3초가 지나서 SYN 패킷이 도달할 수도 있습니다만, 이건 결국 선택의 문제 라고 생각 합니다. 만약 Connection Timeout을 5초로 잡았다면 두 번의 패킷 유실까지는 커버하고 연결이 될 수고 있겠죠. 어쨋든 제 기준은 패킷 유실은 한 번만 허용한다 였기 때문에 3초를 적당한 값으로 설정한 것 입니다.

지금까지 Connection Timeout에 대해 살펴 봤는데요, 이번엔 Read Timeout에 대해 살펴 보겠습니다.

---

## Read Timeout 값 설정하기

Read Timeout은 Connection Timeout에 비해 좀 더 짧게 가져가게 됩니다. Read Timeout에 영향을 주는 패킷 재전송을 위한 타임아웃 값인 RTO가 RTT를 기준으로 만들어져서 보통 1초보다 짧기 때문 입니다.

![](https://blog.kakaocdn.net/dna/cukYHX/btrgCGmlNJt/AAAAAAAAAAAAAAAAAAAAAMEAyvdVz_U9SXMqY4CPnVL4C6_1PVYFq6qWNJRVIiD-/img.png?credential=yqXZFxpELC7KVnFOS48ylbz2pIh7yKj8&expires=1785509999&allow_ip=&allow_referer=&signature=jfxSOrntgDAfuTPrJUqBNkCwb%2Bg%3D)

RTO의 최소값은 200ms이기 때문에 Read Timeout 역시 한 번의 패킷 유실을 고려해서 200ms 보다는 크게 잡습니다. 하지만 Read Timeout의 경우 고려해야 할 다른 요소들이 있는데 바로 RTT와 요청을 받은 쪽에서 요청을 처리하기 위해 소요되는 프로세싱 타임 입니다.

종단 간 RTT가 10ms 이고 요청을 처리하는 데 소요되는 시간이 300 ms 라고 가정해 보겠습니다. 그렇다면 A와 B가 통신하기 위해 필요한 최소한의 시간은 310ms가 됩니다. 여기에 한 번의 패킷 유실이 발생한다고 생각하면 어떻게 될까요?

![](https://blog.kakaocdn.net/dna/cJ9ILc/btrgJX8eJy7/AAAAAAAAAAAAAAAAAAAAADl5wllEntVTmHUmfwjd3TrQPXfEi1nlrO6hRhGK5kOH/img.png?credential=yqXZFxpELC7KVnFOS48ylbz2pIh7yKj8&expires=1785509999&allow_ip=&allow_referer=&signature=M5vhkiQdp1DBd8PFOETyZdBQ3gs%3D)

그림과 같이 B가 A로부터 요청을 받고 요청을 처리하는 데 소요된 시간 300ms 와 B가 A에게 보낸 패킷이 유실 되었음을 인지하고 재전송에 소요된 시간 (RTO) 200ms가 필요 합니다. 여기에 두 패킷이 서로 간에 도착하기 위해 필요한 최소한의 시간인 RTT도 염두에 두어야 하죠. 그래서 한 번의 패킷 유실로 인해 310ms 안에 처리 할 수 있는 요청이 510ms 가 소요 됩니다. 이렇게 Read Timeout은 RTO 외에 RTT와 프로세싱 시간까지 고려해서 설정해야 합니다.

**그래서 이런 것들을 고려해서 제가 생각하는 이상적인 값은 1초 입니다.** 한 번의 패킷 유실로 인해 발생할 수 있는 최대 지연 시간은 200ms이고 여기에 RTT와 프로세싱 시간까지 생각해서 1초 안에는 요청에 대한 응답을 받아야 하지 않을까 라고 생각해서 설정한 값 입니다. 이 값도 위 기준에 따라 패킷 유실은 한 번만 허용한다는 기준으로 설정한 값 입니다. 물론 프로세싱에 소요되는 시간이 1초를 넘는다면 이 값은 아무 의미 없습니다. 모든 요청이 1초를 넘기기 때문에 이런 경우에 Read Timeout을 1초로 잡았다면 모든 요청에서 Read Timeout이 발생하게 되겠죠. 그래서 Read Timeout의 경우에는 프로세싱 시간을 가장 많이 고려해야 합니다.

---

## 마치며

지금까지 Connection Timeout과 Read Timeout에 대해 살펴 봤습니다. 하지만 이 두 값을 설정하기 위해서는 무엇보다 사용하려고 하는 클라이언트가 이 두 값을 설정할 수 있도록 지원하느냐가 중요 합니다. 일부 클라이언트의 경우 두 가지 타임아웃을 그냥 Timeout 이라는 하나의 설정 값으로 통일해서 관리하는 경우도 있기 때문 입니다. 그리고 어떤 값을 설정하더라도 값을 설정한 기준이 있어야 합니다. 그냥 남들이 이렇게 설정하니까 나도 같은 값으로 설정한다가 아니라 Connection Timeout과 Read Timeout의 의미를 정확히 이해하고 운영하고 있는 서비스의 성격에 맞게 기준을 만들어서 설정하는 것이 중요 합니다. 모두 적당한 값을 잘 찾아서 안정적인 서비스 운영을 하시기 바랍니다. 감사합니다.

#### 'IT > DevOps' 카테고리의 다른 글

| [aws-node-termination-handler를 활용해서 EKS 워커 노드에 스팟 인스턴스 적용하기](https://alden-kang.tistory.com/31) (1) | 2021.12.09 |
| --- | --- |
| [Logstash의 Kafka Input 성능 개선 이야기](https://alden-kang.tistory.com/24) (7) | 2021.10.28 |
| [jib와 Github Actions를 이용한 빌드 자동화](https://alden-kang.tistory.com/10) (0) | 2021.08.25 |
| [패킷 덤프를 통해 확인하는 ALB와 NLB의 차이점 (2) - NLB 동작 원리](https://alden-kang.tistory.com/8) (8) | 2021.08.08 |
| [AutoScalingGroup의 Scheduled action 활용하기](https://alden-kang.tistory.com/7) (1) | 2021.08.06 |
