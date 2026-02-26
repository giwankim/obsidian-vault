---
title: "Free Airflow 3.0 Tutorial"
source: "https://www.startdataengineering.com/post/airflow-tutorial/"
author:
  - "[[Joseph Machado]]"
published:
created: 2026-02-26
description: "Master the core concepts of Apache Airflow 3.0 — from your first DAG to advanced scheduling — with hands-on code examples.”"
tags:
  - "clippings"
---
> [!summary]
> A hands-on tutorial covering Apache Airflow 3.0 core concepts including DAG creation, XComs for cross-task communication, dynamic task mapping, and scheduling via cron timetables and asset-based triggers. It also explains how executors run tasks in parallel, how the dag-processor and scheduler work, and how to use the Airflow UI for monitoring and backfills.

## Airflow Is a Must-Know for Data Engineers

If you are a data engineer or looking to break into Data Engineering, Apache Airflow is a must know. If you are worried that

> You don’t have enough time to learn Apache Airflow

> Just using cronjobs will not make your resume pop

This post is for you. Understanding the concepts of Orchestration and scheduling with Apache Airflow will significantly improve your chances in your next data engineering interview.

By the end of this post, you will have learned **how to use Airflow and how Airflow runs your code**, giving you sufficient knowledge to dig into any Airflow system.

To follow along with code you need to do the following.

**Prerequisites**

