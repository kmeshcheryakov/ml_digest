"""
digest_generator.py

This module provides functions for generating a daily digest based on a list of articles.
It leverages the GPT-3.5-turbo model from OpenAI to generate the digest and handles
the process of summarizing articles and creating a themed digest with key points.
"""

from typing import Dict, List

import openai

from ml_digest.text_processing import summarize_article


async def generate_digest_from_summaries(summaries: List[Dict[str, str]]) -> str:
    """
    Create a themed digest with key points from summarized articles.

    :param summaries: A list of dictionaries containing summarized article information.
    :return: A string containing the themed digest.
    """
    conversation = [
        {
            "role": "system",
            "content": "Create a themed digest with key points from these summarized articles:",
        },
    ]

    for summary in summaries:
        conversation.append({"role": "user", "content": summary["summary"]})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation,
    )

    digest = response["choices"][0]["message"]["content"]
    return digest


async def generate_digest(articles: List[Dict[str, str]]) -> str:
    """
    Generate a daily digest based on a list of articles.

    :param articles: A list of dictionaries containing article information.
    :return: A string containing the daily digest.
    """
    summaries = []
    for article in articles:
        summary = await summarize_article(article)
        summaries.append(summary)

    digest = await generate_digest_from_summaries(summaries)
    return digest
