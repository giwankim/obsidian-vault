---
title: "WMS 재고 이관을 위한 분산 락 사용기 | 우아한형제들 기술블로그"
source: "https://techblog.woowahan.com/17416/"
author:
  - "[[jhk]]"
published: 2024-05-28
created: 2026-02-23
description: "WMS 재고 이관 과정에서 발생한 동시성 이슈를 분산 락(Distributed Lock)을 사용해 해결한 경험을 공유하는 글입니다. 본 글은 분산 락에 대해 알고 있는 분들을 대상으로 작성되었습니다. 제가 경험한 내용들이 여러분들의 비즈니스에 도움이 되는 글이 되길 바랍니다. WMS란? 물류에서 사용되는 용어로 상품을 구별하기 위한 고유의 식별 코드입니다. 예를 들어, 인천DC(출발지)에서 송파잠실PPC(목적지)로 배달이 피규어(SKU: S01234)를 10개(이관 수량) 이관하기"
tags:
  - "clippings"
---

> [!summary]
> Woowahan Brothers tech blog post on solving concurrency bugs in their WMS inventory transfer system using Redis distributed locks with a state-key pattern, allowing parallel SKU allocation while preventing simultaneous allocation and cancellation of transfer orders.

## WMS 재고 이관을 위한 분산 락 사용기

2024\. 05. 28.김준홍

