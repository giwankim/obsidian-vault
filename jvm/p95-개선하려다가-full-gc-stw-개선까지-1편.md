---
title: "P95 개선하려다가 Full GC STW 개선까지. 1편"
source: "https://www.rilog.kr/@rilog/posts/589"
author:
  - "[[koreaioi]]"
published: 2026-11-18
created: 2026-11-20
description: "P95를 개선하려다가 Full GC STW까지 최적화하게된 4-5주간의 삽질을 기록 1. 문제 상황 삽질의 시발점은 다음과 같다. 재배포가 없었던 Production 환경 기준, 500ms 이상 읽기 요청이 간헐적으로 발생했습니다. 즉, P95가 갑자기 튀는 문제죠. 2. 원인 파악.…"
tags:
  - "clippings"
---

> [!summary]
> 유휴 상태 뒤 첫 요청에서 P95가 수 초까지 튀고 Minor GC가 1.75초씩 걸리던 현상을 추적한 기록 1편이다. GC 로그의 Real 시간이 User+Sys보다 훨씬 큰 점에서 출발해, 트래픽이 없는 동안 JVM 페이지(Heap·Metaspace)가 디스크 Swap으로 밀려나 Major Page Fault가 발생한다는 가설을 Swap In/Out 지표와 RAM:Swap 비율(1:2.9)로 검증했다. 불필요한 프로세스 제거, swappiness 10 설정, Docker `mem_limit`/`memswap_limit`으로 Swap을 200MB로 제한해 P95를 3초에서 900ms, Minor GC를 200ms로 줄였고, OOM 위험이라는 트레이드오프는 20RPS 부하 테스트로 확인했다.

