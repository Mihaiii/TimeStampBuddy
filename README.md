# **TimeStampBuddy**

Tag [**@TimeStampBuddy**](https://x.com/timestampbuddy) on X (formerly Twitter) with the link to a YouTube video, and it will provide timestamps.

---
## **Cost to Run**

Gemini is free.

HF Space is free.

Supabase is free.

Twitter API is free.

**The cost to run this bot solution is $0**.

## **How to Run**

Install deps:
```bash
pip install -r requirements.txt
```

The main run command is:

```bash
python cron_processor.py
```

### **Environment Setup**

Before running it locally, configure the environment variables:  
Create a `.env` file in the **TimeStampBuddy** folder/directory and populate it with values for the following keys:  

```
COLLECT_CRON_INTERVAL_SEC = 900
PROCESSOR_IDLE_INTERVAL_SEC = 300
PROCESSOR_ACTIVE_INTERVAL_SEC = 20
MAX_PARALLEL_MESSAGES = 1
X_CONSUMER_KEY = ""
X_CONSUMER_SECRET = ""
X_ACCESS_TOKEN = ""
X_ACCESS_TOKEN_SECRET = ""
X_USERID = ""
SUPABASE_URL = ""
SUPABASE_KEY = ""
GEMINI_MODEL = "gemini-2.0-flash-exp"
GEMINI_API_KEY = ""
YT_TRANSCRIPT_PROXY = ""
```

### **Key Descriptions**

- **COLLECT_CRON_INTERVAL_SEC** – The interval (in seconds) for calling X (Twitter) to gather the latest messages mentioning the bot user (e.g., TimeStampBuddy).  
  > *Note: Be mindful of Twitter's rate limits:* [X API Rate Limits](https://developer.x.com/en/docs/x-api/rate-limits).  

- **PROCESSOR_IDLE_INTERVAL_SEC** – The wait time (in seconds) for the message processor (the service that fetches timestamps based on Twitter messages) when no messages are available to process.  

- **PROCESSOR_ACTIVE_INTERVAL_SEC** – The wait time (in seconds) for the message processor (the service that fetches timestamps based on Twitter messages) when messages are available to process. Note that the interval applies between batches of messages, where each batch can contain a maximum number of messages equal to the value of MAX_PARALLEL_MESSAGES. When setting the value for this variable, consider Gemini's RPM (requests per minute) rate limits.

- **MAX_PARALLEL_MESSAGES** – The maximum number of messages that can be processed simultaneously.  

- **X_CONSUMER_KEY, X_CONSUMER_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET** – These values are provided when you create a [Developer account on X (Twitter)](https://developer.x.com/en).  

- **X_USERID** – The bot user's ID. Refer to: [Get User ID](https://developer.x.com/en/docs/x-api/users/lookup/api-reference/get-users-id).  

- **SUPABASE_URL, SUPABASE_KEY** – These values are available after setting up a [Supabase account](https://supabase.com/).  

- **GEMINI_MODEL** – The name of the Gemini model used to generate timestamps based on video transcripts.  

- **GEMINI_API_KEY** – Obtain this key from [Google AI Studio](https://aistudio.google.com/library) → "Get API Key".  

- **YT_TRANSCRIPT_PROXY** – The proxy URL if the service is hosted in the cloud. Leave it empty if you don't want to use a proxy. Refer to this [GitHub Issue](https://github.com/jdepoix/youtube-transcript-api/issues/303) for more details.

## **Hosting**

The service behind the [@TimeStampBuddy account on X](https://x.com/timestampbuddy) is hosted for free on a Huggingface Space. 

The source files can be inspected here: https://huggingface.co/spaces/Mihaiii/TimeStampBuddy/tree/main .
