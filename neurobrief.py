
import os
import json
import argparse
import time
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

FEEDS = [
    "https://www.marktechpost.com/feed/",
    "https://blog.google/technology/ai/rss/",
    "https://news.mit.edu/rss/topic/artificial-intelligence2",
    "https://www.technologyreview.com/feed/",
]

TASKS = {
    "morning": {
        "title": "Morning AI News Intelligence",
        "keywords": [],
        "filename": "morning-ai-news.md",
        "instruction": "Identify the most important recent AI news, explain what happened, why it matters, and provide source links."
    },
    "technology": {
        "title": "Emerging Technology Analysis",
        "keywords": ["technology", "robotics", "agent", "computing", "innovation", "automation"],
        "filename": "technology-analysis.md",
        "instruction": "Analyze emerging technology developments. Identify technical trends, practical applications, and potential limitations."
    },
    "models": {
        "title": "AI Model Release Tracker",
        "keywords": ["model", "llm", "language model", "gemini", "gpt", "claude", "llama", "open source"],
        "filename": "model-releases.md",
        "instruction": "Identify AI model releases and updates. Explain their capabilities, intended uses, and any limitations supported by the source material."
    },
    "industry": {
        "title": "AI Industry Intelligence",
        "keywords": ["company", "funding", "startup", "business", "industry", "investment", "partnership"],
        "filename": "industry-insights.md",
        "instruction": "Analyze AI industry developments, company activity, funding, partnerships, and market implications. Avoid unsupported predictions."
    },
    "evening": {
        "title": "Evening AI Intelligence Digest",
        "keywords": [],
        "filename": "evening-digest.md",
        "instruction": "Create an end-of-day digest. Select the most significant developments, connect related stories, and list important takeaways."
    }
}


def collect_news():
    articles = []
    seen = set()

    for feed_url in FEEDS:
        try:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries[:20]:
                link = entry.get("link", "")

                if not link or link in seen:
                    continue

                seen.add(link)

                articles.append({
                    "title": entry.get("title", "Untitled"),
                    "link": link,
                    "published": entry.get("published", "Date unavailable"),
                    "summary": entry.get("summary", "")[:1500],
                    "source": feed.feed.get("title", feed_url)
                })

        except Exception as error:
            print(f"Feed error: {feed_url}: {error}")

    return articles


def select_articles(articles, keywords):
    if not keywords:
        return articles[:15]

    selected = []

    for article in articles:
        text = (
            article["title"] + " " + article["summary"]
        ).lower()

        if any(word in text for word in keywords):
            selected.append(article)

    return selected[:15]


def gemini_analysis(task, articles):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return "Gemini analysis unavailable: GEMINI_API_KEY is not configured."

    if not articles:
        return "No matching articles were available for this task."

    task_info = TASKS[task]

    source_data = [
        {
            "title": article["title"],
            "source": article["source"],
            "published": article["published"],
            "summary": article["summary"][:800],
            "url": article["link"]
        }
        for article in articles
    ]

    prompt = f"""
You are NeuroBrief AI, an autonomous technology intelligence analyst.

Task: {task_info['title']}

Instructions:
{task_info['instruction']}

Rules:
- Use only the supplied article information.
- Do not invent facts, statistics or announcements.
- Distinguish reported facts from your interpretation.
- Include useful source links.
- Write clear, informative Markdown.
- Avoid repeating the same information.

Articles:
{json.dumps(source_data, ensure_ascii=False)}
"""

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{MODEL}:generateContent"
    )

    for attempt in range(3):
        try:
            response = requests.post(
                url,
                params={"key": api_key},
                json={
                    "contents": [
                        {"parts": [{"text": prompt}]}
                    ],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 1800
                    }
                },
                timeout=(15, 120)
            )

            response.raise_for_status()

            data = response.json()

            return data["candidates"][0]["content"]["parts"][0]["text"]

        except (requests.RequestException, KeyError, IndexError) as error:
            print(f"Gemini attempt {attempt + 1} failed: {error}")

            if attempt < 2:
                time.sleep(10 * (attempt + 1))

    return (
        "Gemini was unavailable after three attempts. "
        "The source collection below is retained for manual review."
    )


def generate_report(task):
    task_info = TASKS[task]

    print(f"Starting NeuroBrief task: {task}")

    articles = collect_news()
    selected = select_articles(
        articles,
        task_info["keywords"]
    )

    analysis = gemini_analysis(task, selected)

    now = datetime.now(timezone.utc)

    report = [
        f"# {task_info['title']}",
        "",
        f"Date: {now:%Y-%m-%d}",
        f"Generated: {now:%H:%M UTC}",
        f"Articles collected: {len(articles)}",
        f"Articles selected: {len(selected)}",
        "",
        "## AI Intelligence Analysis",
        "",
        analysis,
        "",
        "## Source Collection",
        ""
    ]

    for index, article in enumerate(selected, 1):
        report.extend([
            f"### {index}. {article['title']}",
            f"- Source: {article['source']}",
            f"- Published: {article['published']}",
            f"- Link: {article['link']}",
            f"- Description: {article['summary'][:500]}",
            ""
        ])

    report_path = (
        Path("reports")
        / now.strftime("%Y-%m-%d")
        / task_info["filename"]
    )

    report_path.parent.mkdir(parents=True, exist_ok=True)

    report_path.write_text(
        "\n".join(report),
        encoding="utf-8"
    )

    print(f"Report saved: {report_path}")
    print(f"Articles analyzed: {len(selected)}")


def main():
    parser = argparse.ArgumentParser(
        description="NeuroBrief AI Intelligence Agent"
    )

    parser.add_argument(
        "--task",
        choices=list(TASKS.keys()),
        required=True
    )

    args = parser.parse_args()

    generate_report(args.task)


if __name__ == "__main__":
    main()
