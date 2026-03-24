# # ─── ALL IMPORTS ─────────────────────────────
# import os
# import re
# from youtube_transcript_api import YouTubeTranscriptApi
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from langchain_community.vectorstores import FAISS
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_core.documents import Document
# from langchain_groq import ChatGroq
# from dotenv import load_dotenv

# load_dotenv()

# # ─── STEP 1: VIDEO ID EXTRACT ────────────────
# def get_video_id(youtube_url):
#     # Normal video
#     match = re.search(r"v=([^&]+)", youtube_url)
#     if match:
#         return match.group(1)
#     # Shorts
#     match = re.search(r"shorts/([^?]+)", youtube_url)
#     if match:
#         return match.group(1)
#     # youtu.be
#     match = re.search(r"youtu\.be/([^?]+)", youtube_url)
#     if match:
#         return match.group(1)
#     return None

# # ─── STEP 2: TRANSCRIPT FETCH ────────────────
# def get_transcript_direct(youtube_url):
#     video_id = get_video_id(youtube_url)
#     if not video_id:
#         raise ValueError("❌ Invalid YouTube URL!")

#     try:
#         from youtube_transcript_api import YouTubeTranscriptApi
#         from youtube_transcript_api.proxies import WebshareProxyConfig

#         # Free proxy try karo
#         proxy_config = WebshareProxyConfig(
#             proxy_username="",
#             proxy_password="",
#         )
        
#         ytt_api = YouTubeTranscriptApi(proxy_config=proxy_config)
#         fetched = ytt_api.fetch(video_id)
#         transcript_list = list(fetched)

#     except Exception as e:
#         raise ValueError(f"❌ Error: {e}")

#     transcript = " ".join([t.get('text', '') for t in transcript_list])
#     timestamps = []
#     for t in transcript_list:
#         start   = t.get('start', 0)
#         minutes = int(start // 60)
#         seconds = int(start % 60)
#         timestamps.append({
#             'time': f"{minutes:02d}:{seconds:02d}",
#             'text': t.get('text', '')
#         })

#     return transcript, timestamps

# # ─── STEP 3: VIDEO TITLE FETCH ───────────────
# def get_video_title(youtube_url):
#     try:
#         import yt_dlp
#         ydl_opts = {'quiet': True, 'skip_download': True}
#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             info = ydl.extract_info(youtube_url, download=False)
#             return info.get('title', 'YouTube Video')
#     except:
#         return "YouTube Video"

# # ─── STEP 4: NOTES GENERATE ──────────────────
# def generate_notes(transcript, title):
#     llm = setup_llm()

#     prompt = f"""
#     You are an expert note-taker.
#     Create structured notes from this video transcript.

#     Video Title: {title}
#     Transcript: {transcript[:3000]}

#     Create notes in this EXACT format:

#     ## 📌 Main Topics
#     - Topic 1
#     - Topic 2
#     - Topic 3

#     ## 📝 Key Points
#     - Point 1
#     - Point 2
#     - Point 3

#     ## ✅ Action Items
#     - Action 1
#     - Action 2

#     ## 💡 Summary
#     2-3 line summary here
#     """

#     response = llm.invoke(prompt)
#     print("✅ Notes generated")
#     return response.content

# # ─── STEP 5: EMBEDDINGS + FAISS ──────────────
# def create_vectorstore_from_transcript(transcript):
#     splitter = RecursiveCharacterTextSplitter(
#         chunk_size=500,
#         chunk_overlap=50
#     )
#     docs   = [Document(page_content=transcript)]
#     chunks = splitter.split_documents(docs)

#     embeddings = HuggingFaceEmbeddings(
#         model_name="sentence-transformers/all-MiniLM-L6-v2"
#     )

#     vectorstore = FAISS.from_documents(chunks, embeddings)
#     print("✅ Vector store created")
#     return vectorstore

# # ─── STEP 6: Q&A ─────────────────────────────
# def answer_question(vectorstore, question):
#     retriever = vectorstore.as_retriever(
#         search_kwargs={"k": 3}
#     )
#     docs    = retriever.invoke(question)
#     context = "\n".join([d.page_content for d in docs])

#     llm    = setup_llm()
#     prompt = f"""
#     Answer based on video transcript context only.
#     If not in context, say "Not covered in video".

#     Context: {context}
#     Question: {question}
#     Answer:
#     """
#     response = llm.invoke(prompt)
#     return response.content

# # ─── LLM SETUP ───────────────────────────────
# def setup_llm():
#     try:
#         import streamlit as st
#         api_key = st.secrets["GROQ_API_KEY"]
#     except:
#         api_key = os.getenv("GROQ_API_KEY")

#     llm = ChatGroq(
#         api_key=api_key,
#         model_name="llama-3.3-70b-versatile",
#         temperature=0.1
#     )
#     return llm

# # ─── MAIN PIPELINE ───────────────────────────
# def process_video(youtube_url):
#     # Step 1: Transcript direct lo
#     transcript, timestamps = get_transcript_direct(youtube_url)

#     # Step 2: Title fetch karo
#     title = get_video_title(youtube_url)

#     # Step 3: Notes generate karo
#     notes = generate_notes(transcript, title)

#     # Step 4: Vector store banao
#     vectorstore = create_vectorstore_from_transcript(transcript)

#     return {
#         'title': title,
#         'transcript': transcript,
#         'notes': notes,
#         'timestamps': timestamps,
#         'vectorstore': vectorstore,
#         'duration': 0
#     }












# ─── ALL IMPORTS ─────────────────────────────
import os
import re
import requests
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()


