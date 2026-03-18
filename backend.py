from ml_logic import process_video, answer_question


# ─── VIDEO PROCESSING ─────────────────────────
def process_video_backend(youtube_url):
    """
    Frontend se URL receive karo
    ML logic ko call karo
    Result return karo
    """
    try:
        if not youtube_url:
            return None, "Please enter a YouTube URL!"

        if "youtube.com" not in youtube_url and "youtu.be" not in youtube_url:
            return None, "Please enter a valid YouTube URL!"

        # ML logic call karo
        result = process_video(youtube_url)
        return result, None

    except Exception as e:
        return None, str(e)


# ─── Q&A ──────────────────────────────────────
def answer_question_backend(vectorstore, question):
    """
    Question receive karo
    RAG pipeline se answer lo
    """
    try:
        if not vectorstore:
            return "Please process a video first!"

        if not question:
            return "Please enter a question!"

        answer = answer_question(vectorstore, question)
        return answer

    except Exception as e:
        return f"Error: {str(e)}"