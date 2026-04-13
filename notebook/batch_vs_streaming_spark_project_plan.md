# Batch vs. Streaming Analytics at Scale (Apache Spark)

**Course:** Big Data Management Systems and Tools  
**Project Type:** Data analysis + scalable systems comparison  
**Topic:** *Batch vs. Streaming Analytics at Scale: A Comparative Study Using Apache Spark*  
**Dataset:** City of Chicago — *Traffic Crashes – Crashes* (Socrata ID: **85ca-t3if**)  
**Scope:** **2022–2025 inclusive**  
**Streaming method:** **File-based Structured Streaming** (simulated incremental file arrival)  
**Primary use case:** **Time-based aggregations** (counts + severity + causes over time)  
**Comparison type:** **Behavioral comparison** (not strict output parity)  
**Evaluation metrics:** **Latency**, **Complexity**, **Scalability considerations**, **Fault tolerance**  

---

## 0. Executive Summary (for the report)

**Goal:** Implement two data pipelines over the same real-world dataset slice (2022–2025) and compare **batch** vs **streaming** processing using Spark.

- **Batch layer:** Spark DataFrames/Spark SQL compute historical aggregates over the full dataset.
- **Speed layer:** Spark Structured Streaming produces near-real-time aggregates as new files arrive.
- **Architecture framing:** Map findings to **Lambda Architecture** (batch for completeness/correctness; streaming for time-to-insight).

_[Purpose: This section frames the work for a management audience and makes the rest of the report easy to follow.]_

---

## 1. Project Outline + Flowchart + Descriptions (End-to-End)

> This is both an **ordered project outline** and a **flowchart**: follow steps top-to-bottom. Decision points are included as **Yes/No** branches.

### 1.1 Introduction

**1.1.1 Project Overview**  
_[Explain the problem (batch vs streaming), why it matters, and how Spark supports both. Establish that the study focuses on system behavior and architectural trade-offs.]_

**1.1.2 Dataset Description & Relevance**  
_[Describe the Chicago crash dataset, why it is appropriate for time-based analytics, and why a 2022–2025 subset is a reasonable scale for the assignment. Include dataset URL and extraction date for traceability.]_

**1.1.3 Core Questions (Management-Friendly)**
- *How quickly do we get insights?* (**Latency**)
- *How hard is it to implement and operate?* (**Complexity**)
- *How would each approach scale with more data and higher update rates?* (**Scalability considerations**)
- *How does recovery work after a failure?* (**Fault tolerance**)

_[Purpose: These become the “spine” of your report and ensure you’re optimizing for grading criteria.]_

---

### 1.2 Repo, Roles, and Working Agreements (Group of 5–6)

**1.2.1 Repo Structure (Recommended)**

- `data/raw/` — raw CSV as downloaded (Bronze)
- `data/silver/` — canonical cleaned Parquet partitioned by year/month (Silver)
- `data/replay/` — generated micro-batch files for streaming replay
- `data/stream_in/` — directory watched by Structured Streaming
- `outputs/batch/` — batch results (Gold)
- `outputs/streaming/` — streaming results (Gold)
- `src/` — pipeline code
- `notebooks/` — optional exploration notebooks
- `docs/` — report assets, diagrams, dataset citation

_[Purpose: Keeps work reproducible and prevents “where is the latest file?” chaos in a group setting.]_

**1.2.2 Suggested Roles**
- **Data Engineer (Bronze→Silver):** schema, cleaning rules, Parquet partitioning
- **Batch Pipeline Lead:** batch aggregations + output tables
- **Streaming Pipeline Lead:** file-based streaming + checkpointing + windowed aggregations
- **Instrumentation/Comparison Lead:** metrics collection + latency/complexity/scalability/fault tolerance write-up
- **Report Lead:** management-style narrative + visuals + integration
- *(Optional)* **QA/Integration Lead:** runbook, reproducibility checks, final coherence

_[Purpose: Enables parallel work and reduces integration risk.]_

---

### 1.3 Environment & Configuration

**1.3.1 Spark Setup**  
_[Ensure all members can run the same Spark version and Python environment. Decide local mode vs small cluster. Document how to run each pipeline.]_

**1.3.2 Centralized Configuration (Parameters)**
- `YEAR_START = 2022`, `YEAR_END = 2025`
- `WINDOW_SIZE = '1 hour'` *(recommended)*
- `SLIDE = None` or `'15 minutes'` *(optional)*
- `STREAM_TRIGGER = '10 seconds'` *(tune later)*
- `CHUNKING = 'day'` or `'week'` *(decide during replay generation)*

_[Purpose: Parameterization makes experiments repeatable and helps you generate evidence reliably.]_

---

## 2. Data Acquisition & Storage Zones

### 2.1 Bronze: Raw Data Capture

**2.1.1 Store the Raw CSV (Unmodified)**  
_[Save the manually downloaded CSV to `data/raw/`. Do not overwrite it. This supports traceability and is good practice in data engineering.]_

