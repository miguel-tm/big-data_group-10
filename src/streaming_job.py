#!/usr/bin/env python
"""
streaming_job.py

Long-running Spark Structured Streaming job.
Reads Parquet files from a directory and writes
hourly event-time window aggregates to Parquet.
"""

import argparse
import logging
import os

# ── Windows: set Hadoop/Java env vars before PySpark imports ─────────────────
os.environ.setdefault("JAVA_HOME",   r"C:\Program Files\Eclipse Adoptium\jdk-11.0.30.7-hotspot")
os.environ.setdefault("HADOOP_HOME", r"C:\hadoop")
os.environ["PATH"] = os.environ["HADOOP_HOME"] + r"\bin" + os.pathsep + os.environ.get("PATH", "")

import findspark
findspark.init()

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, window, sum as _sum


def parse_args():
    p = argparse.ArgumentParser(description="Structured Streaming job")
    p.add_argument("--input", required=True, help="Streaming input directory")
    p.add_argument("--output", required=True, help="Gold output directory")
    p.add_argument("--checkpoint", required=True, help="Checkpoint directory")
    p.add_argument("--window-size", default="1 hour")
    p.add_argument("--trigger", default="10 seconds")
    p.add_argument("--silver", required=True, help="Path to Silver Parquet (for schema inference)")
    return p.parse_args()


def main():
    args = parse_args()

    spark = SparkSession.builder.appName("StreamingHourlyWindows").getOrCreate()

    # Before (fragile — fails if stream_in is empty):
    # schema = spark.read.parquet(args.input).schema

    # After (robust — Silver is always populated):
    schema = spark.read.parquet(args.silver).schema

    stream = (
        spark.readStream
        .schema(schema)
        .option("pathGlobFilter", "*.parquet")
        .parquet(args.input)
    )

    agg = (
        stream
        .withWatermark("CRASH_DATE", "1 hour")
        .groupBy(window(col("CRASH_DATE"), args.window_size))
        .agg(
            count("*").alias("crashes"),
            _sum("INJURIES_TOTAL").alias("injuries_total"),
            _sum("INJURIES_FATAL").alias("injuries_fatal"),
        )
        .withColumn("window_start", col("window.start"))
        .withColumn("window_end",   col("window.end"))
        .drop("window")
    )

    query = (
        agg.writeStream
        .format("parquet")
        .outputMode("append")
        .option("checkpointLocation", args.checkpoint)
        .trigger(processingTime=args.trigger)
        .start(args.output)
    )

    query.awaitTermination()


if __name__ == '__main__':
    main()
