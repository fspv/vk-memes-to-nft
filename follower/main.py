import logging
from typing import List

import sqlalchemy

import vk.api
from follower.models import VkPost, create_database

db_engine = sqlalchemy.create_engine("sqlite:///test.db")
db_session = create_database(db_engine)

logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)


def get_new_posts(vk_service_token: str, vk_community: str) -> List[vk.api.Post]:
    vk_params = vk.api.VkApiClientParams(vk_service_token)

    posts: List[vk.api.Post] = []

    for post in (
        vk.api.VkApiWall(vk_params).get(domain=vk_community, offset=0, count=10).items
    ):
        logging.debug("Got post %s", post)

        if db_session.query(VkPost).filter_by(id=post.id).first():
            logging.debug("Post %s has already been indexed", post.id)
            continue

        logging.info("New post found %s", post.id)

        db_session.add(VkPost(id=post.id))
        db_session.commit()

        posts.append(post)

    return posts
