import hashlib
import logging
import os
from functools import lru_cache
from typing import List

import requests
import sqlalchemy
import vk.api
from follower.main import get_new_posts

from uploader.models import NFT, create_database

# from typing import List


db_engine = sqlalchemy.create_engine("sqlite:///test.db")
db_session = create_database(db_engine)

logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)
logging.getLogger().setLevel(logging.DEBUG)


_VK_COMMUNITY = os.environ["VK_COMMUNITY"]
_VK_SERVICE_TOKEN = os.environ["VK_SERVICE_TOKEN"]


@lru_cache(None)
def download(url: str) -> bytes:
    response = requests.get(url)

    return response.content


def upload(content: bytes) -> str:
    return ""


def download_and_generate_hash(url: str) -> str:
    content = download(url)

    return hashlib.sha256(content).hexdigest()


def reupload_photo(url: str) -> str:
    upload(download(url))  # TODO: assign new url here
    return url


def schedule() -> List[int]:
    scheduled: List[int] = []

    new_posts = get_new_posts(_VK_SERVICE_TOKEN, _VK_COMMUNITY)

    for post in new_posts:
        if post.is_pinned:
            continue

        for attachment in post.attachments:
            if isinstance(attachment, vk.api.Photo):
                largest_photo = sorted(attachment.sizes)[-1]
                largest_photo_hash = reupload_photo(largest_photo.url)

                if db_session.query(NFT).filter_by(hash=largest_photo_hash).first():
                    continue

                nft = NFT(
                    hash=download_and_generate_hash(largest_photo.url),
                    url=largest_photo_hash,
                )

                db_session.add(nft)
                db_session.flush()
                db_session.refresh(nft)

                scheduled.append(nft.id)

    db_session.commit()

    return scheduled


schedule()
