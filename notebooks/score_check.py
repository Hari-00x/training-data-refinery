import json

records=[]

with open("../data/processed/scored_records.jsonl","r",encoding="utf-8") as f:
    for line in f:
        records.append(json.loads(line))

scores=sorted(r["quality_score"] for r in records)

n=len(scores)

scores = sorted(r["quality_score"] for r in records)

n = len(scores)

print("count:", n)

print("min:", scores[0])

print("25th percentile:", scores[n // 4])

print("median:", scores[n // 2])

print("75th percentile:", scores[3 * n // 4])

print("max:", scores[-1])

records.sort(key=lambda r: r["quality_score"])

print("\nLOWEST 3")

for r in records[:3]:

    print(r["quality_score"], r["url"], r["text"][:100].replace("\n", " "))

print("\nHIGHEST 3")

for r in records[-3:]:

    print(r["quality_score"], r["url"], r["text"][:100].replace("\n", " "))