[Backend](https://techblog.woowahan.com/?pcat=backend)

> WMS 재고 이관 과정에서 발생한 동시성 이슈를 분산 락(Distributed Lock)을 사용해 해결한 경험을 공유하는 글입니다. 본 글은 분산 락에 대해 알고 있는 분들을 대상으로 작성되었습니다. 제가 경험한 내용들이 여러분들의 비즈니스에 도움이 되는 글이 되길 바랍니다.

## WMS란?

![](https://techblog.woowahan.com/wp-content/uploads/2024/05/WMS-750x246.png)

WMS(Warehouse Management System, 창고 관리 시스템)는 물류센터에서 반복되는 수기 작업을 시스템화하여 안정적으로 운영될 수 있도록 합니다. 재고 입/출고 과정을 WMS로 기록하여 재고를 관리하고 재고 흐름을 추적합니다. WMS는 재고 관리 외에도 물류센터 내 다양한 작업을 시스템화하고 있으며 주요 기능은 다음과 같습니다.

- 발주 상품 입고 및 검수/검품 (수량, 품질, 소비기한)
- 실시간 재고 정보 관리
- 고객 주문 정보에 따른 신속하고 정확한 상품 출고

![](https://techblog.woowahan.com/wp-content/uploads/2024/05/20240528_1-750x94.png)

WMS 재고들은 중앙물류기지라고 불리는 DC(Distribution Center)로 입고되며, DC에 입고된 상품들은 지역 거점 센터인 PPC(Picking Packing Center)로 재고가 이관됩니다. 그리고 B마트 서비스로부터 고객 주문이 들어오면 PPC에서 상품이 고객에게 출고됩니다.

![](https://techblog.woowahan.com/wp-content/uploads/2024/05/WMS-process-750x128.jpg)

본 글에서는 WMS 재고를 이관하는 과정에서 마주친 동시성 문제에 대해 살펴보고, 어떤 방법으로 동시성 이슈를 해결해 나갔는지에 대해 공유합니다.

## WMS 재고 이관하기

## 이관요청

DC에서 PPC로 재고를 이관하려면 WMS에서 이관요청서를 생성해야 합니다. 이관요청서에 입력해야 하는 주요 항목은 다음과 같습니다.

- 출발지 센터
- 목적지 센터
- SKU
- 이관 수량

**SKU(Stock Keeping Unit)란?**
물류에서 사용되는 용어로 상품을 구별하기 위한 고유의 식별 코드입니다.

예를 들어, `인천DC(출발지)` 에서 `송파잠실PPC(목적지)` 로 `배달이 피규어(SKU: S01234)` 를 `10개(이관 수량)` 이관하기 위한 이관요청서를 생성했다고 가정합니다. 최초 생성된 이관요청서는 할당 상태가 미할당으로 생성됩니다.

| 출발지 센터 | 목적지 센터 | SKU | 이관 수량 | 할당 상태 |
| --- | --- | --- | --- | --- |
| 인천DC | 송파잠실PPC | 배달이 피규어(S01234) | 10 | 미할당 |

DC 관리자에 의해 생성된 이관요청서로 재고를 옮기려면 할당 상태를 `미할당 → 할당` 으로 만들어야 합니다. 할당 작업은 내부 로직에 의해 자동으로 할당 로케이션을 지정하거나, DC 관리자가 수동으로 할당 로케이션을 지정할 수 있습니다. 재고가 할당되면 할당 상태가 `미할당 → 할당` 으로 변경됩니다.

| 출발지 센터 | 목적지 센터 | SKU | 이관 수량 | 할당 상태 |
| --- | --- | --- | --- | --- |
| 인천DC | 송파잠실PPC | 배달이 피규어(S01234) | 10 | 미할당 → **할당** |

**할당이란?**
동일한 상품이 물류 센터 내 여러 로케이션(위치)에 흩어져 있는 경우, 작업자가 출고할 상품을 선점하는 작업이 필요한데 이 작업을 할당이라고 합니다.

이관요청서를 잘못 생성한 경우(예: SKU 코드를 잘못 입력한 경우) 재고를 이관하지 않기 위해 이관요청서를 취소할 수 있습니다. 취소 대상의 이관요청서는 할당 상태가 미할당이어야 합니다. 즉, 취소를 시도할 때는 최초 이관요청서가 생성되었을 때와 할당 상태가 동일해야 합니다.

![](https://techblog.woowahan.com/wp-content/uploads/2024/05/20240528_2.png)

## 할당과 취소

할당은 **(1)재고 할당** 과 **(2)할당 상태 변경** 이라는 두 가지 작업을 합니다. 이때 할당 상태는 재고 할당 결과에 따라 결정됩니다. 따라서, 할당 상태는 재고 할당을 모두 시도한 후 변경해야 합니다.

**할당 상태란?**
– 할당 (이관요청 수량 = 할당 수량)
– 부분할당 (이관요청 수량 > 할당 수량)
– 미할당 (할당 수량 = 0)
– 취소

취소는 이관요청서에 재고가 할당되지 않은 상태(미할당)만 가능합니다. 이관요청서를 취소하면 할당 상태가 `미할당 → 취소` 상태로 변경됩니다.

|  | 할당 상태 | 비고 |
| --- | --- | --- |
| 할당 | 미할당 → 할당 or 부분할당 | 할당 결과에 따라 할당 상태가 결정됨 |
| 취소 | 미할당 → 취소 | 미할당 상태인 경우에만 취소가 가능 |

## 할당과 취소를 동시에 요청한다면?

> 취소된 이관요청서에 재고가 할당되어 있어요.

DC 관리자로부터 취소된 이관요청서에 재고가 할당되어있다는 문의가 들어왔습니다. 해당 이관요청서를 확인해 보니 동일한 시점에 할당과 취소가 요청된 것을 확인할 수 있었습니다. 한 관리자는 재고 이관을 위해 이관요청서를 할당했고, 동일한 시점에 다른 관리자는 이관요청서를 취소한 것입니다.

![](https://techblog.woowahan.com/wp-content/uploads/2024/05/20240528_3.png)

그런데 어떻게 취소된 이관요청서에 재고가 할당될 수 있었을까요? 먼저 할당 API를 살펴보겠습니다. 앞서 설명한 것처럼 할당은 **(1)재고 할당** 과 **(2)할당 상태 변경** 두 가지 작업을 하고 있으며, 재고 할당 결과(result)에 따라 할당 상태가 변경됩니다.

즉, 할당 API는 재고 할당과 할당 상태 변경의 트랜잭션이 분리되어 있습니다. 그리고 재고 할당은 DB 트랜잭션을 짧게 하기 위해서 이관요청서 단위가 아닌, 이관요청서 하위 SKU 단위로 재고를 할당합니다.

![](https://techblog.woowahan.com/wp-content/uploads/2024/05/20240528_5_3.png)

```kotlin
// 할당 API
@PostMapping("/api/orders/{orderId}/items/{orderItemId}/allocation"
)
fun allocateItem(
    @PathVariable orderId: Long, // 이관요청서 ID
    @PathVariable orderItemId: Long // 이관요청서 하위 SKU(아이템) ID
): AllocateItemResponse {
    // (1) 재고 할당
    val result = orderItemAllocationService.allocateItem(orderItemId)
    if (result) {
        // (2) 할당 상태 변경
        orderAllocationService.updateStatus(orderId)
    }
    return OrderItemAllocationResponse(result)
}
```

할당 API는 SKU 단위로 재고를 할당하기 때문에 이관요청서 하위 SKU들을 병렬로 할당할 수 있습니다. 그리고 이관요청서 할당 상태 변경 전에 분산 락 설정이 되어 있어서, 이관요청서 SKU들을 병렬로 할당하더라도 재고 할당 결과에 따라 할당 상태가 의도한 상태로 변경됩니다.

```kotlin
@Service
class OrderAllocationService(
    // ...
) {
    fun updateStatus(orderId: Long) {
        try {
            // 분산 락 시작
            wmsRedisLock.lock(key = orderId, waitSecond = 5) {
                // 함수형 트랜잭션 적용
                functionalWmsTransactional.run {
                    val order = orderService.getByOrderId(orderId)
                    order.updateStatus() // 할당 결과에 따라 할당 상태 변경
                }
            }
            // 분산 락 종료
        } catch (e: IllegalStateException) {
            throw RuntimeException("(락 획득 실패) 동시성 이슈가 발생했습니다. [orderId: $orderId]"
)
        }
    }
}
```

그런데 왜 재고 할당과 동시에 취소했을 때, 이관요청서 할당 상태가 취소이고 재고가 할당된 상태로 남아 있었을까요? 그 이유는 취소 API가 분산 락 설정 없이 이관요청서 할당 상태를 취소 상태로 변경하고 있었기 때문이었습니다.

```kotlin
// 취소 API
@PostMapping("/api/orders/{orderId}"
)
fun cancel(
    @PathVariable orderId: Long
): OrderCancelResponse {
    val result = orderCancelService.cancel(orderId) // 분산 락 설정 없음
    return OrderCancelResponse(result)
}
```

## 동시성 이슈 원인

동시성 이슈의 원인은 취소 작업에는 분산 락이 걸려 있지 않기 때문입니다. 즉, 재고 할당 중에는 아직 할당 상태가 변경되지 않아 미할당 상태이므로, 취소 요청이 가능합니다. 할당 요청이 처리되고 마지막에 취소 요청이 반영되면서 이관요청서가 할당된 상태로 할당 상태가 취소로 변경된 것입니다.

![](https://techblog.woowahan.com/wp-content/uploads/2024/05/20240528_4-750x398.png)

그렇다면 왜 취소 요청 시에 재고 할당이 해제되지 않았을까요? 그 이유는 취소 로직은 이관요청서 할당 상태만 변경하고 할당과 관련된 작업은 하지 않기 때문입니다. 그럼, 이제 취소 요청에 분산 락을 설정하여 동시성 이슈를 제어해 봅시다.

## 할당과 취소가 동시에 처리되는 것을 막아보자

## 1 단계: 분산 락 추가하기

**키 포인트**
할당, 취소 시 동일한 분산 락 키 사용하기 (이관요청서 단위)

### 해결방법

앞서 동시성 이슈 원인을 살펴본 결과, 이관요청서가 할당 중일 때는 취소 요청이 되지 않아야 합니다. 재고 할당과 취소 로직에 이관요청서 단위로 분산 락을 추가하면, 동시에 이관요청서의 할당 상태를 변경하려는 것을 막을 수 있습니다.

![](https://techblog.woowahan.com/wp-content/uploads/2024/05/20240528_step1_1-750x466.png)

### 문제점

이관요청서 단위로 분산 락을 걸고 할당과 취소를 동시에 해봅시다. 이관요청서에 하나의 SKU만 있는 경우에는 정상적으로 동작하는 것으로 보입니다. 그런데, 이관요청서 하위에 N개 SKU가 있는 경우는 어떻게 될까요? 첫 번째 할당 요청만 성공하고 나머지 할당은 모두 실패합니다.

왜냐하면, 하나의 이관요청서 하위에는 SKU 단위의 데이터가 있으며, SKU 단위로 재고가 할당됩니다. 그런데 이관요청서 단위로 분산 락을 설정하게 되면 어떻게 될까요? 클라이언트에서 이관요청서 하위에 있는 N개의 SKU를 동시에 할당해 달라 요청할 때, 첫 번째 SKU만 할당되고 나머지 SKU들은 분산 락 획득에 실패하여 재고가 할당되지 않습니다.

![](https://techblog.woowahan.com/wp-content/uploads/2024/05/20240528_step1_2-750x460.png)

## 2 단계: 분산 락 대기하기

**키 포인트**
1\. 할당, 취소 시 동일한 분산 락 키 사용하기 (이관요청서 단위)
2\. 분산 락에 waitTime 설정하기

### 해결방법

할당은 이관요청서 단위가 아닌, 이관요청서의 하위 SKU 단위로 진행합니다. 즉, 화면에서 이관요청서 하나를 할당 요청했을 때, 해당 이관요청서 하위에 10개 SKU가 있는 경우 실제로는 10번의 할당 요청 API가 호출됩니다. 따라서 이관요청서 단위로 분산 락 키를 사용하게 되면 첫 번째 할당 요청만 성공하고 나머지는 할당 요청은 실패하게 됩니다.

첫 번째 할당 요청만 성공하고 나머지 할당 요청이 실패하는 것에 대응하기 위해, 분산 락에 waitTime(대기 시간)을 설정해서 순차 처리가 되도록 합니다. 이제 할당과 취소가 동시에 진행되는 것을 막았고, 이관요청서 하위에 N개 SKU가 있는 경우에도 할당이 정상적으로 되는 것을 확인할 수 있습니다.

![](https://techblog.woowahan.com/wp-content/uploads/2024/05/20240528_step2_1-750x468.png)

### 문제점

다만, 이와 같은 해결 방법에도 문제점이 있습니다. 분산 락 waitTime 설정에 의해서 분산 락을 획득하기까지 할당 요청을 처리하는 것을 대기합니다. 즉, 이관요청서의 하위 SKU가 많아질수록 할당 처리 시간이 늘어나게 됩니다.

할당과 취소가 동시에 되는 것은 막았지만, 이 방법은 이관요청서의 할당 속도를 포기하는 방법입니다. 다음 스텝에서 할당과 취소가 동시에 되는 것은 막고, 할당은 병렬로 처리하는 방법에 대해 알아봅니다.

![](https://techblog.woowahan.com/wp-content/uploads/2024/05/20240528_step2_2-750x467.png)

## 3 단계: 분산 락과 상태 키 함께 사용하기

**키 포인트**
1\. 할당, 취소 시 동일한 분산 락 키 사용하기 (이관요청서 단위)
2\. 분산 락에 waitTime 설정하기
3\. 분산 락과 상태 키 함께 사용하기

### 해결방법

이관요청서 단위로 분산 락을 설정하여 할당과 취소가 동시에 되는 것은 막았지만, waitTime이 설정되어 분산 락 획득 대기 시간 만큼 할당이 지연되었습니다. 이번에는 이관요청서 단위로 분산 락을 설정하고 분산 락 안에서 재고 할당과 할당 상태를 변경하는 것이 아니라, 이관요청서가 할당중 상태인지 취소중 상태인지를 체크하는 상태 키를 추가로 사용하도록 수정합니다.

상태 키 분산 락 안에서는 현재 요청이 할당이면 `할당(ALLOCATION)` 값을 Redis에 저장하고, 현재 요청이 취소면 `취소(CANCEL)` 값을 저장합니다. 그리고 상태 값을 저장할 때 해당 키의 유효시간을 갱신합니다.

이관요청서의 현재 상태가 `할당 → 할당` 상태인 경우 다음 로직(재고 할당, 할당 상태 변경)으로 넘어가고, `취소 → 할당` 인 경우는 할당 작업을 진행하지 않고 예외를 발생시키고 요청을 종료합니다. 반대로 취소 요청시 상태가 `취소 → 취소`, `할당 → 취소` 인 경우에도 할당 작업의 처리 방식과 동일합니다.

*즉, Step3 에서는 할당과 취소 작업 전 상태 키 설정 분산 락 안에서 상태 값을 확인하고 이후 로직을 수행할지 여부를 결정합니다.*

![](https://techblog.woowahan.com/wp-content/uploads/2024/05/20240528_step3_1-3-750x406.png)

```kotlin
@Service
class OrderAllocationWebService(
    // ...
) {
    fun allocate(orderId: Long, orderItemId: Long): Boolean {
        tryLock(orderId)
        return allocateItemAndUpdateStatus(orderId, orderItemId)
    }

    private fun tryLock(orderId: Long) {
        try {
            // 분산 락 시작
            wmsRedisLock.lock(key = orderId, waitSecond = 5) {
                val statusKey = "STATUS_KEY:$orderId"

                val status = redisTemplate.opsForValue()[statusKey]?.let { OrderStatus.valueOf(it.toString()) }
                when (status) {
                    // 현재 상태가 할당 또는 null 상태면, 키 값 설정 후 유효시간 30초로 갱신
                    OrderStatus.ALLOCATION, null -> {
                        redisTemplate.opsForValue().set(statusKey, OrderStatus.ALLOCATION, 30, TimeUnit.SECONDS)
                    }
                    // 현재 상태가 취소 상태면, 예외 발생
                    OrderStatus.CANCEL -> {
                        throw RuntimeException("(할당 -> 취소) 동시성 이슈가 발생했습니다. [orderId: $orderId]"
)
                    }
                }
            }
            // 분산 락 종료
        } catch (e: IllegalStateException) {
            throw RuntimeException("(락 획득 실패) 동시성 이슈가 발생했습니다. [orderId: $orderId]"
)
        }
    }

    private fun allocateItemAndUpdateStatus(orderId: Long, orderItemId: Long): Boolean {
        // (1) 재고 할당
        val result = orderItemAllocationService.allocateItem(orderItemId)
        if (result) {
            // (2) 할당 상태 변경 (분산 락 포함)
            orderAllocationService.updateStatus(orderId)
        }
        return result
    }
}
```

상태 키 값을 설정하는 것은 단순히 값만 변경하는 작업이라 빠르게 처리되어 전체 처리 속도에 영향이 적습니다. 할당 API에서 처리 시간이 가장 오래 걸리는 부분은 재고 할당이며, 할당 결과에 따라 할당 상태가 결정되어야 하므로, 할당 상태를 변경하기 전 분산 락 설정이 필요합니다.

재고 할당은 분산 락 밖에서 처리되어 같은 상태의 요청이 들어오더라도 병렬로 처리되며, 현재 상태와 다른 요청이 들어왔을 때는 예외를 발생시켜 처리를 하지 않는 프로세스를 구현할 수 있습니다.

![](https://techblog.woowahan.com/wp-content/uploads/2024/05/20240528_step3_2-4-750x347.png)

## 마무리

지금까지 WMS 재고 이관시 발생한 동시성 이슈를 해결하기 위해 분산 락을 사용하는 과정을 살펴보았습니다. 분산 락은 여러 프로세스가 동일한 자원에 접근할 때 발생할 수 있는 충돌을 방지하고, 시스템의 안정성을 높이는 데 큰 역할을 합니다. WMS에서는 여러 작업이 동시에 수행되더라도 재고 데이터의 일관성을 유지할 수 있도록, 분산 락을 사용하여 시스템의 신뢰성을 높이고 오류를 최소화합니다.

분산 락 적용이 필요하면서도 병렬 처리가 필요한 경우, 상태 키를 설정하여 다음 로직을 수행할지를 결정했습니다. 이를 통해 할당과 취소가 동시에 발생하는 것을 방지할 수 있었고, 동일한 작업의 경우 병렬 처리까지 가능하게 되었습니다. 분산 락을 사용하면서 상태에 따라 로직을 처리할지를 결정할 수 있어 앞으로도 유용하게 사용될 수 있을 것 같습니다.

본 글에서는 이관요청서 하위 SKU 단위로 할당 요청을 처리했지만, 개선안으로는 할당 요청을 이관요청 단위로 받아 하위 SKU들의 할당을 멀티 스레딩 방식으로 처리해 볼 수 있을 것 같습니다. 멀티 스레딩 방식을 사용하게 되면 API의 총 처리 시간 및 API 서버 부하에 대해 고려가 필요합니다. 비즈니스 상황에 따라 멀티 스레딩을 사용한 방식도 고려해 보면 좋을 것 같습니다.

마지막으로, WMS의 동시성 문제를 해결하는 과정에서 분산 락의 중요성을 느낄 수 있었고, 이러한 기술적 해결 방법을 통해 얻은 경험과 노하우를 공유하게 되어 기쁩니다. 본 글이 여러분의 시스템 안정성과 비즈니스 성장에 도움이 되기를 바라며, 더 나은 해결책을 찾아나가는 과정에 함께하기를 기대합니다.

## 더보기

[우아콘2024 – WMS 재고 이관을 위한 분산 락 사용기](https://youtu.be/3HCVD26zycM "우아콘2024 - WMS 재고 이관을 위한 분산 락 사용기")
