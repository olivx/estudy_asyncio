import asyncio
import logging 
import re 
import sys
from typing import IO
import urllib.parse
import urllib.error

import aiofiles 
import aiohttp
from aiohttp import ClientSession

logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
    level=logging.DEBUG,
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)

logger = logging.getLogger('areq')
logging.getLogger('chardet.charsetprober').disable = True

f_logger = logging.FileHandler('logger.log')
f_logger.setLevel(logging.DEBUG)
logger.addHandler(f_logger)

HREF_RE = re.compile(r'href="(.*?)"')

async def fetch_html(url: str, session: ClientSession, **kwargs) -> str:
    """ get html """
    resp = await session.request(method='GET', url=url, **kwargs)
    resp.raise_for_status()
    logger.info('got response [%s] for URL %s', resp.status, url)
    html = await resp.text()
    return html 

async def parse(url: str, session: ClientSession, **kwargs) -> set:
        """ find href in html  """
        found = set ()
        try:
            html = await fetch_html(url=url, session=session, **kwargs)
        except(
            aiohttp.ClientError, 
            aiohttp.http_exceptions.HttpProcessingError,
        )as e:
            logger.error(
                'aiohttp exception for %s [%s]: %s',
                url,
                getattr(e, 'status', None),
                getattr(e, 'message', None),
            )
        except Exception as e:
            logger.exception(
                'non-aiohttp exception occured: %s', getattr(e, '__dict___', None)
            )
        else:
            for link  in HREF_RE.findall(html):
                try:
                    abslink = urllib.parse.urljoin(url, link)
                except(urllib.error.URLError, ValueError):
                    logger.exception('Error parsing URL %s', link)
                    pass 
                else:
                    found.add(abslink)
            logger.info('Found %d links for %s', len(found), url)
            return found

async def write_one(file: IO, url: str, **kwargs) -> None:
    """ write the found url """
    resp = await parse(url=url, **kwargs)
    if not resp:
        return None
    async with aiofiles.open(file, 'a') as f:
        for p in resp:
            await f.write(f'{url}\t{p}\n')
        logger.info("Wrote results for source URL: %s", url)
    
async def bulk_crawl_and_write(file: IO, urls: set, **kwargs)-> None:
    """ crawl  and write concurrently to file for mutiples urls """
    async with ClientSession(trust_env=True) as session:
        tasks = []
        for url in urls:
            tasks.append(
                write_one(file=file, url=url, session=session, **kwargs)
            ) 
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    import pathlib 
    import sys

    assert sys.version_info >= (3, 7)
    here = pathlib.Path(__file__).parent
    with open(here.joinpath('urls.txt')) as infile:
        urls = set(map(str.strip, infile))

    outpath = here.joinpath('foundurls.txt')
    with open(outpath, 'w') as outfile:
        outfile.write('source_url\tparsed_url\n')

    asyncio.run(bulk_crawl_and_write(file=outpath, urls=urls))