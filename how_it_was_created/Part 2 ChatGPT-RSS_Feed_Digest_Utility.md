#### You:
I have a small utility that collect my RSS feeds for last day, and gives me a daily digest based on it. 
Here is the code:
```
#!/bin/env python

import asyncio
import feedparser
import aiohttp
import xml.etree.ElementTree as ET
from aiohttp import ClientSession
from datetime import datetime, timedelta
from dateutil import parser
from tqdm import tqdm
import cchardet as chardet
import openai

openai.api_key = "<KEY>"


# OPML file containing the list of RSS feeds
opml_file = '../test/feeds.xml'

# Function to parse OPML and return a list of RSS feed URLs
def parse_opml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    rss_feeds = []
    
    for outline in root.iter('outline'):
        xml_url = outline.get('xmlUrl')
        if xml_url:
            rss_feeds.append(xml_url)
    
    return rss_feeds

# Function to filter articles published today and yesterday
def filter_recent_articles(entry):
    published = entry.get('published')
    updated = entry.get('updated')

    if not (published or updated):
        return False

    article_date = parser.parse(published or updated)
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    return article_date.date() in (today, yesterday)

# Function to extract required information from an article entry
def extract_article_info(entry):
    return {
        'title': entry.title,
        'link': entry.link,
        'published': entry.get('published', entry.get('updated')),
        'description': entry.summary,
    }


# Asynchronous function to fetch an RSS feed
async def fetch_feed(session, rss_feed, progress_bar, max_retries=3, delay_between_retries=2):
    for attempt in range(max_retries):
        try:
            async with session.get(rss_feed) as response:
                content = await response.read()
                detected_encoding = chardet.detect(content)

                charset = detected_encoding['encoding'] if detected_encoding['encoding'] else 'utf-8'
                decoded_content = content.decode(charset, errors='ignore')
                feed = feedparser.parse(decoded_content, response_headers={'content-type': f'application/xml; charset=utf-8'})
                progress_bar.update(1)
                return feed
        except aiohttp.ClientError as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(delay_between_retries)
            else:
                print(f"Error fetching feed '{rss_feed}': {str(e)}")
                progress_bar.update(1)
                return None

# Asynchronous function to collect and filter articles from multiple feeds
async def fetch_recent_articles(rss_feeds):
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

async def generate_digest(articles):
    conversation = [
        {"role": "system", "content": "You are a helpful assistant. Summarize the following articles concisely:"},
    ]

    for article in articles:
        conversation.append({"role": "user", "content": f"Title: {article['title']}.\nDescription: {article['description']}."})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation,
    )

    summary = response['choices'][0]['message']['content']
    return summary




def collect_articles(opml_file):
    # Parse the OPML file and collect RSS feeds
    rss_feeds = parse_opml(opml_file)

    # Run the asynchronous functions and print the recent articles
    recent_articles = asyncio.run(fetch_recent_articles(rss_feeds))
    return recent_articles


recent_articles = collect_articles(opml_file=opml_file)

for article in recent_articles:
    print(f"Title: {article['title']}")
    print(f"Link: {article['link']}")
    print(f"Published: {article['published']}")
    print(f"Description: {article['description']}\n")


digest = asyncio.run(generate_digest(recent_articles))
print(digest)
```
I need to add new capabilities to the utility 

#### ChatGPT:
Here are a few suggestions for adding new capabilities to your utility:

1. Save the digest to a file or email it:
   Add an option to save the digest as a text file or email it directly to your inbox.

2. Keyword filtering:
   Add an option to filter the articles based on specific keywords, so you only receive articles that are relevant to your interests.

3. Sorting articles:
   Add the ability to sort the articles by various criteria like publication date, author, or source.

4. Summarization options:
   Allow users to choose between different summarization lengths or styles.

5. Categorization:
   Categorize articles by topic, source, or another criterion to make the digest easier to read and navigate.

6. Text-to-Speech:
   Integrate a text-to-speech library to read the digest out loud, providing an option for an audio version of the digest.

7. Schedule the script:
   Schedule the script to run at specific times or intervals (e.g., daily or weekly) so you always receive your digest on time.

8. User Interface:
   Create a simple GUI or web interface for users to interact with the utility, making it more user-friendly.

9. Export to other formats:
   Add the ability to export the digest to other formats like PDF, Markdown, or HTML.

10. Error handling and logging:
    Improve error handling and add logging functionality to help with debugging and monitoring the utility's performance.

To implement these features, you'll need to update your script and import additional libraries as needed. For example, you may need to use libraries like smtplib and email for sending emails, PyPDF2 or WeasyPrint for PDF generation, and tkinter or Flask for creating a user interface.


