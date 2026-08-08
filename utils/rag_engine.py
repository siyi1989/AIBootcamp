import os
import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from utils.document_loader import load_vector_store
from utils.security import SYSTEM_PROMPT, wrap_context_safely

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    (
        "human",
        "Context:\n{context}\n\nQuestion: {question}\n\n"
        "Answer clearly and cite the source document for each fact:",
    ),
])

RELEVANCE_THRESHOLD = 0.3

NO_MATCH_MESSAGE = (
    "I couldn't find anything in the indexed legislation documents that "
    "confidently answers this question. This may mean the topic isn't "
    "covered by the documents currently uploaded, or the question needs "
    "to be rephrased. Please try rewording your question, or check with "
    "an Admin that the relevant document has been uploaded and indexed."
)

# Matches things like "is $200", "— $650", "fee of $300"
DOLLAR_PATTERN = re.compile(r"\$\s?\d")


def get_answer(question: str, k: int = 12):
    vector_store = load_vector_store()
    if vector_store is None:
        return (
            "No documents have been indexed yet. Please ask an Admin to "
            "upload legislation documents and rebuild the index first.",
            [],
            "none",
        )

    # Normal semantic search
    results = vector_store.similarity_search_with_relevance_scores(question, k=k)
    relevant = [(doc, score) for doc, score in results if score >= RELEVANCE_THRESHOLD]

    # Keyword-boost pass: if the question is asking about a fee/amount,
    # also pull in any chunk containing an actual dollar figure, even if
    # it scored below the semantic threshold above.
    asking_about_fee = any(
        w in question.lower() for w in ["fee", "cost", "charge", "price", "amount"]
    )
    if asking_about_fee:
        wide_results = vector_store.similarity_search_with_relevance_scores(question, k=40)
        dollar_chunks = [
            (doc, score) for doc, score in wide_results if DOLLAR_PATTERN.search(doc.page_content)
        ]
        existing_content = {doc.page_content for doc, _ in relevant}
        for doc, score in dollar_chunks:
            if doc.page_content not in existing_content:
                relevant.append((doc, score))
                existing_content.add(doc.page_content)

    if not relevant:
        return NO_MATCH_MESSAGE, [], "low"

    chunks = [doc for doc, score in relevant]
    top_score = max(score for _, score in relevant)

    if top_score >= 0.6:
        confidence = "high"
    elif top_score >= 0.4:
        confidence = "medium"
    else:
        confidence = "low"

    context = wrap_context_safely(chunks)

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))
    chain = PROMPT | llm
    response = chain.invoke({"context": context, "question": question})

    sources = sorted({c.metadata.get("source", "unknown") for c in chunks})
    return response.content, sources, confidence