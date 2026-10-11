import json
import math
import os
import random
import pyarrow as pa
import pyarrow.parquet as pq

input_file = "../data/processed/scored_records.jsonl"
shards_dir = "../data/processed/shards"
SHARD_SIZE = 1000
EVAL_FRACTION = 0.1

random.seed(0)


def write_shards(records, arm_name):
    arm_dir = os.path.join(shards_dir, arm_name)
    os.makedirs(arm_dir, exist_ok=True)

    for i in range(0, len(records), SHARD_SIZE):
        chunk = records[i:i + SHARD_SIZE]
        table = pa.Table.from_pylist(chunk)
        path = os.path.join(arm_dir, f"shard_{i // SHARD_SIZE:05d}.parquet")
        pq.write_table(table, path)

    num_shards = math.ceil(len(records) / SHARD_SIZE)
    total_chars = sum(r["length"] for r in records)
    mean_score = sum(r["quality_score"] for r in records) / len(records)
    print(f"{arm_name:10s} docs={len(records):6d} shards={num_shards:3d} "
          f"chars={total_chars:10d} mean_score={mean_score:.3f}")


def make_shards():
    with open(input_file, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f]

    random.shuffle(records)
    n_eval = int(len(records) * EVAL_FRACTION)
    eval_set = records[:n_eval]
    pool = records[n_eval:]

    half = len(pool) // 2
    top_half = sorted(pool, key=lambda r: r["quality_score"], reverse=True)[:half]
    random_half = random.sample(pool, half)

    write_shards(eval_set, "eval")
    write_shards(pool, "all")
    write_shards(top_half, "top50")
    write_shards(random_half, "random50")


if __name__ == "__main__":
    make_shards()
