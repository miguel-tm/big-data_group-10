
# Batch vs. Streaming Analytics at Scale: A Comparative Study Using Apache Spark

## University of Toronto / University of Waterloo — Winter 2026
**Instructor:** Melissa Singh

## Team Members — Group 10
- Abduljalil Najar
- Haya Tariq
- Oleksiy Kovtonyuk
- Rosy Zhou
- Miguel Morales Gonzalez

---

## Project Overview

This project implements and compares **batch** and **streaming** analytics using Apache Spark on a real-world public dataset (City of Chicago — Traffic Crashes). Both approaches consume the same canonical dataset to highlight differences in **system behavior** (latency, complexity, scalability, fault tolerance) rather than forcing exact output parity.

**Dataset:** City of Chicago — Traffic Crashes – Crashes ([Socrata ID: 85ca-t3if](https://data.cityofchicago.org/Transportation/Traffic-Crashes-Crashes/85ca-t3if))

**Architecture:**
- **Bronze → Silver → Gold** data pipeline
- **Batch path:** Complete historical aggregations
- **Streaming path:** Incremental, event-time windowed aggregations

---

## Repository Structure

```
big-data_group-10/
├── data/
│   ├── checkpoints/                  # Streaming checkpoint state
│   ├── raw/                          # Raw CSV (Bronze)
│   ├── replay/                       # Generated daily replay chunks (Parquet)
│   ├── silver/                       # Canonical Silver Parquet
│   └── stream_in/                    # Streaming input directory (watched)
│
├── notebook/
│   ├── 00_Big_Data-Management_Group10 - CoverPage.ipynb
│   ├── 01_bronze_to_silver.ipynb
│   ├── 02_batch_analysis.ipynb
│   ├── 03_streaming_logic_preview.ipynb
│   ├── 04_orchestration.ipynb
│
├── outputs/
│   ├── batch/                        # Batch Gold outputs
│   └── streaming/                    # Streaming Gold outputs
│
├── src/
│   ├── make_replay_files.py          # Silver → replay chunks
│   ├── dropper.py                    # replay → stream_in (simulated arrival)
│   └── streaming_job.py              # Structured Streaming job
│
├── README.md
└── .gitignore
```

---

## Notebooks & Scripts — Responsibilities

### Notebooks
- **01_bronze_to_silver.ipynb:** ETL — Reads raw CSV, cleans schema, writes Silver Parquet (partitioned by year/month).
- **02_batch_analysis.ipynb:** Batch analytics — Reads Silver, computes aggregations, writes batch Gold outputs, prints summary.
- **03_streaming_logic_preview.ipynb:** Streaming validation — Reads streaming outputs as batch, validates window alignment and schema.
- **04_orchestration.ipynb:** Experiment logbook — Documents batch/streaming runs, captures metrics, provides comparison.

### Scripts
- **src/make_replay_files.py:** Generates replay chunks (daily Parquet) from Silver.
- **src/dropper.py:** Simulates streaming by copying replay chunks into stream_in at intervals.
- **src/streaming_job.py:** Spark Structured Streaming job — watches stream_in, aggregates hourly windows, writes streaming Gold outputs.

---

## Data Model

- **Bronze:** Raw CSV (data/raw/)
- **Silver:** Cleaned, minimal schema Parquet (data/silver/)
- **Gold:** Aggregated outputs (outputs/batch/, outputs/streaming/)

---

## Execution Flow

### 1. One-time Preparation
1. Run `01_bronze_to_silver.ipynb` (creates Silver)
2. Run `02_batch_analysis.ipynb` (creates batch Gold outputs)

### 2. Streaming Experiment Setup
3. Generate replay chunks:
    ```bash
    python src/make_replay_files.py --input data/silver/crashes_parquet --output data/replay --chunking day --overwrite --silver data/silver/crashes_parquet
    ```

### 3. Streaming Experiment (Clean Run)
4. Clear streaming state (optional but recommended):
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

7. Let the system run for a few minutes, then stop dropper.
8. (Optional) Stop and restart streaming_job.py to demo checkpoint recovery.
9. Run `03_streaming_logic_preview.ipynb` and `04_orchestration.ipynb` for validation and summary.

---

## Windows Environment Setup (Summary)

1. **Install Java 11 (Eclipse Temurin recommended)**
2. **Install Hadoop Binaries (winutils.exe, hadoop.dll) for Spark**
3. **Install Anaconda or Python 3.9+**
4. **Install Python dependencies:**
    ```powershell
    pip install pyspark==3.4.0 findspark jupyterlab pandas matplotlib
    ```
5. **Clone this repo and launch JupyterLab**

See the CoverPage notebook for full, step-by-step setup instructions and troubleshooting.

---

## References

- [City of Chicago Open Data Portal — Traffic Crashes – Crashes (85ca-t3if)](https://data.cityofchicago.org/Transportation/Traffic-Crashes-Crashes/85ca-t3if)
- [Apache Spark Structured Streaming Guide](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
