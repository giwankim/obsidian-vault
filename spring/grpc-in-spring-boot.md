---
title: "gRPC in Spring Boot"
source: "https://piotrminkowski.com/2025/12/15/grpc-spring/"
author:
  - "[[piotr.minkowski]]"
published: 2025-12-15
created: 2026-06-27
description: "This article explains how to use the Spring gRPC project to enable built-in support for gRPC services in a Spring Boot application."
tags:
  - "clippings"
---

> [!summary]
> Walks through the new Spring gRPC project (1.0 GA) for building native gRPC services in Spring Boot, replacing abandoned third-party starters. Covers defining `.proto` schemas, generating Java stubs with a Maven plugin, implementing server-side `@GrpcService` classes, wiring inter-service gRPC clients via `GrpcChannelFactory`, calling endpoints with `grpcurl`, and in-process test support.

This article explains how to use the Spring gRPC project to enable built-in support for gRPC services in a Spring Boot application. The Spring gRPC project has just announced its 1.0 GA release. gRPC is a modern open-source Remote Procedure Call (RPC) framework that runs in any environment. By default, it uses Google’s Protocol Buffer for serializing and deserializing structured data. Previously, there was no native support for gRPC in Spring projects. Therefore, if you wanted to simplify the creation of such applications with Spring Boot, you had to use third-party starters such as `net.devh:grpc-server-spring-boot-starter`. This particular project has not been maintained for some time. However, if you want to use it with Spring Boot 3, see my [article](https://piotrminkowski.com/2023/08/29/introduction-to-grpc-with-spring-boot/).

You can compare the Spring support described in this article with the equivalent features in Quarkus by reading the following [article](https://piotrminkowski.com/2023/09/15/introduction-to-grpc-with-quarkus/).

## Source Code

Feel free to use my source code if you’d like to try it out yourself. To do that, you must clone my sample GitHub [repository](https://github.com/piomin/sample-microservices-protobuf.git). It contains four apps. Two of them, `account-service` and `customer-service`, are related to my previous article, which introduces Protocol Buffers with Java. For this article, please refer to the other two apps: `account-service-grpc` and `customer-service-grpc`. Those applications have already been migrated to Spring Boot 4. Once you clone the repository, follow my instructions.

## Protobuf Model Classes and Services

In the first step, we will generate model classes and gRPC services using the.proto manifests. We need to include Google’s standard Protobuf schemas to use STD types **(1)**. Our gRPC service will provide methods for searching accounts using various criteria and a single method for adding a new account **(2)**. These methods will use primitives from the `google.protobuf.*` package and model classes defined inside the `.proto` file as messages. Two messages are defined: the `Account` message **(3)**, which represents a single model class and contains three fields (`id`, `number`, and `customer_id`), and the `Accounts` message, which contains a list of `Account` objects **(4)**.

```
syntax = "proto3";

package model;

option java_package = "pl.piomin.services.grpc.account.model";
option java_outer_classname = "AccountProto";

// (1)
import "empty.proto";
import "wrappers.proto";

// (2)
service AccountsService {
  rpc FindByNumber(google.protobuf.StringValue) returns (Account) {}
  rpc FindByCustomer(google.protobuf.Int32Value) returns (Accounts) {}
  rpc FindAll(google.protobuf.Empty) returns (Accounts) {}
  rpc AddAccount(Account) returns (Account) {}
}

// (3)
message Account {
  int32 id = 1;
  string number = 2;
  int32 customer_id = 3;
}

// (4)
message Accounts {
  repeated Account account = 1;
}
```

```
syntax = "proto3";

package model;

option java_package = "pl.piomin.services.grpc.account.model";
option java_outer_classname = "AccountProto";

// (1)
import "empty.proto";
import "wrappers.proto";

// (2)
service AccountsService {
  rpc FindByNumber(google.protobuf.StringValue) returns (Account) {}
  rpc FindByCustomer(google.protobuf.Int32Value) returns (Accounts) {}
  rpc FindAll(google.protobuf.Empty) returns (Accounts) {}
  rpc AddAccount(Account) returns (Account) {}
}

// (3)
message Account {
  int32 id = 1;
  string number = 2;
  int32 customer_id = 3;
}

// (4)
message Accounts {
  repeated Account account = 1;
}
```

We also have a second application `customer-service-grpc` and thus another Protobuf schema. This gRPC service offers several methods for searching objects and a single method for adding a new customer **(1)**. The `customer-service-grpc` communicates with the `account-service-grpc` app, so we need to generate `Account` and `Accounts` messages **(2)**. Of course, you can create an additional interface module with generated Protobuf classes and share it across both our sample apps. Finally, we need to define our model classes. The `Customer` class includes three primitive fields: `id`, `pesel`, and `name`, the `enum` type, and a list of accounts assigned to the particular customer **(3)**. There is also the `Customers` message containing a list of `Customer` objects **(4)**.

```
syntax = "proto3";

package model;

option java_package = "pl.piomin.services.grpc.customer.model";
option java_outer_classname = "CustomerProto";

import "empty.proto";
import "wrappers.proto";

// (1)
service CustomersService {
  rpc FindByPesel(google.protobuf.StringValue) returns (Customer) {}
  rpc FindById(google.protobuf.Int32Value) returns (Customer) {}
  rpc FindAll(google.protobuf.Empty) returns (Customers) {}
  rpc AddCustomer(Customer) returns (Customer) {}
}

// (2)
message Account {
  int32 id = 1;
  string number = 2;
  int32 customer_id = 3;
}

message Accounts {
  repeated Account account = 1;
}

// (3)
message Customer {
  int32 id = 1;
  string pesel = 2;
  string name = 3;
  CustomerType type = 4;
  repeated Account accounts = 5;
  enum CustomerType {
    INDIVIDUAL = 0;
    COMPANY = 1;
  }
}

// (4)
message Customers {
  repeated Customer customers = 1;
}
```

```
syntax = "proto3";

package model;

option java_package = "pl.piomin.services.grpc.customer.model";
option java_outer_classname = "CustomerProto";

import "empty.proto";
import "wrappers.proto";

// (1)
service CustomersService {
  rpc FindByPesel(google.protobuf.StringValue) returns (Customer) {}
  rpc FindById(google.protobuf.Int32Value) returns (Customer) {}
  rpc FindAll(google.protobuf.Empty) returns (Customers) {}
  rpc AddCustomer(Customer) returns (Customer) {}
}

// (2)
message Account {
  int32 id = 1;
  string number = 2;
  int32 customer_id = 3;
}

message Accounts {
  repeated Account account = 1;
}

// (3)
message Customer {
  int32 id = 1;
  string pesel = 2;
  string name = 3;
  CustomerType type = 4;
  repeated Account accounts = 5;
  enum CustomerType {
    INDIVIDUAL = 0;
    COMPANY = 1;
  }
}

// (4)
message Customers {
  repeated Customer customers = 1;
}
```

Now our task is to generate Java classes from Protobuf schemas. It is best to use a dedicated Maven plugin for this. In this exercise, I am using `io.github.ascopes:protobuf-maven-plugin`. Unlike several other plugins, it is actively developed and works without any additional configuration. All you need to do is place the schemas in the `src/main/proto` directory. By default, classes are generated in the `target/generated-sources/protobuf` directory.

```
<plugin>
  <groupId>io.github.ascopes</groupId>
  <artifactId>protobuf-maven-plugin</artifactId>
  <version>4.1.1</version>
  <configuration>
    <protoc>4.33.1</protoc>
    <binaryMavenPlugins>
      <binaryMavenPlugin>
        <groupId>io.grpc</groupId>
        <artifactId>protoc-gen-grpc-java</artifactId>
        <version>1.77.0</version>
        <options>@generated=omit</options>
      </binaryMavenPlugin>
    </binaryMavenPlugins>
  </configuration>
  <executions>
    <execution>
      <goals>
        <goal>generate</goal>
      </goals>
    </execution>
  </executions>
</plugin>
```

```
<plugin>
  <groupId>io.github.ascopes</groupId>
  <artifactId>protobuf-maven-plugin</artifactId>
  <version>4.1.1</version>
  <configuration>
    <protoc>4.33.1</protoc>
    <binaryMavenPlugins>
      <binaryMavenPlugin>
        <groupId>io.grpc</groupId>
        <artifactId>protoc-gen-grpc-java</artifactId>
        <version>1.77.0</version>
        <options>@generated=omit</options>
      </binaryMavenPlugin>
    </binaryMavenPlugins>
  </configuration>
  <executions>
    <execution>
      <goals>
        <goal>generate</goal>
      </goals>
    </execution>
  </executions>
</plugin>
```

We will also attach the generated Java code under the `` `target/generated-sources/protobuf` `` as a source directory with the `build-helper-maven-plugin` Maven plugin.

```
<plugin>
  <groupId>org.codehaus.mojo</groupId>
  <artifactId>build-helper-maven-plugin</artifactId>
  <executions>
    <execution>
      <id>add-source</id>
      <phase>generate-sources</phase>
      <goals>
        <goal>add-source</goal>
      </goals>
      <configuration>
        <sources>
          <source>target/generated-sources/protobuf</source>
        </sources>
      </configuration>
    </execution>
  </executions>
</plugin>
```

```
<plugin>
  <groupId>org.codehaus.mojo</groupId>
  <artifactId>build-helper-maven-plugin</artifactId>
  <executions>
    <execution>
      <id>add-source</id>
      <phase>generate-sources</phase>
      <goals>
        <goal>add-source</goal>
      </goals>
      <configuration>
        <sources>
          <source>target/generated-sources/protobuf</source>
        </sources>
      </configuration>
    </execution>
  </executions>
</plugin>
```

## Using Spring gRPC on the server side

GRPC stubs have already been generated. For the `account-service-grpc` app you find them here:

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2025/12/Screenshot-2025-12-12-at-12.47.36.png?w=868&ssl=1)

I created a simple in-memory for testing purposes.

```
public class AccountRepository {

    List<AccountProto.Account> accounts;
    AtomicInteger id;

    public AccountRepository(List<AccountProto.Account> accounts) {
        this.accounts = accounts;
        this.id = new AtomicInteger();
        this.id.set(accounts.size());
    }

    public List<AccountProto.Account> findAll() {
        return accounts;
    }

    public List<AccountProto.Account> findByCustomer(int customerId) {
        return accounts.stream().filter(it -> it.getCustomerId() == customerId)
                .toList();
    }

    public AccountProto.Account findByNumber(String number) {
        return accounts.stream()
                .filter(it -> it.getNumber().equals(number))
                .findFirst()
                .orElseThrow();
    }

    public AccountProto.Account add(int customerId, String number) {
        return AccountProto.Account.newBuilder()
                .setId(id.incrementAndGet())
                .setCustomerId(customerId)
                .setNumber(number)
                .build();
    }

}
```

```
public class AccountRepository {

    List<AccountProto.Account> accounts;
    AtomicInteger id;

    public AccountRepository(List<AccountProto.Account> accounts) {
        this.accounts = accounts;
        this.id = new AtomicInteger();
        this.id.set(accounts.size());
    }

    public List<AccountProto.Account> findAll() {
        return accounts;
    }

    public List<AccountProto.Account> findByCustomer(int customerId) {
        return accounts.stream().filter(it -> it.getCustomerId() == customerId)
                .toList();
    }

    public AccountProto.Account findByNumber(String number) {
        return accounts.stream()
                .filter(it -> it.getNumber().equals(number))
                .findFirst()
                .orElseThrow();
    }

    public AccountProto.Account add(int customerId, String number) {
        return AccountProto.Account.newBuilder()
                .setId(id.incrementAndGet())
                .setCustomerId(customerId)
                .setNumber(number)
                .build();
    }

}
```

To use the gRPC starter for Spring Boot, include the following dependency and dependency management section. You can also include the module dedicated to JUnit tests.

```
<dependencies>
  <dependency>
    <groupId>org.springframework.grpc</groupId>
    <artifactId>spring-grpc-spring-boot-starter</artifactId>
  </dependency>
  <dependency>
    <groupId>org.springframework.grpc</groupId>
    <artifactId>spring-grpc-test</artifactId>
    <scope>test</scope>
  </dependency>
  ...
</dependencies>

<dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>org.springframework.grpc</groupId>
      <artifactId>spring-grpc-dependencies</artifactId>
      <version>1.0.0</version>
      <type>pom</type>
      <scope>import</scope>
    </dependency>
  </dependencies>
</dependencyManagement>
```

```
<dependencies>
  <dependency>
    <groupId>org.springframework.grpc</groupId>
    <artifactId>spring-grpc-spring-boot-starter</artifactId>
  </dependency>
  <dependency>
    <groupId>org.springframework.grpc</groupId>
    <artifactId>spring-grpc-test</artifactId>
    <scope>test</scope>
  </dependency>
  ...
</dependencies>

<dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>org.springframework.grpc</groupId>
      <artifactId>spring-grpc-dependencies</artifactId>
      <version>1.0.0</version>
      <type>pom</type>
      <scope>import</scope>
    </dependency>
  </dependencies>
</dependencyManagement>
```

Then we have to create the gRPC service implementation class. It needs to extend the `AccountsServiceImplBase` generated based on the `.proto` declaration. We also need to annotate the whole class with the `@GrpcService` **(1)**. Instead, you can annotate it just with @Service, but I prefer `@GrpcService` for greater transparency. After that, we will override all the methods exposed over gRPC. Our service uses a simple in-memory repository **(2)**. Each method provides a parameter object and the `io.grpc.stub.StreamObserver` class used for returning the responses in a reactive way **(3)** **(4)**.

```
@GrpcService
public class AccountsService extends AccountsServiceGrpc.AccountsServiceImplBase {

    AccountRepository repository;

    public AccountsService(AccountRepository repository) {
        this.repository = repository;
    }

    @Override
    public void findByNumber(StringValue request, StreamObserver<AccountProto.Account> responseObserver) {
        AccountProto.Account a = repository.findByNumber(request.getValue());
        responseObserver.onNext(a);
        responseObserver.onCompleted();
    }

    @Override
    public void findByCustomer(Int32Value request, StreamObserver<AccountProto.Accounts> responseObserver) {
        List<AccountProto.Account> accounts = repository.findByCustomer(request.getValue());
        AccountProto.Accounts a = AccountProto.Accounts.newBuilder().addAllAccount(accounts).build();
        responseObserver.onNext(a);
        responseObserver.onCompleted();
    }

    @Override
    public void findAll(Empty request, StreamObserver<AccountProto.Accounts> responseObserver) {
        List<AccountProto.Account> accounts = repository.findAll();
        AccountProto.Accounts a = AccountProto.Accounts.newBuilder().addAllAccount(accounts).build();
        responseObserver.onNext(a);
        responseObserver.onCompleted();
    }

    @Override
    public void addAccount(AccountProto.Account request, StreamObserver<AccountProto.Account> responseObserver) {
        AccountProto.Account a = repository.add(request.getCustomerId(), request.getNumber());
        responseObserver.onNext(a);
        responseObserver.onCompleted();
    }
}
```

```
@GrpcService
public class AccountsService extends AccountsServiceGrpc.AccountsServiceImplBase {

    AccountRepository repository;

    public AccountsService(AccountRepository repository) {
        this.repository = repository;
    }

    @Override
    public void findByNumber(StringValue request, StreamObserver<AccountProto.Account> responseObserver) {
        AccountProto.Account a = repository.findByNumber(request.getValue());
        responseObserver.onNext(a);
        responseObserver.onCompleted();
    }

    @Override
    public void findByCustomer(Int32Value request, StreamObserver<AccountProto.Accounts> responseObserver) {
        List<AccountProto.Account> accounts = repository.findByCustomer(request.getValue());
        AccountProto.Accounts a = AccountProto.Accounts.newBuilder().addAllAccount(accounts).build();
        responseObserver.onNext(a);
        responseObserver.onCompleted();
    }

    @Override
    public void findAll(Empty request, StreamObserver<AccountProto.Accounts> responseObserver) {
        List<AccountProto.Account> accounts = repository.findAll();
        AccountProto.Accounts a = AccountProto.Accounts.newBuilder().addAllAccount(accounts).build();
        responseObserver.onNext(a);
        responseObserver.onCompleted();
    }

    @Override
    public void addAccount(AccountProto.Account request, StreamObserver<AccountProto.Account> responseObserver) {
        AccountProto.Account a = repository.add(request.getCustomerId(), request.getNumber());
        responseObserver.onNext(a);
        responseObserver.onCompleted();
    }
}
```

Then, we can prepare a similar implementation for the `customer-service-grpc` app. This time, the application not only retrieves data from the in-memory database, but also communicates with the previous application over gRPC. That is why our `@GrpcService` uses a dedicated client bean, which you will learn more about in the next section.

```
@GrpcService
public class CustomersService extends CustomersServiceGrpc.CustomersServiceImplBase {

    CustomerRepository repository;
    AccountClient accountClient;

    public CustomersService(CustomerRepository repository,
                            AccountClient accountClient) {
        this.repository = repository;
        this.accountClient = accountClient;
    }

    @Override
    public void findById(Int32Value request, StreamObserver<CustomerProto.Customer> responseObserver) {
        CustomerProto.Customer c = repository.findById(request.getValue());
        CustomerProto.Accounts a = accountClient.getAccountsByCustomerId(c.getId());
        List<CustomerProto.Account> l = a.getAccountList();
        c = CustomerProto.Customer.newBuilder(c).addAllAccounts(l).build();
        responseObserver.onNext(c);
        responseObserver.onCompleted();
    }

    @Override
    public void findByPesel(StringValue request, StreamObserver<CustomerProto.Customer> responseObserver) {
        CustomerProto.Customer c = repository.findByPesel(request.getValue());
        responseObserver.onNext(c);
        responseObserver.onCompleted();
    }

    @Override
    public void findAll(Empty request, StreamObserver<CustomerProto.Customers> responseObserver) {
        List<CustomerProto.Customer> customerList = repository.findAll();
        CustomerProto.Customers c = CustomerProto.Customers.newBuilder().addAllCustomers(customerList).build();
        responseObserver.onNext(c);
        responseObserver.onCompleted();
    }

    @Override
    public void addCustomer(CustomerProto.Customer request, StreamObserver<CustomerProto.Customer> responseObserver) {
        CustomerProto.Customer c = repository.add(request.getType(), request.getName(), request.getPesel());
        responseObserver.onNext(c);
        responseObserver.onCompleted();
    }
}
```

```
@GrpcService
public class CustomersService extends CustomersServiceGrpc.CustomersServiceImplBase {

    CustomerRepository repository;
    AccountClient accountClient;

    public CustomersService(CustomerRepository repository,
                            AccountClient accountClient) {
        this.repository = repository;
        this.accountClient = accountClient;
    }

    @Override
    public void findById(Int32Value request, StreamObserver<CustomerProto.Customer> responseObserver) {
        CustomerProto.Customer c = repository.findById(request.getValue());
        CustomerProto.Accounts a = accountClient.getAccountsByCustomerId(c.getId());
        List<CustomerProto.Account> l = a.getAccountList();
        c = CustomerProto.Customer.newBuilder(c).addAllAccounts(l).build();
        responseObserver.onNext(c);
        responseObserver.onCompleted();
    }

    @Override
    public void findByPesel(StringValue request, StreamObserver<CustomerProto.Customer> responseObserver) {
        CustomerProto.Customer c = repository.findByPesel(request.getValue());
        responseObserver.onNext(c);
        responseObserver.onCompleted();
    }

    @Override
    public void findAll(Empty request, StreamObserver<CustomerProto.Customers> responseObserver) {
        List<CustomerProto.Customer> customerList = repository.findAll();
        CustomerProto.Customers c = CustomerProto.Customers.newBuilder().addAllCustomers(customerList).build();
        responseObserver.onNext(c);
        responseObserver.onCompleted();
    }

    @Override
    public void addCustomer(CustomerProto.Customer request, StreamObserver<CustomerProto.Customer> responseObserver) {
        CustomerProto.Customer c = repository.add(request.getType(), request.getName(), request.getPesel());
        responseObserver.onNext(c);
        responseObserver.onCompleted();
    }
}
```

## Communication between gRPC Services with Spring

For the `customer-service-grpc` application, we also generated stubs for communication with the `account-service-grpc` app. The list of generated classes is shown below.

![grpc-spring-generated-classes](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2025/12/Screenshot-2025-12-12-at-13.05.04.png?w=856&ssl=1)

grpc-spring-generated-classes

Here’s the `AccountClient` bean implementation. It wraps the method `findByCustomer` provided by the generated `AccountsServiceBlockingStub` client for calling the endpoint from the `customer-service-grpc` application.

```
@Service
public class AccountClient {

    private static final Logger LOG = LoggerFactory.getLogger(AccountClient.class);
    AccountsServiceGrpc.AccountsServiceBlockingStub accountsClient;

    public AccountClient(AccountsServiceGrpc.AccountsServiceBlockingStub accountsClient) {
        this.accountsClient = accountsClient;
    }

    public CustomerProto.Accounts getAccountsByCustomerId(int customerId) {
        try {
            return accountsClient.findByCustomer(Int32Value.newBuilder()
                    .setValue(customerId)
                    .build());
        } catch (final StatusRuntimeException e) {
            LOG.error("Error in communication", e);
            return null;
        }
    }
}
```

```
@Service
public class AccountClient {

    private static final Logger LOG = LoggerFactory.getLogger(AccountClient.class);
    AccountsServiceGrpc.AccountsServiceBlockingStub accountsClient;

    public AccountClient(AccountsServiceGrpc.AccountsServiceBlockingStub accountsClient) {
        this.accountsClient = accountsClient;
    }

    public CustomerProto.Accounts getAccountsByCustomerId(int customerId) {
        try {
            return accountsClient.findByCustomer(Int32Value.newBuilder()
                    .setValue(customerId)
                    .build());
        } catch (final StatusRuntimeException e) {
            LOG.error("Error in communication", e);
            return null;
        }
    }
}
```

Then, the `AccountsServiceBlockingStub` must be registered as a Spring bean. We should inject a `GrpcChannelFactory` into the application configuration and use it to create a gRPC channel. The default `GrpcChannelFactory` implementation creates a “named” channel used to retrieve the configuration needed to connect to the server.

```
@Bean
AccountsServiceGrpc.AccountsServiceBlockingStub accountsClient(GrpcChannelFactory channels) {
  return AccountsServiceGrpc.newBlockingStub(channels.createChannel("local"));
}
```

```
@Bean
AccountsServiceGrpc.AccountsServiceBlockingStub accountsClient(GrpcChannelFactory channels) {
  return AccountsServiceGrpc.newBlockingStub(channels.createChannel("local"));
}
```

Finally, we must set the target address for the “named” channel in the Spring Boot configuration properties. Consequently, we must also override the default gRPC for the current application, since the default `9090` is already taken by the `account-service-grpc` app.

```
spring.grpc.server.port: 9091
spring.grpc.client.channels.local.address: localhost:9090
```

```
spring.grpc.server.port: 9091
spring.grpc.client.channels.local.address: localhost:9090
```

## Call gRPC services

In this section, we will use the `grpcurl` tool to discover and call gRPC services. There are several installation options for [GRPCurl](https://grpcurl.com/). On macOS, we can use the following Homebrew command:

```
brew install grpcurl
```

```
brew install grpcurl
```

Let’s run both our example apps:

```
$ cd account-service-grpc
$ mvn spring-boot:run

$ cd customer-service-grpc
$ mvn spring-boot:run
```

```
$ cd account-service-grpc
$ mvn spring-boot:run

$ cd customer-service-grpc
$ mvn spring-boot:run
```

After starting the application, you should see output similar to that shown below.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2025/12/Screenshot-2025-12-12-at-14.59.59.png?w=2286&ssl=1)

We can use the `grpcurl` CLI tool to call the gRPC services exposed by our sample Spring Boot application. By default, the gRPC server starts on port `9090` in the `PLAINTEXT` mode. To print a list of available services, we need to execute the following command:

```
$ grpcurl --plaintext localhost:9090 list
grpc.health.v1.Health
grpc.reflection.v1.ServerReflection
model.AccountsService
```

```
$ grpcurl --plaintext localhost:9090 list
grpc.health.v1.Health
grpc.reflection.v1.ServerReflection
model.AccountsService
```

Then, let’s display the list of methods exposed by the `model.AccountService`:

```
$ grpcurl --plaintext localhost:9090 list model.AccountsService
model.AccountsService.AddAccount
model.AccountsService.FindAll
model.AccountsService.FindByCustomer
model.AccountsService.FindByNumber
```

```
$ grpcurl --plaintext localhost:9090 list model.AccountsService
model.AccountsService.AddAccount
model.AccountsService.FindAll
model.AccountsService.FindByCustomer
model.AccountsService.FindByNumber
```

Now, let’s call the endpoint described with the command visible above. The name of our method is `model.AccountsService.FindByNumber`. We are also setting the input string parameter to the `222222` value. We can repeat the call several times with different parameter values (`111111`, `222222`, `333333`, …).

```
$ grpcurl --plaintext -d '"222222"' localhost:9090 model.AccountsService.FindByNumber
{
  "id": 2,
  "number": "222222",
  "customer_id": 2
}
```

```
$ grpcurl --plaintext -d '"222222"' localhost:9090 model.AccountsService.FindByNumber
{
  "id": 2,
  "number": "222222",
  "customer_id": 2
}
```

Finally, we can call the method for adding a new account. It takes the JSON object as the input parameter. Then it will return a newly created `Account` object with the incremented `id` field.

```
$ grpcurl --plaintext -d '{"customer_id": 6, "number": "888888"}' localhost:9090 model.AccountsService.AddAccount
{
  "id": 8,
  "number": "888888",
  "customer_id": 6
}
```

```
$ grpcurl --plaintext -d '{"customer_id": 6, "number": "888888"}' localhost:9090 model.AccountsService.AddAccount
{
  "id": 8,
  "number": "888888",
  "customer_id": 6
}
```

Spring gRPC includes some specific metrics in the Actuator `metrics` endpoint.

![](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2025/12/Screenshot-2025-12-12-at-23.57.20.png?w=970&ssl=1)

Actuator metrics for gRPC allow us to measure the number of requests and total processing for a specific service. To check these statistics for the `FindByNumber` service, call the `grpc.server` metric as shown below.

![grpc-spring-metrics](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2025/12/Screenshot-2025-12-13-at-00.05.41.png?w=1464&ssl=1)

grpc-spring-metrics

To test the communication between the gRPC services, we must call the `FindById` service exposed by the `customer-service-gprc` app. This service uses Spring gRPC client support to call the `FindByCustomer` service exposed by the `account-service-gprc` app. Below is an example call with a response.

```
$ grpcurl --plaintext -d '1' localhost:9091 model.CustomersService.FindById
{
  "id": 1,
  "pesel": "12345",
  "name": "Adam Kowalski",
  "accounts": [
    {
      "id": 1,
      "number": "111111",
      "customer_id": 1
    },
    {
      "id": 5,
      "number": "555555",
      "customer_id": 1
    }
  ]
}
```

```
$ grpcurl --plaintext -d '1' localhost:9091 model.CustomersService.FindById
{
  "id": 1,
  "pesel": "12345",
  "name": "Adam Kowalski",
  "accounts": [
    {
      "id": 1,
      "number": "111111",
      "customer_id": 1
    },
    {
      "id": 5,
      "number": "555555",
      "customer_id": 1
    }
  ]
}
```

## Spring Test support for gRPC

Spring provides test support for gRPC. We can start an in-process gRPC server as part of the `@SpringBootTest` test with the `@AutoConfigureInProcessTransport` annotation. Such a server doesn’t listen on the network port. To connect the test client with the in-process server, we should use the auto-configured `GrpcChannelFactory`. The `AccountsServiceBlockingStub` bean is created in the `@TestConfiguration` class, which uses `GrpcChannelFactory` to create a channel for testing purposes. Then we can inject the `AccountsServiceBlockingStub` client bean and use it to call gRPC services.

```
@SpringBootTest
@AutoConfigureInProcessTransport
public class AccountServicesTests {

    @Autowired
    AccountsServiceGrpc.AccountsServiceBlockingStub service;

    @Test
    void shouldFindAll() {
        AccountProto.Accounts a = service.findAll(Empty.newBuilder().build());
        assertNotNull(a);
        assertFalse(a.getAccountList().isEmpty());
    }

    @Test
    void shouldFindByCustomer() {
        AccountProto.Accounts a = service.findByCustomer(Int32Value.newBuilder().setValue(1).build());
        assertNotNull(a);
        assertFalse(a.getAccountList().isEmpty());
    }

    @Test
    void shouldFindByNumber() {
        AccountProto.Account a = service.findByNumber(StringValue.newBuilder().setValue("111111").build());
        assertNotNull(a);
        assertNotEquals(0, a.getId());
    }

    @Test
    void shouldAddAccount() {
        AccountProto.Account a = AccountProto.Account.newBuilder()
                .setNumber("123456")
                .setCustomerId(10)
                .build();

        a = service.addAccount(a);
        assertNotNull(a);
        assertNotEquals(0, a.getId());
    }

    @TestConfiguration
    static class Config {

        @Bean
        AccountsServiceGrpc.AccountsServiceBlockingStub stub(GrpcChannelFactory channels) {
            return AccountsServiceGrpc.newBlockingStub(channels.createChannel("local"));
        }

    }

}
```

```
@SpringBootTest
@AutoConfigureInProcessTransport
public class AccountServicesTests {

    @Autowired
    AccountsServiceGrpc.AccountsServiceBlockingStub service;

    @Test
    void shouldFindAll() {
        AccountProto.Accounts a = service.findAll(Empty.newBuilder().build());
        assertNotNull(a);
        assertFalse(a.getAccountList().isEmpty());
    }

    @Test
    void shouldFindByCustomer() {
        AccountProto.Accounts a = service.findByCustomer(Int32Value.newBuilder().setValue(1).build());
        assertNotNull(a);
        assertFalse(a.getAccountList().isEmpty());
    }

    @Test
    void shouldFindByNumber() {
        AccountProto.Account a = service.findByNumber(StringValue.newBuilder().setValue("111111").build());
        assertNotNull(a);
        assertNotEquals(0, a.getId());
    }

    @Test
    void shouldAddAccount() {
        AccountProto.Account a = AccountProto.Account.newBuilder()
                .setNumber("123456")
                .setCustomerId(10)
                .build();

        a = service.addAccount(a);
        assertNotNull(a);
        assertNotEquals(0, a.getId());
    }

    @TestConfiguration
    static class Config {

        @Bean
        AccountsServiceGrpc.AccountsServiceBlockingStub stub(GrpcChannelFactory channels) {
            return AccountsServiceGrpc.newBlockingStub(channels.createChannel("local"));
        }

    }

}
```

Let’s run our tests. I’m using an IDE, but you can execute them with the `mvn test` command.

![grpc-spring-generated-test](https://i0.wp.com/piotrminkowski.com/wp-content/uploads/2025/12/Screenshot-2025-12-15-at-09.18.15-scaled.png?w=2560&ssl=1)

grpc-spring-generated-test

## Conclusion

Built-in gRPC support in Spring is a significant step forward. Until now, this functionality was missing, but community-developed projects like this [one](https://grpc-ecosystem.github.io/grpc-spring/en/) were eventually abandoned. The Spring gRPC project is still at a relatively early stage of development. Just over a week ago, the version `1.0` was officially released. It is worth following its development while we await new features. However, at this stage, we can already simplify things significantly.
