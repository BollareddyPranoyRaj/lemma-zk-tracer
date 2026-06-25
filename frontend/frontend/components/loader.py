import streamlit as st
import time

def processing_animation():

    steps = [
        "📤 Uploading PDF...",
        "🔒 Creating document hash...",
        "📊 Extracting Revenue...",
        "💰 Extracting EBITDA...",
        "📈 Calculating Growth...",
        "🤖 Generating Investment Memo...",
        "✅ Finalizing Decision..."
    ]

    progress = st.progress(0)

    status = st.empty()

    for i, step in enumerate(steps):

        status.info(step)

        progress.progress((i+1)/len(steps))

        time.sleep(0.7)

    status.success("Analysis Complete!")