![P95 개선하려다가 Full GC STW 개선까지. 1편](https://techcourse-project-2026.s3.ap-northeast-2.amazonaws.com/rilog/images/compact/1-b8967720-6cdb-475c-aeb6-52d5c4a1b892/2000.webp)

P95 개선하려다가 Full GC STW 개선까지. 1편

> P95를 개선하려다가 Full GC STW까지 최적화하게된 4-5주간의 삽질을 기록

## 1\. 문제 상황

삽질의 시발점은 다음과 같다.

![image.png](https://techcourse-project-2026.s3.ap-northeast-2.amazonaws.com/rilog/images/compact/1-810d5149-2bd5-46f4-9f7f-60f541c497d7/2000.webp#938x436)

재배포가 없었던 Production 환경 기준, 500ms 이상 읽기 요청이 간헐적으로 발생했습니다.
즉, P95가 갑자기 튀는 문제죠.

## 2\. 원인 파악.

위 현상을 지속적으로 관찰했고, 몇가지 공통점을 발견할 수 있었습니다.

특정 API가 아니라, 무작위로 발생한다.

RDS에는 SlowQuery, Credit, CPU 성능 등의 문제가 없다.

**Minor GC가 비교적 오래 걸릴 때와 겹친다.**

사실 세가지 공통점에서 가장 중요한 건 3번입니다.

![image.png](https://techcourse-project-2026.s3.ap-northeast-2.amazonaws.com/rilog/images/compact/1-ce17e3f9-d55e-416b-b987-ce64a0d1af08/2000.webp#1000x566)

실제 Production 지표를 보면 유휴 상태이다가 갑자기 요청이 오면, Minor GC가 발생했고, 해당 GC는 1.75s가 걸렸다. 그래서 저는 GC로 인해 응답이 튀었다고 생각했죠..

그런데 알고보니...?

![image.png](https://techcourse-project-2026.s3.ap-northeast-2.amazonaws.com/rilog/images/compact/1-26e8e09d-734d-4f29-9eba-1c99530658c1/2000.webp#1006x562)

더 자세히 보니 시간대가 맞지 않았습니다.
P95가 튀었을 때는 14:20 부근이고 GC는 14:21에 시작했습니다.
여기서 GC가 결정적인 원인은 아니라고 생각했습니다.

하지만 한가지 힌트를 얻었죠.
유휴 상태에서 **API가 튀는 증상** 과 **Minor GC가 오래 걸리는 증상** 이 **비슷한 시기** 에 발생한다는 점입니다.

> 그래서 두 사이에 인과관계는 없을 수 있지만, 같은 원인을 공유하고 있을거라 생각.
> 즉, **Minor GC가 오래 걸리는 이유** 와 **API가 튀는 이유** 가 같을 거라는 추측..!

Minor GC가 왜 오래 걸렸을까요... Minor GC는 대부분 **0.01~0.02ms** 면 끝나는데 말이죠...

당시 Production 환경에서 GC 로그를 켜두지 않았지만, 다행히 개발서버에서 충분히 재현 가능했습니다. 트래픽이 없는 상황에서 발생하기 때문이죠.

역시나 유휴 상태를 유지하고, 조금의 트래픽만 보내도 비슷한 현상을 관찰할 수 있었습니다.

```bash
[info][gc,cpu ] GC(599) User=0.00s Sys=0.02s Real=0.52s
```

User는 GC가 직접 일한 시간.

Sys는 메모리 할당, 해제 같은 시스템 콜을 호출하는 데 걸린 시간.

Real은 프로세스(JVM)이 체감한 시간.

User + Sys는 GC가 일하고 시스템 콜을 호출하기 까지이며, Real은 모두 포함한 시간....
따라서 Real - (User + Sys)는 커널 너머가 일한 시간이다. **0.5s** 동안 커널 너머에는 무슨 일이 있었길래...

GC가 오래 걸린 이유, 저의 가설은!

트래픽이 없는 유휴 동안 Young영역의 객체가 사용되지 않는 페이지로 인식되어 Swap으로 이동

Minor GC가 실행되어 Young영역 객체를 읽는데, Page Fault가 발생하여 디스크 I/O 발생.

Minor GC 시간 증가.

입니다.

그래서 실험을 할 때는 유휴 상태를 유지하다가, 요청이 생길 때, Swap In/Out과 Page Fault를 관측하고 이 수치가 높다면, 제 가설이 맞을거라 생각했습니다.

---

## 2\. 실험

> 이 실험에서는 Minor GC가 오래걸린 이유에 대해 세운 가설을 검증!
> Minor GC 지연 원인을 찾는 이유는 궁극적으로 해결하고자 하는 **P95가 튀는 현상** 과 동일한 원인이라 생각하기 때문.

## 2-1. 실험 준비

실험 전, 관측하기 위한 지표 모니터링 세팅 및 실제 사용자 시나리오와 비슷한 부하테스트 스크립트를 준비했습니다.

실제 운영환경과 같은 데이터를 사용하기 위해, 운영 DB 데이터를 복제한 부하테스트 DB 구축.

JVM 지표 추가 + EC2 시스템 RAM, SWAP 지표 추가 + Spring Application이 사용하는 RAM, SWAP 지표 추가 (Alloy → Prometheus) + GC 로그 추가

운영 환경에서 평상시 EndPoint 비율 확인하고 이를 기반으로 부하 테스트 시나리오 작성.

![image.png](https://techcourse-project-2026.s3.ap-northeast-2.amazonaws.com/rilog/images/compact/1-6976cd6a-96d3-4bfd-9eba-9a6b00832968/2000.webp#952x638)

트래픽이 없는 기간에 테스트 시작!

## 2-2. 실험 결과

실험은 **2026.10.12 20:36:00** 진행
트래픽이 없는 기간에 부하테스트 실행 시, 첫 응답에 P95가 튀는 현상을 관측할 수 있었습니다.

![image.png](https://techcourse-project-2026.s3.ap-northeast-2.amazonaws.com/rilog/images/compact/1-ee4839b2-842a-4b17-9da1-e571c0695c15/2000.webp#936x432)

실제로 GC는 36분 15초가 아닌 37분 15초 즈음에 발생함을 관측

![image.png](https://techcourse-project-2026.s3.ap-northeast-2.amazonaws.com/rilog/images/compact/1-8db38f03-05e7-4f85-a6e4-d4bba21b56fa/2000.webp#2068x1184)

그리고 Swap In/Out과 Page Fault를 보면
요청이 들어온 36분 부근에서 수치가 올랐고, **GC가 발생한 37분 15초** 는 **가장 높은 수치** 를 보였다가 다시 낮아진 걸 확인할 수 있었습니다.
Major Page Fault Max값은 **578ops/s** 까지 치솟은걸 확인할 수 있었고, Swap In/Out도 **741, 620ops/s** 까지 치솟았습니다.

또한 Spring Boot Container가 사용하는 RAM과 Swap 메모리 사용량을 보니

![image.png](https://techcourse-project-2026.s3.ap-northeast-2.amazonaws.com/rilog/images/compact/1-2175773a-2be7-4484-9dd7-32896e2aa45c/2000.webp#1622x154)

200MB: 491MB로 RAM과 SWAP 비중이 **1: 2.9(200MB: 490MB)** 인걸 확인할 수 있었습니다.

이 실험 이후, GC가 오래 걸리는 이유는 오랜 기간 사용되지 않은 JVM 페이지가 **디스크** **Swap** 으로 밀려났기 때문이라고 99% 확신했습죠.

---

## 3\. P95가 튀는 원인

GC가 오래 걸리는 이유는 Swap Memory!!
그런데 우리가 GC 지연 원인을 찾은 건 궁극적으로 P95가 튀는 원인과 같을거라는 추측때문이죠?

따라서 유휴상태에서 P95가 튀는 원인도 Swap과 관련 있을거라 생각했습니다.

유휴상태에서 트래픽이 오면 무엇을 Swap에서 가져올까...?

![image.png](https://techcourse-project-2026.s3.ap-northeast-2.amazonaws.com/rilog/images/compact/1-6837b9ec-44c1-43ca-88e4-7f8677def1a9/2000.webp#820x614)

JVM 메모리 구조

이 사진은 JVM 메모리 구조인데요. 요청이 들어오면 다음 영역을 사용합니다.

**Method Area(Metaspace):** Spring, Tomcat, 내 코드의 클래스 정보

**Heap**: Spring Bean으로 등록된 객체들 (XXXController, XXXService, etc..)

위 영역들은 트래픽이 없으면 사용하지 않을거고, 자연스레 디스크 Swap으로 옮겨질거라 생각했씁니다.

이렇게 RAM과 Swap의 비율이 **200MB**: **490MB** 인 상태가 되고 난 후, 트래픽이 오면 요청을 처리하기 위한 페이지들을 불러오는 험난한 과정으로 인해, 오래 걸리겠구나 생각하게 되었습니다.

---

## 4\. 해결

P95와 Minor GC 지연 원인인 높은 Swap 비중을 해결하기 위해 다음과 같은 시도를 진행했습니다.

## 4-1. RAM Memory 확보하기

기본적으로 RAM Memory를 확보하는 게 중요하다고 생각했습니다.

![image.png](https://techcourse-project-2026.s3.ap-northeast-2.amazonaws.com/rilog/images/compact/1-7249f443-c3a9-49d0-922d-bdba08a49ef9/2000.webp#808x746)

위는 프로세스 별 RAM 메모리 사용량인데요.

amazon-cloudwatch-agent나, cloudflared 같이 필요없는 프로세스가 많이 존재했습니다. 이를 모두 제거하여, 80MB의 가용 메모리를 확보할 수 있었습니다.

## 4-2. swappiness 설정

available memory와 swap memory 선택 확률을 나타내는 swapiness 튜닝 고려했습니다.
swappiness가 100에 가까울수록 메모리가 부족할 때, swap memory를 사용을 선호하고, 0에 가까울수록 ram에 남아 있는 cache를 정리해, available memory 사용하도록 하는데요.

저는 이 swappiness를 10으로 설정해 최대한 RAM Cache를 정리해 사용하도록 튜닝했습니다.

위는 swappiness를 10으로 설정하고 부하테스트 전 지표입니다.

![image.png](https://techcourse-project-2026.s3.ap-northeast-2.amazonaws.com/rilog/images/compact/1-85971b3b-e8bb-4125-bf7b-e059c22e5797/2000.webp#2048x256)

위는 부하테스트를 진행한 직후 지표입니다.

![image.png](https://techcourse-project-2026.s3.ap-northeast-2.amazonaws.com/rilog/images/compact/1-3e9e3938-76aa-4950-9635-d9754630bf26/2000.webp#2048x261)

여기까지만 보면 1:2.9였던 RAM과 Swap 비중이 거의 1:1 비스무리하게 맞춰져 효과가 있다고 생각했죠.

![image.png](https://techcourse-project-2026.s3.ap-northeast-2.amazonaws.com/rilog/images/compact/1-06cd3017-0bd7-4c26-9ff5-9ed5270eaed8/2000.webp#2048x109)

그러나 시간이 지나니, 결국 RAM과 Swap 비중이 다시 역전되어 Swap을 더 사용하게 되었습니다.

이 이유는 swappiness를 낮게 설정하더라도, 이는 **강제 제약이 아니기 때문에**, 시간이 지나 available memory가 남아있음에도 커널이 swap memory 사용을 선택하게 되더군요.

결국 RAM Memory가 충분히 확보 안된 상황에서 swappiness 튜닝으로는 RAM, Swap 최적화 비율은 **1: 1.5** 가 **최선** 이라 생각했습니다.

---

## 4-3. Docker Memory Option Tuning

### 4-3-1. Option과 실험 조건 설명

이제는 Docker Container의 Memory를 직접 건드리기로 했습니다.
가장 간단한 건 **mem\_limit** 과 **memswap\_limit** 인데요.
mem\_limit은 RAM 메모리 제한이며, memswap\_limit은 RAM + Swap 메모리 제한입니다.

> 따라서 Swap Memory 사용을 **200MB** 로 제한하고 싶다면 mem\_limit과 memswap\_limit 차이를 200만큼 설정하면 되는거죠.

Swap 사용량을 제한하고 RAM만 사용하도록하면 P95와 GC 지연을 개선할 수 있을거라 생각했습니다.

그래서 기본 RAM 512MB에 프로세스 제거로 확보한 RAM Memory 중 60MB를 추가했고, 목차3에서 진행한 실험을 재현해보기로 했습니다.

mem\_limit **572MB**, memswap\_lmit **772MB** 로 진행!

### 4-3-1. 실험 결과

실험은 **2026.10.12 23:22:00** 에 시작했습니다.

![image.png](https://techcourse-project-2026.s3.ap-northeast-2.amazonaws.com/rilog/images/compact/1-c473efdf-5cd5-4a43-b190-9d567d7970a8/2000.webp#952x596)

P95

![image.png](https://techcourse-project-2026.s3.ap-northeast-2.amazonaws.com/rilog/images/compact/1-ec6efa6c-4fef-4dde-b822-38f50f91dbc2/2000.webp#1932x1294)

Swap In/Out & Page Fault

![image.png](https://techcourse-project-2026.s3.ap-northeast-2.amazonaws.com/rilog/images/compact/1-ad662247-1e3f-4207-a7ed-cba842f46231/2000.webp#1002x576)

GC STW

유휴 상태에서 **3s** 까지 튀던 P95가 **900ms** 로 줄어든 모습을 확인할 수 있습니다.
또한 Page Fault중 Major Fault가 기존보다 낮아진 걸 확인할 수 있죠.

유휴상태 P95 **3s** -> **900ms**

Major Page Fault는 **578** -> **368**

Swap In은 **741** -> **486**

Swap Out은 **620** -> **511**

Minor GC는 **1.75s** -> **200ms**

RAM의 비중이 높아져 확실히 나아진걸 확인할 수 있었습니다!!
하지만 P95가 수십ms까지 드라마틱하게 개선되지는 않았네요. (여전히 Swap이 존재하기 때문...)

## 5\. Trade Off

최종적으로 P95를 ms단위로 줄였고, Minor GC 시간도 줄였습니다.
이는 Swap Memory 사용을 제한하고 RAM 비중을 높였기 때문이죠. 하지만 이는 완벽한 방법은 아닙니다.

애초에 Swap Memory를 사용한 이유는 RAM이 부족해 CPU 사용률이 갑자기 증가하며 EC2가 멈춰버리기 때문입니다.
(EC2 Micro를 사용하는 백엔드 개발 취준생이라면 십중팔구 경험해봤을겁니다.)

RAM이 부족해, 2GB의 여유로운 Swap Memory를 사용할 수 있음에도 이를 제한해버리면 OOM 발생확률이 높아질 수 있기 때문이죠...

그래서 다음을 확인해보기로 했습니다.

> 현재 Rilog.의 트래픽 상황에서 메모리 사용을 제한할 때, OOM이나 기타 문제가 발생할 수 있는 지?

## 5-1. 현재 트래픽 실험

실제 트래픽 상황은 다음과 같습니다.

현재까지 관측된 최고 RPS는 10.

개발 서버에 메모리 제한을 다음과 같이 적용했으며, PostHog 관측 결과 동시 접속자는 6명

내부적으로 테스트 결과 1명 당 평균 피드에서 초당 3RPS만큼의 요청을 보내는 걸 확인.

당시 관측한 최고 RPS는 10이지만, 피드에서 가장 많은 조회 요청이 일어나기 때문에, 동시 접속자 6명이 피드에서 있다고 생각해 **20RPS** (6x3에서 올림처리)로 가정하고 부하 테스트를 진행했습니다.

## 5-2. 실험 결과

실험은 **2026.10.15 10:51:00** 에 진행

![image.png](https://techcourse-project-2026.s3.ap-northeast-2.amazonaws.com/rilog/images/compact/1-b6ae90cd-4598-493f-b8aa-fb959a68bece/2000.webp#948x494)

중간에 튄 부분 말고는 모든API를 100ms 이내에 응답.

피드 목록 조회 API가 타 API에 비해 응답 시간이 비교적 긴 모습을 관측. → **추후 개선 대상.**

![image.png](https://techcourse-project-2026.s3.ap-northeast-2.amazonaws.com/rilog/images/compact/1-e00d6664-8520-48b8-b61d-a6e44d0162fd/2000.webp#2048x870)

RDS CPU 사용률 (피크 16%)

P95 그리고 EC2 CPU 사용률와 함께 RDS CPU 사용률도 Max 16.0%로 넉넉한 모습을 관측할 수 있었습니다. 따라서 **"20RPS 환경에서는 메모리 제한으로 인한 성능 저하는 매우 적을 것이다"** 라고 결론 내렸습니다.

## 6\. 마무리

튀는 P95와 Minor GC 지연을 해결하기 위해 여러 도전을 해봤는데요.
메모리를 확보하고 swappiness 튜닝과 docker memory 제한 등을 시도했습니다.

최종적으로 다음과 같이 결론지었구요.

> 20RPS 환경에서는 메모리 확보, swappiness 튜닝, 메모리 제한으로 P95, Page Fault, Swap In/Out의 지표를 개선했다. 또한 실 운영환경에서 성능 저하는 적을 것이다

여기서 '적을 것이다'라고 여지를 남긴 데는 이유가 있는데요.
JVM이나 OS 관련 지표를 해석할 때 Claude에 많이 의존한 만큼, 제가 미처 놓친 부분이나 추가로 고려할 지점이 분명 있을 거라 생각했기 때문입니다... 그래서 더 공부해야겠다 생각이 들었네요...

> 제목에서 보셨다싶이 이 여정은 **Full GC STW 개선까지** 이어지는데요. 이 글을 적는 건 이 4-5간의 여정이 끝난 뒤입니다. 맨 처음 정리한 자료를 보면 이때는 정말 아무것도 몰랐구나 싶네요. (지금도 비슷)

2편 곧 올릴게요 화이팅

---
