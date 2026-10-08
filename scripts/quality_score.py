import json

import re

import random

from sklearn.linear_model import LogisticRegression


input_file="../data/processed/deduped_records.jsonl"

output_file="../data/processed/scored_records.jsonl"

random.seed(0)

def extract_features(text):

    words=text.split()

    if not words:

        return [0,0,0,0]

    avg_word_len=sum(len(w) for w in words)/len(words)

    unique_ratio=len(set(words))/len(words)

    alpha_chars=sum(c.isalpha() for c in text)

    alpha_ratio=alpha_chars/len(text) if len(text)>0 else 0

    sentences = re.split(r'[.!?]+', text)

    sentences = [s for s in sentences if s.strip()]

    avg_sentence_len = len(words) / len(sentences) if sentences else 0

    return [avg_word_len, unique_ratio, alpha_ratio, avg_sentence_len]


def shuffle_words(text):

    words=text.split()
    
    random.shuffle(words)

    return " ".join(words)


def repeat_phrase(text):
    
    words=text.split()

    if len(words)<3:
        
        return text
   
    phrase=" ".join(words[:3])

    return (phrase + " ")*30


def truncate_text(text):
    
    return text[:27]


def corrupt_characters(text):

    chars=list(text)

    num_changes=max(1,len(chars)//10)

    for _ in range(num_changes):
        
        idx=random.randint(0,len(chars)-1)

        chars[idx]=""

    return "".join(chars)


def build_training_data():

    X=[]

    y=[]

    with open(input_file, "r", encoding="utf-8") as f:

        records = [json.loads(line) for line in f]

    sample = random.sample(records, min(3000, len(records)))

    corruptions = [shuffle_words, repeat_phrase, truncate_text, corrupt_characters]

    for record in sample:

        text = record["text"]

        X.append(extract_features(text))

        y.append(1)

        corrupt_fn = random.choice(corruptions)

        bad_text = corrupt_fn(text)

        X.append(extract_features(bad_text))

        y.append(0)

    return X, y

def train_and_score():

    X, y = build_training_data()

    model = LogisticRegression()

    model.fit(X, y)

    with open(input_file, "r", encoding="utf-8") as infile, open(output_file, "w", encoding="utf-8") as outfile:

        for line in infile:

            record = json.loads(line)

            text = record["text"]

            features = extract_features(text)

            score = model.predict_proba([features])[0][1]

            record["quality_score"] = round(score, 4)

            outfile.write(json.dumps(record) + "\n")

    print("Training and scoring complete.")

    print(f"Output written to {output_file}")



if __name__ == "__main__":

    train_and_score()
