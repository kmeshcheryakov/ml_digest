"""
rss_reader.py

This module provides functions for parsing and fetching RSS feeds, filtering recent articles,
and extracting article information. It also contains a function to collect articles based on
an OPML file containing a list of RSS feeds.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import aiohttp
import cchardet as chardet
import feedparser
import html2text
from aiohttp import ClientSession
from dateutil import parser
from tqdm import tqdm
import xml.etree.ElementTree as ET


# Function to parse OPML and return a list of RSS feed URLs
def parse_opml(file_path: str) -> List[str]:
    """
    Parse the OPML file and return a list of RSS feed URLs.

    :param file_path: The path to the OPML file containing RSS feed URLs.
    :return: A list of RSS feed URLs.
    """
    tree = ET.parse(file_path)
    root = tree.getroot()
    rss_feeds = []

    for outline in root.iter("outline"):
        xml_url = outline.get("xmlUrl")
        if xml_url:
            rss_feeds.append(xml_url)

    return rss_feeds


# Function to filter articles published today and yesterday
def filter_recent_articles(entry: Dict[str, str]) -> bool:
    """
    Filter articles published today and yesterday.

    :param entry: A dictionary containing article information.
    :return: A boolean indicating whether the article was published today or yesterday.
    """
    published = entry.get("published")
    updated = entry.get("updated")

    if not (published or updated):
        return False

    article_date = parser.parse(published or updated)
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    return article_date.date() in (today, yesterday)


# Function to extract required information from an article entry
def extract_article_info(entry: feedparser.FeedParserDict) -> Dict[str, str]:
    """
    Extract required information from an article entry.

    :param entry: A FeedParserDict object containing article information.
    :return: A dictionary with article title, link, published date, and description.
    """
    h = html2text.HTML2Text()
    h.ignore_links = True
    markdown_description = h.handle(entry.summary)

    return {
        "title": entry.title,
        "link": entry.link,
        "published": entry.get("published", entry.get("updated")),
        "description": markdown_description,
    }


# Asynchronous function to fetch an RSS feed
async def fetch_feed(
    session: ClientSession,
    rss_feed: str,
    progress_bar: tqdm,
    max_retries: int = 3,
    delay_between_retries: int = 2,
) -> Optional[feedparser.FeedParserDict]:
    """
    Fetch an RSS feed asynchronously.

    :param session: An aiohttp.ClientSession object.
    :param rss_feed: The URL of the RSS feed to fetch.
    :param progress_bar: A tqdm progress bar object.
    :param max_retries: The maximum number of retries for fetching a feed (default: 3).
    :param delay_between_retries: The delay between retries in seconds (default: 2).
    :return: A FeedParserDict object containing the feed data, or None if an error occurs.
    """
    for attempt in range(max_retries):
        try:
            async with session.get(rss_feed) as response:
                content = await response.read()
                detected_encoding = chardet.detect(content)

                charset = (
                    detected_encoding["encoding"]
                    if detected_encoding["encoding"]
                    else "utf-8"
                )
                decoded_content = content.decode(charset, errors="ignore")
                feed = feedparser.parse(
                    decoded_content,
                    response_headers={
                        "content-type": f"application/xml; charset=utf-8"
                    },
                )
                progress_bar.update(1)
                return feed
        except aiohttp.ClientError as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(delay_between_retries)
            else:
                print(f"Error fetching feed '{rss_feed}': {str(e)}")
                progress_bar.update(1)
                return None


async def fetch_recent_articles(rss_feeds: List[str]) -> List[Dict[str, str]]:
    """
    Collect and filter articles from multiple feeds asynchronously.

    :param rss_feeds: A list of RSS feed URLs.
    :return: A list of dictionaries containing recent article information.
    """
    recent_articles = []
    async with ClientSession() as session:
        with tqdm(total=len(rss_feeds), desc="Fetching feeds") as pbar:
            tasks = [fetch_feed(session, rss_feed, pbar) for rss_feed in rss_feeds]
            feeds = await asyncio.gather(*tasks)

            for feed in feeds:
                for entry in feed.entries:
                    if filter_recent_articles(entry):
                        article_info = extract_article_info(entry)
                        recent_articles.append(article_info)

    return recent_articles


def collect_articles(opml_file: str) -> List[Dict[str, str]]:
    """
    Collect articles from RSS feeds in an OPML file.

    :param opml_file: The path to the OPML file containing RSS feed URLs.
    :return: A
    list of dictionaries containing recent article information.
    """
    # Parse the OPML file and collect RSS feeds
    rss_feeds = parse_opml(opml_file)

    # Run the asynchronous functions and print the recent articles
    recent_articles = asyncio.run(fetch_recent_articles(rss_feeds))
    return recent_articles