#### You:
Let's start with improvements in the AI prompt. Right now it is just a summary, I want it to look like theme-separated digest that tries to highlight the most important things. 

#### ChatGPT:
To create a theme-separated digest, you can modify the prompt sent to GPT-3.5-turbo and include additional instructions. You can also utilize the titles and descriptions of the articles more effectively to help the model generate a more structured output. Here's an example of how you can modify the `generate_digest` function:

```python
async def generate_digest(articles):
    conversation = [
        {"role": "system", "content": "You are a helpful assistant. Create a theme-separated digest that highlights the most important things from the following articles:"},
    ]

    for article in articles:
        conversation.append({"role": "user", "content": f"Title: {article['title']}.\nDescription: {article['description']}."})

    conversation.append({"role": "user", "content": "Organize the digest by themes and highlight the key points."})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation,
    )

    digest = response['choices'][0]['message']['content']
    return digest
```

By instructing the model to "organize the digest by themes and highlight the key points", it will try to identify common themes among the articles and structure the output accordingly. However, since GPT-3.5-turbo doesn't have explicit support for identifying themes, the quality of the output might vary. If the generated digest doesn't meet your expectations, you can experiment with different instructions or even provide examples of how you'd like the output to be structured.

Keep in mind that GPT-3.5-turbo has a maximum token limit (4096 tokens for this model). If your articles' titles and descriptions are too long, you may need to truncate or omit some of them to fit within this limit.


#### You:
Is this a limit for a total dialog?

#### ChatGPT:
Yes, the token limit (4096 tokens for GPT-3.5-turbo) applies to the total dialogue, including input and output tokens. It covers the conversation history, instructions, and the generated response. If a conversation exceeds this limit, you will need to truncate, omit, or shorten the text to fit within the allowed token count.

Remember that a token can be as short as one character or as long as one word, and the number of tokens also includes formatting tokens like spaces and newlines. If the conversation becomes too long, the model may not provide a meaningful response, or it may not generate any response at all if the token limit is exceeded.

When working with large amounts of text or a long conversation, it's important to manage the token count to ensure the model can generate a useful response. Keep in mind that very long conversations can also lead to incomplete replies, as the response may be cut off due to the token limit.


#### You:
How can I reduce the amount of tokens consumed?

#### ChatGPT:
To reduce the number of tokens consumed in your conversation with the model, you can follow these strategies:

1. Shorten the conversation history:
   Remove or abbreviate less important parts of the conversation history. Keep only the most relevant information needed for the model to understand the context.

2. Be concise with instructions:
   Provide clear and concise instructions to the model. Avoid using overly long or wordy sentences.

3. Summarize or truncate input text:
   If you are providing long titles, descriptions, or any other text, consider summarizing or truncating them to reduce token count.

4. Limit response length:
   You can limit the response length using the `max_tokens` parameter when making an API call. However, be cautious not to set it too low, as this might lead to incomplete or nonsensical responses.

5. Use shorter prompts:
   If you are using multiple prompts or examples, try to shorten them or use fewer examples.

6. Remove unnecessary formatting:
   Minimize the use of spaces, newlines, and other formatting tokens, as they also count towards the token limit.

Keep in mind that while reducing the token count, it's essential to maintain the context and information needed for the model to understand your request and provide meaningful output. Striking a balance between token usage and providing clear instructions is key for successful interactions with the model.


#### You:
Please use the shortest answers possible

#### ChatGPT:
To create a theme-separated digest, modify the `generate_digest` function:

```python
async def generate_digest(articles):
    conversation = [
        {"role": "system", "content": "Create a themed digest with key points from these articles:"},
    ]

    for article in articles:
        conversation.append({"role": "user", "content": f"Title: {article['title']}.\nDescription: {article['description']}."})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation,
    )

    digest = response['choices'][0]['message']['content']
    return digest
```

This version uses shorter instructions while maintaining the desired output.


#### You:
Let's also try to create summaries for each articles, collect them, and then build a digest based on that. These summaries should be concise, but have enough information to later base a digest on them.  

#### ChatGPT:
To achieve this, you can first create summaries for each article and then use those summaries to generate the theme-separated digest. Here's a modified version of the `generate_digest` function:

```python
async def summarize_article(article):
    conversation = [
        {"role": "system", "content": "You are a helpful assistant. Summarize the following article concisely but with enough information for creating a digest later:"},
        {"role": "user", "content": f"Title: {article['title']}.\nDescription: {article['description']}."},
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation,
    )

    summary = response['choices'][0]['message']['content']
    return summary


async def generate_digest_from_summaries(summaries):
    conversation = [
        {"role": "system", "content": "Create a themed digest with key points from these summarized articles:"},
    ]

    for summary in summaries:
        conversation.append({"role": "user", "content": summary})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation,
    )

    digest = response['choices'][0]['message']['content']
    return digest


async def generate_digest(articles):
    summaries = []
    for article in articles:
        summary = await summarize_article(article)
        summaries.append(summary)

    digest = await generate_digest_from_summaries(summaries)
    return digest
```

