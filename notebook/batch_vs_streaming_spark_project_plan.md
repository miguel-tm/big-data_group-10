# Batch vs. Streaming Analytics at Scale (Apache Spark)

**Course:** Big Data Management Systems and Tools  
**Project type:** Data analysis + scalable systems comparison  
**Topic:** *Batch vs. Streaming Analytics at Scale: A Comparative Study Using Apache Spark*  
**Dataset:** City of Chicago — *Traffic Crashes – Crashes* (Socrata ID: **85ca-t3if**)  
**Scope:** **2022–2025** (inclusive)  
**Execution model:** **Hybrid** (4 Jupyter notebooks + 3 Python scripts)  
**Streaming method:** **File-based Spark Structured Streaming** (simulated incremental file arrival)  
**Primary use case:** **Time-based aggregations** (hourly event-time windows; plus daily/monthly batch rollups)  
**Comparison type:** **Behavioral comparison** (not strict output parity)  
**Evaluation dimensions:** **Latency**, **Complexity**, **Scalability considerations**, **Fault tolerance**  

---

## 0. Executive Summary

This project implements and compares **batch** and **streaming** analytics using Apache Spark on a real-world public dataset. Both approaches consume the same canonical dataset (Silver Parquet, 2022–2025) to highlight differences in **system behavior** rather than forcing exact output parity.

- **Batch path (historical):** Spark DataFrames / Spark SQL compute complete aggregates over the full dataset.
- **Streaming path (incremental):** Spark Structured Streaming consumes files as they arrive and produces hourly event-time window aggregates.
- **Architecture framing:** The work follows a simple **Bronze → Silver → Gold** pattern and maps cleanly to a **Lambda Architecture** narrative (batch for completeness, streaming for time-to-first-result).

---

## 1. Final Repository Structure (Authoritative)

> This reflects the final structure used for execution (as implemented).

```text
BIG-DATA_GROUP-10/
├── data/
│   ├── checkpoints/
│   │   └── streaming_job/                 # Structured Streaming checkpoint state
│   ├── raw/
│   │   └── Traffic_Crashes_-_Crashes.csv  # Bronze CSV (unchanged)
│   ├── replay/                            # Generated daily replay chunks (Parquet)
│   ├── silver/                            # Canonical Silver Parquet
│   └── stream_in/                         # Streaming input directory (watched)
│
├── notebook/
│   ├── 01_bronze_to_silver.ipynb
│   ├── 02_batch_analysis.ipynb
│   ├── 03_streaming_logic_preview.ipynb
│   ├── 04_orchestration.ipynb
│   ├── batch_vs_streaming_spark_project_plan.md
│   └── Big_Data-Management_Group10 - CoverPage.ipynb
│
├── outputs/
│   ├── batch/                             # Batch Gold outputs
│   └── streaming/                         # Streaming Gold outputs
│
├── src/
│   ├── make_replay_files.py               # Silver → replay chunks
│   ├── dropper.py                         # replay → stream_in (simulated arrival)
│   └── streaming_job.py                   # Structured Streaming job
│
├── README.md
└── .gitignore
```

---

## 2. Responsibilities (Notebooks vs. Scripts)

### 2.1 Notebooks (4)

#### `01_bronze_to_silver.ipynb` (Run once per dataset snapshot)
**Purpose:** Create canonical **Silver** dataset.

- Read raw CSV (Bronze)
- Select canonical schema (minimal columns)
- Parse `CRASH_DATE` to timestamp
- Filter to 2022–2025 and drop invalid timestamps
- Derive partition columns `year`, `month`
- Write partitioned Parquet to `data/silver/`

**Constraints:**
- No analytics/aggregations
- No streaming logic

---

#### `02_batch_analysis.ipynb` (Batch analytics baseline)
**Purpose:** Produce complete batch **Gold** outputs from Silver.

- Read `data/silver/` only
- Compute time-based aggregations (including hourly event-time windows)
- Write Gold outputs to `outputs/batch/`
- Print a clear batch run summary (rows, time range, elapsed time, outputs)

---

#### `03_streaming_logic_preview.ipynb` (Validation, not orchestration)
**Purpose:** Explain and validate streaming semantics.

- Does **not** run long-lived streaming queries
- Reads **already-produced** streaming outputs as batch (`spark.read.parquet("outputs/streaming")`)
- Validates window alignment (hourly boundaries) and basic sanity invariants
- Confirms streaming output schema matches the batch hourly window output structurally

---

#### `04_orchestration.ipynb` (Experiment logbook + comparison)
**Purpose:** Document the final experiment run and produce report-ready comparison notes.

- Records batch summary (from Notebook 02)
- Records streaming summary (from script execution + output inspection)
- Includes restart / checkpoint observations
- Contains the comparison table and key takeaways for the final report

**Constraint:** No `readStream`, no `awaitTermination`, no orchestration of long-running scripts from the notebook.

---

### 2.2 Scripts (3)

#### `src/make_replay_files.py`
**Purpose:** Generate replay chunks for simulated streaming.

