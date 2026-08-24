# `ByteBuffer` vs `byte[]`

- `byte[]` is a raw JVM array: a fixed-length block of bytes with nothing but a `length` and index access.
- `ByteBuffer` (`java.nio`, since Java 1.4) is a cursor over a block of bytes, plus the machinery for reading and writing structured binary data through it.

## The state a buffer carries

A `byte[]` has one number. A `ByteBuffer` has four:

| Field | Meaning |
| --- | --- |
| `capacity` | Total size, fixed at creation. |
| `position` | Where the next relative read/write happens. |
| `limit` | First index that must not be read/written. |
| `mark` | A remembered position you can `reset()` to. |

The cursor is what makes the fill-then-drain sequence work:

```java
ByteBuffer buf = ByteBuffer.allocate(64);
buf.putInt(42);            // relative write; position 0 -> 4
buf.put((byte) 0x7F);      // position 4 -> 5
buf.flip();                // limit = 5, position = 0  ("stop filling, start draining")
int n = buf.getInt();      // relative read; position 0 -> 4
buf.clear();               // position = 0, limit = capacity (does NOT erase data)
```

> [!note] A buffer is always in fill mode or drain mode, and `flip()` is the switch between them.
> `flip()` pins `limit` to wherever you stopped writing and rewinds `position` to zero. Forgetting it is the most common NIO bug: you read the untouched bytes past your data instead of the bytes you just wrote.

- Use `compact()` rather than `clear()` when you drained only part of the buffer and want to keep the remainder. It shifts the unread bytes to the front.
- Relative ops (`getInt()`) mutate `position`; absolute ops (`getInt(4)`) do not. A buffer is never thread-safe for relative ops.

## What `ByteBuffer` adds

- `getLong()` and friends read multi-byte primitives directly, instead of hand-rolling eight shifts and masks over a `byte[]`. `order(ByteOrder.LITTLE_ENDIAN)` flips byte order for the whole buffer; the JVM is big-endian by default regardless of the hardware.
- `slice()`, `duplicate()`, and `asReadOnlyBuffer()` return new buffers that share the same memory with independent cursors. The `byte[]` equivalent, `Arrays.copyOfRange`, actually copies. Sharing is how you parse a framed protocol without allocating per frame.
- `allocateDirect(n)` allocates outside the Java heap. The GC never moves that memory, so the OS can DMA straight into it. Writing a heap buffer to a channel has to copy through a temporary direct buffer first. This is the main performance reason NIO exists.
- `FileChannel`, `SocketChannel`, and friends read and write `ByteBuffer` only. There is no `byte[]` overload.
- `equals`, `hashCode`, and `compareTo` compare the remaining bytes. `byte[]` uses identity equality, which is why `Arrays.equals` exists.

## What `byte[]` still does better

`byte[]` is simpler, has no cursor to get wrong, serializes trivially, works with every legacy API (`InputStream`, `String` constructors, `MessageDigest`), and costs one allocation with no hidden lifecycle.

## Gotchas

- `clear()` does not erase any bytes. It resets the pointers and leaves the old data to be overwritten.
- Do not use a `ByteBuffer` as a map key. Its `hashCode` comes from the current contents between `position` and `limit`, so mutating the buffer or moving its position loses the key inside the `HashMap`. Copy to a `byte[]` for keys.
- `array()` works only when `hasArray()` is true, which means heap buffers. On a direct or read-only buffer it throws `UnsupportedOperationException`. Guard it, or use `get(byte[])`.
- Direct buffers cost more than heap buffers. Allocation is far more expensive than `allocate()`, and native memory is released by a `Cleaner` once the buffer becomes unreachable, so release depends on the GC. Allocating direct buffers per request can exhaust native memory while the heap still looks healthy. Netty pools them and exposes a reference-counted `ByteBuf` for this reason.

## Modern alternatives

- Since Java 9, `MethodHandles.byteArrayViewVarHandle(int[].class, order)` gives the primitive accessors on a plain `byte[]`, so wanting `getInt` over bytes no longer forces a `ByteBuffer` by itself.
- For off-heap work, `MemorySegment` and `Arena` in `java.lang.foreign` (finalized in Java 22) supersede direct buffers: deterministic deallocation, sizes past the 2 GB `int` ceiling, and release that does not wait on the GC.

## Where this shows up

Spring Data Redis splits along this line. The blocking `RedisConnection` works in `byte[]`, while the reactive `ReactiveRedisConnection` works in `ByteBuffer`, because the reactive stack sits on Netty and channel I/O, where the APIs take buffers. See [[redis-template]].
