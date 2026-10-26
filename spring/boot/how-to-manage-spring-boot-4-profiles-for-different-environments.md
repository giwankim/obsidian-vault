---
title: "How to Manage Spring Boot 4 Profiles for Different Environments"
source: "https://alexanderobregon.substack.com/p/how-to-manage-spring-boot-4-profiles?utm_source=substack&utm_medium=email"
author:
  - "[[Alexander Obregon]]"
published: 2026-10-22
created: 2026-10-26
description: "As a Spring Boot application moves through development, testing, staging, and production, its configuration usually needs to change along the way."
tags:
  - "clippings"
---

> [!summary]
> A long-form guide to environment configuration in Spring Boot 4 built around a report-processing sample: shared defaults in `application.properties`, `application-{profile}.properties` overrides for dev, test, staging and prod, and activating profiles through `spring.profiles.active`, environment variables or command-line arguments. Covers `@Profile` for conditional beans, binding settings to a `@ConfigurationProperties` record, the property-source precedence order (command line over env vars over profile files over packaged defaults) plus `spring.config.additional-location` versus `spring.config.location`, and verifying with `@ActiveProfiles` tests and Actuator's `env`/`configprops` endpoints. The Boot 4 section notes the profile mechanics are unchanged but some property names moved, e.g. `spring.data.mongodb.*` to `spring.mongodb.*`.

As a Spring Boot application moves through development, testing, staging, and production, its configuration usually needs to change along the way. Development may call for detailed logging and a local database, while production typically requires different database connections, logging levels, and processing limits. Spring Boot profiles let us manage these differences by keeping common settings in one place and defining only the values that change between environments, rather than copying entire configuration files. We can also provide settings through environment variables, map related properties to Java objects with `@ConfigurationProperties`, and control which components Spring creates with `@Profile`. Spring Boot 4 supports these features, allowing each environment to receive the configuration it needs without changing the application’s Java code for every deployment.

### Organizing Environment Configuration

Spring Boot reads configuration from several sources when an application starts, including property files, YAML files, environment variables, and command-line arguments. Profiles determine which environment-specific files participate in configuration loading, allowing development, testing, staging, and production to have their own settings while sharing common values. Rather than maintaining a complete configuration file for every environment, we can keep properties that rarely change in one location and define replacements only where they’re needed. Also, Spring Boot loads the appropriate files based on the active profile, so we can move the application between environments without making changes to its Java code.

#### Keeping Shared Settings in One File

Most Spring Boot applications have configuration values that remain the same regardless of where they’re running. Properties such as the application name, default logging level, or general processing settings don’t necessarily need to change between development and production. Keeping these values in a central file reduces repetition and gives every environment the same starting configuration.

Spring Boot automatically reads `application.properties` from `src/main/resources`, making it a natural location for properties shared across environments. When we package the application into an executable JAR file, this configuration is included with it and remains available wherever the application runs.

For our report-processing application, we can begin by adding the following properties to `application.properties`:

```markup
spring.application.name=report-service

app.reports.format=summary
app.reports.batch-size=50

logging.level.root=INFO
```

The `spring.application.name` property identifies our application as `report-service`, while `logging.level.root` establishes `INFO` as the default logging level. Messages at the `INFO` level and higher are permitted by the root logger unless more specific logging configuration changes that behavior.

Meanwhile, the properties beginning with `app.reports` represent custom settings we’ve defined for our application. Spring Boot doesn’t automatically assign behavior to these properties, but it makes their values available for our Java classes to read. The `format` property has a default value of `summary`, and `batch-size` is set to `50`, giving us starting values for how our application processes reports.

Because these values are defined in the shared configuration, they remain available when any of our environment profiles become active. If development needs detailed reports, we can replace the format for that environment while leaving the batch size unchanged. Production could retain summary reports while increasing the number processed per batch, without requiring us to repeat every property from the original file.

This also gives us a central location for changes that should affect every environment. If we decide to change the default report format, we can update its shared property rather than edit the same setting across several environment files. Properties that already have appropriate defaults don’t need to appear again in the environment-specific files.

Spring Boot supports `application.yaml` as well, which represents configuration through nested YAML entries rather than individual property assignments. Both formats support shared configuration, although sticking with the same format throughout an application helps avoid confusion. If `.properties` and YAML files exist in the same location, Spring Boot gives the `.properties` format priority.

