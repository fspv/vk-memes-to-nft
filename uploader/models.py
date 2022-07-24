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


class NFT(Base):
    """
    NFT to be uploaded somewhere
    """

    __tablename__ = "nft"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    hash = sqlalchemy.Column(
        sqlalchemy.String, comment="Hash of the picture", unique=True
    )

    url = sqlalchemy.Column(sqlalchemy.String, comment="URL of the picture")
    opensea_url = sqlalchemy.Column(
        sqlalchemy.String, comment="URL of the asset on OpenSea"
    )
    title = sqlalchemy.Column(sqlalchemy.String, comment="Title of the NFT")
    description = sqlalchemy.Column(sqlalchemy.String, comment="Description of the NFT")
    uploaded = sqlalchemy.Column(
        sqlalchemy.Boolean, comment="Was NFT uploaded to OpenSea?", default=False
    )

    def __repr__(self) -> str:
        return (
            f"<NFT("
            f"id={self.id}, "
            f"url={self.url}, "
            f"opensea_url={self.opensea_url}, "
            f"title={self.title}, "
            f"description={self.description}, "
            f"hash={self.hash}, "
            f"uploaded={self.uploaded}"
            ")>"
        )


def create_database(engine: sqlalchemy.engine.Engine) -> sqlalchemy.orm.session.Session:
    Base.metadata.create_all(engine)

    session_maker = sqlalchemy.orm.sessionmaker()
    session_maker.configure(bind=engine)
    session = session_maker()
    session.commit()

    return session