**2.1.2 Dataset Citation & Provenance**  
_[Create `docs/dataset_citation.md` with dataset URL, Socrata ID (85ca-t3if), extraction date/time, and any notes about updates/amendments.]_

**Decision:** *Do we have written approval for any employer/internal data?*  
- **Yes:** ensure approval is documented  
- **No:** proceed with Chicago open data (recommended)

_[Purpose: Ensures compliance with assignment requirements and avoids delays.]_

---

### 2.2 Silver: Canonical Dataset (CSV → Parquet)

**2.2.1 Schema & Field Selection (Minimum Viable Columns)**

**Keep (final agreed set):**
- **Identifier (traceability):** `CRASH_RECORD_ID`
- **Timestamp:** `CRASH_DATE`
- **Severity:** `INJURIES_TOTAL`, `INJURIES_FATAL`, `MOST_SEVERE_INJURY`
- **Context:** `WEATHER_CONDITION`, `LIGHTING_CONDITION`, `ROADWAY_SURFACE_COND`
- **Causes:** `PRIM_CONTRIBUTORY_CAUSE`, `SEC_CONTRIBUTORY_CAUSE`

_[Purpose: Limits width for performance while keeping enough dimensions to produce meaningful time-based insights.]_

**Decision:** *Keep `CRASH_RECORD_ID`?*  
- **Yes (recommended):** keep it in Silver for debugging and validation; do not group by it  
- **No:** only if you must minimize columns further

_[Purpose: Retaining a UID aids traceability without affecting aggregation performance.]_

**2.2.2 Canonical Cleaning Rules (Minimal + Documented)**
- Parse `CRASH_DATE` as timestamp
- Filter to `YEAR(CRASH_DATE)` in **[2022..2025]**
- Drop rows with invalid/missing `CRASH_DATE`
- Cast injury columns to numeric (handle non-numeric safely)
- Standardize categorical columns (trim, normalize null representations)

**Decision:** *Are there critical null rates in key fields (timestamp/severity)?*  
- **Yes:** define a consistent drop/impute rule and document it  
- **No:** proceed

_[Purpose: Ensures both batch and streaming pipelines operate on stable, consistent types and rules.]_

**2.2.3 Write Partitioned Parquet (Recommended)**
- Output path: `data/silver/crashes_parquet/`
- Partition columns: `year`, `month` derived from `CRASH_DATE`

_[Purpose: Parquet improves Spark performance (columnar reads, compression) and partitioning enables efficient filtering and scalable organization.]_

---

## 3. Batch Pipeline (Historical / Batch Layer)

### 3.1 Batch Objectives

Compute historical aggregates over **all Silver data (2022–2025)**:
- **Crashes per hour/day/week/month**
- **Injuries totals & fatal injuries per window**
- **Top causes over time** (primary and/or secondary)
- Optional: breakdown by weather/lighting/surface

_[Purpose: Batch provides complete-history results and a stable baseline for comparison.]_

### 3.2 Batch Transformations (Spark DataFrames/Spark SQL)

- Read Parquet partitions for 2022–2025
- Create time columns (`year`, `month`, `day`, `hour`) from `CRASH_DATE`
- Aggregations:
  - `count(*) as crashes`
  - `sum(INJURIES_TOTAL)`, `sum(INJURIES_FATAL)`
  - top-N causes per time bucket (optional but recommended)

**Decision:** *Do we need top-N cause ranking?*  
- **Yes:** implement `groupBy(window, cause)` + rank/limit  
- **No:** keep cause as a simple grouped dimension

_[Purpose: Maintains focus on time-based aggregations while optionally enhancing insight.]_

### 3.3 Batch Output & Instrumentation

- Write outputs to `outputs/batch/` (Parquet recommended)
- Capture:
  - start/end timestamps of run
  - total runtime
  - (optional) Spark UI screenshots or logs for evidence

_[Purpose: Collects evidence for the Latency and Scalability sections of the report.]_

---

## 4. Streaming Pipeline (Speed Layer via File-Based Structured Streaming)

### 4.1 Streaming Objectives

Produce near-real-time versions of the batch aggregates as data arrives:
- rolling/windowed crashes per hour
- rolling/windowed injuries totals and fatal injuries per hour
- rolling/windowed top causes (optional)

_[Purpose: Demonstrates time-to-insight and continuous processing behavior.]_

### 4.2 Create Streaming Replay Files (from Silver)

**Approach:** Simulate streaming by feeding the same dataset slice incrementally.

- Read Silver Parquet
- Sort or partition by time (CRASH_DATE)
- Write chunk files to `data/replay/` using a chosen chunking strategy

**Decision:** *Chunk by day or week?*  
- **Day (recommended):** more granular, clearer “arrival” pattern  
- **Week:** fewer files, simpler demo

_[Purpose: A controlled replay makes comparison reproducible and avoids external dependencies like Kafka.]_

### 4.3 File Arrival Simulation (Dropper)

- A simple script copies chunk files from `data/replay/` into `data/stream_in/` at a fixed interval
- This emulates continuous ingestion and allows consistent performance measurements

_[Purpose: Creates velocity while keeping the experiment deterministic and repeatable.]_

