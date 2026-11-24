# NeuroBrief AI

A daily AI news digest that reads selected public RSS feeds, removes duplicate links, and generates a concise Gemini-powered briefing.

## Run locally
```bash
python -m pip install -r requirements.txt
python neurobrief.py
```

Set `GEMINI_API_KEY` to enable AI summaries. Without it, the script still archives feed headlines and links.

## GitHub Actions
Create a repository named `ai-pulse`, upload the files to its root, and add the repository secret `GEMINI_API_KEY`. The workflow runs daily at 08:30 UTC and supports manual runs. Reports are stored in `reports/`.

