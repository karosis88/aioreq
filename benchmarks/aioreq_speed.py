import sys

import aioreq
import asyncio

from time import perf_counter

url, count = sys.argv[1:3]


async def main():
    async with aioreq.Client() as client:
        tasks = []
        for j in range(int(count)):
            tasks.append(client.get(url))
        t1 = perf_counter()
        await asyncio.gather(*tasks)
        time_spent = perf_counter() - t1
        text = f"Url: {url} | Requests: {count} | Time spent: {time_spent}"
        print(text)


asyncio.run(main())
