# RSS Digest Generator

The RSS Digest Generator is a Python-based tool that collects articles from a list of RSS feeds, generates a daily digest, and answers questions based on the collected article summaries. It leverages the GPT-3.5-turbo model from OpenAI to perform text processing tasks such as summarizing articles, extracting topics, and answering questions.

## Features

- Collect articles from multiple RSS feeds
- Filter recent articles based on their publication date
- Generate a daily digest with key points from the collected articles
- Answer questions based on the summarized articles

## Prerequisites

Before you can use the RSS Digest Generator, you need to have the following installed:

- Python 3.7 or higher
- Poetry for dependency management
- OpenAI API key for using OpenAI's GPT-3.5-turbo

## Installation

1. Clone the repository:

git clone https://github.com/yourusername/rss-digest-generator.git
cd rss-digest-generator

2. Install Poetry if you haven't already:

pip install --user poetry

3. Install the required dependencies using Poetry:

poetry install

4. Add your OpenAI API key to the `api_key` variable in the `main.py` script or set it as an environment variable.

## Usage

1. Add your RSS feeds to an OPML file, and update the `opml_file` variable in `main.py` with the path to your OPML file.

2. Run the `main.py` script using Poetry:

poetry run python main.py

3. The script will collect articles from the specified RSS feeds, generate a daily digest, and print it to the console.

4. To ask a question based on the collected article summaries, call the `ask_question` function in the `main.py` script with your question as an argument. For example:

```python
answer = asyncio.run(ask_question(tagged_summaries, "What is the impact of climate change on the economy?"))
print(answer)
```

## License

This project is licensed under the MIT License.

