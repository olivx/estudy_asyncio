import re
import sys
import random
import logging
import asyncio 
import pathlib
import aiofiles
from typing import IO
from aiohttp import ClientSession

logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
    level=logging.DEBUG,
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)

logger = logging.getLogger('downloader')
logging.getLogger('chardet.charsetprober').disable = True

f_logger = logging.FileHandler('logger_async_downloader.log')
f_logger.setLevel(logging.DEBUG)
logger.addHandler(f_logger)

SRC_RE = re.compile(r'(srcset)="(.*?)"')
 # url from test 

async def fecth_html(url: str, session: ClientSession,  **kwargs) -> str:
    """ all src link from _url """
    response = await session.request(method='GET', url=url)
    response.raise_for_status()
    logger.info('GET Response from URL: %s', url)
    html = await response.text()
    return html

async def fecth_content(url: str, session: ClientSession, **kwargs) -> IO:
    """ return content read() from url """
    response = await session.get(url)
    logger.info('GET Content Read from URL: %s', url)
    content = await response.content.read()
    return content 

async def parse_html(url: str, session: ClientSession, **kwargs) -> set:
    """ html and return list off links two donwloads """
    found =  set()
    try:
        html = await fecth_html(url=url, session=session, **kwargs)
    except Exception as e:
        logger.exception(
            'Excetipon error: URL=%s status=[%s]  message=%s',
            url,  
            getattr(e, 'status'),
            getattr(e, 'message')
        )
        return found
    else:
        for _ , link in SRC_RE.findall(html):
            _url = link.split()[0]
            found.add(_url)
        logger.info("URL found %s link  in %s",  len(_url), _url )
    return found


async def write_file(url: str, file_name: str, session: ClientSession, **kwargs) -> None:
    content = await fecth_content(url, session, **kwargs)

    async with aiofiles.open(file_name, 'wb') as infile:
        await infile.write(content)
    logger.info('Wrote File %s from url: %s', file_name, url)


async def donwload(url: str, session: ClientSession, **kwargs) -> None:
    """ make download the img in url """
    urls = await parse_html(url=url, session=session)
    
    tasks = []
    for index, url in enumerate(urls):
        file_name = url.split("/")[-1]
        tasks.append(
            write_file(url, pathlib.Path('downloaded').joinpath(file_name), session=session)
        )
        logger.info('ADD task %s to write file %s in url %s', index, file_name, url)
    await asyncio.gather(*tasks)


async def crawl(urls: str, **kwargs) -> None:
    async with ClientSession(trust_env=True) as session:
        tasks = []
        logger.info('working with %s pages', len(urls))
        for _url in urls:
            tasks.append(donwload(url=_url, session=session))
            logger.info('START with URL %s', _url)
        await asyncio.gather(*tasks)
    


if __name__ == "__main__":
    import argparse
    import shutil
    import time 

    start = time.perf_counter()
    message_start = f'START at {start:0.2f}, executed in seconds'
    logger.info(message_start)

    DEFAULR_PAGES_RANGE = 10
    MAX_PAGES_DOWNLOADER = 7586
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", help="delete all  downloaded images", type=bool)
    parser.add_argument("--pages", help="how many pages would you like to download", type=int)
    args = parser.parse_args()
    

    if args.pages and args.pages > MAX_PAGES_DOWNLOADER:
        error_message =  f'{args.pages} exceeded MAX_PAGES_DOWNLOADER, max value is {MAX_PAGES_DOWNLOADER}'
        logger.error('%s  exceeded MAX_PAGES_DOWNLOADER, max value is %s', args.pages, MAX_PAGES_DOWNLOADER)
        raise ValueError(error_message)
    
    elif args.pages is not None:
        pages_range = args.pages
   
    else:
        pages_range = DEFAULR_PAGES_RANGE
    
    if args.clean:
        if pathlib.Path('downloaded').exists():
            shutil.rmtree(pathlib.Path('downloaded'))

    if not pathlib.Path('downloaded').exists():
        pathlib.Path('downloaded').mkdir()

    urls = []
    for page in range(1, pages_range):
        urls.append(f'https://pixabay.com/en/photos/?image_type=photo&pagi={page}')
    asyncio.run(crawl(urls=urls))

    stop = time.perf_counter()
    elapsed = stop - start 
    message_stop = f'STOP AT {stop:0.2f}, executed in seconds'
    message_finish = f'EXCUTED IN {elapsed:0.2f}, executed in seconds'
    logger.info(message_stop)
    logger.info(message_finish)
   