Sensitive credentials should generally remain outside the packaged configuration. Database passwords, access tokens, and similar values can be supplied through external configuration or a dedicated secrets service rather than being committed to source control. Shared property files are better suited to settings that can safely accompany the application across environments.

#### Adding Profile-Specific Overrides

Environment-specific configuration files follow a naming convention that Spring Boot recognizes automatically. The filename begins with `application-`, followed by the profile name and the configuration file extension. For a profile named `dev`, the corresponding properties file is `application-dev.properties`. Spring Boot doesn’t require particular names for environments, so `dev`, `test`, `staging`, and `prod` are names we choose for our application. What counts is that the profile name in the filename matches the profile activated during startup.

For our report application, we can organize the files inside `src/main/resources` like this:

```markup
src/
└── main/
    └── resources/
        ├── application.properties
        ├── application-dev.properties
        ├── application-test.properties
        ├── application-staging.properties
        └── application-prod.properties
```

All five files belong in the same resources directory, but they serve different purposes. The original `application.properties` provides common values, while the remaining files contain properties intended for their respective environments.

Spring Boot reads the shared configuration alongside the file associated with the active profile. If the same property exists in both files, the profile-specific value takes priority within that configuration location. Properties absent from the active profile’s file can still receive their values from `application.properties`, so there’s no need to repeat settings that haven’t changed.

We’ll start with development by creating `application-dev.properties` and adding the following settings:

```markup
app.reports.format=detailed
logging.level.com.example.reports=DEBUG
```

The report format changes from `summary` to `detailed`, allowing development to receive a more comprehensive reporting format when our application code reads that property.

We’ve also introduced a more specific logging configuration for the `com.example.reports` package. Assuming our report-related classes belong to that package, setting its logging level to `DEBUG` allows more detailed messages from those classes during development.

The shared root logging level remains `INFO`, while the configured package and its descendants receive the more specific `DEBUG` setting. This lets us examine report-related activity in greater detail without changing the logging level throughout the entire application.

Notice that `app.reports.batch-size` doesn’t appear in the development file. Spring Boot still has access to the shared value of `50`, so repeating it would serve no purpose. We only needed to add the properties that differ from the defaults.

Testing can have different requirements, particularly when we want to process smaller batches of data. We can create `application-test.properties` with the following property.

```markup
app.reports.batch-size=5
```

With the `test` profile active, the batch size becomes `5`, while the report format remains `summary` because we haven’t provided a replacement.

The smaller batch size can help keep report-processing tests focused on limited amounts of data, although Spring Boot doesn’t require testing environments to have smaller processing limits. We’re choosing a value that makes sense for our application’s testing needs.

It’s also important to distinguish the profile name from the actual testing process. Naming a file `application-test.properties` doesn’t automatically activate it whenever a test runs. The `test` profile still needs to be selected for Spring Boot to load that configuration, which gives us control over the settings applied during testing.

For staging, we’ll create `application-staging.properties` and provide a different batch size:

```markup
app.reports.batch-size=25
```

Staging environments are commonly used to evaluate an application before releasing changes to production. Depending on the deployment, staging may have settings similar to production or smaller resource limits to accommodate its available infrastructure.

Our staging configuration keeps the shared `summary` format while changing the batch size to `25`. We can introduce other properties later if staging requires different service addresses, timeouts, or logging levels, without needing to copy the entire shared configuration.

Production receives its own configuration through `application-prod.properties`, where we’ll increase the batch size again:

```markup
app.reports.batch-size=100
```

With `prod` active, the application receives a batch size of `100` while retaining the shared report format and default logging configuration.

We now have four environments with different settings, but we haven’t duplicated the application name, report format, or logging properties unnecessarily. Every environment begins with the common configuration and receives replacements only for properties that need different values.

This becomes more valuable as the application grows. If we introduce settings for database connection pools, request timeouts, or external service addresses, we can keep common defaults in `application.properties` and place environment-specific values in their corresponding files. Changes intended for production won’t require editing development configuration, while changes shared across environments can remain in the central file.

Spring Boot also supports profile-specific YAML files, like `application-prod.yaml`, with the same general loading behavior.

For applications with relatively few environment differences, we have an alternative that avoids creating multiple physical configuration files. Spring Boot allows a properties file to contain multiple configuration documents, divided by `#---`. Individual documents can then be activated conditionally through `spring.config.activate.on-profile`.

