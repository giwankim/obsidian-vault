# Standard and Custom Events

Event handling in the `ApplicationContext` is provided through the `ApplicationEvent` class and the `ApplicationListener` interface. If a bean that implements the `ApplicationListener` interface is deployed into the context, every time an `ApplicationEvent` gets published to the `ApplicationContext`, that bean is notified.

You can also create and publish your custom events. The following example shows a simple class that extends Spring's `ApplicationEvent` base class:
```kotlin
class BlockedListEvent(
	source: Any,
	val address: String,
	val content: String) : ApplicationEvent(source)
```

To publish a custom `ApplicationEvent`, call the `publishEvent()` method on an `ApplicationEventPublisher`. Typically, this is done by creating a class that implements `ApplicationEventPublisherAware` and registering it as a Spring bean.

```kotlin
class EmailService : ApplicationEventPublisherAware {
	private lateinit var blockedList: List<String>
	private lateinit var publisher: ApplicationEventPublisher

	fun setBlockedList(blockedList: List<String>) {
		this.blockedList = blockedList
	}

	override fun setApplicationEventPublisher(publisher: ApplicationEventPublisher) {
		this.publisher = publisher
	}

	fun sendEmail(address: String, content: String) {
		if (blockedList.contains(address)) {
			publisher.publishEvent(BlockedListEvent(this, address, content))
			return
		}
		// send email...
	}
}
```

At configuration time, the Spring container detects that `EmailService` implements `ApplicationEventPublisherAware` and automatically calls `setApplicationEventPublisher()`.

To receive the custom `ApplicationEvent`, you can create a class that implements `ApplicationListener` and register it as a Spring bean.
```kotlin
class BlockedListNotifier : ApplicationListener<BlockedListEvent> {
	lateinit var notificationAddress: String

	override fun onApplicationEvent(event: BlockedListEvent) {
		// notify appropriate parties via notificationAddress...
	}
}
```

You can register as many event listeners as you wish, but note that, by default, event listeners receive events synchronously. This means that the `publishEvent()` method blocks until all listeners have finished processing the event. One advantage of this synchronous and single-threaded approach is that, when a listener receives an event, it operates inside the transaction context of the publisher if a transaction context is available.

## Annotation-based Event Listeners

 You can register an event listener on any method of a managed bean by using the `@EventListner` annotation. The `BlockedListNotifier` can be rewritten as follows:
 ```kotlin
 class BlockedListNotifier {
	 lateinit var notificationAddress: String

	 @EventListener
	 fun processBlockedListEvent(event: BlockedListEvent) {
		// notify appropriate parties via notificationAddress...
	 }
 }
 ```

## Asynchronous Listeners

If you want a particular listener to process events asynchronously, you can reuse the regular @Async support.
```kotlin
@EventListener
@Async
fun processBlockedListEvent(event: BlockedListEvent) {
	// BlockedListEvent is processed in a separate thread
}
```

## Ordering Listeners

## Generic Events
