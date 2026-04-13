#!/usr/bin/env python
"""
streaming_job.py

Long-running Spark Structured Streaming job.
Reads Parquet files from a directory and writes
hourly event-time window aggregates to Parquet.
"""

import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, window, sum as _sum


def parse_args():
    p = argparse.ArgumentParser(description="Structured Streaming job")
    p.add_argument("--input", required=True, help="Streaming input directory")
    p.add_argument("--output", required=True, help="Gold output directory")
    p.add_argument("--checkpoint", required=True, help="Checkpoint directory")
    p.add_argument("--window-size", default="1 hour")
    p.add_argument("--trigger", default="10 seconds")
    return p.parse_args()


def main():
    args = parse_args()

    spark = SparkSession.builder.appName("StreamingHourlyWindows").getOrCreate()

    schema = spark.read.parquet(args.input).schema

    stream = (
        spark.readStream
        .schema(schema)
        .parquet(args.input)
    )

    agg = (
        stream
        .withWatermark("CRASH_DATE", "1 hour")
        .groupBy(window(col("CRASH_DATE"), args.window_size))
        .agg(
            _sum("INJURIES_TOTAL").alias("injuries_total"),
            _sum("INJURIES_FATAL").alias("injuries_fatal"),
        )
        .withColumnRenamed("window.start", "window_start")
        .withColumnRenamed("window.end", "window_end")
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
