import streamlit as st

from utils.fee_extraction import extract_fees_from_documents, load_fee_register

st.title("📊 Fee Register")
st.caption(
    "A structured, browsable table of every fee mentioned across all indexed "
    "documents — auto-extracted by the AI. Always verify against the source "
    "legislation before relying on this for official decisions."
)

if st.session_state.get("role") == "Admin":
    if st.button("🔄 Generate / Refresh Fee Register", type="primary"):
        progress_bar = st.progress(0, text="Starting...")

        def update_progress(page_num, total_pages):
            progress_bar.progress(
                page_num / total_pages,
                text=f"Scanning page {page_num} of {total_pages}...",
            )

        df = extract_fees_from_documents(progress_callback=update_progress)
        progress_bar.empty()
        st.success(f"Extracted {len(df)} fee entries.")

st.divider()

df = load_fee_register()

if df.empty:
    st.info(
        "No fee register generated yet. "
        + ("Click the button above to build one." if st.session_state.get("role") == "Admin"
           else "Ask an Admin to generate it.")
    )
else:
    doc_filter = st.multiselect("Filter by document", options=sorted(df["document"].unique()))
    search_term = st.text_input("Search fee name / conditions", "")

    filtered = df.copy()
    if doc_filter:
        filtered = filtered[filtered["document"].isin(doc_filter)]
    if search_term:
        mask = (
            filtered["fee_name"].str.contains(search_term, case=False, na=False)
            | filtered["conditions"].str.contains(search_term, case=False, na=False)
        )
        filtered = filtered[mask]

    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.caption(f"Showing {len(filtered)} of {len(df)} total fee entries.")

    st.download_button(
        "⬇️ Download as CSV",
        data=filtered.to_csv(index=False),
        file_name="caas_fee_register.csv",
        mime="text/csv",
    )