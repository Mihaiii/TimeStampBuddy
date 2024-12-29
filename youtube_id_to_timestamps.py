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
    def __init__(self):
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
        self.proxy = os.environ.get("YT_TRANSCRIPT_PROXY", "")

    def _seconds_to_hhmmss(self, seconds):
        td = timedelta(seconds=round(seconds))
        return str(td)

    def _get_transcript(self, youtube_id):
        logging.info(f"{youtube_id} - making the request to get the transcript")
        proxies = {"https": self.proxy, "http": self.proxy} if self.proxy else None
        #TODO: get the language from the text from the tweet
        data = YouTubeTranscriptApi.get_transcript(youtube_id, languages=['en', 'es', 'de'], proxies=proxies)
        logging.info(f"{youtube_id} - got the transcript. First 5 objs: {data[:5]}")
        transformed_data = [
            {
                "text": item["text"],
                "start": self._seconds_to_hhmmss(item["start"])
            }
            for item in data
        ]
        return json.dumps(transformed_data, indent=4)

    def _upload_to_gemini(self, file_content, mime_type=None):
        with tempfile.NamedTemporaryFile(suffix=".tmp", mode='w+', encoding='utf-8') as tmpfile:
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
                "Attached you have the transcript of a YouTube video. It's a JSON file that has the following properties: text - what is said, meaning the actual transcript, start: the second of that fragment in the video.\n\nI want you to make a summary of the video based on that transcript data and also include the timestamps (make sure they are in HH:MM:SS format), meaning between what hour, minute and second in the video a generated topic/idea is mentioned. Make the topics short. Have lots of topics. Have one topic per line and each line starts with the timestamps.\n\nHere is an example of how your response look like. Pay attention to the format. This is the summary for another video:\n\n0:00 - Introduction\n2:03 - Startup philosophy\n9:34 - Low points\n13:03 - 12 startups in 12 months\n19:55 - Traveling and depression\n32:34 - Indie hacking\n36:37 - Photo AI\n1:12:53 - How to learn AI\n1:21:30 - Robots\n1:29:47 - Hoodmaps\n1:53:52 - Learning new programming languages\n2:03:24 - Monetize your website\n2:09:59 - Fighting SPAM\n2:13:33 - Automation\n2:24:58 - When to sell startup\n2:27:52 - Coding solo\n2:33:54 - Ship fast\n2:42:38 - Best IDE for programming\n2:52:09 - Andrej Karpathy\n3:01:34 - Productivity\n3:15:21 - Minimalism\n3:24:07 - Emails\n3:31:20 - Coffee\n3:39:05 - E/acc\n3:41:21 - Advice for young people\n\nDon't make it too granular. Extract the main ideas/chapters and present them. Only have a chapter at every few minutes, like in the example. Mention as timestamp the beginning of each chapter. See the provided example from above for a better understanding.\n",
            ]
        }

        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(initial_message['parts'])
        logging.info(f"{youtube_id} - First response received")
        chat_session.history.append(
            {
                "role": "model",
                "parts": [response.text]
            }
        )

        follow_up_message = "That's good, but it's too granular. Extract the main ideas/chapters and present them. Only have a chapter at every few minutes, like in the example. Mention as timestamp the beginning of each chapter. See the provided example from above for a better understanding. Answer only with the timestamps and chapters, nothing else."
        response = chat_session.send_message(follow_up_message)
        logging.info(f"{youtube_id} - {response.text}")
        return response.text