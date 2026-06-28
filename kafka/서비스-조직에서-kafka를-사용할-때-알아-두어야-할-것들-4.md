---
title: "서비스 조직에서 Kafka를 사용할 때 알아 두어야 할 것들 (4)"
source: "https://d2.naver.com/helloworld/1025526"
author:
published:
created: 2026-06-28
description:
tags:
  - "clippings"
---

> [!summary]
> NAVER ENGINEERING DAY 2025에서 발표된 Kafka 프로듀서 최적화 세션(4편)이다. Kafka 자료 구조를 배경으로 프로듀서와 브로커가 메시지를 주고받는 방식과 linger.ms, batch.size, buffer.memory를 통한 최적화 방법을 설명한다. 또한 (재)압축 동작 방식과 compression.type, compression.{type}.level을 활용한 압축 최적화를 다룬다.

네이버 사내 기술 교류 행사인 NAVER ENGINEERING DAY 2025(5월)에서 발표되었던 세션을 공개합니다.
[서비스 조직에서 Kafka를 사용할 때 알아 두어야 할 것들 (3)](https://d2.naver.com/helloworld/2472336) 을 보고 오시면 좋습니다. 1,2편은 사내용으로 발표되어 아쉽지만 외부 공개는 어려운 점 양해 부탁드립니다.

<iframe width="800" height="450" src="https://tv.naver.com/embed/79196054?autoPlay=true" frameborder="0" allowfullscreen=""></iframe>

#### 발표 내용

Kafka 프로듀서 최적화하기 + 압축 기능 활용하기

#### 목차

- 배경: Kafka 자료 구조
	- Kafka 자료 구조는 어떻게 생겼는가?
- 프로듀서 동작 방식 및 최적화 방법
	- 프로듀서와 브로커는 어떻게 메시지를 주고받는가?
		- linger.ms, batch.size, buffer.memory 사용법
- 압축 동작 방식 및 최적화 방법
	- (재)압축은 어떻게 이루어지는가?
		- compression.type, compression.{type}.level 사용법

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

0

등록된 댓글이 없습니다.
