---
title: "프로덕션 환경에서 사용하는 golang과 gRPC | 뱅크샐러드"
source: "https://blog.banksalad.com/tech/production-ready-grpc-in-golang/"
author:
published:
created: 2026-11-04
description: "안녕하세요, 뱅크샐러드 엔지니어링 파운데이션의 정겨울입니다. 뱅크샐러드는 마이크로 서비스 환경에서 다양한 언어와 프로토콜을 활용해 서비스를 운영하고 있습니다. 하나의 서비스는 요청을 처리하기 위해 다른 서비스의 API를 호출하는데 대부분의 기존 서비스는 REST API를 통해 JSON…"
tags:
  - "clippings"
---

> [!summary]
> Banksalad explains why it adopted gRPC with Go, valuing protobuf as the source of truth for service APIs over the performance gain, after its API docs kept going stale. It covers a single idl repository with committed generated code, grpc-gateway for JSON compatibility, and service-owned Go clients that wrap legacy REST APIs in protobuf types. The rest builds up the production interceptor chain: structured logging with logrus and ctxtags, stack traces via pkg/errors, and statsd metrics.

![프로덕션 환경에서 사용하는 golang과 gRPC](https://blog.banksalad.com/static/a93e921ebc82f0617437e18fdfbae22b/263b1/cover.webp)

안녕하세요, 뱅크샐러드 엔지니어링 파운데이션의 정겨울입니다.

뱅크샐러드는 마이크로 서비스 환경에서 다양한 언어와 프로토콜을 활용해 서비스를 운영하고 있습니다. 하나의 서비스는 요청을 처리하기 위해 다른 서비스의 API를 호출하는데 대부분의 기존 서비스는 REST API를 통해 JSON으로 통신하고 있습니다. 최근 기존 서비스 안정화 작업 및 신규 서비스 개발 시 go 언어로 개발을 진행하면서 internal 서비스 간 네트워크 통신에 gRPC를 활용하는 비중이 점점 커지고 있습니다. 그 과정에서 뱅크샐러드가 왜 go와 gRPC를 사용했고 gRPC를 잘 쓰기 위해 무엇을 고민했는지 공유하고자 합니다.

## 왜 gRPC를 사용하는가

[gRPC](https://grpc.io/) 는 HTTP/2 레이어 위에서 [Protocol Buffers](https://developers.google.com/protocol-buffers) (이하 protobuf)를 사용해 직렬화된 바이트 스트림으로 통신하므로 JSON 기반의 통신보다 더 가볍고 그만큼 통신 속도가 빠릅니다. 때문에 internal 통신이 빈번한 마이크로 서비스 구조에서 gRPC를 적용했을 때 latency 감소 및 더 많은 트래픽을 처리하는 성능의 이점을 기대해 gRPC를 도입해볼 수 있습니다.

하지만 뱅크샐러드는 protobuf와 gRPC가 **각 서비스의 API를 정의하는 source of truth** 가 될 수 있다는 점을 성능의 이점보다 더 큰 장점으로 여겨 도입했습니다.

클라이언트 개발자와 서버 개발자는 사이에 API를 두고 각자 기능을 구현합니다. 기존에 뱅크샐러드는 [API Blueprint](https://apiblueprint.org/) 와 [swagger](https://swagger.io/) 를 이용해 API를 문서화하고 명세를 검토하고 합의한 문서를 기준으로 기능을 구현해왔습니다. 하지만 API 문서를 기준으로 막상 개발하다 보면 수정사항이 발생하고, 이를 코드에는 반영하지만 정작 API 문서에는 반영하지 않아 API 명세가 점점 노후화되는 일이 반복되어 왔습니다. 그렇게 어느 순간부터 API 문서는 신뢰를 잃기 시작했으며 API 문서를 본격적으로 최신화하자니 거기에 시간을 쏟을 여유는 없고, 노후화된 문서가 원인이 되어 또 다른 버그가 발생하고, 신규입사자가 코드 파악을 위해 문서를 보며 헤매다가 질문을 하면 누군가가 “아 구두로 합의했는데 API 문서에 반영을 못 했습니다…”로 답이 나오는 일이 발생했습니다.

이에 뱅크샐러드는 gRPC와 protobuf를 사용해 마이크로서비스의 기능을 RPC로 선언했습니다. RPC마다 request, response 모델인 message를 정의하고, 이를 Swift, Java(Kotlin), Go, Python 등등 각 언어에서 import 하여 사용할 수 있도록 코드를 생성해 서버에서는 무조건 generated code를 사용해 protobuf 파일을 source of truth로 삼아 구현하며 기존의 문제를 해결했습니다.

![data 이모지](https://blog.banksalad.com/static/328ea6ca60f49ccc90a95579844a7cef/1e0c2/tada.png "data 이모지")

…라고 말하기까지 우리가 풀어야 할 문제는 무척 많았습니다. 당장이라도 protobuf를 이용해 API 명세를 버전 관리도하고 정합성도 보장하고 싶고 generated code를 이용해 gRPC 통신을 하고 싶었지만, go로 서버를 구현하기도 전 protobuf부터 잘 쓰기 위한 문제가 많았습니다. 인터넷에 검색해도 gRPC와 protobuf를 이용한 example, sample, tutorial 수준 이상의 자료는 찾기 힘들었고, 그 때 마다 현재 우리가 진짜 해결하고 싶은 문제가 무엇인지, 우리 조직에 맞는 최선의 선택을 내려야 했습니다.

## 우리가 마주한 문제들

protobuf와 gRPC를 잘 쓰기와 더불어 gRPC 서버를 golang으로 구현하기까지 많은 고민이 있었습니다.

- protobuf 명세를 어떻게 관리할지, 각 서비스의 protobuf를 각 서비스 코드 리포지토리에서 가지고 있을지, 아니면 하나의 공통 리포지토리에서 가질지, 또 protobuf를 Swift, Java, Go, Python 등등의 코드로 어떻게 변환시킬지, 어떤 모습이 협업할 때 병목 지점을 많이 만들지 않는 좋은 모습일지
- 새로운 서비스는 gRPC로 만든다고 해도 그 서비스를 호출하는 다른 기존 서비스는 JSON을 통한 REST API 통신을 하는데 이런 호환성을 어떻게 챙길지
- 반대로 go 서버에서 기존 서비스를 호출하면 JSON 응답을 줄 텐데 여기에 protobuf를 어떻게 적용할지, 또 어떻게 제대로 적용됐는지 테스트 코드를 작성할 수 있을지
- gRPC 서버간 통신에서 자잘한 호출 과정을 어떻게 좀 더 간편하게 할 수 있을지
- gRPC와 go 기반 서버의 프로젝트 구조는 어떻게 잡아야 할지
- 구조화된 로깅을 하기 위해선 어떻게 해야 할지, gRPC 관련 정보를 middleware 단에서 로깅하고 싶으면, 에러가 발생했을 때 stacktrace를 로깅하고 싶다면
- statsd를 이용해 메트릭을 기록하고 싶다면, 요청의 수와 응답 코드, latency 같은 기본적인 건 자동으로 로그를 남기게 하고 싶다면 어떻게 해야 할지

production에서 go를 활용해 gRPC 서비스를 운영하려면 이런 문제들은 반드시 풀어야만 했습니다. 여러 서비스를 만들며 문제를 풀기 위해 어떤 게 필요할지 논의를 반복하고, 경험을 기반으로 나름대로 노하우가 쌓이고 토대가 마련되기 시작했습니다.

## 뱅크샐러드의 gRPC 패턴

### protobuf를 한 곳에서 관리하는 idl 리포지터리

서비스마다 protobuf를 정의하면 해당 기능을 구현하는 클라이언트 개발자와 서버 개발자 간의 명세 논의는 편해집니다. 하지만 기존의 노후화된 API 문서 때문에 발생하는 고통을 생각해봤을 때, protobuf를 하나의 리포지토리로 모으는 편이 source of truth를 만들기에 좀 더 적합하다고 판단했습니다. 아직 성숙하지 않은 protobuf 사용 사례가 각 서비스 리포지토리 마다 파편화되어 녹이 스는 걸 경계함과 동시에 뱅크샐러드 기술조직은 ‘본인의 일이 아니더라도 언제든 참견해 함께 성장하자’라는 문화를 장려하기에 모두가 손쉽게 참여하는 환경을 위해 하나의 리포지토리에서 시작했습니다.

기술적인 면을 보더라도 protobuf 파일을 기반으로 여러 언어로 변환하고 필요하다면 이를 언어별 패키지 저장소에 업데이트하는 파이프라인을 만들기에도 하나의 리포지토리를 갖는 것이 관리 비용 면에서도 부담이 적었습니다.

그렇게 뱅크샐러드의 모든 protobuf는 IDL([Interface Definition Language](https://en.wikipedia.org/wiki/Interface_description_language))이 되어 **하나의 리포지토리 안에 존재** 합니다. 실제 리포지토리 명도 idl로 만들어 여러 서비스에서 사용하는 protobuf를 한데 모아 정의해 관리하고 있습니다.

![idl 리포지토리 github 스크린샷](https://blog.banksalad.com/static/7509e30b775c8d4b1e713a16e863c408/4e1ad/idl.png)

idl 리포지토리 github 스크린샷

뱅크샐러드의 idl 리포지토리

idl 리포지토리는 protobuf 파일뿐 아니라 [protoc](https://github.com/protocolbuffers/protobuf) 를 통해 변환된 Go, Java, Java Lite, Python, Swagger, Swift 파일 등이 있는 gen 폴더까지 git에 포함해 관리하고 있습니다. protobuf와 gRPC는 protoc 버전, plugin 버전에 따라 생성되는 결과물이 다를 수 있는데 이를 통일하지 않고 각자 generate 해 사용하면 문제가 될 수 있기에 일부러 위와 같이 포함해 사용하고 있습니다. 리포지토리의 용량은 조금 커질지 몰라도 CI의 lint, generate & diff 테스트를 통해 다른 버전의 protoc를 사용과 잘못된 generate를 방지하고 있습니다.

이 외에도 스타일 가이드나 gRPC first design 등의 이야기도 하고 싶지만 idl과 protobuf에 관해선 다른 블로그 글에서 더 자세하게 다루겠습니다.

### gRPC Layer의 구성

기본적인 gRPC 서버를 구동하기 위한 코드는 크게 복잡하지 않았습니다.

```go
import (
    "context"
    "net"

    grpc_middleware "github.com/grpc-ecosystem/go-grpc-middleware"
    grpc_recovery "github.com/grpc-ecosystem/go-grpc-middleware/recovery"
    "google.golang.org/grpc"

    "github.com/rainist/idl/gen/go/apis/external/v1/app"
    "github.com/rainist/app/config"
    "github.com/rainist/app/server/handler"
)

type AppServer struct {
    app.AppServer

    cfg config.Config
}

func NewAppServer(cfg config.Config) (*AppServer, error) {
    return &AppServer{cfg: cfg}, nil
}

func (s *AppServer) HealthCheck(
    ctx context.Context,
    req *app.HealthCheckRequest,
) (*app.HealthCheckResponse, error) {
    return handler.HealthCheck()(ctx, req)
}

func NewGRPCServer(cfg config.Config) (*grpc.Server, error) {
    grpcServer := grpc.NewServer(
        grpc_middleware.WithUnaryServerChain(
            grpc_recovery.UnaryServerInterceptor(),
        ),
    )

    appServer, err := NewAppServer(cfg)
    if err != nil {
        return nil, err
    }

    app.RegisterAppServer(grpcServer, appServer)

    return grpcServer, nil
}

func ServeGRPC(cfg config.Config) error {
    lis, err := net.Listen("tcp", ":"+cfg.Setting().GRPCServerPort)
    if err != nil {
        return err
    }

    grpcServer, err := NewGRPCServer(cfg)
    if err != nil {
        return err
    }

    return grpcServer.Serve(lis)
}
```

`grpc_server.go` - 가장 간단한 형태의 gRPC 서버

위와 같이 가장 최소한으로 구성할 수 있으나 gRPC를 처음 다뤄보면서 헷갈렸던 건 unary라는 개념과 interceptor, server register 부분이었기에 go와 gRPC 조합을 처음 접하는 다른 개발자들도 쉽게 적응할 수 있도록 아래의 내용을 간략히 문서로 만들어 공유했습니다.

![공유한 문서 중 unary 관련 내용](https://blog.banksalad.com/static/2f62c29683d330759d155c9cd5d09026/b49e7/unary.png)

공유한 문서 중 unary 관련 내용

![공유한 문서 중 interceptor 관련 내용](https://blog.banksalad.com/static/c8df17960a780f8055ed60d861760422/5745f/interceptor.png)

공유한 문서 중 interceptor 관련 내용

![공유한 문서 중 recovery와 register 관련 내용](https://blog.banksalad.com/static/5aa2a8dc80c6c156113f6619aba192eb/ca756/recovery.png)

공유한 문서 중 recovery와 register 관련 내용

만들면서 이해하는 `grpc_server.go` 문서의 일부

### grpc-gateway를 이용한 JSON 통신

새로운 서비스는 gRPC로 만들었지만, 기존의 다른 뱅크샐러드 서비스들은 여전히 JSON 기반의 REST API로 통신하고 있었습니다. 기존 서비스들이 새로운 서비스의 API를 호출하기 위해선 gRPC와 protobuf를 사용하도록 수정해야하는데 그런 서비스가 한두 개가 아니었고, 또 구성하고 있는 기술 스택 역시 모두 go가 아니라 python, scala 등 다양했습니다.

상황이 이렇다 보니 우리에겐 다른 서비스에 어떻게 하면 gRPC를 빨리 붙일 수 있는지보단 **gRPC 서비스가 HTTP JSON 통신을 지원** 해 기존 서비스들과의 호환을 지원하는 방법이 필요했습니다.

이를 go의 [grpc-gateway](https://github.com/grpc-ecosystem/grpc-gateway) 를 사용해 gRPC layer를 바라보는 HTTP layer를 두고 idl도 이를 지원하도록 반영하는 것으로 JSON API 제공의 문제를 해결할 수 있었습니다.

```diff
syntax = "proto3";

  package user;
+
+ import "google/api/annotations.proto";

  service User {
-   rpc GetUser(GetUserRequest) returns (GetUserResponse);
+   rpc GetUser(GetUserRequest) returns (GetUserResponse) {
+     option (google.api.http) = {
+       get: "/v1/users/{user_id}"
+     };
+   }
  }
```

`user` 서비스의 JSON 지원을 위한 protobuf 수정

```go
import (
    "context"
    "net/http"

    "github.com/grpc-ecosystem/grpc-gateway/runtime"
    "google.golang.org/grpc"

    "github.com/rainist/app/config"
    "github.com/rainist/idl/gen/go/apis/v1/app"
)

func ServeHTTP(cfg config.Config) error {
    ctx := context.Background()
    ctx, cancel := context.WithCancel(ctx)
    defer cancel()

    mux := runtime.NewServeMux(
        runtime.WithMarshalerOption(
            runtime.MIMEWildcard,
            &runtime.JSONPb{
                OrigName:     true,
                EmitDefaults: true,
            },
        ),
    )
    options := []grpc.DialOption{
        grpc.WithInsecure(),
    }

    if err := app.RegisterAppHandlerFromEndpoint(
        ctx,
        mux,
        cfg.Setting().GRPCServerEndpoint,
        options,
    ); err != nil {
        return err
    }

    return http.ListenAndServe(":"+cfg.Setting().HTTPServerPort, mux)
}
```

grpc-gateway를 이용한 `http_server.go`

위 코드처럼 grpc-gateway를 이용해 gRPC endpoint를 바라보는 layer를 만들고 JSON request, response를 적절히 마샬링해주는 옵션과 함께 사용해 gRPC port가 아닌 HTTP port로 들어온 요청은 HTTP layer를 거쳐 JSON body를 주고받을 수 있도록 해주었습니다.

### 기존 서비스를 호출하기 위한 golang client

기존 서비스가 새로운 gRPC 서비스를 호출하기 위해 grpc-gateway로 JSON API를 지원했다면 반대로 gRPC 서비스가 기존 서비스를 호출할 때도 어떻게 하면 관심사를 분리해 잘 호출할 수 있을까 고민했습니다. 편하게 가자면 `net/http` 를 이용해 JSON API를 호출해 받아온 데이터를 캐스팅해 사용할 수 있었지만 우리는 protobuf로 얻은 이점을 포기하고 싶지 않았습니다.

그래서 먼저 idl에 **기존 서비스의 API를 protobuf로 표현** 했습니다. grpc-gateway 때처럼 기존 서비스를 나타내는 service와 RPC, request/response message를 정의하고 URL path를 지정해 다른 gRPC 서비스처럼 믿고 사용할 수 있는 network 모델을 만들었습니다.

> 기존 서비스를 protobuf로 표현하기 위해 노후화된 API 문서를 참고할 수 없어 실제 코드를 보며 작업할 수밖에 없었습니다. 가장 빈번하게 사용되는 서비스부터 하나씩 하나씩 지금도 계속 protobuf 작업을 진행하고 있습니다.

이제 이를 가져다 사용해야 하는데 하나의 서비스는 다른 여러 서비스에 호출될 수 있으므로 gRPC 서비스 쪽보단 기존 서비스 쪽에 golang client를 만들었습니다. 기존 서비스가 사용하던 언어가 python이든 scala든 상관없이 root path에 새롭게 정의한 idl을 가져다 사용하는 client를 만들었습니다. 이질적이라 볼 수 있는 golang client 코드를 떡하니 root path에 두는 게 처음엔 어색하다 싶었지만 하나의 서비스, 리포지토리마다 코드 오너가 있는 뱅크샐러드에선 다른 서비스가 본인의 서비스를 잘 호출할 수 있도록 SDK, client를 제공하는 게 오너십 관점에서 더 바람직한 모습이었습니다.

![grpc 서비스가 다른 서비스를 client를 사용해 호출하는 도식](https://blog.banksalad.com/static/28139a8889c971226d8aa382d57606e3/51584/client.png)

grpc 서비스가 다른 서비스를 client를 사용해 호출하는 도식

client 내부에선 여전히 실제 host와 URL path로 JSON 통신을 하지만 이를 protobuf로 캐스팅하고 에러를 처리하는 책임은 기존 서비스에 있습니다. 이를 사용하는 gRPC 서비스에선 request와 response라는 필요한 정보만 보는 식으로 관심사를 적절하게 분리할 수 있었고, go 기반의 gRPC 서비스에서는 단순히 `import "github.com/rainist/{service}"` 만으로 함수를 호출하듯 다른 서비스의 REST API를 호출할 수 있게 되었습니다.

```go
type Client struct {
    httpClient   *http.Client
    tokenHost string
}

func NewTokenClient(httpClient *http.Client, tokenHost string) *Client {
    return &Client{
        httpClient:   httpClient,
        tokenHost: tokenHost,
    }
}

func (c *Client) CreateToken(
    ctx context.Context,
    req *token.CreateTokenRequest,
    opts ...grpc.CallOption,
) (*token.CreateTokenResponse, error) {
    createTokenURL := fmt.Sprintf("%s/v1/tokens", c.tokenHost)

    marshaler := jsonpb.Marshaler{
        EmitDefaults: true,
        OrigName:     true,
    }
    requestJSON, err := marshaler.MarshalToString(req)
    if err != nil {
        return nil, errors.WithStack(ErrBadRequest)
    }

    resp, err := c.httpClient.Post(
        createTokenURL,
        JsonContentType,
        strings.NewReader(requestJSON),
    )
    if err != nil {
        return nil, errors.WithStack(err)
    }
    defer resp.Body.Close()

    if resp.StatusCode == http.StatusBadRequest {
        return nil, errors.WithStack(ErrBadRequest)
    }
    if resp.StatusCode != http.StatusCreated {
        respBody := ""
        respBodyBytes, err := ioutil.ReadAll(resp.Body)
        if err != nil {
            respBody = err.Error()
        } else {
            respBody = string(respBodyBytes)
        }
        return nil, errors.WithStack(status.Error(codes.Unknown, "create token resp body: "+respBody))
    }

    createTokenResponse := &token.CreateTokenResponse{}
    unmarshaler := jsonpb.Unmarshaler{
        AllowUnknownFields: true,
    }
    if err = unmarshaler.Unmarshal(resp.Body, createTokenResponse); err != nil {
        return nil, errors.WithStack(err)
    }

    return createTokenResponse, nil
}
```

기존에 REST API를 제공하는 `token` 서비스의 golang client

이렇게 client 코드가 있으니 이 코드가 JSON을 제대로 캐스팅하는지, 특정 상황에 의도한 에러를 실제로 발생시키는지 등을 테스트 코드로 검증할 수 있습니다. 이때 HTTP 통신 부분을 mocking 하여 테스트 코드를 짤 수도 있지만 golang에선 [`net/http/httptest`](https://golang.org/pkg/net/http/httptest/) 모듈을 사용해 테스트 케이스마다 특정 응답을 반환하는 테스트 서버를 선언하고 이 URL을 client 생성 함수에 넘겨 mocking 없이도 유의미한 테스트가 가능합니다.

```go
func TestTokenClient_CreateToken(t *testing.T) {
    req := &token.CreateTokenRequest{
        UserId: 123,
    }

    t.Run("bad request", func(t *testing.T) {
        //make HTTP server to respond with 400
        testServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            w.WriteHeader(http.StatusBadRequest)
        }))
        defer testServer.Close()

        cli := NewTokenClient(
            testServer.Client(),
            testServer.URL,
        )
        ctx := context.Background()
        resp, err := cli.CreateToken(ctx, req)
        err = errors.Cause(err)

        //check if bad request is handled properly
        assert.EqualError(t, err, ErrBadRequest.Error())
        assert.Nil(t, resp)
    })
}
```

`httptest` 를 활용한 테스트 케이스

### gRPC 서비스간 호출

위의 사례와 마찬가지로 gRPC 서비스 간 호출도 좀 더 쉽게 하기 위해서 각 서비스는 저마다의 client를 제공하고 있습니다.

```go
import (
    "sync"

    grpc_middleware "github.com/grpc-ecosystem/go-grpc-middleware"
    "google.golang.org/grpc"

    "github.com/rainist/go-banksalad"
    "github.com/rainist/idl/gen/go/apis/v1/app"
)

var (
    once sync.Once
    cli  app.AppClient
)

func GetAppClient(serviceHost, caller string) app.AppClient {
    once.Do(func() {
        conn, _ := grpc.Dial(
            serviceHost,
            grpc.WithInsecure(),
            grpc.WithUnaryInterceptor(
                grpc_middleware.ChainUnaryClient(
                    banksalad.ForwardBanksaladHeadersUnaryClientInterceptor(),
                    banksalad.AddCallerUnaryClientInterceptor(caller),
                ),
            ),
        )

        cli = app.NewAppClient(conn)
    })

    return cli
}
```

서비스 간 호출에서 뱅크샐러드 내부에서 사용하는 커스텀 헤더를 좀 더 편하게 넘겨주고, 누가 누구를 호출했는지 좀 더 쉽게 추적하기 위해서 `go-banksalad` 라는 리포지토리에 유용한 middleware를 정의해 사용하고 있습니다.

이때 client 코드 자체는 [`sync.Once`](https://golang.org/pkg/sync/#Once) 를 사용해 싱글톤으로 반환하지만 실제로 client를 가져와 사용하는 곳에선 gRPC server를 선언하는 가장 바깥 레이어에서 client를 한 번만 생성해 이를 각 RPC 핸들러에 주입해 사용하고 있습니다.

### 옵저버빌리티를 확보하기 위한 로깅

서비스를 production에서 운영하기 위해선 위에서 언급한 **호환성** 뿐만 아니라 안정적인 운영을 위한 **옵저버빌리티** 를 확보해야 합니다. 뱅크샐러드는 안정화 기간을 거쳐 옵저버빌리티 인프라를 구축했었고, 새롭게 만드는 gRPC 서비스 또한 로깅과 stats를 고려해야 했습니다. 단순히 로깅을 하는 것 이상으로 중요한 건 언제 어떤 정보를 적절히 로깅하느냐 라고 생각해 뱅크샐러드도 옵저버빌리티 확보를 위한 가장 적절한 로깅 스택을 구성했습니다.

#### 의미 있는 로깅

로깅 라이브러리를 선택하기에 앞서 우리에게 필요한 로깅은 무엇인가 물어봤을 때 `info`, `warning`, `error`, `fatal` 로 나누어지는 레벨별 로깅보단 로깅을 할 때 어떤 구조로 로깅하느냐가 제일 중요했습니다.

golang의 기본 log 라이브러리에서 앞서 말한 4단계의 로깅을 지원하는데 각기 따지고 보면 우리에게 필요한 건 info 하나였습니다.<sup><a href="https://dave.cheney.net/2015/11/05/lets-talk-about-logging">1</a></sup>

- warning 같은 경우 error는 아니지만 미래에 문제가 될 수 있으니 주의를 갖고 보라는 의미인데 이는 info 혹은 error를 쓰고 옵저버빌리티 툴로 의미 있게 사용하면 되지 굳이 warning을 사용할 이유가 없었습니다.
- fatal의 경우는 에러 메시지를 출력하고 곧장 종료되는데 서비스가 정상적으로 실행된 이후에는 큰 의미가 없고 golang의 [“don’t panic”](https://github.com/golang/go/wiki/CodeReviewComments#dont-panic) 과 정반대의 기능이라 마찬가지로 fatal을 사용할 이유가 없었습니다.
- error의 경우 에러가 발생했고 에러를 처리하는 과정에서 필요한 정보를 로깅을 하는데 사용하는 것인데 이 역시 에러가 적절히 처리된다면 info를 쓰는 것과 다를 바가 없다고 생각했습니다.

결국 우리에게 중요한 건 **레벨별 로깅보다는 로깅을 하는 시점에 어떤 구조화된 정보가 있는지** 였습니다.

#### logrus

golang의 gRPC는 로깅 라이브러리로 [zap](https://github.com/uber-go/zap) 과 [logrus](https://github.com/sirupsen/logrus) 헬퍼 함수를 지원합니다. zap 라이브러리는 성능을 이점으로 내세우고 있지만, JSON encoder를 사용하는 것이 아닌 string manipulation으로 구현되어 있어 1 level 로깅만 가능하고 로깅할 때마다 타입을 명시해줘야 하기에 우리가 원하는 구조화된 로깅을 위해선 logrus가 더 적절했습니다.

logrus로 로깅을 한다고 하여도 이를 gRPC 요청에 있는 유용한 정보와 함께 로깅을 해야 비로소 유용한 로그가 됩니다. 이를 위해 아까 위에서 본 gRPC layer에서 interceptor로 logrus interceptor를 넘겨주어 좀 더 맥락이 있는 로깅을 할 수 있었습니다.

```diff
+ logrus.ErrorKey = "grpc.error"
+ logrusEntry := logrus.NewEntry(logrus.StandardLogger())

  grpcServer := grpc.NewServer(
      grpc_middleware.WithUnaryServerChain(
+         grpc_logrus.UnaryServerInterceptor(logrusEntry),
          grpc_recovery.UnaryServerInterceptor(),
      ),
  )
```

RPC 핸들러에서 `logrus.WithField("method", "ListBanks").Info("Return nil slice")` 처럼 로깅을 했을 때 interceptor 유무의 차이는 다음과 같이 나타납니다.

```json
{
    "grpc.code": "OK",
    "grpc.method": "ListBanks",
    "grpc.service": "organization.Organization",
    "grpc.start_time": "2020-01-06T15:11:17+09:00",
    "grpc.time_ms": 0.042,
    "level": "info",
    "msg": "finished unary call with code OK",
    "span.kind": "server",
    "system": "gRPC",
    "time": "2020-01-06T15:11:17+09:00"
}
```

있을 때

```json
{
    "level": "info",
    "method": "ListBanks",
    "msg": "Return nil slice",
    "time": "2020-01-06T15:11:35+09:00"
}
```

없을 때

#### tags를 이용해 로그에 필드 하나만 추가하기

구조화된 로깅은 보통 요청 전체를 로그로 남길 때 사용합니다. RPC 핸들러에서 요청한 `User ID` 하나를 로깅하거나 맥락에 맞는 정보를 로깅하고 싶을 때는 gRPC의 tags middleware를 사용하고 있습니다.

```diff
logrus.ErrorKey = "grpc.error"
  logrusEntry := logrus.NewEntry(logrus.StandardLogger())

  grpcServer := grpc.NewServer(
      grpc_middleware.WithUnaryServerChain(
+         grpc_ctxtags.UnaryServerInterceptor(
+             grpc_ctxtags.WithFieldExtractor(
+                 grpc_ctxtags.CodeGenRequestFieldExtractor,
+             ),
+         ),
          grpc_logrus.UnaryServerInterceptor(logrusEntry),
          grpc_recovery.UnaryServerInterceptor(),
      ),
  )
```

gRPC request에서 각종 필드 정보를 extract 할 수 있는 predefined function을 interceptor에서 사용할 field extractor 함수로 설정합니다. interceptor를 등록하면 아래처럼 RPC 핸들러에서 필요한 정보를 로깅할 수 있습니다.

```go
tags := grpc_ctxtags.Extract(ctx)
tags.Set("user_id", 123)
```

참고로 tags interceptor는 핸들러로 request를 넘기기 전까지만 정의해두었는데 핸들러에서 태깅 한 필드는 언제 로깅되는지 의아해할 수 있지만 앞서 사용했던 logrus interceptor에서 새로운 context에서 re-extract 로직을 구현해 두었기에 핸들러에서 태깅 한 정보가 온전히 로그로 남을 수 있습니다.

#### 장애 대응을 위한 stacktrace

에러가 났을 때 왜 해당 에러가 발생했는지 맥락을 제공해 주는 stacktrace가 없다면 어떤 RPC에서 에러가 발생했었는지 알 수는 있지만, 그 안에서 호출되는 수많은 함수 중 어디서 실제 오류가 발생했는지 파악하기 어렵습니다. 이런 stacktrace를 로깅하기 위해 핸들러에서 에러가 반환되면 위에서 언급한 tags를 이용해 자동으로 별도의 필드에 stacktrace를 남겨주는 interceptor를 설정했습니다.

```diff
logrus.ErrorKey = "grpc.error"
  logrusEntry := logrus.NewEntry(logrus.StandardLogger())

  grpcServer := grpc.NewServer(
      grpc_middleware.WithUnaryServerChain(
          grpc_ctxtags.UnaryServerInterceptor(
              grpc_ctxtags.WithFieldExtractor(
                  grpc_ctxtags.CodeGenRequestFieldExtractor,
              ),
          ),
          grpc_logrus.UnaryServerInterceptor(logrusEntry),
+         banksalad.LogStackTraceUnaryServerInterceptor(),
          grpc_recovery.UnaryServerInterceptor(),
      ),
  )
```

interceptor 설정과 더불어 error를 반환하는 RPC 핸들러 안쪽 함수들에서도 별도로 [`pkg/errors`](https://blog.banksalad.com/tech/production-ready-grpc-in-golang/github.com/pkg/errors) 라이브러리를 사용해 stacktrace를 반환하는 에러에 담아주고 있습니다. 이때 error를 한 번 감싸주었다면 바깥 함수들에서 또 감싸주면 안쪽의 stacktrace가 유실되기에 이를 유의해 사용하고 있습니다.

```go
if err != nil {
    return nil, errors.WithStack(error)
}
```

```text
rpc error: code = Internal desc = something wrong
github.com/rainist/sampleapp/server/handler.Get.func1
    /sampleapp/server/handler/sample_handler.go:105
github.com/rainist/sampleapp/server.(*sampleappServer).Get
    /sampleapp/server/grpc_server.go:45
github.com/rainist/idl/gen/go/apis/v1/sampleapp._Sampleapp_Get_Handler.func1
    /go/pkg/mod/github.com/rainist/idl@v0.0.0/gen/go/apis/v1/sampleapp/sampleapp.pb.go:599
github.com/grpc-ecosystem/go-grpc-middleware/recovery.UnaryServerInterceptor.func1
    /go/pkg/mod/github.com/grpc-ecosystem/go-grpc-middleware@v1.1.0/recovery/interceptors.go:30
github.com/grpc-ecosystem/go-grpc-middleware.ChainUnaryServer.func1.1.1
    /go/pkg/mod/github.com/grpc-ecosystem/go-grpc-middleware@v1.1.0/chain.go:25
github.com/rainist/go-banksalad.LogStackTraceUnaryServerInterceptor.func1
    /go/pkg/mod/github.com/rainist/go-banksalad@v0.0.0/grpc_interceptor.go:33
github.com/grpc-ecosystem/go-grpc-middleware.ChainUnaryServer.func1.1.1
    /go/pkg/mod/github.com/grpc-ecosystem/go-grpc-middleware@v1.1.0/chain.go:25
```

multiline으로 표현되는 에러 로그

### 옵저버빌리티를 위한 statsd

로깅뿐만 아니라 [statsd](https://github.com/statsd/statsd) 를 이용해 각종 time serial한 메트릭 정보를 쌓는 것도 중요합니다. 뱅크샐러드는 stats를 쌓기 위해 [telegraf](https://github.com/influxdata/telegraf) 를 이용하고 있는데 이 telegraf에 손쉽게 메트릭을 보낼 수 있도록 `go-banksalad` 리포지토리에서 statsd client를 제공하고 있으며, 위와 마찬가지로 unary interceptor를 제공해 request마다 기본적인 stats를 찍을 수 있도록 하고 있습니다.

```diff
logrus.ErrorKey = "grpc.error"
  logrusEntry := logrus.NewEntry(logrus.StandardLogger())

+ stats := banksalad.NewStatsdClient(banksalad.StatsdOptions{
+     StatsdAddr: "telegraf:8125",
+     Prefix:     "development.myapp",
+     Logger:     logrusEntry,
+ })

  grpcServer := grpc.NewServer(
      grpc_middleware.WithUnaryServerChain(
          grpc_ctxtags.UnaryServerInterceptor(
              grpc_ctxtags.WithFieldExtractor(
                  grpc_ctxtags.CodeGenRequestFieldExtractor,
              ),
          ),
          grpc_logrus.UnaryServerInterceptor(logrusEntry),
+         banksalad.StatsUnaryServerInterceptor(stats),
          banksalad.LogStackTraceUnaryServerInterceptor(),
          grpc_recovery.UnaryServerInterceptor(),
      ),
  )
```

![chronograf 대시보드](https://blog.banksalad.com/static/2f72380aef7a51286894978acf6f7f71/55091/statsd.png)

chronograf 대시보드

statsd로 집계한 p50, p90, p99 latency

statsd interceptor까지 추가한 시점에서 보니 프로덕션에서 gRPC를 쓰기 위한 구성은 맨 처음의 기본적인 gRPC 서버와 비교해 정말 많은 차이가 난다고 느낄 수 있었습니다.

```go
grpcServer := grpc.NewServer(
    grpc_recovery.UnaryServerInterceptor(),
)
```

가장 기본적인 gRPC 서버 옵션

## gRPC를 넘어

이렇게 protobuf부터 로깅과 statsd까지 뱅크샐러드가 겪은 문제가 무엇이었고 각기 어떤 방식으로 해결해왔는지 정리해 봤습니다. 위에서 소개했듯 뱅크샐러드는 그동안 나름의 고민과 경험을 통해 조직의 문제를 해결할 수 있는 구조로 gRPC 서비스를 구성해왔습니다. 위 주제 중 몇몇은 다른 블로그 글로 더 자세히 말씀드릴 기회가 있을 것이고 앞으로도 계속 나타날 문제도 각 상황에 맞게 잘 해결하고자 합니다.

긴 글 읽어주셔서 감사합니다. gRPC 및 go 기반의 서버를 운영하시거나 도입을 고려하시는 분께 도움이 되었으면 합니다.

---

go를 프로덕션에서 사용하고 싶으신 분, gRPC의 성능과 protobuf 기반 협업에 관심 있으신 분, 실리콘밸리 테크 기업들의 베스트 프랙티스들을 알고 싶으신 분 모두 💚뱅크샐러드💚에서 함께 이야기해요! 🙂

보다 빠르게 뱅크샐러드에 도달하는 방법 🚀

[지원하기](https://corp.banksalad.com/jobs/?category=tech&utm_source=BS_WEB_blog&utm_medium=BS_blog_tech&utm_campaign=BS_blog_tech_contents&utm_content=%2Ftech%2Fproduction-ready-grpc-in-golang%2F)
