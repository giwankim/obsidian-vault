---
title: "How Debezium Works"
source: "https://datamethods.substack.com/p/how-debezium-works?utm_source=post-email-title&publication_id=5418758&post_id=204311430&utm_campaign=email-post-title&isFreemail=true&r=8x3s&triedRedirect=true&utm_medium=email"
author:
  - "[[Jordan Goodman]]"
published: 2026-07-01
created: 2026-07-01
description: "Used by Airbyte, Apache Flink, and Google BigQuery as a core dependency in production, Debezium is an open source distributed platform for change data capture."
tags:
  - "clippings"
---

> [!summary]
> Debezium is an open-source distributed change-data-capture platform that reads committed changes from a database's transaction log (Postgres WAL, MySQL binlog, SQL Server/Oracle/Mongo equivalents) and converts them into structured before/after events, typically published to Kafka via Kafka Connect. Reliable CDC requires far more than log reading: initial snapshots, offset management, schema history, transaction ordering, queue backpressure, and crash recovery. Because offsets are saved only *after* events reach durability, Debezium favors at-least-once (duplicate) delivery — so downstream consumers must be idempotent.

Used by Airbyte, Apache Flink, and Google BigQuery as a core dependency in production, Debezium is an open source distributed platform for change data capture.

Debezium captures committed database changes and turns them into structured events.

It is commonly used to move inserts, updates, and deletes from operational databases into Kafka, data warehouses, search systems, caches, and other downstream platforms.

The basic flow is:

- source database
- transaction log
- Debezium connector
- event queue
- Kafka or another destination
- saved source position

The output looks simple, but reliable change data capture requires more than reading a database log.

Debezium must also handle initial snapshots, transaction order, schema changes, restarts, duplicate delivery, source-log retention, and downstream slowdowns.

**The database is the source of truth**

Debezium captures changes after the source database accepts them.

It does not capture a button click, an API request, or an ORM method call. It captures the committed result of those operations.

Different databases expose committed changes in different ways:

- PostgreSQL: write-ahead log and logical replication
- MySQL: binary log
- SQL Server: CDC change tables populated from the transaction log
- Oracle: redo logs
- MongoDB: change streams

Debezium provides a connector for each supported database. Each connector understands the source-specific log format and converts it into a more consistent event structure.

Every connector must solve the same general problems:

- Where should reading begin?
- How is the existing table state copied?
- How are new changes captured without a gap?
- How are transactions ordered?
- How are schema changes tracked?
- How is progress saved?
- What happens after a crash?

**How Debezium is deployed**

Debezium is most commonly run through Kafka Connect.

Kafka Connect manages:

- connector configuration
- connector processes
- offset storage
- serialization
- Kafka publication
- worker status
- restarts and failover

Debezium can also run through Debezium Server or Debezium Engine.

Debezium Server reads from a source connector and sends records directly to a supported destination without requiring a user-managed Kafka Connect deployment.

Debezium Engine embeds a connector inside a Java application. This gives the application more control, but it also makes the application responsible for event handling, offset storage, acknowledgement, and recovery.

The connector is only one part of the delivery system. Reliability also depends on where offsets are stored and whether the destination has safely accepted an event.

**The initial snapshot**

A database transaction log contains changes. It does not necessarily contain a complete copy of every current row.

When Debezium starts against an existing database, it normally needs to create a baseline before it can process new changes. This baseline is the initial snapshot.

The simplified process is:

- Open a consistent view of the source database.
- Record the current source-log position.
- Read the selected tables.
- Emit each existing row as a snapshot record.
- Start streaming new changes from the recorded position.

The important requirement is that no committed change can be lost between the snapshot and the start of streaming.

Snapshot records typically use the operation code r, meaning that the row was read from the existing table state rather than created by a new insert.

For large tables, Debezium can use incremental snapshots. Instead of copying an entire table in one operation, it reads the table in smaller key ranges while normal CDC continues.

That creates a coordination problem: a row might be updated while its range is being copied. Debezium compares the snapshot rows with live changes during that window and avoids emitting an older snapshot row after a newer update.

**Reading the transaction log**

After the snapshot, Debezium continuously reads the source database’s change mechanism.

**PostgreSQL**

PostgreSQL writes changes to the write-ahead log, usually called the WAL.

The WAL exists primarily for durability and crash recovery. PostgreSQL records a change in the WAL before the related table page is written to permanent storage. If the server crashes, PostgreSQL can replay WAL records and recover committed changes.

Debezium does not usually parse raw physical WAL records directly. PostgreSQL logical replication converts WAL activity into logical messages describing table changes.

The main PostgreSQL objects involved are:

- publication: Defines which tables are exposed for logical replication.
- replication slot: Stores the consumer position and retains required WAL.
- replica identity: Defines how updates and deletes identify a row.
- LSN: The ordered position in the PostgreSQL WAL.

