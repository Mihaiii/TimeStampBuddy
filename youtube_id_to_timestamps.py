from youtube_transcript_api import YouTubeTranscriptApi
import json
from datetime import timedelta
import os
import time
import google.generativeai as genai
import tempfile
import json
import logging

DEFAULT_GEMINI_MODEL = "gemini-2.0-flash-exp"


class YoutubeIdToTimestamps:
    def __init__(self, max_response_length):
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
        pr = os.environ.get("YT_TRANSCRIPT_PROXY", "")
        self.proxies = None
        if pr:
            self.proxies = {
                "https": pr.replace("http://", "https://"),
                "http": pr.replace("https://", "http://"),
            }
        self.max_response_length = max_response_length
        self.language_codes = [
    "en", "es", "de", "pt", "fr", "ab", "aa", "af", "ak", "sq", "am", "ar", "hy", "as", "ay", "az",
    "bn", "ba", "eu", "be", "bho", "bs", "br", "bg", "my", "ca", "ceb", "zh-Hans", "zh-Hant", "co",
    "hr", "cs", "da", "dv", "nl", "dz", "eo", "et", "ee", "fo", "fj", "fil", "fi", "gaa", "gl", "lg",
    "ka", "el", "gn", "gu", "ht", "ha", "haw", "iw", "hi", "hmn", "hu", "is", "ig", "id", "iu", "ga",
    "it", "ja", "jv", "kl", "kn", "kk", "kha", "km", "rw", "ko", "kri", "ku", "ky", "lo", "la", "lv",
    "ln", "lt", "lua", "luo", "lb", "mk", "mg", "ms", "ml", "mt", "gv", "mi", "mr", "mn", "mfe", "ne",
    "new", "nso", "no", "ny", "oc", "or", "om", "os", "pam", "ps", "fa", "pl", "pt-PT", "pa", "qu",
    "ro", "rn", "ru", "sm", "sg", "sa", "gd", "sr", "crs", "sn", "sd", "si", "sk", "sl", "so", "st",
    "su", "sw", "ss", "sv", "tg", "ta", "tt", "te", "th", "bo", "ti", "to", "ts", "tn", "tum", "tr",
    "tk", "uk", "ur", "ug", "uz", "ve", "vi", "war", "cy", "fy", "wo", "xh", "yi", "yo", "zu"
        ]

    def _seconds_to_hhmmss(self, seconds):
        td = timedelta(seconds=round(seconds))
        return str(td)

    def _get_transcript(self, youtube_id):
        logging.info(f"{youtube_id} - making the request to get the transcript")
        #transcript_list = YouTubeTranscriptApi.list_transcripts(youtube_id)
        #transcript = transcript_list.find_generated_transcript(self.language_codes)
        #if not transcript:
        #    logging.error("No auto generated transcript found")
        data = YouTubeTranscriptApi.get_transcript(
            youtube_id, languages=['en', 'es', 'de', 'pt'], proxies=self.proxies
        )
        logging.info(f"{youtube_id} - got the transcript. First 5 objs: {data[:5]}")
        transformed_data = [
            {"text": item["text"], "start": self._seconds_to_hhmmss(item["start"])}
            for item in data
        ]
        return json.dumps(transformed_data, indent=4)

    def _upload_to_gemini(self, file_content, mime_type=None):
        with tempfile.NamedTemporaryFile(
            suffix=".tmp", mode="w+", encoding="utf-8"
        ) as tmpfile:
            tmpfile.write(file_content)
            tmp_path = tmpfile.name
            file = genai.upload_file(tmp_path, mime_type=mime_type)
            return file

    def _wait_for_files_active(self, files):
        for name in (file.name for file in files):
            file = genai.get_file(name)
            while file.state.name == "PROCESSING":
                time.sleep(10)
                file = genai.get_file(name)
            if file.state.name != "ACTIVE":
                raise Exception(f"File {file.name} failed to process")

    def get_timestamps(self, youtube_id):
        file_content = self._get_transcript(youtube_id)
        model = genai.GenerativeModel(
            model_name=os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
            generation_config={
                "temperature": 1,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
                "response_mime_type": "text/plain",
            },
        )

        files = [
            self._upload_to_gemini(file_content, mime_type="text/plain"),
        ]
        logging.info(f"{youtube_id} - Will wait for files to be active")
        self._wait_for_files_active(files)
        logging.info(f"{youtube_id} - Files were attached")
        initial_message = {
            "role": "user",
            "parts": [
                files[0],
                "Attached you have the transcript of a YouTube video. It's a JSON file that has the following properties: text - what is said, meaning the actual transcript, start: the second of that fragment in the video.\n\nI want you to make a summary of the video based on that transcript data and also include the timestamps (make sure they are in HH:MM:SS format), meaning between what hour, minute and second in the video a generated topic/idea is mentioned. Make the topics short. Have lots of topics. Have one topic per line and each line starts with the timestamps.\n\nHere is an example of how your response look like. Pay attention to the format. This is the summary for another video:\n\n0:00 - Introduction\n13:03- 12 startups in 12 months\n36:37 - Photo AI\n1:12:53 - How to learn AI\n2:03:24 - Monetize your website\n3:01:34 - Productivity\n3:41:21 - Advice for young people\n\nDon't make it too granular. Extract the main ideas/chapters and present them. Only have a chapter at every few minutes, like in the example. Mention as timestamp the beginning of each chapter. See the provided example from above for a better understanding.\n",
            ],
        }
        
        MAX_RESPONSE_LENGTH = self.max_response_length

        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(initial_message["parts"])
        logging.info(f"{youtube_id} - First response received - {len(response.text)=}")
        chat_session.history.append({"role": "model", "parts": [response.text]})

        follow_up_message = f"That's good, but it's too granular. The full response must have less than {MAX_RESPONSE_LENGTH} characters, including new lines. Extract the main ideas/chapters and present them. Only have a chapter at every few minutes, like in the example. Mention as timestamp the beginning of each chapter. See the provided example from above for a better understanding. Answer only with the timestamps and chapters, nothing else and remember to make the response short enought to not exceed {MAX_RESPONSE_LENGTH} characters."
        response = chat_session.send_message(follow_up_message)
        logging.info(f"{youtube_id} - Seconds response received - {len(response.text)=}")
        chat_session.history.append({"role": "model", "parts": [response.text]})
        
        follow_up_message = f"Make it even shorter. Just merge chapters into bigger categories. Provide the final response. Only few chapters with just the big picture."
        response = chat_session.send_message(follow_up_message)
        logging.info(f"{youtube_id} - {response.text} - {len(response.text)=}")
        return response.text[:MAX_RESPONSE_LENGTH]
