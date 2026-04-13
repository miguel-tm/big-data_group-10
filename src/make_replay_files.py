#!/usr/bin/env python
"""
make_replay_files.py

Generate deterministic replay chunks from the Silver Parquet dataset.
This script is OFFLINE (no streaming) and safe to re-run.
"""

import argparse
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, date_trunc


def parse_args():
    p = argparse.ArgumentParser(description="Generate replay files from Silver Parquet")
    p.add_argument("--input", required=True, help="Path to Silver Parquet dataset")
    p.add_argument("--output", required=True, help="Path to write replay files")
    p.add_argument("--chunking", choices=["day", "week"], default="day")
    p.add_argument("--overwrite", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    spark = SparkSession.builder.appName("MakeReplayFiles").getOrCreate()

    df = spark.read.parquet(args.input)

    if args.chunking == "day":
        df = df.withColumn("chunk_key", to_date(col("CRASH_DATE")))
    else:
        df = df.withColumn("chunk_key", date_trunc("week", col("CRASH_DATE")))

    mode = "overwrite" if args.overwrite else "errorifexists"

    (
        df.write
        .mode(mode)
        .partitionBy("chunk_key")
        .parquet(args.output)
    )

    logging.info("Replay files written to %s", args.output)
    spark.stop()


if __name__ == "__main__":
    main()