We could represent the shared report settings and the development override inside a single `application.properties` file:

```markup
spring.application.name=report-service

app.reports.format=summary
app.reports.batch-size=50

#---
spring.config.activate.on-profile=dev
app.reports.format=detailed
```

The first document contains properties available regardless of the active profile. The `#---` marker begins a new configuration document, and `spring.config.activate.on-profile=dev` tells Spring Boot that the properties following it belong to the `dev` profile.

If development is active, the report format becomes `detailed`. For other profiles, that conditional document doesn’t contribute its properties, leaving the shared value of `summary` available.

This produces the same development format override as our earlier `application-dev.properties` file, so we’d choose either method rather than define the same property in both locations.

YAML supports multiple configuration documents as well, although its document separator is `---` without the comment prefix.

For applications with several environments, individual profile-specific files give us dedicated locations for their settings. Projects with fewer differences may benefit from conditional documents in a single file instead. Both methods let us keep shared defaults while providing different values for the environments that need them.

#### Activating the Right Profile

Creating profile-specific configuration files gives Spring Boot the files it needs, but we still need to tell it which profile should be active when the application starts. The selected profile determines which environment-specific configuration participates in the startup process, allowing us to control the application’s settings without editing the files whenever we change environments.

Spring Boot provides the `spring.profiles.active` property for selecting active profiles. We can supply this value through shared configuration, an operating system environment variable, or a command-line argument.

During local development, passing the profile directly when starting the packaged application is a convenient option. Assuming our application is packaged as `app.jar`, we can start it with the development profile through the following command.

```markup
java -jar app.jar --spring.profiles.active=dev
```

The `java -jar app.jar` portion starts our packaged application, while `--spring.profiles.active=dev` tells Spring Boot to activate the `dev` profile before completing configuration loading.

Spring Boot then loads the common settings from `application.properties` and applies the properties defined in `application-dev.properties`.

For our report application, this gives us a `detailed` report format, a batch size of `50`, and `DEBUG` logging for the configured report package. We haven’t changed any Java classes or modified the shared property values to get those development settings.

The same application can be started with the staging profile by providing `--spring.profiles.active=staging` instead. Spring Boot then loads the staging configuration, giving our report processor a batch size of `25` while preserving the shared report format.

To start the application with the production configuration, we’ll change the argument to `prod`:

```markup
java -jar app.jar --spring.profiles.active=prod
```

Production now receives the batch size of `100` from `application-prod.properties`, while the shared report format remains `summary` and the root logging level stays at `INFO`.

The packaged JAR remains identical between these launches. We don’t need to modify our Java classes or rebuild the application to select a different environment. Changing the active profile is enough for Spring Boot to load the corresponding configuration files.

For deployments, specifying the active profile through an operating system environment variable is another common option. This lets the deployment environment provide its configuration without requiring us to include the profile name directly in the Java startup command.

Spring Boot recognizes `SPRING_PROFILES_ACTIVE` as the environment variable corresponding to `spring.profiles.active`.

In a Bash-compatible shell, we can set that variable before starting our application:

```markup
export SPRING_PROFILES_ACTIVE=prod
java -jar app.jar
```

The `export` command assigns `prod` to the environment variable and makes it available to processes launched from that shell. When we start the application with `java -jar app.jar`, Spring Boot reads the variable and activates the production profile.

Deployment platforms can provide the same variable through their configuration facilities, allowing the appropriate profile to be selected without modifying the packaged application. We can give development, staging, and production their own profile values while deploying the same JAR file across those environments.

Spring Boot also permits `spring.profiles.active` inside the shared `application.properties` file. However, defining it externally gives each deployment control over its environment rather than permanently associating the packaged configuration with a particular profile.

If we start the application without specifying an active profile, Spring Boot falls back to a default profile named `default`. The shared `application.properties` file still loads normally, and Spring Boot also checks for `application-default.properties` if that file exists.

We can change the default profile through `spring.profiles.default`, although leaving it as `default` is sufficient for applications where deployment environments explicitly select their active profiles.

There is an important restriction on where these properties can be declared. Both `spring.profiles.active` and `spring.profiles.default` must be defined in non-profile-specific configuration sources. We cannot place them inside files such as `application-dev.properties` or documents activated through `spring.config.activate.on-profile`.

