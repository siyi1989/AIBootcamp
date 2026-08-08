import json
import os
import re
import time
from pathlib import Path

import pandas as pd
from langchain_openai import ChatOpenAI

from utils.document_loader import load_all_documents

FEE_REGISTER_FILE = Path("data/fee_register.csv")

SECONDS_BETWEEN_CALLS = 2

EXTRACTION_PROMPT = """You are extracting structured fee information from a page of
CAAS legislation. Read the text below and identify every distinct fee amount
mentioned, if any.

For each fee found, output an object with these fields:
- "fee_name": short descriptive name (e.g. "UA operator permit — first type of unmanned aircraft")
- "amount": the dollar amount as written (e.g. "$650"). If it's a formula or "not specified", say so.
- "conditions": any conditions that apply (e.g. application date range, category)
- "clause_reference": the paragraph/clause number if visible (e.g. "1(a)(i)")

Respond with ONLY a JSON array, nothing else. If no fees are mentioned on this
page, respond with an empty array: []

Page text:
{page_text}
"""


def _extract_json(text: str):
    """Pull a JSON array out of the LLM response, tolerating stray text/code fences."""
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return []
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return []


def extract_fees_from_documents(progress_callback=None):
    """Scan every page of every uploaded document and extract structured fee data.
    Saves the result to data/fee_register.csv and returns it as a DataFrame."""
    pages = load_all_documents()
    if not pages:
        return pd.DataFrame()

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))
    rows = []

    for i, page in enumerate(pages):
        if progress_callback:
            progress_callback(i + 1, len(pages))

        text = page.page_content.strip()
        if len(text) < 30:
            continue

        prompt = EXTRACTION_PROMPT.format(page_text=text[:4000])
        try:
            response = llm.invoke(prompt)
            fees = _extract_json(response.content)
        except Exception:
            fees = []

        for fee in fees:
            if not isinstance(fee, dict):
                continue
            rows.append({
                "document": page.metadata.get("source", "unknown"),
                "page": (page.metadata.get("page", 0) or 0) + 1,
                "fee_name": fee.get("fee_name", ""),
                "amount": fee.get("amount", ""),
                "conditions": fee.get("conditions", ""),
                "clause_reference": fee.get("clause_reference", ""),
            })

        time.sleep(SECONDS_BETWEEN_CALLS)

    df = pd.DataFrame(rows)
    FEE_REGISTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(FEE_REGISTER_FILE, index=False)
    return df


def load_fee_register():
    if not FEE_REGISTER_FILE.exists():
        return pd.DataFrame()
    return pd.read_csv(FEE_REGISTER_FILE)