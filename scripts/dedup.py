from datasketch import MinHash,MinHashLSH
import json

input_file="../data/processed/cleaned_records.jsonl"
output_file="../data/processed/deduped_records.jsonl"

num_perm=128

threshold=0.8

def get_minhash(text,num_perm=num_perm):

    m=MinHash(num_perm=num_perm)

    words=text.split()

    shingles=[" ".join(words[i:i+3]) for i in range(len(words)-2)]

    for shingle in shingles:

        m.update(shingle.encode("utf-8"))

    return m


def dedup_records():

    lsh=MinHashLSH(threshold=threshold, num_perm=num_perm)

    kept=0

    total=0

    with open(input_file,'r',encoding="utf-8") as infile,open(output_file,'w',encoding="utf-8") as outfile:

        for line in infile:

            total+=1

            record=json.loads(line)

            text=record["text"]

            minhash=get_minhash(text)

            result=lsh.query(minhash)

            if result:

                continue

            lsh.insert(f"doc_{total}",minhash)

            outfile.write(json.dumps(record) + "\n")

            kept+=1

    print(f"Total records seen: {total}")

    print(f"Records kept: {kept}")

    print(f"Records dropped: {total - kept}")


if __name__=="__main__":

    dedup_records()