This keeps the selection of active profiles independent of the configuration documents that depend on those profiles being active.

Spring Boot also supports activating multiple profiles during the same application startup. We can provide their names as a comma-delimited value, which allows more than one profile-specific configuration file to participate in configuration loading.

```markup
java -jar app.jar --spring.profiles.active=dev,metrics
```

Both profiles become active, so Spring Boot can load configuration associated with `dev` and `metrics` alongside the shared properties.

The `metrics` profile is an optional name we’ve chosen for this example. We could create an `application-metrics.properties` file containing monitoring-related settings and activate it alongside whichever environment requires those settings.

If multiple active profiles contain conflicting properties in profile-specific files at the same configuration location, Spring Boot applies a last-wins rule. With `dev,metrics`, a value from `application-metrics.properties` can replace the same property defined in `application-dev.properties`.

This gives us flexibility when certain configuration groups should apply alongside the main environment. Still, for development, testing, staging, and production, selecting a single environment profile generally keeps the configuration more organized and reduces the chance of conflicting values.

Spring Boot reports active profile information during startup, which can help us confirm that the intended environment has been selected. If our application starts with unexpected settings, checking the reported active profiles gives us a starting point before examining the individual configuration files.

With the appropriate profile active, we can keep shared settings in `application.properties` and let Spring Boot load the environment-specific values that belong to that deployment.

### Applying Configuration in Java

Configuration files determine which property values are available in each environment, but our Java classes still need a way to access those values and respond to the active profile. Spring Boot provides annotations that let us register components conditionally, bind related properties to Java objects, and read the final configuration without manually opening property files. We can also control which source takes priority when the same property has been defined in multiple locations. These features allow us to keep environment differences in configuration while the application continues running the same Java code across development, testing, staging, and production.

#### Selecting Beans with @Profile

Configuration files handle differences in property values, but some environments need different Spring components rather than different settings. Development may require a local implementation of a service, while production connects to an external provider. Spring gives us the `@Profile` annotation to control which beans are registered in the application context based on the active profiles.

Spring beans are objects managed by the Spring container, which creates them and makes them available to other components through dependency injection. Normally, Spring registers eligible beans when the application starts, but adding `@Profile` lets us restrict their registration to particular environments.

We can place `@Profile` on classes annotated with `@Component` or `@Configuration`, or apply it directly to individual `@Bean` methods. The placement determines how broadly the condition applies. Adding it to a configuration class restricts registration of that class and the beans declared within it, while placing it on a method restricts only the bean created by that method.

For our report application, we’ll create a configuration class that registers a development-specific startup message:

```markup
package com.example.reports;

import org.springframework.boot.ApplicationRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;

@Configuration(proxyBeanMethods = false)
public class ProfileNoticeConfiguration {

    @Bean
    @Profile("dev")
    ApplicationRunner developmentNotice() {
        return args -> System.out.println(
            "Development profile is active"
        );
    }
}
```

We begin with `@Configuration`, which identifies `ProfileNoticeConfiguration` as a class containing Spring bean definitions. The `proxyBeanMethods = false` setting tells Spring that it doesn’t need to intercept calls between `@Bean` methods in this configuration class.

Inside the class, we’ve defined an `ApplicationRunner` bean through the `developmentNotice()` method. Spring Boot executes registered `ApplicationRunner` beans during startup after the application context has been initialized, making this a convenient place for actions that should happen as the application starts.

The `@Profile("dev")` annotation controls when Spring registers this particular bean. If we activate the `dev` profile, Spring creates the runner, and it prints the development message during startup.

Starting the application with `prod`, however, means the bean won’t be registered, so the message doesn’t appear. We don’t need to add conditional statements inside `developmentNotice()` because Spring determines if the bean belongs in the application context before creating it.

This becomes more practical when different environments require different implementations of the same service. We could register a local report delivery component for development and a production component that communicates with an external service. Other classes could depend on the same Java interface, with Spring injecting the implementation registered for the active profile.

When defining alternative implementations, we should arrange their profile conditions so Spring doesn’t register multiple competing beans for a dependency that expects a single implementation. Conflicting bean registrations can lead to dependency injection errors if Spring can’t determine which bean to inject.

The annotation also accepts multiple profile names. Writing `@Profile({"dev", "test"})` allows a component to be registered when either `dev` or `test` is active, which can help when both environments need the same supporting component.

