import os
import openai
import asyncio
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

async def summarize_diff(before_bytes, after_bytes, result):
    before_text = ""
    after_text = ""

    # Try to extract text portions for summarization
    for diff in result.get("diffs", []):
        before_text += diff["meta"].get("before", "") + "\n"
        after_text += diff["meta"].get("after", "") + "\n"

    if not before_text.strip() or not after_text.strip():
        return

    prompt = f"""
You are a precise technical summarizer.
Summarize the main content and differences between these two documents.

Document A:
{before_text[:4000]}

Document B:
{after_text[:4000]}

Detected diffs:
{result['diffs'][:10]}

Return a structured summary with:
1. Overview of A
2. Overview of B
3. Key differences
    """

    try:
        client = openai.AsyncOpenAI()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
        )
        result["summary"] = response.choices[0].message.content
    except Exception as e:
        result["summary"] = f"LLM summarization failed: {e}"
