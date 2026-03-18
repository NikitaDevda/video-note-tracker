# ─── ALL IMPORTS ─────────────────────────────
import whisper
import yt_dlp
import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_groq import ChatGroq
from dotenv import load_dotenv          

load_dotenv()

# ─── STEP 1: YOUTUBE AUDIO DOWNLOAD ──────────
def download_audio(youtube_url):
    """
    YouTube video se audio download karo
    yt_dlp use hota hai — best YouTube downloader
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'audio.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        title = info.get('title', 'Video')
        duration = info.get('duration', 0)
    print(f"✅ Audio downloaded: {title}")
    return "audio.mp3", title, duration


# ─── STEP 2: SPEECH TO TEXT ───────────────────
def transcribe_audio(audio_path):
    """
    Whisper AI = Real DL Model (by OpenAI)
    Audio ko text mein convert karta hai
    Yeh tumhara actual DL kaam hai!
    """
    print("🎤 Transcribing audio (DL model running)...")
    model = whisper.load_model("base")  # DL model load
    result = model.transcribe(
        audio_path,
        verbose=False
    )
    transcript = result['text']
    segments = result['segments']  # Timestamps ke saath
    print(f"✅ Transcription done: {len(transcript)} chars")
    return transcript, segments


# ─── STEP 3: TIMESTAMPS BANANA ────────────────
def extract_timestamps(segments):
    """
    Har segment ka timestamp extract karo
    Sirf empty text skip karo
    """
    timestamps = []

    for seg in segments:
        text = seg['text'].strip()

        # Empty segments skip karo
        if not text:
            continue

        minutes = int(seg['start'] // 60)
        seconds = int(seg['start'] % 60)

        timestamps.append({
            'time': f"{minutes:02d}:{seconds:02d}",
            'text': text
        })

    print(f"✅ Extracted {len(timestamps)} timestamps")
    return timestamps


# ─── STEP 4: STRUCTURED NOTES BANANA ──────────
def generate_notes(transcript, title):
    """
    LLM se structured notes generate karo
    Prompt Engineering = NLP skill
    """
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


# ─── STEP 5: EMBEDDINGS + FAISS ───────────────
def create_vectorstore_from_transcript(transcript):
    """
    Transcript ko FAISS mein store karo
    Taaki baad mein Q&A kar sako
    Yeh tumhara RAG kaam hai!
    """
    # Chunks banao
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    docs = [Document(page_content=transcript)]
    chunks = splitter.split_documents(docs)

    # Embeddings (DL Model)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # FAISS Vector Store (ML)
    vectorstore = FAISS.from_documents(chunks, embeddings)
    print("✅ Vector store created for Q&A")
    return vectorstore


# ─── STEP 6: Q&A ON VIDEO ─────────────────────
def answer_question(vectorstore, question):
    """
    Video ke baare mein koi bhi question pucho
    RAG pipeline use hoti hai
    """
    # Similar chunks dhundho (ML)
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": 3}
    )
    docs = retriever.invoke(question)
    context = "\n".join([d.page_content for d in docs])

    # LLM se answer lo
    llm = setup_llm()
    prompt = f"""
    Answer based on video transcript context only.
    If not in context, say "Not covered in video".
    
    Context: {context}
    Question: {question}
    Answer:
    """
    response = llm.invoke(prompt)
    return response.content


# ─── LLM SETUP ────────────────────────────────
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


# ─── MAIN PIPELINE ────────────────────────────
def process_video(youtube_url):
    """
    Complete pipeline:
    URL → Audio → Text → Notes + Timestamps + QA
    """
    # Step 1: Download
    audio_path, title, duration = download_audio(youtube_url)

    # Step 2: Transcribe (DL)
    transcript, segments = transcribe_audio(audio_path)

    # Step 3: Timestamps
    timestamps = extract_timestamps(segments)

    # Step 4: Notes (LLM)
    notes = generate_notes(transcript, title)

    # Step 5: Vector Store (ML)
    vectorstore = create_vectorstore_from_transcript(transcript)

    # Cleanup
    if os.path.exists(audio_path):
        os.remove(audio_path)

    return {
        'title': title,
        'transcript': transcript,
        'notes': notes,
        'timestamps': timestamps,
        'vectorstore': vectorstore,
        'duration': duration
    }