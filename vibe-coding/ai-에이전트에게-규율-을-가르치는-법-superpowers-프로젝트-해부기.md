---
title: "AI 에이전트에게 \"규율\"을 가르치는 법 - Superpowers 프로젝트 해부기"
source: "https://codex.epril.com/ai-superpowers"
author:
published: 2026-03-26
created: 2026-03-26
description: "Claude Code 플러그인 \"Superpowers\"를 코드 레벨까지 해부하면서 발견한 것들"
tags:
  - "clippings"
  - "coding-agents"
  - "vibe-coding"
  - "prompt-engineering"
  - "claude-code"
---

> [!summary]
> A deep analysis of the Superpowers Claude Code plugin, exploring how it enforces discipline on AI agents through techniques like negative prompting, anti-rationalization tables, persuasion psychology, and sub-agent architectures. Key takeaways include the power of pre-commitment declarations, the importance of skill description design (CSO), and zero-dependency plugin distribution.

![AI 에이전트에게 "규율"을 가르치는 법 - Superpowers 프로젝트 해부기](https://image.codex.epril.com/covers/906021f1-9f13-4d0e-a5c0-17341c070990.jpg)

> Claude Code 플러그인 "Superpowers"를 코드 레벨까지 해부하면서 발견한 것들. AI 에이전트의 행동을 체계적으로 제어하는 프롬프트 엔지니어링의 현재와 미래.

---

## 들어가며

AI 코딩 에이전트가 점점 강력해지고 있다. Claude Code, Cursor, Codex, Gemini CLI 같은 도구들이 실제 개발 현장에서 쓰이고 있고, 코드 생성 능력은 이미 인상적인 수준이다.

그런데 한 가지 문제가 있다.

**AI 에이전트는 "규율"이 없다.**

테스트를 건너뛰고, 근본원인을 조사하지 않고 수정부터 시도하고, "아마 될 거야"라고 말하면서 검증을 생략한다. 인간 주니어 개발자와 비슷한 문제를 보인다. 다만 AI는 훨씬 빠르게, 훨씬 확신에 차서 이런 실수를 한다.

[Superpowers](https://github.com/obra/superpowers) 라는 오픈소스 프로젝트는 이 문제를 정면으로 다룬다. 14개의 "스킬"로 구성된 이 Claude Code 플러그인은, AI 에이전트가 소프트웨어를 개발하는 **방식 자체** 를 체계적으로 제어한다.

나는 이 프로젝트의 모든 파일을 읽고, 모든 스킬을 분석했다. 그 과정에서 예상치 못한 것들을 많이 발견했다.

---

## 1\. 발견: AI도 합리화한다

Superpowers에서 가장 놀라웠던 것은 **합리화 방지 테이블** 이다.

TDD 스킬에는 이런 테이블이 있다:

| AI의 변명 | 현실 |
| --- | --- |
| "이건 너무 간단해서 테스트 안 해도 돼" | 간단한 코드가 깨진다. 테스트 30초면 된다. |
| "나중에 테스트 쓸게" | 즉시 통과한 테스트는 아무것도 증명 못 한다 |
| "이미 수동 테스트 했어" | 수동!= 체계적. 기록 없음, 재실행 불가 |
| "테스트 프레임워크가 없어" | 스크립트 하나면 된다. 프레임워크 없어도 테스트 가능 |

이건 인간 개발자의 변명이 아니다. **AI 에이전트가 실제로 하는 합리화** 다.

LLM은 지시를 "해석"할 수 있다. "테스트를 먼저 작성하라"라는 지시를 받아도, "이건 설정 파일이니까 테스트가 필요 없다"고 스스로 판단한다. 이건 버그가 아니라 LLM의 본질적 특성이다. 자연어를 이해하기 때문에, 자연어의 예외를 만들 수도 있다.

Superpowers의 해결책은 **미리 모든 예외를 차단하는 것** 이다. 31개의 합리화 시나리오를 나열하고, 각각에 대해 "아니, 이 경우에도 적용된다"라고 명시한다.

이건 프롬프트 엔지니어링의 새로운 패턴이다. **네거티브 프롬프팅** - 무엇을 하라고 말하는 것보다, 무엇을 하지 말아야 하는지의 예외를 차단하는 것이 더 효과적이다.

---

## 2\. 발견: 설득 심리학이 프롬프트에 적용된다

Superpowers의 `writing-skills` 스킬에는 `persuasion-principles.md` 라는 파일이 있다. Meincke et al. (2025)의 연구를 인용하면서, AI 에이전트의 규율 준수율을 높이는 7가지 설득 원칙을 설명한다.

연구 결과: **적절한 설득 원칙을 적용하면 준수율이 33%에서 72%로 상승** 한다.

| 원칙 | 프롬프트 적용 |
| --- | --- |
| **Authority** | "YOU MUST", "Never", "No exceptions" |
| **Commitment** | "Announce: 'Using \[skill\] to \[purpose\]'" (사전 선언) |
| **Scarcity** | "Before proceeding", "BEFORE any response" (순서 제약) |
| **Social Proof** | "Every time", "Always" (규범 설정) |

그중에서도 **Commitment** 원칙이 인상적이다. Superpowers는 AI에게 스킬을 사용하기 전에 "Using brainstorming skill to design the feature"라고 **선언하게** 한다. 이 선언이 심리적 잠금 장치가 되어, 선언한 워크플로우를 따를 확률을 높인다.

반면 **Liking** (호감) 원칙은 규율 강제 스킬에서 명시적으로 금지된다. "친근한 톤으로 규칙을 이야기하면 규칙을 어겨도 괜찮다는 인상을 준다"는 것이 이유다.

AI 에이전트를 위한 프롬프트를 쓸 때, 우리는 심리학 논문을 읽어야 할지도 모른다.

---

SEO(Search Engine Optimization)가 구글을 위한 최적화라면, **CSO는 AI 에이전트를 위한 최적화** 다.

Superpowers의 각 스킬에는 `description` 필드가 있다. 이건 Claude가 어떤 스킬을 적용할지 결정할 때 읽는 메타데이터다. 여기서 놀라운 발견이 있었다:

```yaml
YAMLCopy# BAD: 워크플로우 요약을 포함하면 Claude가 description만 읽고 스킬 본문을 건너뜀
description: "Use for TDD - write test first, watch it fail, write minimal code, refactor"

# GOOD: 트리거 조건만 기술하면 Claude가 반드시 스킬 본문을 로드
description: "Use when implementing any feature or bugfix, before writing implementation code"
```

description에 워크플로우를 요약하면, Claude가 그 요약만으로 충분하다고 판단하고 전체 SKILL.md를 읽지 않는다. 예를 들어 "code review between tasks"라고 쓰면 1번만 리뷰하지만, 실제 스킬에는 2단계 리뷰(스펙 준수 -> 코드 품질)가 정의되어 있다.

이건 구글 검색에서 meta description이 너무 완전하면 사용자가 클릭하지 않는 것과 정확히 같은 현상이다.

앞으로 AI 에이전트 도구, MCP 서버, 스킬 시스템을 만들 때, description 필드의 설계가 도구의 활용도를 결정할 것이다.

---

## 4\. 발견: Zero-Dependency의 아름다움

Superpowers의 브레인스토밍 서버(`server.cjs`)는 354줄의 Node.js 코드로 HTTP 서버와 WebSocket 서버를 구현한다. 외부 의존성이 **하나도 없다**.

- Express 대신 `http.createServer`
- Socket.io 대신 RFC 6455 직접 구현
- Chokidar 대신 `fs.watch`

이전 버전에서는 Express + Socket.io를 사용했고, `node_modules` 가 ~1,200줄이었다. 이걸 모두 제거하고 내장 모듈만으로 재작성했다.

**왜?** 이 서버는 Claude Code 플러그인의 일부로 배포된다. 사용자가 `npm install` 을 실행할 필요가 없어야 한다. 의존성이 있으면 설치 과정에서 문제가 생길 수 있고, 버전 충돌이 생길 수 있고, 보안 취약점이 생길 수 있다.

RFC 6455 WebSocket 프로토콜을 직접 구현한 코드가 특히 인상적이었다:

```javascript
JAVASCRIPTCopyfunction computeAcceptKey(clientKey) {
  return crypto.createHash('sha1')
    .update(clientKey + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11')
    .digest('base64');
}
```

이 매직 스트링(`258EAFA5-E914-47DA-95CA-C5AB0DC85B11`)은 RFC 6455에 정의된 고정 GUID다. WebSocket 핸드셰이크의 근본적인 원리를 직접 구현한 것이다.

교훈: **플러그인/라이브러리를 배포할 때, 의존성을 0으로 만드는 것의 가치는 생각보다 크다.**

---

## 5\. 발견: 서브에이전트 패턴 - AI 팀 시뮬레이션

Superpowers의 `subagent-driven-development` 은 사실상 **소프트웨어 팀의 역할 분담을 AI로 재현** 한 것이다.

```
Copy컨트롤러 (Tech Lead)
  ├── 구현자 서브에이전트 (Developer)
  ├── 스펙 리뷰어 서브에이전트 (QA)
  └── 코드 품질 리뷰어 서브에이전트 (Senior Dev)
```

각 서브에이전트는 독립된 세션으로 실행되며, **신선한 컨텍스트** 를 갖는다. 이전 작업의 편향에 영향받지 않는다.

가장 인상적인 설계 결정은 \*\*"서브에이전트에게 파일 읽기를 요청하지 마라"\*\*는 원칙이다. 대신 컨트롤러가 모든 필요한 텍스트를 프롬프트에 직접 포함시킨다. 이유:

1. 서브에이전트가 파일을 찾지 못할 수 있다
2. 파일 경로가 worktree에 따라 다를 수 있다
3. 전체 텍스트를 주면 서브에이전트의 첫 액션이 항상 "구현"이 된다

또한 스펙 리뷰어에게는 "구현자의 보고서를 신뢰하지 마라. 직접 코드를 읽어라"라고 지시한다. **불신 기반 검증** 이다. 인간 조직에서 QA가 개발자의 "테스트 완료" 보고를 믿지 않고 직접 확인하는 것과 같다.

이 패턴은 AI 에이전트 아키텍처의 미래를 보여준다. 단일 에이전트가 모든 것을 하는 것이 아니라, 역할별 에이전트가 서로를 검증하는 구조.

---

## 6\. 발견: Polyglot 스크립트 - CMD와 Bash가 하나의 파일에

`hooks/run-hook.cmd` 는 CMD.exe와 bash 모두에서 유효한 파일이다:

```bash
BASHCopy: << 'CMDBLOCK'
@echo off
REM Windows에서 실행: bash를 찾아서 스크립트 실행
...
CMDBLOCK
# Unix에서 실행: 위의 : 는 no-op
exec bash "$PLUGIN_ROOT/hooks/$1"
```

CMD에서 `:`는 레이블이고, bash에서 `:`는 no-op이다. `<< 'CMDBLOCK'` 는 CMD에서 무시되고, bash에서는 heredoc으로 Windows 코드 블록을 건너뛴다.

단일 파일로 두 플랫폼을 지원하는 이 테크닉은 AI 도구 뿐 아니라 어떤 크로스플랫폼 CLI 도구에서든 유용하다.

---

## 7\. 배운 것: 실전에 적용할 교훈들

### 프롬프트 엔지니어링

1. **네거티브 프롬프팅이 포지티브보다 강력하다** - "이렇게 해라"보다 "이런 변명은 통하지 않는다"가 효과적
2. **Iron Law 패턴** - "NO X WITHOUT Y"라는 절대 규칙은 LLM이 잘 따른다
3. **사전 선언(Commitment)이 행동을 고정시킨다** - AI가 "이 스킬을 사용하겠다"고 선언하면 이탈 확률이 줄어듦
4. **Description은 검색 키지 요약이 아니다** - 워크플로우를 요약하면 도구가 제대로 사용되지 않음

### AI 에이전트 아키텍처

1. **역할 기반 서브에이전트가 단일 에이전트보다 신뢰할 수 있다** - 구현자/리뷰어 분리로 품질 향상
2. **불신 기반 검증** - 자기 보고를 믿지 않고 독립적으로 확인하는 패턴
3. **신선한 컨텍스트** - 새 서브에이전트는 이전 작업의 편향에서 자유롭다

### 소프트웨어 설계

1. **Zero-dependency는 배포 마찰을 제거한다** - 특히 플러그인/라이브러리에서 중요
2. **점진적 공개(Progressive Disclosure)** - 필요할 때만 상세 정보를 로드
3. **자기 참조적 시스템** - 스킬을 작성하는 스킬이 존재하고, 그것도 TDD로 개발됨

---

## 8\. 앞으로 해보고 싶은 것들

### 나만의 스킬 세트 만들기

Superpowers의 구조를 그대로 활용해서 도메인 특화 스킬을 만들어보고 싶다:

- **Spring Boot 개발 스킬**: 엔티티 설계 -> Repository -> Service -> Controller 순서 강제
- **API 설계 스킬**: OpenAPI 스펙 먼저 -> 코드 생성 -> 통합 테스트
- **데이터 파이프라인 스킬**: 스키마 정의 -> 변환 로직 -> 데이터 품질 테스트

Superpowers의 `writing-skills` 스킬이 이 과정을 안내한다. 특히 "스킬을 TDD로 개발하라"는 원칙이 흥미롭다 - 스킬 없이 AI가 실패하는 시나리오를 먼저 만들고, 그 실패를 해결하는 최소한의 스킬을 작성하는 것.

### 팀 규율을 코드화하기

팀의 코딩 표준, 리뷰 기준, 아키텍처 원칙을 Superpowers 스타일의 스킬로 만들면, AI 에이전트가 팀의 규율을 자동으로 따르게 할 수 있다.

예: "우리 팀은 Error를 throw하지 않고 Result 타입을 사용한다"를 스킬로 만들면, AI가 코드를 생성할 때 자동으로 Result 패턴을 적용한다.

### 멀티에이전트 리뷰 파이프라인

Superpowers의 2단계 리뷰(스펙 준수 -> 코드 품질)를 확장해서:

1. **보안 리뷰어**: OWASP Top 10 체크
2. **성능 리뷰어**: N+1 쿼리, 메모리 릭 감지
3. **접근성 리뷰어**: WCAG 준수 확인
4. **문서 리뷰어**: API 문서 완전성 확인

각각 독립된 서브에이전트로 실행하면, 인간 리뷰어 4명을 고용한 것과 비슷한 효과를 얻을 수 있을 것이다.

### CSO 최적화 프레임워크

MCP 서버, AI 도구, 스킬 시스템의 description 필드를 최적화하는 체계적인 방법론을 만들어보고 싶다. A/B 테스트로 어떤 description이 더 높은 활용률을 보이는지 측정하는 것이다.

---

## 마치며

Superpowers를 분석하면서 가장 크게 느낀 것은, **AI 에이전트의 시대에 "프로세스"의 가치가 더 높아진다는 것** 이다.

AI는 코드를 빠르게 생성할 수 있지만, 좋은 소프트웨어를 만드는 것은 코드 생성이 아니라 프로세스다. 설계하고, 계획하고, 테스트하고, 검증하고, 리뷰하는 과정. Superpowers는 이 과정을 AI에게 가르치는 방법을 보여준다.

그리고 그 방법은 놀랍도록 인간적이다. 합리화 방지, 설득 심리학, 불신 기반 검증, 사전 선언 - 이것들은 모두 인간 조직에서 수십 년간 사용해온 기법들이다. AI 에이전트가 더 인간처럼 행동할수록, 인간 조직의 지혜가 더 유용해진다.

166개 파일, 21,400줄의 코드와 문서를 분석하면서, 나는 AI 에이전트 시대의 소프트웨어 엔지니어링이 어떤 모습일지 엿볼 수 있었다. 코드를 작성하는 것은 AI가 하지만, **어떻게 작성할지를 설계하는 것** 은 여전히 인간의 몫이다. 그리고 그 설계가 점점 더 정교해지고 있다.

---

*이 글에서 분석한 Superpowers 프로젝트는 [github.com/obra/superpowers](https://github.com/obra/superpowers) 에서 확인할 수 있습니다. MIT 라이선스로 공개되어 있으며, Claude Code, Cursor, Codex, OpenCode, Gemini CLI에서 사용할 수 있습니다.*

## 댓글 0개

아직 댓글이 없습니다. 첫 댓글을 남겨보세요.

Subscribe

### 새 글을 이메일로 받아보세요

새로운 블로그 포스트나 위키 페이지가 게시되면 알려드립니다. 스팸 없이, 가치 있는 콘텐츠만 전달합니다.
