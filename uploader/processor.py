import logging
import os

import sqlalchemy

from uploader.models import NFT, create_database
from uploader.worker import (
    OpenseaAutomaticUploaderAuthData,
    OpenseaAutomaticUploaderParams,
    OpenseaAutomaticWorker,
)

_METAMASK_PASSWORD = os.environ["METAMASK_PASSWORD"]
_METAMASK_RECOVERY_PHRASE = os.environ["METAMASK_RECOVERY_PHRASE"]
_TWO_CAPTCHA_KEY = os.environ["TWO_CAPTCHA_KEY"]
_OPENSEA_COLLECTION = os.environ["OPENSEA_COLLECTION"]
_OPENSEA_UPLOADER_DIR = os.environ["OPENSEA_UPLOADER_DIR"]

logging.getLogger().setLevel(logging.DEBUG)

db_engine = sqlalchemy.create_engine("sqlite:///test.db")
db_session = create_database(db_engine)


def process() -> None:
    """
    Process "to upload" NFT queue

    This is a temporary solution, before we have a proper queue

    In the absense of a queue, we just take all the NFTs that are not uploaded
    yet and spin up an upload worker for each one of them
    """
    upload_queue = db_session.query(NFT).filter_by(uploaded=False)

    uploader_params = OpenseaAutomaticUploaderParams(
        collection=_OPENSEA_COLLECTION,
        uploader_dir=_OPENSEA_UPLOADER_DIR,
        auth_data=OpenseaAutomaticUploaderAuthData(
            password=_METAMASK_PASSWORD,
            recovery_phrase=_METAMASK_RECOVERY_PHRASE,
            two_captcha_key=_TWO_CAPTCHA_KEY,
        ),
    )
    worker = OpenseaAutomaticWorker([nft.id for nft in upload_queue], uploader_params)
    worker.upload()


process()
