import streamlit as st
from extractor import extract_text_from_pdf
from llm_engine import analyze_transcript

st.set_page_config(page_title="Research Tool", layout="wide")

st.title("AI Research Tool — Earnings Call Analyzer")

uploaded_file = st.file_uploader("Upload Earnings Transcript (PDF)", type=["pdf"])

if uploaded_file:
    with st.spinner("Extracting text from PDF..."):
        text = extract_text_from_pdf(uploaded_file)

    if not text or len(text) < 50:
        st.error("❌ OCR failed to extract text. Try another PDF.")
        st.stop()

    st.success(f"Text extracted. Length: {len(text)} characters")


    st.success(f"Text extracted. Length: {len(text)} characters")

    if st.button("Run Research Tool"):
        with st.spinner("Analyzing transcript..."):
            # --- TEMP small test ---
            # text = text[:8000]   # only first ~8k chars for first run

            result = analyze_transcript(text, mode="OPENAI")

        
        st.success("Analysis Complete")

        st.subheader("Management Tone")
        st.write(result.get("management_tone"))

        st.subheader("Confidence Level")
        st.write(result.get("confidence_level"))

        st.subheader("Key Positives")
        st.write(result.get("key_positives"))

        st.subheader("Key Concerns")
        st.write(result.get("key_concerns"))

        st.subheader("Forward Guidance")
        st.json(result.get("forward_guidance"))

        st.subheader("Capacity Utilization")
        st.write(result.get("capacity_utilization"))

        st.subheader("Growth Initiatives")
        st.write(result.get("growth_initiatives"))