# ─── STEP 1: VIDEO ID EXTRACT ─────────────────
def extract_video_id(youtube_url):
    youtube_url = youtube_url.strip()
    patterns = [
        r"(?:v=)([a-zA-Z0-9_-]{11})",
        r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:embed/)([a-zA-Z0-9_-]{11})",
        r"(?:shorts/)([a-zA-Z0-9_-]{11})",
        r"(?:live/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)
    raise ValueError(
        "❌ Invalid YouTube URL!\n"
        "Supported formats:\n"
        "• https://www.youtube.com/watch?v=VIDEO_ID\n"
        "• https://youtu.be/VIDEO_ID\n"
        "• https://youtube.com/shorts/VIDEO_ID"
    )


# ─── STEP 2: SUPADATA API KEY ─────────────────
def get_supadata_key():
    api_key = None
    try:
        import streamlit as st
        api_key = st.secrets.get("SUPADATA_API_KEY")
    except:
        pass
    if not api_key:
        api_key = os.getenv("SUPADATA_API_KEY")
    if not api_key:
        raise ValueError(
            "❌ SUPADATA_API_KEY nahi mili!\n"
            "Streamlit Secrets mein add karo:\n"
            "SUPADATA_API_KEY = 'your_key_here'\n\n"
            "Free key lo: supadata.ai"
        )
    return api_key


# ─── STEP 3: TRANSCRIPT FETCH ─────────────────
def get_transcript_from_url(youtube_url):
    """
    Supadata API se transcript fetch karo
    Cloud IP block nahi hoga — proxy ki zaroorat nahi!
    """
    video_id = extract_video_id(youtube_url)
    print(f"🎬 Fetching transcript for video: {video_id}")

    api_key = get_supadata_key()
    headers = {"x-api-key": api_key}

    # Pehle English try karo, phir Hindi
    for lang in ["en", "hi"]:
        try:
            response = requests.get(
                "https://api.supadata.ai/v1/youtube/transcript",
                params={"videoId": video_id, "lang": lang},
                headers=headers,
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", [])
                if content:
                    full_text = " ".join([t["text"] for t in content])
                    segments = [
                        {
                            "start": t.get("offset", 0) / 1000,
                            "text": t["text"]
                        }
                        for t in content
                    ]
                    print(f"✅ Transcript fetched ({lang}): {len(full_text)} chars")
                    return full_text, segments
        except Exception as e:
            print(f"Lang {lang} failed: {e}")
            continue

    # Koi bhi lang nahi mili — language param ke bina try karo
    try:
        response = requests.get(
            "https://api.supadata.ai/v1/youtube/transcript",
            params={"videoId": video_id},
            headers=headers,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            content = data.get("content", [])
            if content:
                full_text = " ".join([t["text"] for t in content])
                segments = [
                    {
                        "start": t.get("offset", 0) / 1000,
                        "text": t["text"]
                    }
                    for t in content
                ]
                print(f"✅ Transcript fetched (auto): {len(full_text)} chars")
                return full_text, segments
        else:
            raise ValueError(f"API error: {response.status_code} - {response.text}")
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(
            f"❌ Transcript fetch nahi hua!\n"
            f"Possible reasons:\n"
            f"• Video private/deleted hai\n"
            f"• Is video mein captions nahi hain\n"
            f"• Supadata API key invalid hai\n\n"
            f"Error: {str(e)}"
        )

    raise ValueError(
        "❌ Transcript nahi mila!\n"
        "• Video mein captions/subtitles hone chahiye\n"
        "• YouTube pe video open karo → '...' → 'Open transcript' check karo"
    )


# ─── STEP 4: TIMESTAMPS BANANA ────────────────
def extract_timestamps(segments):
    timestamps = []
    for seg in segments:
        text = seg['text'].strip()
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


# ─── STEP 5: STRUCTURED NOTES ─────────────────
def generate_notes(transcript, title):
    llm = setup_llm()
    prompt = f"""
    You are an expert note-taker.
    Create structured notes from this video transcript.
    IMPORTANT: Always write notes in ENGLISH, even if transcript is in Hindi or any other language.

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


# ─── STEP 6: EMBEDDINGS + FAISS ───────────────
def create_vectorstore_from_transcript(transcript):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    docs = [Document(page_content=transcript)]
    chunks = splitter.split_documents(docs)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    vectorstore = FAISS.from_documents(chunks, embeddings)
    print("✅ Vector store created")
    return vectorstore


# ─── STEP 7: Q&A ──────────────────────────────
def answer_question(vectorstore, question):
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(question)
    context = "\n".join([d.page_content for d in docs])
    llm = setup_llm()
    prompt = f"""
    Answer based on video transcript context only.
    If not in context, say "Not covered in video".
    Answer in the same language as the question.

    Context: {context}
    Question: {question}
    Answer:
    """
    response = llm.invoke(prompt)
    return response.content


# ─── LLM SETUP ────────────────────────────────
def setup_llm():
    api_key = None
    try:
        import streamlit as st
        api_key = st.secrets.get("GROQ_API_KEY")
    except:
        pass
    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "❌ GROQ_API_KEY nahi mili!\n"
            "Streamlit Secrets mein add karo:\n"
            "GROQ_API_KEY = 'gsk_your_key_here'"
        )
    return ChatGroq(
        api_key=api_key,
        model_name="llama-3.3-70b-versatile",
        temperature=0.1
    )


# ─── MAIN PIPELINE ────────────────────────────
def process_video(youtube_url):
    transcript, segments = get_transcript_from_url(youtube_url)
    timestamps = extract_timestamps(segments)
    notes = generate_notes(transcript, "YouTube Video")
    vectorstore = create_vectorstore_from_transcript(transcript)
    return {
        'title': 'YouTube Video',
        'transcript': transcript,
        'notes': notes,
        'timestamps': timestamps,
        'vectorstore': vectorstore,
        'duration': 0
    }