Spring supports profile expressions as well, including negation through `!`. With `@Profile("!prod")`, the component is registered whenever the `prod` profile is not active. That includes startup with the default profile if `prod` hasn’t been activated.

We should keep in mind that `@Profile` controls bean registration rather than property values or access permissions. For settings such as report format, batch size, or logging level, configuration properties are generally sufficient. Conditional beans become appropriate when the components themselves need to differ between environments.

#### Binding Settings with @ConfigurationProperties

Custom configuration properties become more convenient when we can access them through Java objects instead of retrieving individual values throughout the application. Spring Boot provides `@ConfigurationProperties` for mapping related properties into a class or record, giving us a central location to represent configuration that belongs to the same feature.

Our report application already defines `app.reports.format` and `app.reports.batch-size`, which control the report format and processing batch size. Rather than retrieving these properties individually whenever we need them, we can create a Java record that holds both values.

We’ll name the record `ReportProperties` and give it the same property prefix we’ve been defining in our configuration files:

```markup
package com.example.reports;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app.reports")
public record ReportProperties(
    String format,
    int batchSize
) {
}
```

The `@ConfigurationProperties` annotation tells Spring Boot that this record represents properties beginning with `app.reports`. We don’t include the individual property names in the annotation because Spring Boot matches them to the record components during configuration binding.

Our `format` component receives the value of `app.reports.format`, while `batchSize` receives the value of `app.reports.batch-size`.

Notice that the property name contains a hyphen, but the Java component follows camel case naming. Spring Boot supports this through relaxed binding, which allows property names written in different supported naming styles to map to Java fields or record components without requiring identical spelling.

Spring Boot also handles converting values into the declared Java types. The report format remains a `String`, while the batch size becomes an `int`. If we provide a value that cannot be converted into the required type, configuration binding can fail during application startup.

Records are a good choice for this type of configuration because their components are initialized through the constructor and can’t be reassigned afterward. We can read their values through generated accessor methods without writing getters, setters, or a constructor ourselves.

To make `ReportProperties` available through Spring’s dependency injection system, we need to register it as a bean. Spring Boot provides `@ConfigurationPropertiesScan`, which searches for eligible classes annotated with `@ConfigurationProperties`.

We can add this annotation to our main application class:

```markup
package com.example.reports;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class ReportApplication {

    public static void main(String[] args) {
        SpringApplication.run(ReportApplication.class, args);
    }
}
```

The `@SpringBootApplication` annotation identifies our main application class and includes the standard Spring Boot configuration and component scanning behavior.

By adding `@ConfigurationPropertiesScan`, we’re telling Spring Boot to search for configuration property classes beginning in the package containing `ReportApplication`.

Because our record belongs to `com.example.reports`, Spring Boot can discover it during startup and register it as a bean. If the record were located outside the scanned package hierarchy, we’d need to specify the appropriate package for scanning.

We also don’t need to annotate `ReportProperties` with `@Component`. Configuration property scanning handles its registration, allowing Spring Boot to create the record through constructor binding.

With the configuration record registered, we can inject it into a service that needs access to report settings.

For our application, we’ll create `ReportDescriptionService`, which reads the report format and batch size:

```markup
package com.example.reports;

import org.springframework.stereotype.Service;

@Service
public class ReportDescriptionService {

    private final ReportProperties properties;

    public ReportDescriptionService(ReportProperties properties) {
        this.properties = properties;
    }

    public String description() {
        return "Format = " + properties.format()
            + ", batch size = " + properties.batchSize();
    }
}
```

The `@Service` annotation registers `ReportDescriptionService` as a Spring-managed component. We’ve declared a `ReportProperties` field and provided it through the constructor, allowing Spring to inject the configuration object when creating the service.

Inside `description()`, we call `properties.format()` and `properties.batchSize()` to retrieve the current configuration values. These accessor methods are generated automatically because `ReportProperties` is a Java record.

With the `dev` profile active, calling `description()` returns `Format = detailed, batch size = 50`, reflecting the development format override and the shared batch size.

If we run the application with `prod`, the same method returns `Format = summary, batch size = 100`.

We haven’t changed the service or created different versions of the record for each environment. Spring Boot resolves the active configuration before binding the properties, so our service receives the values associated with the current environment.

