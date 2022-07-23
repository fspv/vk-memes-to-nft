import enum

# import pg8000
import sqlalchemy
import sqlalchemy.orm
# from google.cloud.sql.connector import connector
from sqlalchemy.orm.decl_api import DeclarativeMeta

mapper_registry = sqlalchemy.orm.registry()


class Base(metaclass=DeclarativeMeta):
    __abstract__ = True
    registry = mapper_registry
    metadata = mapper_registry.metadata

    __init__ = mapper_registry.constructor


class VkPostType(enum.Enum):
    PHOTO = "photo"
    VIDEO = "video"
    LINK = "link"
    # TODO: add all types here


class VkPost(Base):
    __tablename__ = "vk_post"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)

    def __repr__(self) -> str:
        return f"<VkPost(" f"id={self.id}" ")>"


def create_database(engine: sqlalchemy.engine.Engine) -> sqlalchemy.orm.session.Session:
    Base.metadata.create_all(engine)

    session_maker = sqlalchemy.orm.sessionmaker()
    session_maker.configure(bind=engine)
    session = session_maker()
    session.commit()

    return session