This implementation first creates summaries for each article by calling the `summarize_article` function. Then, it uses the generated summaries to create a theme-separated digest with the `generate_digest_from_summaries` function.


#### You:
Also, probably we want to convert html to markdown for the articles so it takes less tokens

#### ChatGPT:
To convert HTML to Markdown, you can use the `html2text` library. First, install the library using pip:

```bash
pip install html2text
```

Then, update the `extract_article_info` function to convert the article's description from HTML to Markdown:

```python
import html2text

# Function to extract required information from an article entry
def extract_article_info(entry):
    h = html2text.HTML2Text()
    h.ignore_links = True
    markdown_description = h.handle(entry.summary)

    return {
        'title': entry.title,
        'link': entry.link,
        'published': entry.get('published', entry.get('updated')),
        'description': markdown_description,
    }
```

This will convert the HTML content of the article's description to Markdown before it's passed to the `generate_digest` function. Converting HTML to Markdown can help reduce token count, especially when the HTML content contains a lot of tags and formatting.


#### You:
This creates plain text, but that's ok

#### ChatGPT:
My apologies for the confusion. You're right, the `html2text` library converts HTML to plain text with Markdown-style formatting. If you're satisfied with plain text, you can use the updated `extract_article_info` function as it is. Converting HTML to plain text can still help reduce token count by removing the HTML tags and keeping only the essential text content.


#### You:
Another thing, I think it would be useful to send not only the description, but a titile too

#### ChatGPT:
Certainly! You can modify the `summarize_article` function to include both the title and description in the conversation for summarization. Here's the updated `summarize_article` function:

```python
async def summarize_article(article):
    conversation = [
        {"role": "system", "content": "You are a helpful assistant. Summarize the following article concisely but with enough information for creating a digest later:"},
        {"role": "user", "content": f"Title: {article['title']}.\nDescription: {article['description']}."},
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation,
    )

    summary = response['choices'][0]['message']['content']
    return f"**{article['title']}**\n{summary}"
```

This version of the function adds the article's title as bold text (using `**` for Markdown-style formatting) followed by the generated summary. When you call the `generate_digest_from_summaries` function, it will now receive summaries that include the titles. This will make the final digest more informative and easier to understand.


#### You:
Nice. What if I want to later ask questions like "What about Wrocław, what happened here?"

#### ChatGPT:
If you want to enable querying the digest for specific information like "What about Wrocław, what happened here?", you can create a new function that takes the generated digest and a question as input, then sends the question to GPT-3.5-turbo along with the digest for context. Here's an example of such a function:

```python
async def ask_question(digest, question):
    conversation = [
        {"role": "system", "content": "You are a helpful assistant. Use the provided digest to answer the user's questions:"},
        {"role": "user", "content": f"Here's the digest:\n{digest}"},
        {"role": "user", "content": question},
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation,
    )

    answer = response['choices'][0]['message']['content']
    return answer
```

Once you have the digest, you can use this function to ask questions about specific topics or locations mentioned in the digest. For example:

```python
question = "What about Wrocław, what happened here?"
answer = asyncio.run(ask_question(digest, question))
print(answer)
```

This function will send the provided digest along with the question to the model, and it will attempt to answer the question using the information from the digest. Note that the quality of the answer depends on the information available in the digest and the clarity of the question.


#### You:
But this would leave out info from the previous summaryzation, right?

#### ChatGPT:
You're correct. The `ask_question` function I provided earlier uses only the generated digest as context. If you want to ensure that the model has access to the individual summaries during the question-answering process, you can modify the function to include the summaries as part of the conversation.

Here's an updated version of the `ask_question` function that takes the summaries as an input and provides them as context:

```python
async def ask_question(summaries, question):
    conversation = [
        {"role": "system", "content": "You are a helpful assistant. Use the provided article summaries to answer the user's questions:"},
    ]

    for summary in summaries:
        conversation.append({"role": "user", "content": f"Summary: {summary}"})

    conversation.append({"role": "user", "content": question})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation,
    )

    answer = response['choices'][0]['message']['content']
    return answer
```

Now you can call this function with the list of summaries and your question:

```python
question = "What about Wrocław, what happened here?"
answer = asyncio.run(ask_question(summaries, question))
print(answer)
```

By providing the summaries as context, the model will have access to the information from the individual summaries, which can lead to more accurate and detailed answers.


