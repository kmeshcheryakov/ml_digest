#!/bin/env python
"""
main.py

This module serves as the main entry point for the RSS Digest Generator. It imports and uses functions
from the rss_reader, text_processing, digest_generator, and question_answering modules to collect articles,
generate a daily digest, and answer questions based on the collected article summaries.
"""

import asyncio
import openai

from ml_digest.digest_generator import generate_digest
from ml_digest.rss_reader import collect_articles

openai.api_key = ""

# OPML file containing the list of RSS feeds
opml_file = "../test/feeds.xml"


def main():
    recent_articles = collect_articles(opml_file=opml_file)

    for article in recent_articles:
        print(f"Title: {article['title']}")
        print(f"Link: {article['link']}")
        print(f"Published: {article['published']}")
        print(f"Description: {article['description']}\n")

    digest = asyncio.run(generate_digest(recent_articles))
    print(digest)


if __name__ == "__main__":
    main()
