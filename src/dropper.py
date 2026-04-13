#!/usr/bin/env python
""" 
dropper.py

Simulate data-in-motion by atomically copying or moving replay Parquet files
into a directory watched by Spark Structured Streaming.

Uniqueness tweak:
- The destination filename is prefixed with the replay chunk folder name
  (e.g., chunk_key=2022-01-01__part-00021-....parquet) to avoid collisions.

This script does NOT use Spark.
"""

import argparse
import logging
import shutil
import time
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description="Simulate file arrival for Structured Streaming")
    p.add_argument("--source", required=True, help="Directory containing replay chunk folders/files")
    p.add_argument("--dest", required=True, help="Streaming input directory being watched by Spark")
    p.add_argument("--interval-seconds", type=int, default=5, help="Seconds between drops (default: 5)")
    p.add_argument("--move", action="store_true", help="Move files instead of copying (default: copy)")
    return p.parse_args()


def atomic_transfer(src: Path, dest: Path, move: bool):
    """Atomic copy/move into destination.

    Strategy:
    1) copy/move to a temporary name
    2) rename to final name (atomic on most file systems)
    """
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    if move:
        shutil.move(str(src), str(tmp))
    else:
        shutil.copy2(str(src), str(tmp))
    tmp.rename(dest)


def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    source_dir = Path(args.source)
    dest_dir = Path(args.dest)
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Deterministic order: sorted by full path
    parquet_files = sorted([p for p in source_dir.rglob("*.parquet") if p.is_file()])

    if not parquet_files:
        logging.warning("No .parquet files found under %s", source_dir)
        return

    logging.info("Starting dropper")
    logging.info("Replay source : %s", source_dir)
    logging.info("Stream input  : %s", dest_dir)
    logging.info("Interval (s)  : %s", args.interval_seconds)
    logging.info("Mode          : %s", "move" if args.move else "copy")
    logging.info("Files to drop : %d", len(parquet_files))

    for i, src_file in enumerate(parquet_files, start=1):
        # Prefix with the immediate parent folder name (e.g., chunk_key=YYYY-MM-DD)
        chunk_folder = src_file.parent.name
        safe_name = f"{chunk_folder}__{src_file.name}"
        dest_file = dest_dir / safe_name

        logging.info("Dropping %d/%d: %s", i, len(parquet_files), safe_name)
        atomic_transfer(src_file, dest_file, move=args.move)
        time.sleep(args.interval_seconds)

    logging.info("Dropper completed successfully")


if __name__ == "__main__":
    main()
