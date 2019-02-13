import re
import sys
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
_url = 'https://pixabay.com/en/photos/?image_type=photo' # url from test 

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


async def wrote_file(url: str, file_name: str, session: ClientSession, **kwargs) -> None:
    content = await fecth_content(url, session, **kwargs)

    async with aiofiles.open(file_name, 'wb') as infile:
        await infile.write(content)
    logger.info('Wrote File %s from url: %s', file_name, url)


async def donwload(url: str, session: ClientSession, **kwargs) -> None:
    """ make download the img in url """
    urls = await parse_html(url=_url, session=session)
    
    tasks = []
    for index, url in enumerate(urls):
        file_name = url.split("/")[-1]
        tasks.append(
            wrote_file(url, pathlib.Path('downloaded').joinpath(file_name), session=session)
        )
        logger.info('ADD task %s to write file %s in url %s', index, file_name, url)
    await asyncio.gather(*tasks)


async def crawl(url: str, **kwargs) -> None:
    async with ClientSession(trust_env=True) as session:
        await asyncio.gather(donwload(url=_url, session=session))
    


if __name__ == "__main__":
    if not pathlib.Path('downloaded').exists():
        pathlib.Path('downloaded').mkdir()
    
    asyncio.run(crawl(url=_url))