- Reads Silver Parquet (`--input data/silver/...`)
- Creates deterministic chunks by **day** (or week)
- Writes to `data/replay/`

**CLI:**
```bash
python src/make_replay_files.py --input data/silver/crashes_parquet --output data/replay --chunking day --overwrite
```

---

#### `src/dropper.py`
**Purpose:** Simulate data-in-motion.

- Copies one Parquet file every N seconds from `data/replay/` to `data/stream_in/`
- Uses atomic rename to ensure Spark reads complete files
- Ensures destination filenames are unique (prefixes with `chunk_key=YYYY-MM-DD__...`)

---

#### `src/streaming_job.py`
**Purpose:** Long-running Spark Structured Streaming consumer.

- Watches `data/stream_in/` for new Parquet files
- Uses event-time windows on `CRASH_DATE` (1 hour)
- Uses watermarking (1 hour)
- Writes Parquet outputs to `outputs/streaming/` (append mode)
- Uses checkpoints under `data/checkpoints/streaming_job/`

---

## 3. Data Model (Silver Schema)

### 3.1 Bronze
- Raw CSV downloaded from the dataset portal
- Stored unchanged in `data/raw/`

### 3.2 Silver (Canonical)
**Goal:** Keep only the minimum viable columns needed for time-based and context analysis.

**Columns retained:**
- `CRASH_RECORD_ID` (traceability only)
- `CRASH_DATE`
- `INJURIES_TOTAL`, `INJURIES_FATAL`, `MOST_SEVERE_INJURY`
- `WEATHER_CONDITION`, `LIGHTING_CONDITION`, `ROADWAY_SURFACE_COND`
- `PRIM_CONTRIBUTORY_CAUSE`, `SEC_CONTRIBUTORY_CAUSE`

**Storage:**
- Parquet, partitioned by `year` and `month`
- Location: `data/silver/`

### 3.3 Gold (Outputs)
- Batch Gold outputs: `outputs/batch/`
- Streaming Gold outputs: `outputs/streaming/`

---

## 4. Gold Outputs (Final)

### 4.1 Batch Gold outputs (written to `outputs/batch/`)
Final set produced by `02_batch_analysis.ipynb`:

- `crashes_by_hour_window`
- `crashes_by_date`
- `crashes_by_month`
- `injuries_by_month`
- `crashes_by_weather`
- `crashes_by_lighting`
- `crashes_by_roadway`

### 4.2 Streaming Gold outputs (written to `outputs/streaming/`)
Final set produced by `streaming_job.py`:

- `crashes_by_hour_window` (hourly event-time window aggregates)

> Note: We intentionally kept streaming scope focused on hourly window output to emphasize behavioral differences (time-to-first-result, incremental updates, checkpoint recovery).

---

## 5. Authoritative Execution Flow

### 5.1 One-time preparation
1. Run `01_bronze_to_silver.ipynb` (creates Silver)
2. Run `02_batch_analysis.ipynb` (creates batch Gold outputs)

### 5.2 Streaming experiment setup
3. Generate replay chunks:
   ```bash
   python src/make_replay_files.py --input data/silver/crashes_parquet --output data/replay --chunking day --overwrite
   ```

### 5.3 Streaming experiment (clean run)
4. Clear streaming state (optional but recommended for a clean comparison):
   - `outputs/streaming/`
   - `data/stream_in/`
   - `data/checkpoints/streaming_job/`

5. Start streaming consumer (Terminal A):
   ```bash
   python src/streaming_job.py --input data/stream_in --output outputs/streaming --checkpoint data/checkpoints/streaming_job --window-size "1 hour" --trigger "10 seconds"
   ```

6. Start dropper (Terminal B):
   ```bash
   python src/dropper.py --source data/replay --dest data/stream_in --interval-seconds 5
   ```

7. Let the system run for a short controlled period (e.g., a few minutes), then stop dropper.

8. (Fault tolerance demo) Stop and restart `streaming_job.py` using the **same checkpoint** path.

9. Run `03_streaming_logic_preview.ipynb` (validation) and `04_orchestration.ipynb` (summary + comparison).

---

## 6. Behavioral Comparison Framework (What We Measure)

- **Latency:** batch end-to-end runtime vs streaming time-to-first-output and incremental updates
- **Complexity:** number of components and operational steps
- **Scalability considerations:** bounded scan vs continuous ingestion; state size for windows
- **Fault tolerance:** batch rerun vs streaming checkpoint restart

---

## 7. Report Mapping (Required Outline)

The final report follows the required data analysis outline:

- **Objectives:** goals, questions, hypothesis, approach
- **Data Preparation:** data source, cleaning, schema selection, ETL challenges
- **Analysis:** batch outputs + streaming outputs + comparison across the four dimensions
- **Conclusions:** findings, trade-offs, limitations, and recommendations
- **References (MLA):** dataset URL + Spark docs + any external sources

---

## 8. References

- City of Chicago Open Data Portal — Traffic Crashes – Crashes (85ca-t3if):
  https://data.cityofchicago.org/Transportation/Traffic-Crashes-Crashes/85ca-t3if
- Apache Spark Structured Streaming Guide:
  https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html
