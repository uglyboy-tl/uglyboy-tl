#!/usr/bin/env python3
# -*-coding:utf-8-*-

from pathlib import Path
from datetime import datetime
from typing import Dict, Union
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup
from loguru import logger

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip,deflate,sdch',
    'Accept-Language': 'zh-CN,zh;q=0.8'
}

session = requests.Session()

MAX_FILES = 10

def scrape_url(url: str) -> Dict[str, Dict[str, Union[str, None]]]:
    logger.info(f"Scraping URL: {url}")
    try:
        r = session.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
    except Exception as err:
        logger.error(f"{err.__class__.__name__} occurred: {err}")
        return {}

    soup = BeautifulSoup(r.content, 'html.parser')
    items = soup.select('div.Box article.Box-row')

    results = {}
    logger.debug(f"Found {len(items)} items")
    for item in items:
        try:
            a: Tag = item.find("h2", class_="lh-condensed").a # type: ignore
            title = a.text.strip().replace("\n", "").replace(" ", "")
            url = "https://github.com" + a['href']
        except:
            logger.debug(item)
            continue
        description_tag = item.find("p", class_="col-9")
        if description_tag is not None:
            description = description_tag.text.strip().replace('\r', '').replace('\n', '')
        else:
            description = None
        results[title] = {'title': title, 'url': url, 'description': description}
    return results


def scrape_lang(language: str) -> Dict[str, Dict[str, Union[str, None]]]:
    url = f'https://github.com/trending/{quote_plus(language)}'
    r1 = scrape_url(url)
    url = f'https://github.com/trending/{quote_plus(language)}?spoken_language_code=zh'
    r2 = scrape_url(url)
    return {**r1, **r2}

def write_markdown(lang, results):
    if lang == '':
        content = '## All Languages\n\n'
    else:
        content = '## ' + lang.capitalize() + '\n\n'
    for result in results.values():
        content += "- [{title}]({url}) - {description}\n".format(title=result['title'], url=result['url'],
            description=result['description'])
    date = datetime.now().strftime("%Y-%m-%d")
    file_path = Path(f"./trending/{date}.md")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.touch(exist_ok=True)
    with file_path.open('a', encoding='utf-8') as f:
            f.write(content)

def delete_old_files():
    date_format = "%Y-%m-%d"
    file_path = Path("./trending/")

    # 获取所有 .md 文件，并根据日期排序
    files = sorted(file_path.glob('*.md'), key=lambda f: datetime.strptime(f.stem, date_format), reverse=True)

    # 如果文件数量超过 10，删除最老的文件
    if len(files) > MAX_FILES:
        for file in files[MAX_FILES:]:
            file.unlink()

if __name__ == '__main__':
    languages = ['', 'python', 'javascript', 'typeScript', 'go', 'rust', 'c++', 'c', 'html', 'css', 'unknown']
    for lang in languages:
        results = scrape_lang(lang)
        write_markdown(lang, results)
        delete_old_files()