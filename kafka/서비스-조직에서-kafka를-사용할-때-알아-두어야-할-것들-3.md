---
title: "서비스 조직에서 Kafka를 사용할 때 알아 두어야 할 것들 (3)"
source: "https://d2.naver.com/helloworld/2472336"
author:
published:
created: 2026-06-28
description:
tags:
  - "clippings"
---

> [!summary]
> NAVER ENGINEERING DAY 2025에서 발표된 Kafka 메타데이터 세션(3편)이다. Kafka metadata가 무엇인지, 브로커-클라이언트 및 브로커 간 메타데이터가 어떻게 교환되는지 동작 메커니즘을 설명한다. 서비스 개발자 관점에서 관련 옵션을 어떻게 설정하면 좋은지를 다룬다.

네이버 사내 기술 교류 행사인 NAVER ENGINEERING DAY 2025(5월)에서 발표되었던 세션을 공개합니다.
[서비스 조직에서 Kafka를 사용할 때 알아 두어야 할 것들 (4)](https://d2.naver.com/helloworld/1025526) 에서 이어집니다. 1,2편은 사내용으로 발표되어 아쉽지만 외부 공개는 어려운 점 양해 부탁드립니다.

<iframe width="800" height="450" src="https://tv.naver.com/embed/79195901?autoPlay=true" frameborder="0" allowfullscreen=""></iframe>

#### 발표 내용

Kafka Client는 어떻게 클러스터의 전체 상태를 알 수 있는가? 서비스를 개발하는 입장에서 관련 옵션을 어떻게 잡아 주면 좋은가? 에 대해 설명합니다.

#### 목차

- Kafka metadata란 무엇인가?
- 동작 매커니즘
	- 브로커 - 클라이언트 간 metadata 교환
		- 브로커 간 metadata 교환
- 결론
	- ... 그리고 하나 더

> ##### ◎ NAVER ENGINEERING DAY란?
>
> NAVER에서는 사내 개발 경험과 기술 트렌드를 교류를 할 수 있는 프로그램이 많이 있습니다. 그중 매회 평균 70개 이상의 발표가 이루어지는 NAVER ENGINEERING DAY를 빼놓을 수 없는데요.
> 2016년부터 시작된 ENGINEERING DAY는 실무에서의 기술 개발 경험과 새로운 기술과 플랫폼 도입 시 유용하게 활용될 수 있는 팁 등을 공유하며 서로 배우고 성장하는 네이버의 대표적인 사내 개발자 행사입니다.
> 올해 진행된 NAVER ENGINEERING DAY의 일부 세션을 공개합니다.

![](https://d2.naver.com/image/20250616/659836361533.png)

글쓴이

이동진|NAVER 테크 플랫폼

소개

네이버 플랫폼 조직에서 사내 카프카 서비스 개발을 하고 있습니다.

##### 댓글

2

- 이태현
	안녕하세요. 혹시 1편과 2편은 업로드 계획이 따로 없으신 걸까요?
	2025-06-27 13:44
	[**답글** 1](#)
	**공감/비공감** [공감 *11*](#) [비공감 *0*](#)
