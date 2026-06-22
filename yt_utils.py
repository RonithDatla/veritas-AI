from youtube_transcript_api import YouTubeTranscriptApi

def get_youtube_transcript(url):
    try:
        import re

        match = re.search(r"(v=|youtu\.be/)([^&?/]+)", url)
        if not match:
            print("Invalid URL")
            return None

        video_id = match.group(2)

        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        print("Available transcripts:", transcript_list)

        # ✅ Try ALL transcripts one by one
        for transcript in transcript_list:
            try:
                print("Trying:", transcript)
                result = transcript.fetch()

                text = " ".join([t["text"] for t in result])
                if text.strip():
                    return text

            except Exception as e:
                print("Fetch failed:", e)

        # ✅ Try translation fallback
        for transcript in transcript_list:
            try:
                print("Trying translate:", transcript)
                result = transcript.translate("en").fetch()

                text = " ".join([t["text"] for t in result])
                if text.strip():
                    return text

            except Exception as e:
                print("Translate failed:", e)

        print("All transcript attempts failed")
        return None

    except Exception as e:
        print("Transcript error:", e)
        return None