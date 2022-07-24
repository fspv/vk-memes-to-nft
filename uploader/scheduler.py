import hashlib
import logging
import os
from typing import List

import sqlalchemy

import vk.api
from follower.main import get_new_posts
from uploader.models import NFT, create_database
from uploader.utils import download_and_generate_hash, reupload_photo, strip_tags

db_engine = sqlalchemy.create_engine("sqlite:///test.db")
db_session = create_database(db_engine)

logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)
logging.getLogger().setLevel(logging.DEBUG)


_VK_COMMUNITY = os.environ["VK_COMMUNITY"]
_VK_SERVICE_TOKEN = os.environ["VK_SERVICE_TOKEN"]


def schedule_local() -> List[int]:
    scheduled: List[int] = []

    photo_dir = "../opensea-upload/memy/out/"

    files = sorted([file for file in os.listdir(photo_dir) if file.endswith(".jpg")])

    for file in files:
        with open(photo_dir + file, "rb") as fd:
            content = fd.read()

            photo_hash = hashlib.sha256(content).hexdigest()

        description = ""
        description_file = file + "_description.txt"

        if os.path.exists(photo_dir + description_file):
            with open(photo_dir + description_file) as fd:
                description = fd.read()

        file_id = int(file.split("_")[0])

        if db_session.query(NFT).filter_by(hash=photo_hash).first():
            continue

        nft = NFT(
            id=file_id,
            hash=photo_hash,
            url="file://" + file,
            title=f"Mem #{file_id}",
            description=strip_tags(description),
            uploaded=True,
        )

        db_session.add(nft)
        db_session.flush()
        db_session.refresh(nft)

        scheduled.append(nft.id)

    db_session.commit()

    return scheduled


def schedule() -> List[int]:
    scheduled: List[int] = []

    new_posts = get_new_posts(_VK_SERVICE_TOKEN, _VK_COMMUNITY)

    for post in new_posts:
        if post.is_pinned:
            continue

        already_uploaded = False

        for attachment in post.attachments:
            if isinstance(attachment, vk.api.Photo):
                for size in attachment.sizes:
                    photo_hash = download_and_generate_hash(size.url)

                    found_nft = db_session.query(NFT).filter_by(hash=photo_hash).first()

                    if found_nft:
                        logging.info("NFT found in database: %s", found_nft)
                        already_uploaded = True

        if already_uploaded:
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
                    description=strip_tags(post.text),
                )

                db_session.add(nft)
                db_session.flush()
                db_session.refresh(nft)

                nft.title = f"Mem #{nft.id}"

                scheduled.append(nft.id)

    db_session.commit()

    return scheduled


# schedule_local()
schedule()
