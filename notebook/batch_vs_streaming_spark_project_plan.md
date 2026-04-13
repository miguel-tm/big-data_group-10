# Batch vs. Streaming Analytics at Scale (Apache Spark)

**Course:** Big Data Management Systems and Tools  
**Project Type:** Data analysis + scalable systems comparison  
**Topic:** *Batch vs. Streaming Analytics at Scale: A Comparative Study Using Apache Spark*  
**Dataset:** City of Chicago — *Traffic Crashes – Crashes* (Socrata ID: **85ca-t3if**)  
**Scope:** **2022–2025 inclusive**  
**Execution model:** **Hybrid (Jupyter notebooks + Python scripts)**  
**Streaming method:** **File-based Structured Streaming** (simulated incremental file arrival)  
**Primary use case:** **Time-based aggregations** (counts, severity, and causes over time)  
**Comparison type:** **Behavioral comparison** (not strict output parity)  
**Evaluation metrics:** **Latency**, **Complexity**, **Scalability considerations**, **Fault tolerance**  

---

## 0. Executive Summary

This project implements and compares **batch** and **streaming** analytics using Apache Spark on a real-world dataset. Both approaches process the same canonical dataset (2022–2025) to highlight differences in system behavior rather than exact result equivalence.

- **Batch layer:** Spark DataFrames / Spark SQL compute historical aggregates over the full dataset.
- **Speed layer:** Spark Structured Streaming produces near-real-time aggregates as new files arrive.
- **Architecture framing:** Findings are interpreted using **Lambda Architecture** (batch for completeness/correctness, streaming for time-to-insight).

---

## 1. End-to-End Project Flow (Outline + Flowchart)

> The steps below are sequential and form the authoritative execution order. Each step produces artifacts consumed by downstream steps.

---

## 2. Notebook & Script Responsibilities (Hybrid Model)

### 2.1 Jupyter Notebooks (Design, Validation, Explanation)

#### 2.1.1 `01_bronze_to_silver.ipynb` (Run Once)

**Purpose:** Create the canonical **Silver** dataset.

- Read raw CSV (Bronze) ✅
- Select minimal agreed schema ✅
- Parse `CRASH_DATE` and filter to 2022–2025 ✅
- Apply minimal cleaning rules ✅
- Derive `year` and `month` for partitioning ✅
- Write partitioned Parquet (Silver) ✅

**Constraints:**
- No analytics or aggregations
- No streaming logic
- Intended to be executed once per dataset snapshot

Outputs:
- `data/silver/crashes_parquet/year=YYYY/month=MM/`

---

#### 2.1.2 `02_batch_analysis.ipynb`

**Purpose:** Perform historical analytics using batch processing.

- Read Silver Parquet only ✅
- Construct time-based features (hour/day/week/month) ✅
- Compute full-history aggregations ✅
- Optionally visualize trends ✅
- Write batch results to Gold outputs ✅

**Examples:**
- Crashes per hour/day
- Injury totals and fatal injuries over time
- Top contributory causes per time window

Outputs:
- `outputs/batch/`

---

#### 2.1.3 `03_streaming_logic_preview.ipynb`

**Purpose:** Prototype and validate Structured Streaming logic.

- Define streaming schema explicitly ✅
- Configure `readStream` from input directory ✅
- Implement event-time windowed aggregations ✅
- Run short-lived preview queries (console/memory sink) ✅
- Validate semantics (windows, aggregation correctness) ✅

**Constraints:**
- No long-running queries
- No fault tolerance demonstrations
- No checkpoint restart experiments

---

### 2.2 Python Scripts (Operational & Reproducible)

#### 2.2.1 `make_replay_files.py`

- Read Silver Parquet
- Generate deterministic micro-batch chunk files (day or week)
- Write files to `data/replay/`

---

#### 2.2.2 `dropper.py`

- Simulate data-in-motion
- Atomically copy files from `data/replay/` to `data/stream_in/`
- Control arrival rate via time interval

---

#### 2.2.3 `streaming_job.py`

- Long-running Structured Streaming job
- Read from `data/stream_in/`
- Use event-time windows (1 hour)
- Enable checkpointing
- Write streaming outputs to Gold

---

## 3. Data Model & Storage Zones

### 3.1 Bronze (Raw)

- Raw CSV as downloaded
- Stored unchanged for traceability

### 3.2 Silver (Canonical)

**Columns retained:**
- `CRASH_RECORD_ID` (traceability only)
- `CRASH_DATE`
- `INJURIES_TOTAL`, `INJURIES_FATAL`, `MOST_SEVERE_INJURY`
- `WEATHER_CONDITION`, `LIGHTING_CONDITION`, `ROADWAY_SURFACE_COND`
- `PRIM_CONTRIBUTORY_CAUSE`, `SEC_CONTRIBUTORY_CAUSE`

**Storage:**
- Parquet, partitioned by `year` and `month`

### 3.3 Gold (Results)

- Batch outputs
- Streaming outputs

---

## 4. Streaming Replay & Fault Tolerance

- Streaming is simulated using file arrival
- Replay files emulate velocity
- Checkpointing enabled in `streaming_job.py`

**Fault tolerance test:**
1. Start streaming job
2. Ingest several replay files
3. Stop the job intentionally
4. Restart with same checkpoint path

Expected behavior: resume without reprocessing committed data.

---

## 5. Behavioral Comparison Framework

| Dimension | Description |
|---------|-------------|
| Latency | Time to first and incremental results |
| Complexity | Code, configuration, and operational burden |
| Scalability considerations | Conceptual scaling with volume & velocity |
| Fault tolerance | Rerun vs checkpoint recovery |

---

## 6. Report Mapping to Assignment Requirements

- **Objectives:** Define problem, questions, and approach
- **Data Preparation:** Bronze → Silver transformation
- **Analysis:** Batch vs Streaming comparison
- **Conclusions:** Learnings, recommendations, limitations
- **References:** Dataset + external sources

---

## 7. Final Locked Decisions (Summary)

- Hybrid execution model (Notebooks + Scripts)
- Canonical Silver dataset created once
- File-based streaming (no Kafka)
- Behavioral comparison only
- Metrics: latency, complexity, scalability considerations, fault tolerance

---

## 8. References

- Dataset: https://data.cityofchicago.org/Transportation/Traffic-Crashes-Crashes/85ca-t3if
- Spark Structured Streaming Guide: https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html
