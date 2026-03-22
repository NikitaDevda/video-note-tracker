# ─── ALL IMPORTS ─────────────────────────────
import os
import re
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

# ─── STEP 1: VIDEO ID EXTRACT ────────────────
def get_video_id(youtube_url):
    # Normal video
    match = re.search(r"v=([^&]+)", youtube_url)
    if match:
        return match.group(1)
    # Shorts
    match = re.search(r"shorts/([^?]+)", youtube_url)
    if match:
        return match.group(1)
    # youtu.be
    match = re.search(r"youtu\.be/([^?]+)", youtube_url)
    if match:
        return match.group(1)
    return None

# ─── STEP 2: TRANSCRIPT FETCH ────────────────
def get_transcript_direct(youtube_url):
    video_id = get_video_id(youtube_url)
    if not video_id:
        raise ValueError("❌ Invalid YouTube URL!")

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api.proxies import WebshareProxyConfig

        # Free proxy try karo
        proxy_config = WebshareProxyConfig(
            proxy_username="",
            proxy_password="",
        )
        
        ytt_api = YouTubeTranscriptApi(proxy_config=proxy_config)
        fetched = ytt_api.fetch(video_id)
        transcript_list = list(fetched)

    except Exception as e:
        raise ValueError(f"❌ Error: {e}")

    transcript = " ".join([t.get('text', '') for t in transcript_list])
    timestamps = []
    for t in transcript_list:
        start   = t.get('start', 0)
        minutes = int(start // 60)
        seconds = int(start % 60)
        timestamps.append({
            'time': f"{minutes:02d}:{seconds:02d}",
            'text': t.get('text', '')
        })

    return transcript, timestamps

# ─── STEP 3: VIDEO TITLE FETCH ───────────────
def get_video_title(youtube_url):
    try:
        import yt_dlp
        ydl_opts = {'quiet': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            return info.get('title', 'YouTube Video')
    except:
        return "YouTube Video"

# ─── STEP 4: NOTES GENERATE ──────────────────
def generate_notes(transcript, title):
    llm = setup_llm()

    prompt = f"""
    You are an expert note-taker.
    Create structured notes from this video transcript.

    Video Title: {title}
    Transcript: {transcript[:3000]}

    Create notes in this EXACT format:

    ## 📌 Main Topics
    - Topic 1
    - Topic 2
    - Topic 3

    ## 📝 Key Points
    - Point 1
    - Point 2
    - Point 3

    ## ✅ Action Items
    - Action 1
    - Action 2

    ## 💡 Summary
    2-3 line summary here
    """

    response = llm.invoke(prompt)
    print("✅ Notes generated")
    return response.content

# ─── STEP 5: EMBEDDINGS + FAISS ──────────────
def create_vectorstore_from_transcript(transcript):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    docs   = [Document(page_content=transcript)]
    chunks = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectorstore = FAISS.from_documents(chunks, embeddings)
    print("✅ Vector store created")
    return vectorstore

# ─── STEP 6: Q&A ─────────────────────────────
def answer_question(vectorstore, question):
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": 3}
    )
    docs    = retriever.invoke(question)
    context = "\n".join([d.page_content for d in docs])

    llm    = setup_llm()
    prompt = f"""
    Answer based on video transcript context only.
    If not in context, say "Not covered in video".

    Context: {context}
    Question: {question}
    Answer:
    """
    response = llm.invoke(prompt)
    return response.content

# ─── LLM SETUP ───────────────────────────────
def setup_llm():
    try:
        import streamlit as st
        api_key = st.secrets["GROQ_API_KEY"]
    except:
        api_key = os.getenv("GROQ_API_KEY")

    llm = ChatGroq(
        api_key=api_key,
        model_name="llama-3.3-70b-versatile",
        temperature=0.1
    )
    return llm

# ─── MAIN PIPELINE ───────────────────────────
def process_video(youtube_url):
    # Step 1: Transcript direct lo
    transcript, timestamps = get_transcript_direct(youtube_url)

    # Step 2: Title fetch karo
    title = get_video_title(youtube_url)

    # Step 3: Notes generate karo
    notes = generate_notes(transcript, title)

    # Step 4: Vector store banao
    vectorstore = create_vectorstore_from_transcript(transcript)

    return {
        'title': title,
        'transcript': transcript,
        'notes': notes,
        'timestamps': timestamps,
        'vectorstore': vectorstore,
        'duration': 0
    }
