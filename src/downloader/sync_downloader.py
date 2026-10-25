import time
import requests
from .config import SUBREDDITS_IT, DATA_PATH, URL


DATA_PATH.mkdir(parents=True, exist_ok=True)


class SyncDownloader:
    def download_file(self, url, file_path, retries=5):
        for attempt in range(retries):
            try:
                downloaded = file_path.stat().st_size if file_path.exists() else 0

                headers = {}
                if downloaded:
                    headers["Range"] = f"bytes={downloaded}-"

                with requests.get(url, headers=headers, stream=True, timeout=(15, 60)) as response:
                    if response.status_code == 416:
                        print(f"Файл уже скачан: {file_path}")
                        return

                    response.raise_for_status()

                    if downloaded and response.status_code != 206:
                        downloaded = 0

                    mode = "ab" if downloaded and response.status_code == 206 else "wb"

                    with open(file_path, mode) as file:
                        for chunk in response.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                file.write(chunk)

                print(f"Файл скачан: {file_path}")
                return

            except (requests.exceptions.RequestException, OSError) as e:
                print(f"Попытка {attempt + 1}/{retries}: {e}")
                if attempt == retries - 1:
                    raise
                time.sleep(attempt + 1)

    def download_subreddit(self, subreddit):
        response = requests.get(URL + subreddit, timeout=60)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list) and data and isinstance(data[0], str):
            file_url = data[0]
            file_path = DATA_PATH / f"{subreddit}.parquet"
            self.download_file(file_url, file_path)
        else:
            print(f"Ошибка: ожидался list, пришёл {type(data).__name__}")

    def download(self):
        for subreddit in SUBREDDITS_IT:
            try:
                self.download_subreddit(subreddit)
            except (requests.RequestException, OSError, ValueError) as error:
                print(f"Ошибка для {subreddit}: {error}")