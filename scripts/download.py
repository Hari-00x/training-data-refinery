import os
import shutil
import requests

BASE_URL = "https://data.commoncrawl.org/"
WET_PATH = (
    "crawl-data/CC-MAIN-2024-46/segments/1730477027552.27/wet/"
    "CC-MAIN-20241101184224-20241101214224-00000.warc.wet.gz"
)
raw_dir = "../data/raw"


def download_wet():
    os.makedirs(raw_dir, exist_ok=True)
    url = BASE_URL + WET_PATH
    final_path = os.path.join(raw_dir, os.path.basename(WET_PATH))
    temp_path = final_path + ".part"

    if os.path.exists(final_path):
        print(f"Already downloaded, skipping: {final_path}")
        return

    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        expected = response.headers.get("Content-Length")
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(response.raw, f)

    actual = os.path.getsize(temp_path)
    if expected is not None and actual != int(expected):
        os.remove(temp_path)
        raise RuntimeError(f"Size mismatch: expected {expected}, got {actual}")

    os.rename(temp_path, final_path)
    print(f"Downloaded {final_path} ({actual} bytes)")


if __name__ == "__main__":
    download_wet()
