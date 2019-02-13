import os
import time
import random
import asyncio
import itertools as it 

async def makeitem(size: int = 5) -> str:
    return os.urandom(size).hex()

async def randint(a: int, b: int) -> int:
    return random.randint(a, b)

async def randsleep(a: int = 1, b: int = 5, caller = None) -> None:
    i = await randint(a, b)
    if caller:
        print(f'{caller} sleeping for {i} seconds.')
    await asyncio.sleep(i)

async def produce(name: int, q: asyncio.Queue) -> None:
    n = await randint(1, 5)
    for _ in it.repeat(None, n):
        i = await makeitem()
        t = time.perf_counter()
        await q.put((i, t))
        print(f'Producer {name} added <{i}> to queue.')

async def consume(name: int, q: asyncio.Queue) -> None:
    while True:
        await randsleep(caller=f'Consumer {name}')
        i, t = await q.get()
        now = time.perf_counter()
        print(f'Consumer {name} got element <{i}>', 
        f' in {now-t:0.5f} seconds')
        q.task_done()

async def main(nprod: int, ncon: int):
    q = asyncio.Queue()
    produces = [asyncio.create_task(produce(n, q)) for n in range(nprod)]
    consumers = [asyncio.create_task(consume(n, q)) for n in range(ncon)]
    await asyncio.gather(*produces)
    await q.join() 
    for c in consumers:
        c.cancel()

if __name__ == "__main__":
    import argparse
    random.seed(444)
    parser =  argparse.ArgumentParser()
    parser.add_argument('-p', '--nprod', type=int, default=5)
    parser.add_argument('-c', '--ncon', type=int, default=1)
    ns = parser.parse_args()
    start = time.perf_counter()
    asyncio.run(main(** ns.__dict__))
    elapsed = time.perf_counter() - start
    print(f'Program complete in elapsed {elapsed:0.5} seconds')

