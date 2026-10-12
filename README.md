# Training Data Refinery

An Airflow pipeline that turns raw Common Crawl web text into cleaned, deduplicated, quality-scored Parquet shards. It is the data-curation step that comes before language-model pretraining.

**Scope:** one Common Crawl WET file (CC-MAIN-2024-46, about 30k documents). More files can be added the same way (see [Limitations](#limitations)).

![DAG graph](docs/dag_graph.png)

## Pipeline

```
download → clean → dedup → score → shards → anomalies
```

| Task | Script | What it does | Result (latest run) |
|---|---|---|---|
| download | `scripts/download.py` | Streams the WET file, skips it if already present, writes to a `.part` file and renames only after a size check | 1 file, ~88 MB |
| clean | `scripts/clean.py` | Keeps English documents of 200+ characters, drops known error-page phrases, normalizes whitespace | 29,800 → 12,733 documents |
| dedup | `scripts/dedup.py` | MinHash (128 permutations) on 3-word shingles, LSH at 0.8 similarity | 12,733 → 12,453 (280 removed) |
| score | `scripts/quality_score.py` | Random-forest quality score (0 to 1) per document | 12,453 scored |
| shards | `scripts/make_shards.py` | Holds out 10% as an eval set and writes 1,000-document Parquet shards for three arms: all, top 50% by score, random 50% | eval, all, top50, random50 |
| anomalies | `scripts/shard_anomalies.py` | Per-shard statistics with leave-one-out z-scores | `shard_report.json` |

## Quality scorer

There are no human labels, so the training data is synthetic: each real document is a positive example, and a randomly corrupted copy (repeated phrase, truncation, deleted characters, menu-style line breaks, stopword removal) is a negative one.

- **Features (8):** average word length, unique-word ratio, alphabetic ratio, digit ratio, stopword ratio, average line length, short-line ratio, share of lines ending in punctuation.
- **Model:** random forest (100 trees, max depth 8).
- **Evaluation:** 600 held-out documents plus a corrupted copy of each. Overall accuracy was **87.7%**.

| Kind | Accuracy |
|---|---|
| real | 94.8% |
| repeat_phrase | 71.2% |
| truncate_text | 100% |
| corrupt_characters | 35.6% |
| menu_style | 90.1% |
| keyword_list | 100% |

These figures come from a development run on an earlier 12,447-document input, so a rerun differs slightly.

**Iteration history** (details in [docs/progress_log.md](docs/progress_log.md)):
1. A first 4-feature logistic regression gave scores clustered at 0.49 to 0.55. Word shuffling left every feature unchanged, so identical inputs carried both labels.
2. The 8-feature version looked better at 78% but failed on menu-style text (4.5%). My corruption code had flattened newlines, so the model learned "one long line = bad" instead of anything about quality (shortcut learning).
3. Fixing the corruptions to preserve line structure dropped accuracy to 65%, which was the honest number. A random forest could handle features that are bad at both extremes, and it recovered to 87.7%.

## Anomaly detection

For each full 1,000-document shard: median length, mean quality score, and share of short documents are compared against the *other* shards (leave-one-out) with a z-score threshold of 3.5. A shard is also flagged if one domain exceeds 5% of its documents. The first version compared each shard against a baseline that included itself and flagged 7 of 12 clean shards (masking, a quantized domain metric, outlier-driven means). In the development run the fixed version flagged one of 11 evaluated shards, which I attribute to sampling variation from a small baseline.

## Run it

Needs Docker Desktop (with WSL2 on Windows) and about 4 GB of RAM available to Docker.

```
git clone https://github.com/Hari-00x/<repo-name>.git
cd <repo-name>
echo -e "AIRFLOW_UID=$(id -u)" > .env
mkdir -p dags logs plugins config data/raw data/processed
docker compose build
docker compose up airflow-init
docker compose up -d
```

Open `localhost:8080` (login `airflow` / `airflow`), unpause `training_data_refinery`, and trigger it. A full run takes roughly 10 minutes.

## Design notes

- **Idempotent download:** reruns skip existing files, and the `.part` plus rename step means a crashed download never leaves a file that looks complete.
- **Zones:** raw files in `data/raw`, intermediate JSON Lines and final Parquet shards in `data/processed`.
- **Parquet for the final shards:** columnar, compressed, and readable one column at a time.
- **Reproducibility:** scoring and sharding use fixed seeds. Language detection is not seeded, so counts shift by a few documents between runs (12,713, 12,730, and 12,733 across three runs).

## Limitations

- **One file, ~30k documents.** Dedup runs within the file only, so the 2.2% duplicate rate understates real duplication across a crawl.
- **The quality scorer measures detection of simulated junk, not real quality.** It is blind to character-level noise (35.6% on corrupted characters), scores skew high, and the final scoring pass includes the ~2,400 documents it trained on.
- **The anomaly detector has only been run on clean shards,** not tested against injected failures, and its baseline is built from about 10 shards.
- **Container dependencies are unpinned** (`docker/requirements.txt`), so versions may differ from the development venv.
- **Local-development setup:** default Airflow credentials and a blank Fernet key. Not for production.

## Next steps

- Ablation: train small language models on `all`, `top50`, and `random50` and compare loss on the held-out eval shards
- Process more WET files and deduplicate across them
- Move storage to S3

## Layout

```
dags/refinery_pipeline.py     Airflow DAG
docker/                       Dockerfile and container requirements
docker-compose.yaml           Airflow stack (Postgres, Redis, Celery)
scripts/                      pipeline stages
notebooks/inspect_wet.py      exploration script
docs/progress_log.md          iteration history
```