### 4.4 Structured Streaming Query (Windows + Checkpointing)

- Create a streaming DataFrame reading from `data/stream_in/`
- Use **event-time windows** on `CRASH_DATE` (e.g., 1 hour)
- Optional watermarking if you simulate late arrivals
- Configure **checkpointing** (`data/checkpoints/...`) for recovery

**Decision:** *Is the stream keeping up with file arrivals?*  
- **No:** increase trigger interval, reduce complexity, or scale resources  
- **Yes:** proceed

_[Purpose: Shows real streaming concepts (event time, windows, fault tolerance) aligned with course content.]_

### 4.5 Streaming Output & Instrumentation

- Write to `outputs/streaming/`
- Capture:
  - time to first output (latency)
  - micro-batch processing times (from progress logs)
  - checkpoint-based restart behavior

_[Purpose: Collects evidence for Latency and Fault tolerance sections.]_

### 4.6 Fault Tolerance Demonstration (Planned Test)

**Test:**
1. Start stream and ingest several chunks
2. Stop the stream intentionally
3. Restart using the same checkpoint directory
4. Observe whether processing resumes without reprocessing already-committed data

_[Purpose: Provides a concrete, reportable example of streaming recovery semantics.]_

---

## 5. Batch vs Streaming: Behavioral Comparison (Core Analysis)

> This is the section most directly tied to your grading rubric: it demonstrates understanding of scaling trade-offs and explains them clearly.

### 5.1 Comparison Framework (Your 4 Metrics)

1) **Latency**  
_[Time to first insight; batch completion time vs streaming incremental availability.]_

2) **Complexity**  
_[Implementation effort (code paths, configuration), operational overhead (checkpointing, triggers, windowing, replay setup).]_

3) **Scalability considerations**  
_[How each approach would scale with higher data volume, more years, or faster arrivals; discuss partitioning, parallelism, and resource behavior conceptually.]_

4) **Fault tolerance**  
_[Batch reruns vs streaming checkpoint/restart behavior; discuss trade-offs.]_

### 5.2 Evidence Collection Plan

- Batch: runtime + output size + notes
- Streaming: time-to-first-output + per-trigger processing time + restart observations

_[Purpose: Ensures the comparison is evidence-based rather than purely opinion.]_

### 5.3 Architecture Interpretation (Lambda Architecture)

- **Batch layer:** recompute accurate aggregates over full history
- **Speed layer:** produce timely incremental aggregates as new events arrive

_[Purpose: Connects your work to course architecture concepts and provides a clean narrative for the report.]_

---

## 6. Conclusions, Recommendations, and Report Assembly

### 6.1 Conclusions (What We Learned)

- Summarize key findings for each metric (latency, complexity, scalability, fault tolerance)
- Identify scenarios where batch is preferable vs streaming

_[Purpose: Converts implementation into insights — essential for a management-style report.]_

### 6.2 Recommendations (Management Briefing Style)

- Recommend batch for retrospective reporting and completeness
- Recommend streaming for time-sensitive monitoring and early warning signals
- Recommend hybrid approach when both are needed (Lambda framing)

_[Purpose: Demonstrates ability to explain technical trade-offs to non-technical stakeholders.]_

### 6.3 Limitations & Future Work

- Dataset amendments/updates may affect “truth” over time; batch recomputation can correct historical results
- Kafka ingestion could be added for a more production-like pipeline

_[Purpose: Shows maturity and awareness of real-world considerations.]_

---

## 2. Report Outline Mapping (to Assignment Requirements)

If you are performing a data analysis, the report should follow:

1) **Objectives** — goals, questions, hypotheses, approach  
2) **Data Preparation** — source, data quality, cleaning, tools, challenges  
3) **Analysis** — trends/patterns + batch vs streaming behavioral comparison  
4) **Conclusions** — learnings + recommendations + limitations  
5) **References** — dataset URL + any external sources

_[Purpose: Ensures the final report complies with the assignment instructions and stays within page limit.]_

---

## 3. Appendix (Implementation Notes / Decisions)

### 3.1 Final Locked Decisions
- Dataset: Chicago Traffic Crashes (85ca-t3if)
- Years: 2022–2025
- Storage: Raw CSV (Bronze) → Partitioned Parquet by year/month (Silver)
- Streaming: file-based streaming (directory watch) with replay file drops
- Comparison: behavioral
- Metrics: latency, complexity, scalability considerations, fault tolerance
- Columns kept: UID + time + severity + context + causes

### 3.2 Suggested Output Tables
- `batch_crashes_by_hour`
- `batch_injuries_by_hour`
- `batch_top_causes_by_day` (optional)
- `stream_crashes_by_hour_window`
- `stream_injuries_by_hour_window`
- `stream_top_causes_window` (optional)

---

## 4. References (to include in report)

- Dataset landing page: https://data.cityofchicago.org/Transportation/Traffic-Crashes-Crashes/85ca-t3if
- Dataset metadata/API (schema, columns): https://data.cityofchicago.org/api/views/85ca-t3if
- Spark Structured Streaming guide: https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html

