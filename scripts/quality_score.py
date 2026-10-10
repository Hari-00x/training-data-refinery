import json
import re
import random
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

input_file = "../data/processed/deduped_records.jsonl"
output_file = "../data/processed/scored_records.jsonl"

random.seed(0)

STOPWORDS = {"the", "and", "of", "to", "in", "is", "that", "for", "it", "with",
             "as", "on", "was", "are", "this", "be", "by", "at", "or", "from"}


def extract_features(text):
    words = text.split()
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not words or not lines:
        return [0] * 8

    avg_word_len = sum(len(w) for w in words) / len(words)
    unique_ratio = len(set(words)) / len(words)
    alpha_ratio = sum(c.isalpha() for c in text) / len(text)
    digit_ratio = sum(c.isdigit() for c in text) / len(text)
    stopword_ratio = sum(w.lower() in STOPWORDS for w in words) / len(words)

    avg_line_len = sum(len(l) for l in lines) / len(lines)
    short_line_ratio = sum(len(l) < 40 for l in lines) / len(lines)
    punct_end_ratio = sum(l[-1] in ".!?" for l in lines) / len(lines)

    return [avg_word_len, unique_ratio, alpha_ratio, digit_ratio,
            stopword_ratio, avg_line_len, short_line_ratio, punct_end_ratio]


def repeat_phrase(text):
    out = []
    for line in text.split("\n"):
        words = line.split()
        if len(words) < 3:
            out.append(line)
            continue
        phrase = " ".join(words[:3])
        out.append(" ".join([phrase] * max(1, len(words) // 3)))
    return "\n".join(out)


def truncate_text(text):
    return text[:27]


def corrupt_characters(text):
    chars = list(text)
    num_changes = max(1, len(chars) // 10)
    for _ in range(num_changes):
        idx = random.randint(0, len(chars) - 1)
        chars[idx] = ""
    return "".join(chars)


def menu_style(text):
    words = text.split()
    lines = [" ".join(words[i:i+2]) for i in range(0, len(words), 2)]
    return "\n".join(lines)


def keyword_list(text):
    out = []
    for line in text.split("\n"):
        out.append(" ".join(w for w in line.split() if w.lower() not in STOPWORDS))
    return "\n".join(out)


corruptions = {
    "repeat_phrase": repeat_phrase,
    "truncate_text": truncate_text,
    "corrupt_characters": corrupt_characters,
    "menu_style": menu_style,
    "keyword_list": keyword_list,
}


def make_rows(records):
    X = []
    y = []
    kinds = []

    for record in records:
        text = record["text"]

        X.append(extract_features(text))
        y.append(1)
        kinds.append("real")

        name, corrupt_fn = random.choice(list(corruptions.items()))
        X.append(extract_features(corrupt_fn(text)))
        y.append(0)
        kinds.append(name)

    return X, y, kinds


def train_and_score():
    with open(input_file, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f]

    sample = random.sample(records, min(3000, len(records)))
    split = int(len(sample) * 0.8)
    train_records = sample[:split]
    test_records = sample[split:]

    X_train, y_train, _ = make_rows(train_records)
    X_test, y_test, kinds_test = make_rows(test_records)

    model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=0)
    model.fit(X_train, y_train)

    print(f"Overall test accuracy: {model.score(X_test, y_test):.2%}")

    preds = model.predict(X_test)

    for kind in ["real"] + list(corruptions):
        idx = [i for i, k in enumerate(kinds_test) if k == kind]
        correct = sum(preds[i] == y_test[i] for i in idx)
        print(f"  {kind:20s} {correct / len(idx):.2%}  (n={len(idx)})")

    names = ["avg_word_len", "unique_ratio", "alpha_ratio", "digit_ratio",
             "stopword_ratio", "avg_line_len", "short_line_ratio", "punct_end_ratio"]


    print("\nFeature importances:")
    for n, c in zip(names, model.feature_importances_):
        print(f"  {n:18s} {c:.2f}")

    print("\nMean feature values by kind:")

    for kind in ["real"] + list(corruptions):
        rows = [X_test[i] for i, k in enumerate(kinds_test) if k == kind]
        means = [sum(col) / len(col) for col in zip(*rows)]
        print(f"  {kind:20s}", [round(m, 2) for m in means])

    with open(output_file, "w", encoding="utf-8") as outfile:
        for record in records:
            features = extract_features(record["text"])
            score = model.predict_proba([features])[0][1]
            record["quality_score"] = round(score, 4)
            outfile.write(json.dumps(record) + "\n")

    print("Training and scoring complete.")
    print(f"Output written to {output_file}")


if __name__ == "__main__":
    train_and_score()