The replication slot is operationally important. If Debezium stops reading, PostgreSQL may continue retaining WAL for the slot. If the connector remains offline long enough, retained WAL can consume the database server’s disk.

**MySQL**

MySQL writes row changes to the binary log, or binlog.

The connector reads events for:

- inserts
- updates
- deletes
- transaction commits
- binlog rotation
- schema changes

A MySQL source position may include the binlog filename, byte offset, row position, and GTID information.

The connector also needs to know the table definition that applied when each event was written. A column position in an older binlog event may refer to a different schema than the current table definition.

**The event pipeline**

The source-specific connector reads and decodes database changes, but it does not send each record directly to the destination.

The internal flow is roughly:

- database reader
- Debezium event conversion
- bounded queue
- runtime polling
- transformation and serialization
- destination

The queue separates database reading from destination writing.

This matters because source databases and downstream systems run at different speeds. Debezium may be able to read changes faster than Kafka or another sink can accept them.

The queue has a fixed capacity. When it becomes full, Debezium slows or pauses reading from the source.

This is called backpressure.

- queue fills
- source reading slows
- replication lag increases
- source logs are retained longer

Backpressure protects the Debezium process from unlimited memory use, but it does not eliminate the pressure. It moves the problem toward source-log retention and replication lag.

**Event structure**

A Debezium row event usually has a key and a value.

The key normally comes from the source table’s primary key:

{

“order\_id”: 1001

}

The value contains the row before and after the change, along with source metadata:

{

“before”: {

“order\_id”: 1001,

“status”: “pending”

},

“after”: {

“order\_id”: 1001,

“status”: “shipped”

},

“source”: {

“connector”: “postgresql”,

“database”: “sales”,

“schema”: “public”,

“table”: “orders”,

“transaction\_id”: 81293,

“lsn”: 238492936

},

“op”: “u”

}

Common operation codes are:

- c: insert
- u: update
- d: delete
- r: snapshot read
- t: truncate, where supported

The source database controls how complete the before image is.

For PostgreSQL, replica identity determines which old values are available for updates and deletes. For MySQL, binlog row-image settings affect the amount of old and new row data included.

Kafka deployments may also produce a tombstone after a delete. A tombstone has the same key as the deleted record and a null value. Kafka log compaction can use it to remove older records for that key.

**Offsets**

An offset is Debezium’s saved source position.

It answers the question: Where should this connector resume after a restart?

The exact value depends on the database.

PostgreSQL:

- WAL position or LSN
- transaction state
- snapshot state

MySQL:

- binlog filename
- byte position
- row number
- GTID state
- snapshot state

A reliable delivery sequence is:

- Read a source change.
- Convert it into an output event.
- Make the event durable in the destination.
- Save the matching source offset.
- Acknowledge progress to the source when required.

If Debezium publishes an event and crashes before saving the offset, the event may be published again after restart.

This produces at-least-once delivery.

If Debezium saved the offset before the event became durable, a crash could cause the event to be skipped permanently. Debezium is designed to prefer duplicate delivery over silent loss.

Downstream systems should therefore assume that duplicate events are possible.

Common ways to handle duplicates include:

- primary-key merges
- event identifiers
- source positions
- idempotent writes
- deduplication windows

Kafka Connect can provide stronger source-record and offset coordination in supported exactly-once configurations. That guarantee ends at the Kafka boundary. A downstream database still needs its own transactional or idempotent loading logic.

**Schema history**

An offset tells Debezium where to resume. It does not always tell Debezium how the table was structured at that position.

Assume a table originally contains:

- id
- name
- Later, a column is added:
	- id
		- name
		- status

If the connector restarts from a position before the schema change, it must interpret older records using the old two-column structure. Reading only the current three-column schema could decode older data incorrectly.

Debezium maintains schema information as it processes changes. Some connectors also store an internal schema history containing table definitions and schema changes associated with source-log positions.

During restart, Debezium can rebuild the schema that was valid at the saved offset before it resumes reading.

Schema history is connector state, not normal business data. Losing it can make safe recovery impossible even when the source offset is still available.

PostgreSQL logical replication sends relation metadata through the replication stream, so its behavior differs from MySQL and several other connectors. The general requirement remains the same: every log event must be decoded using the correct schema version.

**Transactions**

A source transaction may update several rows across several tables.

Debezium preserves the source order of those changes and can attach transaction metadata such as:

- transaction ID
- event order within the transaction
- number of events in the transaction
- begin and end markers

This allows a consumer to identify which events belonged to the same source transaction.

It does not automatically make the destination transactionally atomic. A sink must explicitly buffer and commit a group of events together if it needs the destination to preserve the same all-or-nothing boundary.

