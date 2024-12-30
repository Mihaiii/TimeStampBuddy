from . import BasePlatform
from typing import List, Tuple, Dict
from misc import TSBMessage, Status
import os
import logging
from tweepy.asynchronous import AsyncClient
import requests
from urllib.parse import urlparse
import re


class Twitter(BasePlatform):
    def __init__(self):
        consumer_key = os.environ.get("X_CONSUMER_KEY", "")
        consumer_secret = os.environ.get("X_CONSUMER_SECRET", "")
        access_token = os.environ.get("X_ACCESS_TOKEN", "")
        access_token_secret = os.environ.get("X_ACCESS_TOKEN_SECRET", "")

        self.client = AsyncClient(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )
        self.timestampbuddy_userid = os.environ.get("X_USERID", "")

    async def gather_messages(self, since_message_id: str) -> List[TSBMessage]:
        logging.debug("gather_messages")
        response = await self.client.get_users_mentions(
            id=self.timestampbuddy_userid,
            expansions="author_id",
            user_auth=True,
            max_results=100,
            since_id=since_message_id,
        )
        logging.info(response)
        if not response.data:
            return []
        return [
            TSBMessage(
                status=Status.empty.value,
                msg_text=m.text,
                msg_from=next(
                    x.username
                    for x in response.includes["users"]
                    if x.id == m.author_id
                ),
                msg_id=m["id"],
            )
            for m in response.data
        ]

    async def reply(self, text: str, platform_message_id: str) -> None:
        logging.debug("reply")
        response = await self.client.create_tweet(
            text=text, in_reply_to_tweet_id=platform_message_id
        )
        logging.info(response)

    def get_original_url(self, message_text: str) -> str:
        logging.debug("get_original_url")

        # https://stackoverflow.com/a/6041965
        url_pattern = r"(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])"

        match = re.search(url_pattern, message_text)
        url = match.group(0) if match else message_text
        logging.info(f"first url in msg or msg if no url: {url}")
        try:
            parsed_url = urlparse(url)

            if parsed_url.netloc == "t.co":
                response = requests.head(url, allow_redirects=True)
                logging.info(response.url)
                return response.url

            return url
        except Exception as e:
            return url

    def get_max_response_length(self) -> int:
        return 280