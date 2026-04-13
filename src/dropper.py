#!/usr/bin/env python
"""
dropper.py

Simulate data-in-motion by atomically copying replay files
into a directory watched by Spark Structured Streaming.
"""

import argparse
import logging
import shutil
import time
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description="Drop replay files into streaming input dir")
    p.add_argument("--source", required=True, help="Replay files directory")
    p.add_argument("--dest", required=True, help="Streaming input directory")
    p.add_argument("--interval-seconds", type=int, default=5)
    p.add_argument("--move", action="store_true")
    return p.parse_args()


def atomic_transfer(src: Path, dest: Path, move: bool):
    tmp = dest.with_suffix(dest.suffix + '.tmp')
    if move:
        shutil.move(src, tmp)
    else:
        shutil.copy2(src, tmp)
    tmp.rename(dest)


def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    src_dir = Path(args.source)
    dest_dir = Path(args.dest)
    dest_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(p for p in src_dir.rglob('*.parquet') if p.is_file())

    logging.info("Dropping %d files", len(files))

    for i, f in enumerate(files, start=1):
        logging.info("Dropping %d/%d: %s", i, len(files), f.name)
        atomic_transfer(f, dest_dir / f.name, args.move)
        time.sleep(args.interval_seconds)

    logging.info("Dropper completed")


if __name__ == '__main__':
    main()
