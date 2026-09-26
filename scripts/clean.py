from warcio.archiveiterator import ArchiveIterator
from langdetect import detect, LangDetectException
import json
import re

raw_file = "../data/raw/CC-MAIN-20241101184224-20241101214224-00000.warc.wet.gz"
output_file = "../data/processed/cleaned_records.jsonl"

junk_patterns = [
    "404 not found",
    "403 forbidden",
    "page not found",
    "access denied"
]

def is_junk(text):
    lowered = text.lower()
    for pattern in junk_patterns:
        if pattern in lowered:
            return True
    return False

def normalize(text):
    text = re.sub(r"\n{3,}", "\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()

def clean_wet():
    kept = 0
    total = 0

    with open(raw_file, 'rb') as stream, open(output_file, "w") as out:
        for record in ArchiveIterator(stream):
            if record.rec_type != 'conversion':
                continue

            total += 1

            url = record.rec_headers.get_header("WARC-Target-URI")
            content = record.content_stream().read().decode("utf-8", errors="ignore")

            if len(content) < 200:
                continue

            try:
                lang = detect(content)
            except LangDetectException:
                continue

            if lang != "en":
                continue

            if is_junk(content):
                continue

            cleaned = normalize(content)

            record_out = {
                "url": url,
                "text": cleaned,
                "length": len(cleaned)
            }
            out.write(json.dumps(record_out) + "\n")

            kept += 1

    print(f"Total records seen: {total}")
    print(f"Records kept: {kept}")
    print(f"Records dropped: {total - kept}")

if __name__ == "__main__":
    clean_wet()
