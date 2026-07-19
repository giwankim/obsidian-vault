---
title: "Data Engineering For Beginners"
source: "https://de101.startdataengineering.com/"
author:
  - "[[Joseph Machado]]"
published:
created: 2026-07-19
description:
tags:
  - "clippings"
---

> [!summary]
> Free online book by Joseph Machado that teaches data engineering fundamentals for newcomers, emphasizing the "why" behind each tool rather than just the "how". Readers work hands-on with SQL (Spark SQL), Python, the PySpark DataFrame API, Docker, dbt, and Airflow, culminating in a capstone project that combines them all. Exercises run locally via Docker Compose and Jupyter notebooks against the TPC-H bicycle-parts data warehouse dataset.

## Start here

Are you trying to break into a high-paying data engineering job, but

> Don’t know where to start?

> Feel overwhelmed by the amount of tools, systems, topics, frameworks to master

> Trying to switch from an adjacent field, but the switch is harder than you had assumed

Then this book is for you. This book is for anyone who wants to get into data engineering, but feels stuck, confused, and ends up spending a lot of time going in circles. This book is designed to help you lay the foundations for a great career in the field of data.

As a data engineer, your primary mission will be to enable stakeholders to effectively utilize data to inform their decisions. The entirety of this book will focus on how you can do this.

## What you get from reading this book

This book is designed to get you up to speed with the fundamentals of data engineering as quick as possible. With that in mind, the principles of this book are

1. **Spaced learning** Coding as you read the book and exercises to practice understanding
2. **Explain why, along with the how** for each topic covered. Not just SQL, Python, but why DEs use SQL, why is Python essential in data engineering, why the data model is key to an effective data warehouse, etc

The **`outcomes for the reader`**:

1. **Understanding of the fundamentals** of the data engineering stack
2. Experience with the most **in-demand industry tools**: SQL (with Spark), Python, Pyspark Dataframe API, Docker, dbt, & Airflow
3. **Capstone project** that puts together all the in-demand tools, as shown below

![Capstone Architecture](https://de101.startdataengineering.com/images/capstone.png)

Capstone Architecture

## How to use this book

This book is written to guide you from having little knowledge of data engineering to being proficient in the core ideas that underpin modern data engineering.

I recommend reading the book in order and following along with the code examples.

Each chapter includes exercises, for which you will receive solutions via email (Sign up below).

## To LLMs or Not

Every chapter features multiple executable code blocks and exercises. While it is easy to use LLMs to solve them, it is crucial that you try to code them yourself without LLMs (especially if you are starting out in coding).

Working on code without assistance will help you learn the fundamentals and enable you to use LLMs effectively.

## Running code in this book

All the code in this book assumes you have followed the **[setup](https://de101.startdataengineering.com/#setup)** steps below

## Setup

The code for SQL, Python, and data model sections are written using Spark SQL. To run the code, you will need the prerequisites listed below.

**Prerequisites**

1. [git version >= 2.37.1](https://github.com/git-guides/install-git)
2. [Docker version >= 20.10.17](https://docs.docker.com/engine/install/) and [Docker compose v2 version >= v2.10.2](https://docs.docker.com/compose/#compose-v2-and-the-new-docker-compose-command).

**Windows users**: please setup WSL and a local Ubuntu Virtual machine following **[the instructions here](https://ubuntu.com/tutorials/install-ubuntu-on-wsl2-on-windows-10#1-overview)**.

Install the above prerequisites on your ubuntu terminal; if you have trouble installing docker, follow **[the steps here](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-22-04#step-1-installing-docker)** (only Step 1 is necessary).

Fork this repository **[data\_engineering\_for\_beginners\_code](https://github.com/josephmachado/data_engineering_for_beginners_code/tree/main?tab=readme-ov-file#setup)**.
![GitHub Fork](https://de101.startdataengineering.com/images/fork.png) After forking, clone the repo to your local machine and start the containers as shown below:

```bash
# Replace your-user-name with your github username
git clone https://github.com/your-user-name/data_engineering_for_beginners_code.git
cd data_engineering_for_beginners_code
docker compose up -d --build
sleep 30
```

Important

To follow along with the code in this course, please ensure you create the data needed for the exercises. **After starting the Docker container**, do the following.

1. Open Jupyter Lab at [http://localhost:8888](http://localhost:8888/)
2. **`Create the data needed`** for the exercises by running the code in the notebook at [http://localhost:8888/lab/tree/notebooks/starter-notebook.ipynb](http://localhost:8888/lab/tree/notebooks/starter-notebook.ipynb)
3. Open the Airflow UI with [http://localhost:8080/](http://localhost:8080/) and trigger the DAG and ensure that it runs successfully.

![Airflow DAG](https://de101.startdataengineering.com/images/run_dag.png)

Airflow DAG

You can shut down the containers with `docker compose down -v`, when you are done with the course.

## Running code with Jupyter Notebooks

The code in this course can be run via Jupyter Notebooks.

![Notebook Template](https://de101.startdataengineering.com/images/nb_template.png)

Notebook Template

You can make a copy of the [starter\_template.ipynb](https://github.com/josephmachado/data_engineering_for_beginners_code/blob/main/notebooks/starter_template.ipynb) and try out the code in this course. If you are creating a new notebook, make sure to select the `Python 3 (ipykernel)` Notebook.

You can also see the running Spark session at [http://localhost:8080](http://localhost:8080/).

## Data

We will use the TPCH dataset for exercises and examples throughout this book. The TPC-H data represents a bicycle parts seller’s data warehouse, where we record orders, items that make up that order (lineitem), supplier, customer, part (parts sold), region, nation, and partsupp (parts supplier).

**Note**: Have a copy of the data model as you follow along; this will help you understand the examples provided and answer exercise questions.

![Data Model](https://de101.startdataengineering.com/images/tpch_erd.png)

Data Model
