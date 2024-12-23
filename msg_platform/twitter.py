from . import BasePlatform
from typing import List, Tuple, Dict
from misc import TSBMessage, Status
import os
import logging
import tweepy

class Twitter(BasePlatform):
    def __init__(self):
        consumer_key = os.environ.get("X_CONSUMER_KEY", '')
        consumer_secret = os.environ.get("X_CONSUMER_SECRET", '')
        access_token = os.environ.get("X_ACCESS_TOKEN", '')
        access_token_secret = os.environ.get("X_ACCESS_TOKEN_SECRET", '')
        print(consumer_key, consumer_secret, access_token, access_token_secret)
        self.client = tweepy.Client(
            consumer_key=consumer_key, consumer_secret=consumer_secret,
            access_token=access_token, access_token_secret=access_token_secret
        )
        self.timestampbuddy_userid = os.environ.get("X_USERID", '')

    async def gather_messages(self, since_message_id: str) -> Tuple[List[TSBMessage], dict[str, str]]:
        logging.debug("gather_messages")
        params = {"id": self.timestampbuddy_userid, "expansions": "author_id", "user_auth": True}
        if since_message_id:
            params["since_id"] = since_message_id
        response = await self.client.get_users_mentions(**params)
        logging.info(response)
        return [TSBMessage(status=Status.empty.value, msg_text=m["text"], msg_from=next(x["username"] for x in response["includes"]["users"] if x["id"] == m["author_id"]), msg_id=m["id"]) for m in response["data"]], response.headers

    async def reply(self, text: str, platform_message_id: str) -> None:
        logging.debug("reply")
        response = await self.client.create_tweet(text=text, in_reply_to_tweet_id=platform_message_id)
        logging.info(response)