This becomes valuable when an application has several related configuration properties. We can group report settings into `ReportProperties`, create a different configuration class for database-related custom settings, and continue accessing those values through constructor injection.

Properties that must meet particular requirements should also be checked through configuration validation when appropriate. Spring Boot supports Jakarta Bean Validation for `@ConfigurationProperties` classes when the necessary validation dependencies and annotations are present. This allows invalid configuration to be rejected during startup rather than reaching a component later.

The record itself doesn’t automatically provide our report defaults. Those values come from the configuration files we’ve already defined, giving us a consistent location for managing differences between environments.

#### Following Property Precedence

Different configuration sources can define the same property, so Spring Boot needs a consistent way to determine which value the application receives. This is handled through property source precedence, where sources with higher priority can replace values from sources with lower priority.

We’ve already seen how an active profile can replace a value from `application.properties`. That behavior is part of a broader ordering system that includes external configuration files, operating system environment variables, Java system properties, and command-line arguments. For normal application startup, packaged `application.properties` values have lower priority than packaged profile-specific configuration values. External configuration files have higher priority than their packaged counterparts, with external profile-specific files taking priority over external shared files.

Operating system environment variables can then override values from those configuration files. Java system properties have higher priority than operating system environment variables, while command-line arguments take priority over these sources by default.

Spring Boot supports other property sources as well, including overrides intended for tests, but these are the sources we’ll encounter most frequently when configuring applications for different deployment environments.

Returning to our report application, the shared configuration provides a batch size of `50`, while the production profile replaces it with `100`.

Now, our production deployment may need a batch size of `150` without modifying the packaged configuration. We can provide that value through an operating system environment variable.

In a Bash-compatible shell, we’ll define it through the following command:

```markup
export APP_REPORTS_BATCHSIZE=150
```

The variable `APP_REPORTS_BATCHSIZE` corresponds to our custom property `app.reports.batch-size`.

Spring Boot supports converting property names to their environment variable equivalents by replacing periods with underscores, removing hyphens, and converting letters to uppercase.

Following those rules, `app.reports.batch-size` becomes `APP_REPORTS_BATCHSIZE`, which Spring Boot can bind to our configuration record.

If the `prod` profile is active and this environment variable has been exported, the final batch size becomes `150`, replacing the value of `100` from `application-prod.properties`.

This allows deployment configuration to take priority over packaged defaults without requiring changes to the JAR file. We can provide different externally managed values depending on the environment where the application runs, while keeping the original configuration files unchanged.

Command-line arguments give us another way to override individual properties. Assuming the production profile has already been selected through the deployment environment, we can start the application with a different batch size.

```markup
java -jar app.jar --app.reports.batch-size=200
```

The `--app.reports.batch-size=200` argument tells Spring Boot to provide `200` for that property during startup.

Because command-line arguments have higher priority than operating system environment variables and configuration files, our `ReportProperties` record now receives a batch size of `200`.

The environment variable can still contain `150`, and `application-prod.properties` can still contain `100`, but neither takes priority over the command-line value in this situation.

This precedence behavior gives us several ways to control configuration depending on how the application is deployed. Packaged properties provide defaults, profile-specific files contain environment differences, and external sources can supply replacement values without rebuilding the application.

External configuration files also participate in the same system. Spring Boot searches supported locations outside the packaged application, including the current directory and its `config` directory.

For deployments requiring configuration files in other locations, we can provide `spring.config.additional-location` to include extra directories or files alongside Spring Boot’s default configuration locations. This differs from `spring.config.location`, which replaces the default search locations with the locations we specify.

The distinction becomes important when a deployment provides configuration through mounted files or directories. We can retain the packaged defaults while allowing properties supplied by the deployment environment to take priority where appropriate.

Sensitive values are another reason to keep configuration external. Database credentials and service tokens can be supplied through managed environment configuration or dedicated secrets services rather than being committed into repository files.

When a property receives an unexpected value, checking the different sources that define it can help identify the cause. The value in `application-prod.properties` may be correct, but an environment variable or command-line argument could be replacing it during startup.

Our Java classes don’t need special handling for those differences. Spring Boot resolves the property according to its precedence rules, and `@ConfigurationProperties` receives the final value during binding.

#### Checking Spring Boot 4 Behavior

The profile features we’ve been applying remain available in Spring Boot 4, including `@Profile`, `@ConfigurationProperties`, `@ConfigurationPropertiesScan`, and the existing profile-specific configuration conventions. We can continue organizing environment configuration through the same annotations and property files while following the current Spring Boot configuration system.

