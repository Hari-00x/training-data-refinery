# Training Data Refinery: Progress Log

Scope: one Common Crawl WET file (CC-MAIN-2024-46, segment file 00000), English only.

## Pipeline funnel

| Stage | Script | Records |
|---|---|---|
| Raw WET records | notebooks/inspect_wet.py | 29,800 |
| After clean (length, language, junk phrases, normalize) | scripts/clean.py | ~12,730 |
| After near-duplicate removal (MinHash, 3-word shingles, LSH 0.8) | scripts/dedup.py | 12,447 |

Language detection is slightly non-deterministic (12,713 vs 12,730 kept across runs). Dedup is within one file only, so the 2.2% duplicate rate understates real duplication.

## Quality scorer: iteration history

No human labels exist. Training data is synthetic: each real document is a positive, and a randomly corrupted copy is a negative.

### Run 1: logistic regression, 4 features
Features: avg word length, unique-word ratio, alphabetic ratio, avg sentence length.
Result: scores clustered at 0.49 to 0.55 (median 0.52, max 0.69).
Cause: word shuffling leaves all four features unchanged, so identical inputs carried both labels. Negatives also did not resemble real web junk, and there was no held-out test.

### Run 2: 8 features, held-out test (80/20 split by document)
Overall accuracy 78.42%, but menu_style only 4.50%.
Cause (confirmed by learned weights and per-type feature means): my corruption code used bare split/join, which flattened newlines. Every negative became one very long line, so the model learned "long line = bad". This is shortcut learning.

### Run 3: line-preserving corruptions
Overall accuracy fell to 64.67%. The earlier 78% was inflated by the shortcut.
New problem: repeat_phrase fell to 25.96%.
Likely cause (not verified): unique_ratio is bad at both extremes (repeated text is very low, truncated fragments very high), and a linear model gives one weight per feature, so it cannot express that.

### Run 4: random forest (100 trees, max depth 8)
Overall accuracy 87.67% on held-out documents.

| Kind | Accuracy |
|---|---|
| real | 94.83% |
| repeat_phrase | 71.15% |
| truncate_text | 100.00% |
| corrupt_characters | 35.59% |
| menu_style | 90.09% |
| keyword_list | 100.00% |

Most important features: stopword_ratio 0.30, short_line_ratio 0.23, unique_ratio 0.16.
Score spread on all 12,447 documents: min 0.02, quartiles 0.68 / 0.82 / 0.88, max 0.95.
Spot check: the lowest-scored pages were navigation-heavy listings (an embassy page, a tag archive, a calendar). The highest were mixed: one real blog post, plus a privacy page and a tag page.

## Known limitations

- Accuracy measures detection of my own simulated junk, not real quality.
- Features cannot see character-level noise (corrupt_characters at 35.6%).
- Scores lean high: most real pages pass the "not a simulated corruption" test.
- The final scoring loop includes the ~2,400 training documents, so their scores are slightly optimistic.
- Positives are noisy: the "real" set still contains some junk.

## Lessons

- Inspect outputs and evaluate on held-out data before building on top.
- A metric that drops after a fix can mean the earlier number was inflated.
- Synthetic labels are only as good as their realism.

## Next

Rank-based shard selection (top 50% vs random 50% vs all data), Parquet packing, shard anomaly detection, small-model ablation, Airflow DAG, README.
