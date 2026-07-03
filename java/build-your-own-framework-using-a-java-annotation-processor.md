---
title: "Build your own framework using a Java annotation processor"
source: "https://virtuslab.com/blog/backend/build-framework-java-annotation-processor"
author:
  - "[[Jacek Dubikowski]]"
published: 2024-01-23
created: 2026-07-03
description: "A step-by-step guide for Java developers on how to build a framework using a Java annotation processor."
tags:
  - "clippings"
---

> [!summary]
> A hands-on tutorial that builds a minimal dependency-injection framework using a Java annotation processor, the compile-time approach used by Micronaut and Quarkus (versus Spring's runtime reflection). It walks through writing a `BeanProcessor` that finds `@jakarta.inject.Singleton` classes, generates `BeanDefinition` implementations with JavaPoet, and provisions beans at runtime via a `BeanProvider` backed by the Reflections library. Also covers annotation-processor testing with Google's compile-testing library, with transactions promised in a follow-up part.

A majority of developers in the JVM world work on various web applications, most of which are based on a framework like Spring or Micronaut. However, some people state that frameworks produce a too big overhead. I decided to see how valid such claims are and how much work is necessary to replicate what frameworks provide us out-of-the-box.

This article isn’t about whether or not it is feasible to use a framework or when to use it. It is about writing your framework – tinkering is the best way of learning!

For the sake of simplicity, we will use a demo app code. The application consists of

- Singular service
- Two repositories
- Two POJOs

## No framework

The starting point of an application without a framework would look like the [code](https://github.com/JacekDubikowski/build-your-own-framework/blob/main/testapp/src/main/java/io/jd/testapp/NoFrameworkApp.java) below:

```
public class NoFrameworkApp {
    public static void main(String[] args) {
        ParticipationService participationService = new ManualTransactionParticipationService(
                new ParticipantRepositoryImpl(),
                new EventRepositoryImpl(),
                new TransactionalManagerStub()
        );
        participationService.participate(new ParticipantId(), new EventId());
    }
}
```

As we can see, the application’s main method is responsible for providing the implementation of interfaces that *ManualTransactionParticipationService* depends on. The developer must know which ParticipationService implementation should be created in the main method. When using a framework, programmers typically don’t need to create instances and dependencies on their own. They rely on the core feature of the frameworks – **Dependency Injection**.

So, let’s take a look at a simple implementation of the dependency injection container based on annotation processing.

## What is a Dependency Injection?

### Dependency Injection Pattern

*Dependency Injection*, or *DI*, is a pattern for providing class instances its instance variables (its dependencies).

But how is this done? The pattern separates responsibility for object creation from its usage. The required objects are provided (“injected”) during runtime, and the pattern’s implementation handles the creation and lifecycle of the dependencies.

The feature has its advantages, like decreased coupling, simplified testing, and increased flexibility. But also drawbacks: framework dependence, harder debugging, or more work at the beginning of the project.

*NOTE: Dependency Injection is the implementation of* [*Inversion of control*](https://www.martinfowler.com/bliki/InversionOfControl.html)*!*

### Available Dependency Injection solutions

There are at least a few DI frameworks widely adopted in the Java world.

- [Spring](https://spring.io/) – DI was the initial part of this project, and it’s still the core concept for the framework.
- [Guice](https://github.com/google/guice) – Google’s DI framework/library.
- [Dagger](https://dagger.dev/dev-guide/) – popular in the Android world.
- [Micronaut](https://micronaut.io/) – part of the framework.
- [Quarkus](https://quarkus.io/guides/cdi-reference) – part of the framework.
- [Java/Jakarta CDI](https://www.cdi-spec.org/) – standard DI framework that originates in Java EE 6.

Most of these DI frameworks use annotations as one of the possible ways to configure the bindings. By bindings, I mean the configuration of which implementations should be used for interfaces or which dependencies should be provided to create objects.

In fact, DI is so popular that there was a [Java Specification Request](https://jcp.org/en/jsr/detail?id=330) made for it.

### Annotations handling

#### Runtime-based handling

Spring, the most popular Java framework, processes annotations in runtime. The solution is heavily based on the reflection mechanism. The reflection-based approach is one of the possible ways to handle annotations, and if you would like to follow that lead, please refer to [Java Own Framework – step by step](https://github.com/Patresss/Java-Own-Framework---step-by-step).

#### Compile-based handling

In addition to runtime handling, there is another approach. The **part** of the dependency injection can happen during [*annotation processing*](https://www.youtube.com/watch?v=xswPPwYPAFM), a process that occurs during compile time. It has become popular lately thanks to Micronaut and Quarkus as they utilise the approach.

Annotation processing isn’t just for dependency injection. It is a part of various tools. For example, in libraries like [Lombok](https://projectlombok.org/) or [MapStruct](https://mapstruct.org/).

#### Annotation Processing and Processors

The purpose of annotation processing is to **generate not modify** files. It can also make some compile-time checks, like ensuring that all class fields are final. If something is wrong, the processor may fail the compilation and provide the programmer with information about an error.

Annotation processors are written in Java and are used by javac during the compilation. However, programmers must compile the processor before using it. It cannot directly process itself.

The processing happens in rounds. In every round, the compiler searches for annotated elements. Then the compiler matches annotated elements to the processors that declared being interested in processing them. Any generated files become input for the next round of the compilation. If there are no more files to process, the compilation ends.

#### How to observe the work of annotation processors

There are two compiler flags -XprintProcessorInfo and -XprintRounds that will present the information about the compilation process and the compilation rounds.

Round 1:

```
input files: {io.jd.Data}
       annotations: [io.jd.AllFieldsFinal]
       last round: false
```

Processor io.jd.AnnotationProcessor matches \[/io.jd.SomeAnnotation\] and returns true.

Round 2:

```
input files: {}
annotations: []
last round: true
```

We can make some assumptions based on the code above. First, we need the framework to provide annotations for pointing classes. I decided to use the standardised jakarta.inject.\* library for annotation. To be more precise, just the jakarta.inject.Singleton. The same is used by *Micronaut*.

The second thing we can be sure about is that we need a *BeanProvider*. The frameworks like to refer to it using the word Context, like ApplicationContext.

The third necessary thing is an annotation processor that will process the mentioned annotation(s). It should produce classes allowing the framework to provide the expected dependencies in runtime.

The framework should use the reflection mechanism as little as possible.

For the sake of simplicity, we would assume the framework:

- handles concrete classes annotated with *@Singleton* that have one constructor only,
- utilises the singleton scope (each bean will have only one instance for a given *BeanProvider*).

### How should the framework work?

The annotation processing approach is powerful and offers many ways to achieve the goal. Therefore, the design is the point where we should start. We will begin with a basic version, which we will develop gradually as the article develops.

The diagram below shows the high-level architecture of the desired solution.

```
interface Water {
    String name();
}

@Singleton
class SparklingWater implements Water {

    @Override
    String name() {
        return "Bubbles";
    }
}

public class App {
    public static void main(String[] args) {
        BeanProvider provider = BeanProviderFactory.getInstance();
        var bean = beanProvider.provider(SoftDrink.class);
        System.out.println(bean.name()); // prints "Bubbles"
    }
}
```

As you can see, we need a *BeanProcessor* to generate implementations of the *BeanDefinition* for each bean. Then the *BeanDefinition* s are picked by *BaseBeanProvider,* which implements the [*BeanProvider*](https://github.com/JacekDubikowski/build-your-own-framework/blob/main/framework/src/main/java/io/jd/framework/BeanProvider.java) (not in the diagram). In the application code, we use the *BaseBeanProvider,* created for us by the *BeanProviderFactory*. We also use the *ScopeProvider* interface that is supposed to handle the scope of the bean lifespan. In the example, as mentioned, we only care about the singleton scope.

### Implementation of the framework

The framework itself is placed in the Gradle subproject called *framework*.

#### Basic interfaces

Let’s start with the [*BeanDefinition* interface](https://github.com/JacekDubikowski/build-your-own-framework/blob/main/framework/src/main/java/io/jd/framework/BeanDefinition.java).

```
package io.jd.framework;

public interface BeanDefinition<T> {
    T create(BeanProvider beanProvider);

    Class<T> type();
}
```

The interface only has two methods: type() to provide a *Class* object for the bean class and one to build the bean itself. The create(…) method accepts the *BeanProvider* to get its dependencies needed during build time as it is not supposed to create them, hence the DI.

The framework will also need the [BeanProvider](https://github.com/JacekDubikowski/build-your-own-framework/blob/main/framework/src/main/java/io/jd/framework/BeanProvider.java) interface with just two methods.

```
package io.jd.framework;

public interface BeanProvider {
    <T> T provide(Class<T> beanType);

    <T> Iterable<T> provideAll(Class<T> beanType);
}
```

The provideAll(…) method provides all beans that match the parameter Class\<T> beanType. By match, I mean that the given bean is a subtype or is the same type as the given beanType. The provide(…) method is almost the same but provides only one matching bean. An exception is thrown in the case of no beans or more than one bean.

#### Annotation processor

We expect the annotation processor to find classes annotated with *@Singleton*. Then check if they are valid (no interfaces, abstract classes, just one constructor). The final step is creating the implementation of the *BeanDefinition* for each annotated class.

So we should start by implementing it, right?

The test-driven-development would object. We will get back to the tests later. Now, let’s focus on implementation.

#### Step 1 – Define the processor

Let’s define our processor:

```
import javax.annotation.processing.AbstractProcessor;

class BeanProcessor extends AbstractProcessor {

}
```

Our processor will extend the provided *AbstractProcessor* instead of fully implementing the *Processor* interface.

The [actual implementation](https://github.com/JacekDubikowski/build-your-own-framework/blob/main/framework/src/main/java/io/jd/framework/processor/BeanProcessor.java) differs from what you are seeing. Don’t worry; it will be used to the full extent in the next step. The simplified version shown here is enough to do the actual DI work.

Step 2 – Add annotations

```
import javax.annotation.processing.AbstractProcessor;
import javax.annotation.processing.SupportedAnnotationTypes;
import javax.annotation.processing.SupportedSourceVersion;
import javax.lang.model.SourceVersion;

@SupportedAnnotationTypes({"jakarta.inject.Singleton"}) // 1
@SupportedSourceVersion(SourceVersion.RELEASE_17) // 2
class BeanProcessor extends AbstractProcessor {

}
```

Thanks to the usage of the *AbstractProcess,* we don’t have to override any methods. The annotations can be used instead:

1. @SupportedAnnotationTypes corresponds to *Processor.getSupportedAnnotationTypes* and is used to build the returned value. As defined, the processor cares only for @jakarta.inject.Singleton. 2.
2. @SupportedSourceVersion(SourceVersion.RELEASE\_17) corresponds to *Processor.getSupportedSourceVersion* and is used to build the returned value. The processor will support language up to the level of Java 17.

Step 3 – Override the process method

Please assume that the code below is included in the BeanProcessor class body.

```
@Override
 public boolean process(Set<? extends TypeElement> annotations, RoundEnvironment roundEnv) { // 1
     try {
         processBeans(roundEnv); // 2
     } catch (Exception e) {
         processingEnv.getMessager() // 3
             .printMessage(ERROR, "Exception occurred %s".formatted(e));
     }
     return false; // 4
 }
```

1. The annotations param provides a set of annotations represented as *Element* s. The annotations are represented at least by the *TypeElement* s interface. It may seem unusual, as everyone is used to *java.lang.Class* or broader *java.lang.reflect.Type*, which is runtime representations.
	1. On the other hand, there is also the compile-time representation.
		2. Let me introduce the [*Element* interface](https://docs.oracle.com/en/java/javase/17/docs/api/java.compiler/javax/lang/model/element/Element.html), the common interface for all language-level compile-time constructs such as classes, modules, variables and packages. It is worth mentioning that there are subtypes corresponding to the constructs like *PackageElement* or [*TypeElement*](https://docs.oracle.com/en/java/javase/17/docs/api/java.compiler/javax/lang/model/element/TypeElement.html).
		3. The processor code is going to use the *Element* s a lot.
2. As the processor should catch any exception and log it, we will use the try and catch clauses here. The BeanProcessor.processBeans method will provide the actual annotation processing.
3. The annotation processor framework provides the [*Messager*](https://docs.oracle.com/en/java/javase/17/docs/api/java.compiler/javax/annotation/processing/Messager.html) instance to the user through the processingEnv field of *AbstractProcessor*. The *Messager* is a way to report any errors, warnings, etc.
	It defines four overloaded methods printMessage(…), and the first parameter of the methods is used to define message type using [Diagnostic.Kind enum](https://docs.oracle.com/en/java/javase/17/docs/api/java.compiler/javax/tools/Diagnostic.Kind.html). In the code, there is an example of an error message.
	If a processor throws an exception, the compilation will fail without extra diagnostic data.
4. There is no need to claim the annotations, so the method returns false.

Step 4 – Write the actual processing

```
private void processBeans(RoundEnvironment roundEnv) {
    Set<? extends Element> annotated = roundEnv.getElementsAnnotatedWith(Singleton.class); // 1
    Set<TypeElement> types = ElementFilter.typesIn(annotated); // 2
    var typeDependencyResolver = new TypeDependencyResolver(); // 3
    types.stream().map(t -> typeDependencyResolver.resolve(t, processingEnv.getMessager())) // 4
            .forEach(this::writeDefinition); // 5
}
```

1. First, the *RoundEnvironment* is used to provide all elements from the compilation round annotated with *@Singleton*.
2. Then the [*ElementFilter*](https://docs.oracle.com/en/java/javase/17/docs/api/java.compiler/javax/lang/model/util/ElementFilter.html) is used to get only *TypeElement* s out of annotated. It could be wise to fail here when annotated differs in size from types, but one can annotate anything with *@Singleton,* and we don’t want to handle that. Therefore, we won’t care for anything other than [*TypeElement* s](https://docs.oracle.com/en/java/javase/17/docs/api/java.compiler/javax/lang/model/element/TypeElement.html). They represent class and interface elements during compilation.
- The *ElementFilter* is a utility class that filters *Iterable<? extends Element>* or *Set<? extends Element>* to get elements matching criteria with type narrowed to matching *Element* implementation.
1. As the next step, we instantiate the *TypeDependencyResolver,* which is part of our framework. The class is responsible for getting the type element, checking if it has only one constructor and what are the constructor parameters. We will cover its code later on.
2. Then we resolve our dependencies using the *TypeResolver* to be able to build our *BeanDefinition* instance.
3. The last thing to do is write Java files with definitions. We will cover it in Step 5.

Getting back to the *TypeDefinitionResolver*, the code below shows the implementation:

```
public class TypeDependencyResolver {

    public Dependency resolve(TypeElement element, Messager messager) {
       var constructors = ElementFilter.constructorsIn(element.getEnclosedElements()); // 1
       return constructors.size() == 1 // 2
               ? resolveDependency(element, constructors) // 3
               : failOnTooManyConstructors(element, messager, constructors); // 4
    }

    private Dependency resolveDependency(TypeElement element, List<ExecutableElement> constructors) { // 5
        ExecutableElement constructor = constructors.get(0);
        return new Dependency(element, constructor.getParameters().stream().map(VariableElement::asType).toList());
    }
    ...
}
```

1. The *ElementFilter,* which we’re already familiar with, gets the constructors of the element.
2. A check is carried out to ensure our element has just one constructor.
3. If there is one constructor, we follow the process.
4. In case there is more than one, the compilation fails. You can see the failOnTooManyConstructors method implementation [here](http://framework/src/main/java/io/jd/framework/processor/TypeDependencyResolver.java). The single constructor creates a *Dependency* object with the element and its dependencies. It will be used for writing the actual Java code. Seeing the *Dependency* implementation would be beneficial, so please take a look:

```
public final class Dependency {
       private final TypeElement type;
       private final List<TypeMirror> dependencies;

       ...

       public TypeElement type() {
           return type;
       }

       public List<TypeMirror> dependencies() {
           return dependencies;
       }
       ...
   }
```

You may have noticed the strange type [*TypeMirror*](https://docs.oracle.com/en/java/javase/17/docs/api/java.compiler/javax/lang/model/type/TypeMirror.html). It represents a type in Java language (literally language, as this is a compile-time thing).

Step 5 – Writing definitions

How can I write Java source code?

To write Java code during annotation processing, you can use almost anything. You are good to go as long as you end up with *CharSequence* / *String* / *byte\[\].*

In examples on the Internet, you will find that it is popular to use *StringBuffer*. Honestly, I find it inconvenient to write any source code like that. There is a better solution available for us.

[JavaPoet](https://github.com/square/javapoet) is a library for writing Java source code using JavaAPI. You will see it in action in the next section.

To write Java code during annotation processing, you can use almost anything. You are good to go as long as you end up with *CharSequence* / *String* / *byte\[\].*

In examples on the Internet, you will find that it is popular to use *StringBuffer*. Honestly, I find it inconvenient to write any source code like that. There is a better solution available for us.

[JavaPoet](https://github.com/square/javapoet) is a library for writing Java source code using JavaAPI. You will see it in action in the next section.

Missing part of BeanProcessor

Getting back to *BeanProcessor*. Some parts of the file were not revealed yet. Let us get back to it:

```
private void writeDefinition(Dependency dependency) {
    JavaFile javaFile = new DefinitionWriter(dependency.type(), dependency.dependencies()).createDefinition(); // 1
    writeFile(javaFile);
}

private void writeFile(JavaFile javaFile) { // 2
    try {
        javaFile.writeTo(processingEnv.getFiler());
    } catch (IOException e) {
        processingEnv.getMessager().printMessage(ERROR, "Failed to write definition %s".formatted(javaFile));
    }
}
```

The writing is done in two steps:

1. *The DefinitionWriter* creates the *BeanDefinition*, and a JavaFile instance contains it.
2. The programmer writes the implementation to the actual file using provided via processingEnv [Filer](https://cr.openjdk.java.net/~iris/se/17/latestSpec/api/java.compiler/javax/annotation/processing/Filer.html) instance. Should writing fail, the compilation will fail, and the compiler will print the error message.

*Filer* is an interface that supports file creation for an annotation processor. The place for the generated files to be stored is configured through the -s javac flag. However, most of the time, build tools handle it for you. In that case, the files are stored in a directory like build/generated/sources/annotationProcessor/java for Gradle or similar for different tools.

The creation of Java code takes place in *DefinitionWriter,* and you will see the implementation in a moment. However, the question is what such a definition looks like. I think an example will show it best.

An example of what should be written

For the below Bean:

```
@Singleton
public class ServiceC {
    private final ServiceA serviceA;
    private final ServiceB serviceB;

    public ServiceC(ServiceA serviceA, ServiceB serviceB) {
        this.serviceA = serviceA;
        this.serviceB = serviceB;
    }
}
```

The definition should look like the code below:

```
public class $ServiceC$Definition implements BeanDefinition<ServiceC> { // 1
  private final ScopeProvider<ServiceC> provider =  // 2
          ScopeProvider.singletonScope(beanProvider -> new ServiceC(beanProvider.provide(ServiceA.class), beanProvider.provide(ServiceB.class)));

  @Override
  public ServiceC create(BeanProvider beanProvider) { // 3
    return provider.apply(beanProvider);
  }

  @Override
  public Class<ServiceC> type() { // 4
    return ServiceC.class;
  }
}
```

There are four elements here:

1. An inconvenient name to prevent people from using it directly. The class should implement BeanDefinition\<BeanType>.
2. A field of type *ScopeProvider,* responsible for instantiation of bean and ensuring its lifetime (scope).

Singleton scope is the only scope the framework covers, so the *ScopeProvider.singletonScope()* method will be the only one used. The Function<BeanProvider, Bean>, used to instantiate the bean is passed to the method ScopeProvider.singletonScope.

I will cover the implementation of the *ScopeProvider* later. For now, it is enough to know that it will ensure just one instance of the bean in our DI context.

However, if you are curious, the source code is available [here](https://github.com/JacekDubikowski/build-your-own-framework/blob/main/framework/src/main/java/io/jd/framework/ScopeProvider.java).

1. The actual create method uses the provider and connects it with the beanProvider through the apply method.
2. The implementation of the type method is a simple task.

The example shows that the only bean-specific things are the type passed to BeanDefinition declaration, new call, and field/returned types.

Implementation of the *DefinitionWriter*

To keep this concise, I will omit the private methods’ code, the constructor and some small snippets. Let us see the overview of Java code that writes Java code. Here is a link to the full [code](https://github.com/JacekDubikowski/build-your-own-framework/blob/main/framework/src/main/java/io/jd/framework/processor/DefinitionWriter.java).

```
class DefinitionWriter {
    private final TypeElement definedClass; // 1
    private final List<TypeMirror> constructorParameterTypes; // 1
    private final ClassName definedClassName; // 1

    public JavaFile createDefinition() {
        ParameterizedTypeName parameterizedBeanDefinition = ParameterizedTypeName.get(ClassName.get(BeanDefinition.class), definedClassName); // 3
        var definitionSpec = TypeSpec.classBuilder("$%s$Definition".formatted(definedClassName.simpleName())) // 2
                .addSuperinterface(parameterizedBeanDefinition) // 3
                .addMethod(createMethodSpec()) // 4
                .addMethod(typeMethodSpec()) // 5
                .addField(scopeProvider()) // 6
                .build();
        return JavaFile.builder(definedClassName.packageName(), definitionSpec).build(); // 7
    }

    private MethodSpec createMethodSpec() { ... } // 4

    private MethodSpec typeMethodSpec() { ... } // 5

    private FieldSpec scopeProvider() { ... }  // 6

    private CodeBlock singletonScopeInitializer() { ... }  // 6
}
```

Phew, that is a lot. Don’t be afraid; it’s simpler than it looks.

1. There are three instance fields:
- TypeElement definedClass is our bean,
- List\<TypeMirror> constructorParameterTypes contains parameters for bean constructor (who would guess, right?),
- ClassName definedClassName is the JavaPoet object, created out of definedClass. It represents a fully qualified name for classes.
1. *TypeSpec* is a JavaPoet class representing Java type creation (classes and interfaces). It is created using the classBuilder static method, in which we pass our strange name, constructed based on the actual bean type name.
2. ParameterizedTypeName.get(ClassName.get(BeanDefinition.class), definedClassName) creates code that represents BeanDefinition\<BeanTypeName>, which is applied as a super interface of our class through the addSuperinterface method.
3. The create() method implementation is not that hard, and it’s quite self-explanatory. Please look at the createMethodSpec() method and its application.
4. The same applies to the type() method as for the create().
5. The scopeProvider() is similar to the previous methods. However, the tricky part is to invoke the constructor. The singletonScopeInitializer() is responsible for creating a constructor call wrapped in ScopeProvider.singletonScope(beanProvider -> …). We call BeanProvider.provide for every parameter to get the dependency and keep the calls in the order of the constructor parameters.

Ok, the *BeanDefinition* s are ready. Now, we move on to the *ScopeProvider*.

ScopeProvider Implementation

```
public interface ScopeProvider<T> extends Function<BeanProvider, T> { // 1

    static <T> ScopeProvider<T> singletonScope(Function<BeanProvider, T> delegate) { // 2
        return new SingletonProvider<>(delegate);
    }
}

final class SingletonProvider<T> implements ScopeProvider<T> { // 3
    private final Function<BeanProvider, T> delegate;
    private volatile T value;

    SingletonProvider(Function<BeanProvider, T> delegate) {
        this.delegate = delegate;
    }

    public synchronized T apply(BeanProvider beanProvider) {
        if (value == null) {
            value = delegate.apply(beanProvider);
        }
        return value;
    }
}
```

1. You can see the sealed interface definition that extends Function<BeanProvider, T>. So the Function.apply() method is available.
2. Factory method for SingletonProvider
3. Implementation of the SingletonScope is based on any kind of lazy value implementation in Java. In the synchronized apply method, we only create the instance of our bean if there isn’t one. The value field is marked as volatile to prevent issues in a multithreaded environment.

Now we are ready. It is time for the runtime part of the framework.

Step 5 – Runtime provisioning of beans

Runtime provisioning is the last part of the framework to work on. The *BeanProvider* interface has already been defined. Now we just need the implementation to do the actual provisioning.

The *BaseBeanProvider* must have access to all instantiated *BeanDefinition* s. This is because the *BaseBeanProvider* shouldn’t be responsible for creating and providing the beans.

The BeanProvider Factory

Due to the mentioned fact, the *BeanProviderFactory* took responsibility via the static BeanProvider getInstance(String… packages) method. Where packages parameter defines places to look for the *BeanDefinition* s present on the classpath. This is the code:

```
public class BeanProviderFactory {

    private static final QueryFunction<Store, Class<?>> TYPE_QUERY = SubTypes.of(BeanDefinition.class).asClass(); // 2

    public static BeanProvider getInstance(String... packages) { // 1
        ConfigurationBuilder reflectionsConfig = new ConfigurationBuilder() // 3
                .forPackages("io.jd") // 4
                .forPackages(packages) // 4
                .filterInputsBy(createPackageFilter(packages)); // 4
        var reflections = new Reflections(reflectionsConfig); // 5
        var definitions = definitions(reflections); // 6
        return new BaseBeanProvider(definitions); // 8
    }

    private static FilterBuilder createPackageFilter(String[] packages) { // 4
       var filter = new FilterBuilder().includePackage("io.jd");
       Arrays.asList(packages).forEach(filter::includePackage);
       return filter;
    }

    private static List<? extends BeanDefinition<?>> definitions(Reflections reflections) { // 6
        return reflections
                .get(TYPE_QUERY)
                .stream()
                .map(BeanProviderFactory::getInstance) // 7
                .toList();
    }

    private static BeanDefinition<?> getInstance(Class<?> e) { // 7
        try {
            return (BeanDefinition<?>) e.getDeclaredConstructors()[0].newInstance();
        } catch (InstantiationException | IllegalAccessException | InvocationTargetException ex) {
            throw new FailedToInstantiateBeanDefinitionException(e, ex);
        }
    }
}
```

1. The method is responsible for getting an instance of the *BeanProvider*.
2. Here is where it gets interesting. I define constant TYPE\_QUERY with a very specific type from the [Reflections library](https://github.com/ronmamo/reflections). The project [README.md](https://github.com/ronmamo/reflections/blob/master/README.md) defines it as:
- *Reflections* scans and indexes your project’s classpath metadata, allowing reverse transitive query of the type system on runtime.

I encourage you to read more about it, but I will just explain how it is used in the code. The defined *QueryFunction* will be used to scan the classpath in runtime to find all subtypes of the *BeanDefinition*.

1. The configuration is created for the *Reflections* object. It will be used in the next part of the code.
2. The configuration is defined by the parameters and the package filter that the BeanProviderFactory will scan the io.jd package and the passed packages. Thanks to that, the framework only provides beans from the expected packages.
3. The *Reflections* object is created. It will be responsible for performing our query later in the code.
4. The reflections object performs the TYPE\_QUERY. It will create all the *BeanDefinition* instances using static BeanDefinition<?> getInstance(Class<?> e).
5. The method that creates instances of *BeanDefinition* uses the reflection. When there’s an exception, the code wraps it in a custom RuntimeException. The code of the custom exception is [here](https://github.com/JacekDubikowski/build-your-own-framework/blob/main/framework/src/main/java/io/jd/framework/FailedToInstantiateBeanDefinitionException.java).
6. The instance of *BeanProvider* interface in the form of *BaseBeanProvider* instance, which source will be presented in the next few paragraphs.

BaseBeanProvider

So, how is the *BaseBeanProvider* implemented? It is easy to embrace. The source code in the repository is very similar, but (**S** poiler alert!) changed to handle @Transactional in Part 4.

```
class BaseBeanProvider implements BeanProvider {
    private final List<? extends BeanDefinition<?>> definitions;

    public BaseBeanProvider(List<? extends BeanDefinition<?>> definitions) {
        this.definitions = definitions;
    }

    @Override
    public <T> List<T> provideAll(Class<T> beanType) { // 1
        return definitions.stream().filter(def -> beanType.isAssignableFrom(def.type()))
                .map(def -> beanType.cast(def.create(this)))
                .toList();
    }

    @Override
    public <T> T provide(Class<T> beanType) { // 2
        var beans = provideAll(beanType);     // 2
        if (beans.isEmpty()) { // 3
            throw new IllegalStateException("No bean of given type: '%s'".formatted(beanType.getCanonicalName()));
        } else if (beans.size() > 1) { // 4
            throw new IllegalStateException("More than one bean of given type: '%s'".formatted(beanType.getCanonicalName()));
        } else {
            return beans.get(0); // 5
        }
    }
}
```

1. provideAll(Class\<T> beanType) takes all of the *BeanDefinition* and finds all type() methods, which return Class<?> that is a subtype or exactly provided beanType. Thanks to that, it can collect all matching beans.
2. provide(Class\<T> beanType) is also simple. It reuses the provideAll method and then takes all matching beans.
3. The piece of code makes check if there is any bean matching the beanType and throws an exception if not.
4. The piece of code makes check if there is more than one bean matching the beanType and throw an exception if yes.
5. If there is just one matching bean, it is returned.

That’s it!

We got all the parts. Now we should check if the code works.

Did we miss something?

Shouldn’t we have started with tests of the annotation processor? How can the annotation processor be tested?

Annotation processor testing

The annotation processor is rather poorly prepared for being tested. One way to test it is to create a separate project/Gradle or Maven submodule. It would then use the annotation processor, and compilation failure would mean something is wrong. It doesn’t sound good, right?

The other option is to utilise the [compile-testing](https://github.com/google/compile-testing) library created by Google. It simplifies the testing process, even though the tool isn’t perfect. Please find the tutorial on how to use it [here](https://chermehdi.com/posts/compiler-testing-tutorial/).

I introduced both approaches in the article’s repository. The *compile-testing* was used for “unit tests”, and the *integrationTest* module was used for “integration tests”.

You can find the test implementation and configuration in the *framework* subproject’s files below:

1. [build.gradle](https://github.com/JacekDubikowski/build-your-own-framework/blob/main/framework/build.gradle)
2. [test dir](https://github.com/JacekDubikowski/build-your-own-framework/tree/main/framework/src/test/java)
3. [integrationTest dir](https://github.com/JacekDubikowski/build-your-own-framework/tree/main/framework/src/integrationTest/java)

Step 7 – A working framework

In the beginning, there was [*NoFrameworkApp*](https://github.com/JacekDubikowski/build-your-own-framework/blob/main/testapp/src/main/java/io/jd/testapp/NoFrameworkApp.java):

```
public class NoFrameworkApp {
    public static void main(String[] args) {
        ParticipationService participationService = new ManualTransactionParticipationService(
                new ParticipantRepositoryImpl(),
                new EventRepositoryImpl(),
                new TransactionalManagerStub()
        );
        participationService.participate(new ParticipantId(), new EventId());
    }
}
```

If the main is run, we got the three lines printed:

```
Begin transaction
Participant: 'Participant[]' takes part in event: 'Event[]'
Commit transaction
```

It looks like this with [*FrameworkApp*](https://github.com/JacekDubikowski/build-your-own-framework/blob/main/testapp/src/main/java/io/jd/testapp/FrameworkApp.java):

```
public class FrameworkApp {
    public static void main(String[] args) {
        BeanProvider provider = BeanProviderFactory.getInstance();
        ParticipationService participationService = provider.provide(ParticipationService.class);
        participationService.participate(new ParticipantId(), new EventId());
    }
}
```

However, to make it work, we have to add *@Singleton* here and there. Please refer to the source code in the [directory](https://github.com/JacekDubikowski/build-your-own-framework/tree/main/testapp/src/main/java/io/jd/testapp). If we run that main, we will get the same result:

```
Begin transaction
Participant: 'Participant[]' takes part in event: 'Event[]'
Commit transaction
```

Therefore, we can call it a success. The framework works like a charm!

What’s next?

Once you checked the result of running the code from the previous paragraph, you saw there were additional messages. They are about the beginning and committing a transaction.

Handling the transactions is also typical for frameworks. I will cover how to handle transactions in the next article of this series.
