import streamlit as st

from utils.security import sanitize_user_input
from utils.rag_engine import get_answer
from utils.feedback import save_feedback

st.title("💬 Chat Assistant")
st.caption(
    "Ask a question about CAAS fees legislation. Answers are grounded in "
    "the indexed documents and include source citations."
)

CONFIDENCE_BADGES = {
    "high": "🟢 High confidence",
    "medium": "🟡 Medium confidence",
    "low": "🔴 Low confidence — please verify",
    "none": "⚪ No documents indexed",
}

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

question = st.chat_input(
    "e.g. What is the fee for issuing an Air Operator Certificate?"
)

if question:
    clean_question = sanitize_user_input(question)
    if clean_question != question:
        answer, sources, confidence, metadata = clean_question, [], "low", {}
    else:
        with st.spinner("Searching legislation..."):
            answer, sources, confidence, metadata = get_answer(clean_question)

    st.session_state.chat_history.append(
        {
            "question": question,
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
            "meta": metadata,
            "voted": None,
        }
    )
    st.rerun()

for i, entry in enumerate(st.session_state.chat_history):
    with st.chat_message("user"):
        st.write(entry["question"])
    with st.chat_message("assistant"):
        st.caption(CONFIDENCE_BADGES.get(entry.get("confidence"), ""))
        st.write(entry["answer"])
        if entry.get("meta"):
            meta = entry["meta"]
            st.caption(
                f"⏱ {meta.get('timestamp', '-')}, backend={meta.get('backend', '-')}, retrievals={meta.get('retrieval_count', 0)}"
            )
        if entry["sources"]:
            st.caption("Sources: " + ", ".join(entry["sources"]))

        if entry["voted"] is None:
            col1, col2, col3 = st.columns([1, 1, 8])
            if col1.button("👍", key=f"up_{i}"):
                save_feedback(entry["question"], entry["answer"], entry["sources"], "up")
                entry["voted"] = "up"
                st.rerun()
            if col2.button("👎", key=f"down_{i}"):
                save_feedback(entry["question"], entry["answer"], entry["sources"], "down")
                entry["voted"] = "down"
                st.rerun()
        else:
            st.caption(f"Feedback recorded: {'👍' if entry['voted'] == 'up' else '👎'}")

with st.sidebar:
    st.subheader("🕘 Question History")
    if st.session_state.chat_history:
        for i, entry in enumerate(reversed(st.session_state.chat_history), 1):
            st.markdown(f"**{i}.** {entry['question']}")
    else:
        st.caption("No questions asked yet this session.")
    if st.button("Clear history"):
        st.session_state.chat_history = []
        st.rerun()