1. [Docker version >= 20.10.17](https://docs.docker.com/engine/install/) and [Docker compose v2 version >= v2.10.2](https://docs.docker.com/compose/#compose-v2-and-the-new-docker-compose-command).

Clone and start the container as shown below:

```bash
git clone https://github.com/josephmachado/airflow-tutorial.git
cd airflow-tutorial
docker compose up -d --build
```

Open Airflow at [http://localhost:8080](http://localhost:8080/) and stop containers after you are done with `docker compose down`.

## Define Pipelines With DAG

A directed acyclic graph (DAG) is a one-way graph with no cycles, making it ideal for representing batch data pipelines.

Use the DAG function or `@dag` decorator to define a DAG in Airflow. Define properties and attributes for your DAG, such as: `dag_id`, `description`, `start_date`, `end_date`, `dagrun_timeout` and many more [shown here](https://airflow.apache.org/docs/task-sdk/stable/api.html#airflow.sdk.DAG).

### Use XComs to Communicate Across Tasks

Tasks are meant to be self-contained. However, there are cases where cross-task communication is required. This is where XComs helps.

`XComs is a key-value pair` system into which a task can add a value, and another task can then read that value with its key. In the above `simple_etl` our tasks move data between each other in this code block:

```python
# Wire up the pipeline
    raw = extract()
    cleaned = transform(raw)
    load(cleaned)
```

We can see the XComs value in the UI as shown below.

![XComs](https://www.startdataengineering.com/post/airflow-tutorial/xcoms.png)

XComs

By default, XComs are stored in the Airflow DB, so it is not recommended for large values. For large values, you would have to define a [custom XComs backend, such as cloud storage](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/xcoms.html#custom-xcom-backends).

### Create DAGs Dynamically

We can dynamically generate DAGs using standard Python. See the below code from `./airflow/dags/create_dynamic_dags.py`.

![Dynamic DAG](https://www.startdataengineering.com/post/airflow-tutorial/dynamic_dag.png)

Dynamic DAG

Within a DAG, we can dynamically create tasks as shown below.

```python
"""
Simple Dynamic DAG — Airflow 3
code at: ./airflow-tutorial/blob/main/airflow/dags/dynamic_dag.py
Each item in the list gets its own task instance at runtime.
"""

import pendulum
from airflow.sdk import dag, task

@dag(
    dag_id="simple_dynamic_dag",
    schedule="@daily",
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    tags=["dynamic", "example"],
)
def simple_dynamic():
    @task()
    def process(table: str) -> str:
        """
        This task is dynamically mapped — one instance per item.
        Airflow creates 3 task instances at runtime:
          process-orders, process-customers, process-products
        """
        result = f"Processed table: {table.upper()}"
        print(result)
        return result

    @task()
    def summarise(results: list[str]) -> None:
        """Receives all mapped outputs as a single list."""
        print("Summary:")
        for r in results:
            print(f"  ✓ {r}")

    items = ["orders", "customers", "products"]

    # .expand() is what makes it dynamic —
    # one task instance is created per element in \`items\`
    processed = process.expand(table=items)

    summarise(processed)

simple_dynamic()
```

We can see the `process` task having 3 instances, one per item.

![Task Mapping](https://www.startdataengineering.com/post/airflow-tutorial/task_mapping.png)

Task Mapping

We used a simple mapping to map to 3 elements in a list. However, there are complex task generation strategies .

## DAGs Can Be Scheduled or Set to Run When a Dataset Is Updated

DAGs can be set to run at a given frequency or start in response to an update in a dataset.

### Scheduling DAGs

Important

Data pipelines are designed to process data for some chunk of time. This chunk of time is called the `data interval`.

#### When Data Interval to Be Processed = Pipeline Frequency

Most data pipelines are designed to process data for the most recent time range. This means that if your pipeline runs every day at **12:00 A.M., it is meant to capture yesterday’s data from 12:00:00 AM to 11:59:59 PM yesterday for that run**.

Important

The **data interval** for a `@daily` run will be 12:00:00 AM yesterday to 12:00:00 AM today.

![Data Interval](https://www.startdataengineering.com/post/airflow-tutorial/data_interval.png)

Data Interval

Even if the DAG does not start exactly at 12:00:00 AM every day, your pipeline will need to know the start and end times of the interval to be processed.

Airflow scheduling is built around this concept and provides the start and end times as variables in the DAG. Let’s look at an example.

```python
# Code at ./airflow-tutorial/blob/main/airflow/dags/standard_data_interval_example.py

import pendulum
from airflow.sdk import dag, task, get_current_context
from airflow.timetables.interval import CronDataIntervalTimetable

@dag(
    dag_id="minutely_interval_printer",
    schedule=CronDataIntervalTimetable(
        "* * * * *",  # every minute
        timezone=pendulum.timezone("UTC"),
    ), # this is equivalent to just using cron directly as schedule="* * * * *"
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    tags=["example", "timetable"],
)
def minutely_interval_printer():
    @task()
    def print_interval() -> None:
        context = get_current_context()

        start = context["data_interval_start"]
        end = context["data_interval_end"]
        duration_seconds = (end - start).total_seconds()

        print(f"data_interval_start : {start}")
        print(f"data_interval_end   : {end}")
        print(f"Window duration     : {duration_seconds:.0f} seconds")

    print_interval()

minutely_interval_printer()
```

We can see the `context[data_interval_start]` & `context[data_interval_end]` in the task level logs as shown below.

![Data Interval](https://www.startdataengineering.com/post/airflow-tutorial/data_interval_tt.png)

Data Interval

We use the `CronDataIntervalTimetable` method to define the pipeline frequency. The pipeline frequency is used to derive the data interval.

While cron runs at the same frequency, you can also use `DeltaDataIntervalTimetable` to tell the DAG to run every n(say 30) minutes. Here’s a quick comparison of the two.

| DAG start | 12:38 PM | 12:38 PM |
| --- | --- | --- |
| 1st run | 1:00 PM | 1:08 PM |
| 2nd run | 1:30 PM | 1:38 PM |
| 3rd run | 2:00 PM | 2:08 PM |
| Data window | Fixed clock intervals | Relative to last run |
| Misses 12:38–1:00 PM? | ✅ Yes | ❌ No |

**Key takeaway**: Cron snaps to the clock, so the first 22 minutes of data are lost. Delta starts counting from when you actually turn it on.

#### When Data Interval!= Pipeline Frequency

There are cases where you will want to run your pipelines, but process data for a different data interval (or not need interval logic).

E.g., consider a rolling-window data-interval processing or a pipeline that runs every month but only processes data for the last 4 days, etc.

![Overlapping Data Interval](https://www.startdataengineering.com/post/airflow-tutorial/overlapping_data_interval.png)

Overlapping Data Interval

We can define this with the `trigger pattern`. Let’s look at the example below.

```python
# Code at ./airflow-tutorial/blob/main/airflow/dags/custom_data_interval_example.py

import pendulum
from datetime import timedelta
from airflow.sdk import dag, task, get_current_context
from airflow.timetables.trigger import CronTriggerTimetable

@dag(
    dag_id="custom_data_interval_minutely_interval_printer",
    schedule=CronTriggerTimetable(
        "* * * * *",  # every minute on the hour
        timezone="UTC",
        interval=timedelta(hours=1),  # data window = previous hour → now
    ),
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    tags=["example", "timetable"],
)
def hourly_interval_printer():
    @task()
    def print_interval() -> None:
        context = get_current_context()

        start = context["data_interval_start"]
        end = context["data_interval_end"]

        print(f"data_interval_start : {start}")
        print(f"data_interval_end   : {end}")
        total = int((end - start).total_seconds())
        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f"Window duration : {hours}h {minutes}m {seconds}s")

    print_interval()

hourly_interval_printer()
```

![Cron Trigger](https://www.startdataengineering.com/post/airflow-tutorial/trigger.png)

Cron Trigger

We can see how the pipeline is scheduled every minute, but the data interval is an hour.

### Event Driven DAGs

There are many cases when you want to run a pipeline when the upstream data to that pipeline is updated.

With `asset-based scheduling`, you define the assets a pipeline produces and use them as a trigger for any downstream pipeline. Let’s look at the example below.

![Asset Dags](https://www.startdataengineering.com/post/airflow-tutorial/asset_dags.png)

Asset Dags

1. The asset is identified by a unique url
2. A task outlet tells Airflow that the specified outlet asset is updated
3. The consumer DAG will use the asset as a schedule
4. The `triggering_asset_event` will be filled in by Airflow and have the information about the asset and the DAG that updated it

We can see how an upstream dag run completion triggers a downstream dag.

![Asset Scheduling](https://www.startdataengineering.com/post/airflow-tutorial/asset.png)

Asset Scheduling

When the upstream pipeline completes, the downstream pipeline gets triggered.

Before asset-based scheduling, Airflow used to use

- `TriggerDagRunOperator` task in the upstream DAG to start the downstream DAG.
- `ExternalTaskSensor` task for the downstream DAG to wait for the upstream DAG to finish successfully.

Both of these approaches are hard to maintain and debug.

We can also define the downstream DAG to wait for multiple assets to complete one update before starting.

![Multiple Asset Scheduling](https://www.startdataengineering.com/post/airflow-tutorial/assets_schedule.png)

Multiple Asset Scheduling

We can also combine asset-based scheduling with time-based scheduling to ensure that the workflow remains responsive to data changes and consistently runs regular checks or updates. See for details.

## Run Tasks in Parallel With Executors

Airflow tasks are run in parallel using the [executors](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/index.html).

We use the LocalExecutor, which runs tasks as individual Python processes.

```bash
# Bash Into the Running Docker Container

docker exec -ti airflow-tutorial bash

ps aux | grep '[a]irflow worker' | wc -l # This will show 32 workers

cat airflow.cfg | grep 'parallelism ='
# airflow.cfg Contains Airflows Configuration and

# This Will Shown Parallelism = 32 Corresponding

# To the 32 We See From the Previous Command
```

See a list of executors available [here](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/index.html#). Shown below is a list of popular executors from [Airflow’s 2025 survey](https://airflow.apache.org/blog/airflow-survey-2025/).

![Executor usage](https://www.startdataengineering.com/post/airflow-tutorial/executor_usage.png)

Executor usage

The executors are swappable, so you can start with a LocalExecutor and scale to other executors as needed.

We can use [pools](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/pools.html) to limit the number of tasks that can be run in parallel.

For example, if your Airflow is starting 1000s of tasks, your system resources may get overwhelmed. In such cases, you can create a pool and limit it to 100, so only 100 tasks will run in parallel at any given time.

You can assign higher priority weights to high-urgency tasks.

## Airflow’s Dag Processor Creates DAGs, and the Scheduler Starts Them

When you create a Python file with a DAG definition, the `dag-processor` is responsible for parsing it and creating a DAG. The DAG information is stored in Airflow’s database.

Once the DAGs are created, they are monitored by the `scheduler` process, which checks (by default every minute) whether any DAGs need to be started.

Let’s take a look at these processes as shown below.

```bash
docker exec -ti airflow-tutorial bash

ps aux | grep '[d]ag-processor' # You will see the dag-processor process

ps aux | grep '[a]irflow scheduler' # You will see the scheduler process
```

## See Run Times, Configs, DAG Visualizations, Run Backfills With Airflow UI

Airflow UI enables you to dig into individual DAGs, tasks, check logs, view the code used to create the DAG, etc.

![UI](https://www.startdataengineering.com/post/airflow-tutorial/ui.GIF)

UI

You will also be able to see cross-dag dependencies when using asset-based scheduling.

![Cross DAG Dependency](https://www.startdataengineering.com/post/airflow-tutorial/asset_dag.png)

Cross DAG Dependency

You can also trigger a [backfill](https://www.startdataengineering.com/post/how-to-backfill-sql-query-using-apache-airflow/#what-is-backfilling) from the Airflow UI. Use the Airflow config tab to store variable values and connection credentials that can be reused across DAGs.

## Conclusion

To recap, we saw

1. [How to create pipelines with Airflow DAGs](https://www.startdataengineering.com/post/airflow-tutorial/#define-pipelines-with-dag)
2. [Scheduling a DAG](https://www.startdataengineering.com/post/airflow-tutorial/#scheduling-dags)
3. [Designing a DAG to start when there is an update to upstream data.](https://www.startdataengineering.com/post/airflow-tutorial/#event-driven-dags)
4. [How executors run your tasks](https://www.startdataengineering.com/post/airflow-tutorial/#run-tasks-in-parallel-with-executors)
5. [How DAG processor and scheduler take your Python code and start a DAG](https://www.startdataengineering.com/post/airflow-tutorial/#airflows-dag-processor-creates-dags-and-the-scheduler-starts-them)
6. [How to see run times, configs, DAG visualizations, and run backfills with Airflow UI](https://www.startdataengineering.com/post/airflow-tutorial/#see-run-times-configs-dag-visualizations-run-backfills-with-airflow-ui)

Airflow is a very powerful (& complex) orchestrator and scheduler, use this tutorial to understand how to use Airflow and practice building a portfolio project from [one of these](https://www.startdataengineering.com/post/data-engineering-projects/#projects-from-least-to-most-complex)
