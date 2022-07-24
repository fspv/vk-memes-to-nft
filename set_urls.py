import hashlib
import json
import logging
import os
import time

import requests
import sqlalchemy
import tqdm

from uploader.models import NFT, create_database

logging.basicConfig()
# logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)
# logging.getLogger().setLevel(logging.DEBUG)

db_engine = sqlalchemy.create_engine("sqlite:///test.db")
db_session = create_database(db_engine)


def download(url: str) -> bytes:
    response = requests.get(url)

    return response.content


def download_and_generate_hash(url: str) -> str:
    content = download(url)

    return hashlib.sha256(content).hexdigest()


session = requests.Session()

with open("urls.txt") as fd:
    lines = fd.readlines()[:]
    for pos, line in tqdm.tqdm(enumerate(lines), total=len(lines)):
        opensea_url = line.strip()
        _, _, _, _, _, address, number = opensea_url.split("/")

        if db_session.query(NFT).filter_by(opensea_url=opensea_url).first():
            continue

        time.sleep(1)

        try:
            url = f"https://api.opensea.io/api/v1/asset/{address}/{number}?format=json"

            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.53 Safari/537.36",
            }

            response = session.get(url, headers=headers)

            data = json.loads(response.text)

            if data.get("success", True):
                image_url = data["image_url"] + "=s0"

                image_hash = download_and_generate_hash(image_url)

                found_nft = db_session.query(NFT).filter_by(hash=image_hash).first()

                if found_nft:
                    if found_nft.opensea_url:
                        if found_nft.opensea_url != opensea_url:
                            opensea = int(data["name"].split("#")[1])
                            database = int(found_nft.title.split("#")[1])

                            if database < opensea:
                                print(
                                    f"NFT {data['name']} is a duplicate for {found_nft.title}"
                                )
                                continue
                            else:
                                print(
                                    f"Overwriting {found_nft.title} by {data['name']}"
                                )

                    if found_nft.url.startswith("file://"):
                        found_nft.url = image_url

                    found_nft.title = data["name"]
                    found_nft.description = data["description"]
                    found_nft.opensea_url = opensea_url

                    print(found_nft)
            db_session.commit()
        except Exception as e:
            logging.exception(e)
