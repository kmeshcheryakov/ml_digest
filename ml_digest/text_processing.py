"""
text_processing.py

This module provides functions for text processing tasks, such as summarizing articles and
extracting topics from questions. It leverages the GPT-3.5-turbo model from OpenAI to perform
these tasks.
"""

from typing import Dict

import openai


async def summarize_article(article: Dict[str, str]) -> Dict[str, str]:
    """
    Summarize an article and identify its main topic.

    :param article: A dictionary containing article information.
    :return: A dictionary with the summarized article and its main topic.
    """
    conversation = [
        {
            "role": "system",
            "content": "You are a helpful assistant. Summarize the following article concisely but with enough information for creating a digest later. Also, identify the main topic of the article:",
        },
        {
            "role": "user",
            "content": f"Title: {article['title']}.\nDescription: {article['description']}.",
        },
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation,
    )

    response_text = response["choices"][0]["message"]["content"]
    summary, topic = response_text.split("\n", 1)
    return {"summary": summary, "topic": topic.strip()}


async def extract_topic_from_question(question: str) -> str:
    """
    Identify the main topic of a question.

    :param question: A string containing the question.
    :return: A string containing the main topic of the question.
    """
    conversation = [
        {
            "role": "system",
            "content": "You are a helpful assistant. Identify the main topic of this question:",
        },
        {"role": "user", "content": question},
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation,
    )

    topic = response["choices"][0]["message"]["content"]
    return topic.strip()