Long-running or very large transactions can increase memory use, temporary storage, and replication latency because the connector may need to retain transaction context until the source commits or rolls back.

**Heartbeats and signals**

A database may be active while none of the selected tables are changing. In that case, the connector still needs a way to show that it is alive and advance its saved position.

Heartbeat events periodically record the current source position.

They are useful for:

- monitoring connector activity
- advancing offsets
- advancing PostgreSQL slot feedback
- reducing unnecessary source-log retention
- measuring lag

Signals are control messages sent to Debezium. They can request actions such as starting an incremental snapshot without replacing the entire connector configuration.

These features are important in production because CDC connectors need operational controls, not only data extraction logic.

Transformations and serialization

Debezium creates a full change-event envelope. Kafka Connect or another runtime can transform that event before writing it to the destination.

A common transformation extracts only the after state:

{

“order\_id”: 1001,

“status”: “shipped”

}

This format is easier for many consumers, but it can remove useful information:

- old row values
- operation type
- source position
- transaction metadata
- snapshot status
- delete handling
- source timestamps

The full Debezium envelope is more useful for auditing, debugging, replay, and transaction reconstruction.

After transformations, the runtime serializes events as JSON, Avro, Protobuf, or another configured format.

**Failure Behavior**

Debezium is designed to recover from interruptions, but recovery depends on the relationship between the last event delivered, the last source offset saved, and the source log still available.

**Event Published Before the Offset Is Saved**

An event may reach the destination just before Debezium crashes, but the corresponding source offset may not yet be persisted.

When the connector restarts, it resumes from the older saved offset and emits the event again.

**Consequence:** Duplicate delivery is possible, so downstream systems should use idempotent writes, primary-key merges, or another deduplication method.

**Saved Source Position Is No Longer Available**

Debezium resumes from a stored log position. If the source database deletes or recycles the required transaction-log segment before the connector restarts, that position can no longer be read.

**Consequence:** The connector cannot continue from its saved offset and may require a new snapshot or manual state recovery.

**PostgreSQL Replication Slot Falls Behind**

A PostgreSQL replication slot prevents the database from deleting WAL that Debezium has not yet confirmed.

If Debezium is offline or processing too slowly, PostgreSQL continues retaining the required WAL.

**Consequence:** WAL usage grows on the source server and can eventually consume all available disk space.

**MySQL Binlog Expires**

MySQL retains binary logs for a configured period. If the binlog file or GTID range containing Debezium’s saved position is removed, the connector loses its restart point.

**Consequence:** Streaming cannot resume from the saved position, and a new snapshot may be required.

**Schema History Is Missing**

The source offset tells Debezium where to resume, but it does not always provide enough information to interpret the table structure at that point in time.

If the required schema history is missing or corrupted, Debezium may be unable to decode older log records safely.

**Consequence:** Connector startup may fail rather than risk producing incorrectly mapped data.

**Destination Processing Slows Down**

If the destination processes events more slowly than Debezium reads them, the connector’s internal queue begins to fill.

Once the queue reaches capacity, Debezium slows or pauses source-log consumption.

**Consequence:** Replication lag increases, and the source database must retain transaction-log data for longer.

**Database Failover**

After a database failover, Debezium must reconnect to a server that exposes compatible transaction history and source metadata.

For PostgreSQL, this includes WAL continuity, publications, replication slots, and database identity. For MySQL, GTIDs generally make failover easier than server-specific binlog filenames and offsets.

**Consequence:** If the replacement server cannot provide the expected log history or identifiers, the connector may be unable to resume without state repair or a new snapshot.

**Monitoring**

A production Debezium deployment should monitor both the connector and the source database.

Important connector metrics include:

- task status
- snapshot progress
- current source offset
- source-to-connector lag
- queue capacity
- records processed per second
- error count
- heartbeat activity
- transaction size and duration
- destination publication latency

Important source metrics include:

- PostgreSQL retained WAL
- PostgreSQL replication-slot lag
- MySQL binlog retention
- SQL Server CDC cleanup windows
- Oracle redo availability
- database disk usage

A connector process can be running while no longer making useful progress. The important questions are:

- Is the source offset advancing?
- Is the destination receiving events?
- Is the required source log still available?
- Is replication lag increasing?
- Is the source retaining an unsafe amount of log data?

**The practical model**

Debezium performs six core jobs:

- Copy the existing table state through a consistent snapshot.
- Continue from the exact log position associated with that snapshot.
- Convert database-specific changes into a common event format.
- Track the schema and transaction context required to interpret changes.
- Save source offsets only after events reach the required durability point.
- Recover through replay when delivery status is uncertain.

The database-log reader is only one part of the system. The harder work is coordinating snapshots, offsets, schemas, queues, acknowledgements, source retention, and restarts without losing committed changes.
