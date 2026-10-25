import asyncio
import re
from pathlib import Path

import aiohttp
import aiofiles

from src.config import SUBREDDITS_IT, DATA_PATH, URL


DATA_PATH = Path(DATA_PATH)
DATA_PATH.mkdir(parents=True, exist_ok=True)


class AsyncDownloader:
    async def download_file(self, session, url, file_path, retries=5):
        for attempt in range(retries):
            try:
                downloaded = file_path.stat().st_size if file_path.exists() else 0

                headers = {}
                if downloaded:
                    headers["Range"] = f"bytes={downloaded}-"

                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=None, sock_connect=15, sock_read=60)
                ) as response:
                    if response.status == 416:
                        print(f"Уже скачан: {file_path} ({downloaded:,} байт)")
                        return

                    response.raise_for_status()

                    if downloaded and response.status == 206:
                        content_range = response.headers.get("Content-Range", "")
                        match = re.match(r"bytes (\d+)-(\d+)/(\d+|\*)", content_range)

                        if not match or int(match.group(1)) != downloaded:
                            raise ValueError("Некорректный Content-Range")

                        total_size = (
                            int(match.group(3))
                            if match.group(3) != "*"
                            else None
                        )
                        mode = "ab"

                    else:
                        downloaded = 0
                        total_size = (
                            int(response.headers["Content-Length"])
                            if response.headers.get("Content-Length", "").isdigit()
                            else None
                        )
                        mode = "wb"

                    async with aiofiles.open(file_path, mode) as file:
                        async for chunk in response.content.iter_chunked(1024 * 1024):
                            await file.write(chunk)

                final_size = file_path.stat().st_size

                if total_size is not None and final_size != total_size:
                    raise OSError(
                        f"Размер не совпал: {final_size} вместо {total_size} байт"
                    )

                print(f"Скачан: {file_path} ({final_size:,} байт)")
                return

            except (aiohttp.ClientError, asyncio.TimeoutError, OSError, ValueError) as error:
                print(f"{file_path.name}: попытка {attempt + 1}/{retries}: {error}")

                if attempt == retries - 1:
                    raise

                await asyncio.sleep(attempt + 1)

    async def download_subreddit(self, session, subreddit, semaphore):
        async with semaphore:
            async with session.get(f"{URL}{subreddit}") as response:
                response.raise_for_status()
                data = await response.json()

            if not isinstance(data, list) or not data or not isinstance(data[0], str):
                raise ValueError(f"Некорректный ответ API для {subreddit}")

            file_path = DATA_PATH / f"{subreddit}.parquet"
            await self.download_file(session, data[0], file_path)

    async def download_all(self):
        semaphore = asyncio.Semaphore(4)

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
            tasks = [
                self.download_subreddit(session, subreddit, semaphore)
                for subreddit in SUBREDDITS_IT
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for subreddit, result in zip(SUBREDDITS_IT, results):
                if isinstance(result, BaseException):
                    print(f"Ошибка для {subreddit}: {result}")