Spring Boot 4 builds on Spring Framework 7 and requires Java 17 or later. It also reorganizes several internal modules and updates configuration properties associated with particular technologies.

Some built-in property names changed during the transition from Spring Boot 3.x to Spring Boot 4. MongoDB configuration gives us a good example, where properties like `spring.data.mongodb.uri` and `spring.data.mongodb.host` have moved to `spring.mongodb.uri` and `spring.mongodb.host`.

Not every property beginning with `spring.data.mongodb` changed, however. Certain settings associated specifically with Spring Data MongoDB retain that prefix, including `spring.data.mongodb.auto-index-creation`.

For applications moving from Spring Boot 3.x, we should check the configuration properties associated with the dependencies our application relies on. The profile structure itself doesn’t need to change, but renamed configuration properties must be updated so Spring Boot can apply the intended settings.

Testing the configuration gives us a way to confirm that each environment receives the values we’ve defined, rather than relying entirely on what appears in the property files.

Spring Boot supports the `@ActiveProfiles` annotation through the Spring Test framework, allowing us to activate particular profiles while running tests.

For our report application, we’ll create a JUnit test that starts the Spring application context with the `test` profile active and checks the values bound to `ReportProperties`.

With `spring-boot-starter-test` available as a test dependency, we can create the following test with JUnit Jupiter and AssertJ:

```markup
package com.example.reports;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@ActiveProfiles("test")
class ReportPropertiesTests {

    @Autowired
    private ReportProperties properties;

    @Test
    void loadsTestProfileSettings() {
        assertThat(properties.format())
            .isEqualTo("summary");

        assertThat(properties.batchSize())
            .isEqualTo(5);
    }
}
```

The `@SpringBootTest` annotation tells Spring Boot to create an application context for the test, allowing it to load the application’s configuration and register the Spring beans required for testing.

We’ve also added `@ActiveProfiles("test")`, which activates the `test` profile for this test class. Spring Boot therefore loads our testing configuration alongside the shared properties when preparing the application context.

The `@Autowired` annotation injects the `ReportProperties` bean into the test, giving us access to the values Spring Boot has already bound.

Inside `loadsTestProfileSettings()`, we check the report format and batch size through AssertJ assertions. The `assertThat()` method receives the actual property value, while `isEqualTo()` checks that it matches the value we expect.

The first assertion expects `summary`, which comes from our shared `application.properties` file because the testing profile doesn’t replace that setting.

Our second assertion expects `5`, matching the batch size provided by `application-test.properties`.

If either assertion receives an unexpected value, the test fails and identifies which expectation wasn’t met. Assuming no higher-priority property source overrides the values, both assertions pass with the configuration we’ve established.

We can follow the same testing method for other profiles when their configuration needs verification. Tests can check values directly through configuration property objects, which helps us confirm that the application receives the intended settings without manually examining every property file.

Spring Boot also provides configuration inspection facilities through its Actuator module. The `env` endpoint can provide information about environment properties and their sources, while `configprops` provides information about configuration properties bound to Spring beans.

These endpoints require Spring Boot Actuator and appropriate endpoint exposure settings. Access should be restricted because configuration information can contain sensitive details, and Spring Boot applies sanitization rules to endpoint responses.

For our report application, these facilities can help us investigate situations where the application receives a different value from the expected configuration. We can examine the active environment, identify the property source involved, and compare the resolved values with those received by `ReportProperties`.

By combining profile-aware tests with Spring Boot’s configuration inspection capabilities, we can verify the settings applied to each environment while keeping our Java components focused on reading and applying the configuration they receive.

### Conclusion

Spring Boot profiles let us manage environment-specific settings while keeping common properties in `application.properties`. We can activate profiles at startup, override values through external configuration, and rely on property precedence to determine which settings take priority. With `@Profile`, we control which beans Spring registers, while `@ConfigurationProperties` binds the resolved values to Java objects. Profile-aware tests then help us verify that development, testing, staging, and production receive their intended configuration without changing the application’s Java code.

![](https://substackcdn.com/image/fetch/$s_!Yc0y!,w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fb20a6800-fe35-43e8-8c6d-d05acb4977c5_276x276.png)

Spring Boot icon by Icons8
