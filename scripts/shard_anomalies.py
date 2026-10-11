import glob
import json
import os
import statistics
from collections import Counter
from urllib.parse import urlparse
import pyarrow.parquet as pq

ARM = "all"
shards_dir = f"../data/processed/shards/{ARM}"
report_file = "../data/processed/shard_report.json"

SHARD_SIZE = 1000
Z_THRESHOLD = 3.5
MAX_DOMAIN_SHARE = 0.05
Z_METRICS = ["median_length", "mean_score", "short_doc_share"]


def shard_stats(path):
    table = pq.read_table(path)
    lengths = table.column("length").to_pylist()
    scores = table.column("quality_score").to_pylist()
    urls = table.column("url").to_pylist()
    n = len(lengths)

    domains = Counter(urlparse(u).netloc for u in urls)

    return {
        "shard": os.path.basename(path),
        "n_docs": n,
        "mean_length": statistics.mean(lengths),
        "median_length": statistics.median(lengths),
        "mean_score": statistics.mean(scores),
        "short_doc_share": sum(l < 500 for l in lengths) / n,
        "top_domain_share": domains.most_common(1)[0][1] / n,
    }


def detect_anomalies():
    paths = sorted(glob.glob(os.path.join(shards_dir, "*.parquet")))
    stats = [shard_stats(p) for p in paths]
    full = [s for s in stats if s["n_docs"] == SHARD_SIZE]

    print(f"{'shard':22s}{'docs':>6s}{'med_len':>9s}{'mean_score':>11s}"
          f"{'short%':>8s}{'topdom%':>9s}  flags")

    for s in stats:
        s["flags"] = []
        evaluated = s["n_docs"] == SHARD_SIZE

        if evaluated:
            others = [o for o in full if o is not s]
            for m in Z_METRICS:
                values = [o[m] for o in others]
                mean = statistics.mean(values)
                std = statistics.pstdev(values)
                if std == 0:
                    continue
                z = (s[m] - mean) / std
                if abs(z) > Z_THRESHOLD:
                    s["flags"].append(f"{m} (z={z:+.1f})")

            if s["top_domain_share"] > MAX_DOMAIN_SHARE:
                s["flags"].append(f"top_domain_share ({s['top_domain_share']:.1%})")

        note = "" if evaluated else " [partial shard, not evaluated]"
        print(f"{s['shard']:22s}{s['n_docs']:6d}{s['median_length']:9.0f}"
              f"{s['mean_score']:11.3f}{s['short_doc_share']:8.1%}"
              f"{s['top_domain_share']:9.1%}  {', '.join(s['flags']) or '-'}{note}")

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print(f"\nReport written to {report_file}")


if __name__ == "__main__":
    detect_anomalies()