#### You:
What if we first tag the summaries with possible topics and then try to use the topic to select summaries to send as a context? In this case we would also need to extract topic from the question, right? 

#### ChatGPT:
Yes, you can first tag the summaries with possible topics, then use the extracted topic from the question to select relevant summaries to send as context. Here's an outline of the steps you can follow:

1. Create a function to extract topics from the summaries.
2. Create a function to extract the topic from the question.
3. Modify the `ask_question` function to select relevant summaries based on the extracted topic from the question.

Here's an example implementation of the three steps:

```python
# Step 1: Function to extract topics from the summaries
async def extract_topic(summary):
    conversation = [
        {"role": "system", "content": "You are a helpful assistant. Identify the main topic of this summary:"},
        {"role": "user", "content": summary},
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation,
    )

    topic = response['choices'][0]['message']['content']
    return topic.strip()

# Step 2: Function to extract the topic from the question
async def extract_topic_from_question(question):
    conversation = [
        {"role": "system", "content": "You are a helpful assistant. Identify the main topic of this question:"},
        {"role": "user", "content": question},
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation,
    )

    topic = response['choices'][0]['message']['content']
    return topic.strip()

# Step 3: Modify the ask_question function
async def ask_question(summaries, question):
    question_topic = await extract_topic_from_question(question)
    relevant_summaries = []

    for summary in summaries:
        summary_topic = await extract_topic(summary)
        if summary_topic.lower() == question_topic.lower():
            relevant_summaries.append(summary)

    conversation = [
        {"role": "system", "content": "You are a helpful assistant. Use the provided relevant article summaries to answer the user's questions:"},
    ]

    for summary in relevant_summaries:
        conversation.append({"role": "user", "content": f"Summary: {summary}"})

    conversation.append({"role": "user", "content": question})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation,
    )

    answer = response['choices'][0]['message']['content']
    return answer
```

Now, when you call the `ask_question` function with the list of summaries and your question, the model will first extract the topic from the question and then use the relevant summaries as context to provide an answer.

Note that this approach involves multiple API calls (one for each summary and one for the question), which can increase the overall cost and processing time. It's important to keep this in mind when using this method.


#### You:
Let's modify the first step. We already have the summarize_article function, can we also ask the model to include the topics in the response?

#### ChatGPT:
Yes, you can modify the `summarize_article` function to ask the model to include the main topic in the response. Here's an updated version of the `summarize_article` function that requests both the summary and the main topic:

```python
async def summarize_article(article):
    conversation = [
        {"role": "system", "content": "You are a helpful assistant. Summarize the following article concisely but with enough information for creating a digest later. Also, identify the main topic of the article:"},
        {"role": "user", "content": f"Title: {article['title']}.\nDescription: {article['description']}."},
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation,
    )

    response_text = response['choices'][0]['message']['content']
    summary, topic = response_text.split('\n', 1)
    return {"summary": summary, "topic": topic.strip()}
```

This function will return a dictionary containing both the summary and the main topic. You'll need to update the part of your code that processes the summaries accordingly:

```python
summaries = asyncio.run(summarize_articles(recent_articles))

tagged_summaries = []
for summary_info in summaries:
    tagged_summaries.append({
        'summary': summary_info['summary'],
        'topic': summary_info['topic'],
    })
```

With this modification, you can now use the `tagged_summaries` list in the `ask_question` function to provide context based on the extracted topics. Just make sure to adjust the function's input and processing accordingly.


#### You:
Modify the ask_question function now

#### ChatGPT:
Now that you have the `tagged_summaries` list with both the summary and the main topic, you can modify the `ask_question` function accordingly. You no longer need the `extract_topic` function, as the topics are already included in the tagged summaries.

Here's the updated `ask_question` function that uses the `tagged_summaries`:

```python
async def ask_question(tagged_summaries, question):
    question_topic = await extract_topic_from_question(question)
    relevant_summaries = []

    for summary_info in tagged_summaries:
        if summary_info['topic'].lower() == question_topic.lower():
            relevant_summaries.append(summary_info['summary'])

    conversation = [
        {"role": "system", "content": "You are a helpful assistant. Use the provided relevant article summaries to answer the user's questions:"},
    ]

    for summary in relevant_summaries:
        conversation.append({"role": "user", "content": f"Summary: {summary}"})

    conversation.append({"role": "user", "content": question})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation,
    )

    answer = response['choices'][0]['message']['content']
    return answer
```

Now you can call the `ask_question` function with the list of `tagged_summaries` and your question. The function will use the topics to select the relevant summaries as context and attempt to answer the question based on that information:

```python
question = "What about Wrocław, what happened here?"
answer = asyncio.run(ask_question(tagged_summaries, question))
print(answer)
```
