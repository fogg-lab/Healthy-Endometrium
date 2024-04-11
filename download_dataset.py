import argparse
import os
import shutil
from time import sleep
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

PROGRESS_INTERVAL = 50
URLS_LIST_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "dataset_urls.txt")
NUM_DOWNLOAD_RETRIES = 6
MAX_WORKERS = 10

def download_file(url, download_dir):
    file_path = os.path.join(download_dir, url.split("cloudfront.net/")[1])
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    success = False
    for attempt in range(NUM_DOWNLOAD_RETRIES):
        try:
            with requests.get(url, stream=True) as r:
                if r.status_code == 200:
                    with open(file_path, "wb") as f:
                        shutil.copyfileobj(r.raw, f)
                    success = True
                else:
                    print(f"Error downloading {url}: Status code {r.status_code}")
        except Exception as e:
            print(f"Error: {e}")
        # Download request failed, wait a sec and try again
        sleep(0.25 * (attempt + 1))
    if not success:
        print(f"Error downloading {url}: Status code {r.status}")
    return success

def download_directory(download_dir):
    os.makedirs(download_dir, exist_ok=True)
    with open(URLS_LIST_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.startswith("https://")]

    save_path = os.path.abspath(download_dir)
    print(f"Downloading {len(urls)} files to: {save_path}...")

    files_downloaded = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {executor.submit(download_file, url, download_dir): url for url in urls}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                success = future.result()
                if success:
                    files_downloaded += 1
                    if files_downloaded % PROGRESS_INTERVAL == 0:
                        progress_percent = round(100 * files_downloaded / len(urls), 1)
                        print(f"Progress: {progress_percent}% ({files_downloaded}/{len(urls)} files downloaded)")
            except Exception as exc:
                print(f"{url} generated an exception: {exc}")

    print(f"Download complete. Files saved at: {save_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download a dataset folder from AWS S3.")
    parser.add_argument("local_folder_path", type=str, help="Local path to download the dataset")
    args = parser.parse_args()
    download_directory(os.path.join(args.local_folder_path))
