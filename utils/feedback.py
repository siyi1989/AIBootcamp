import csv
from datetime import datetime
from pathlib import Path

FEEDBACK_FILE = Path("data/feedback.csv")


def save_feedback(question: str, answer: str, sources: list, vote: str):
    """Append one feedback record. vote is 'up' or 'down'."""
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    file_exists = FEEDBACK_FILE.exists()
    with open(FEEDBACK_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "question", "answer", "sources", "vote"])
        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            question,
            answer,
            "; ".join(sources),
            vote,
        ])