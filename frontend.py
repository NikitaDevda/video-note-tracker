import streamlit as st
from backend import process_video_backend, answer_question_backend

# ─── PAGE CONFIG ──────────────────────────────
st.set_page_config(
    page_title="AI Video Note Taker",
    page_icon="🎥",
    layout="wide"
)

# ─── HEADER ───────────────────────────────────
st.title("🎥 AI Video Note Taker")
st.markdown("Convert any YouTube video into structured notes, timestamps & action items!")
st.markdown("---")

# ─── SIDEBAR ──────────────────────────────────
with st.sidebar:
    st.header("🔗 Enter Video URL")
    youtube_url = st.text_input(
        "YouTube URL",
        placeholder="https://www.youtube.com/watch?v=..."
    )
    process_btn = st.button("🚀 Generate Notes", use_container_width=True)
    st.markdown("---")
    st.markdown("### How to use:")
    st.markdown("1. Paste YouTube URL")
    st.markdown("2. Click Generate Notes")
    st.markdown("3. View notes & timestamps")
    st.markdown("4. Ask questions about video!")

# ─── PROCESS VIDEO ────────────────────────────
if process_btn and youtube_url:
    with st.spinner("⏳ Processing video... (may take 2-3 mins)"):
        result, error = process_video_backend(youtube_url)

        if result:
            st.session_state.result = result
            st.success(f"✅ Done! Video: {result['title']}")
        else:
            st.error(f"❌ Error: {error}")

# ─── SHOW RESULTS ─────────────────────────────
if "result" in st.session_state and st.session_state.result:
    result = st.session_state.result

    # Tabs banao
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Notes",
        "⏱️ Timestamps",
        "💬 Q&A",
        "📄 Transcript"
    ])

    # ── TAB 1: NOTES ──────────────────────────
    with tab1:
        st.markdown(f"## 📹 {result['title']}")
        st.markdown(result['notes'])
        st.download_button(
            label="📥 Download Notes",
            data=result['notes'],
            file_name="notes.txt",
            mime="text/plain"
        )

    # ── TAB 2: TIMESTAMPS ─────────────────────
    with tab2:
        st.markdown("## ⏱️ Key Timestamps")
        for ts in result['timestamps']:
            col1, col2 = st.columns([1, 5])
            with col1:
                st.markdown(f"**⏱️ {ts['time']}**")
            with col2:
                st.markdown(ts['text'])
            st.markdown("---")

    # ── TAB 3: Q&A ────────────────────────────
    with tab3:
        st.markdown("## 💬 Ask About This Video")
        question = st.text_input(
            "Your question:",
            placeholder="What is the main topic?"
        )
        ask_btn = st.button("🔍 Get Answer")

        if ask_btn and question:
            with st.spinner("🤔 Finding answer..."):
                answer = answer_question_backend(
                    result['vectorstore'],
                    question
                )
            st.markdown("### 💡 Answer:")
            st.write(answer)

            # History
            if "qa_history" not in st.session_state:
                st.session_state.qa_history = []
            st.session_state.qa_history.append({
                "q": question, "a": answer
            })

        # Show history
        if "qa_history" in st.session_state:
            st.markdown("### 📝 Previous Questions")
            for item in reversed(st.session_state.qa_history):
                st.markdown(f"**Q:** {item['q']}")
                st.markdown(f"**A:** {item['a']}")
                st.markdown("---")

    # ── TAB 4: TRANSCRIPT ─────────────────────
    with tab4:
        st.markdown("## 📄 Full Transcript")
        st.text_area(
            "Transcript",
            result['transcript'],
            height=400
        )
        st.download_button(
            label="📥 Download Transcript",
            data=result['transcript'],
            file_name="transcript.txt",
            mime="text/plain"
        )