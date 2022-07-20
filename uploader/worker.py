import abc
import json
import logging
import os
import pathlib
import subprocess
import tempfile
import urllib.parse
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from typing import Generic, Iterator, List, TypeVar, Union

import requests
import sqlalchemy

from uploader.models import NFT, create_database

db_engine = sqlalchemy.create_engine("sqlite:///test.db")
db_session = create_database(db_engine)

_UploaderParams = TypeVar("_UploaderParams")


@dataclass
class PropertyOpenseaUploaderStuct:
    pass


@dataclass
class LevelOpenseaUploaderStuct:
    pass


@dataclass
class StatOpenseaUploaderStuct:
    pass


# pylint: disable=too-many-instance-attributes
@dataclass
class NFTOpenseaUploaderStuct:
    file_path: str
    nft_name: str
    external_link: str = ""
    description: str = ""
    collection: str = ""
    properties: List[PropertyOpenseaUploaderStuct] = field(default_factory=list)
    levels: List[LevelOpenseaUploaderStuct] = field(default_factory=list)
    stats: List[StatOpenseaUploaderStuct] = field(default_factory=list)
    unlockable_content: List[Union[str, bool]] = field(default_factory=list)
    explicit_and_sensitive_content: bool = False
    supply: int = 0
    blockchain: str = ""


@dataclass
class ResultOpenseaUploaderStuct:
    nft: List[NFTOpenseaUploaderStuct] = field(default_factory=list)


@dataclass
class ImageFileOpenseaUploaderStuct:
    file_path: str
    description: str


class WorkerBase(abc.ABC, Generic[_UploaderParams]):
    """
    Worker uploads given NFTs into theee destination

    This is a generic class, concrete implementation should be defined in a subclass
    """

    _ids: List[int]

    def __init__(self, ids: List[int], uploader_params: _UploaderParams) -> None:
        """
        1. Downloads files
        2. Initialises uploader
        3. Executes the uploader with files to upload
        """
        self._ids = ids
        self._uploader_params = uploader_params

    @lru_cache(None)
    def _download(self, url: str, dst_dir: str) -> pathlib.Path:
        """
        Downloads a specified file into a destination directory

        Returns a path to the donwloaded file
        """

        logging.info("Downloading %s to %s", url, dst_dir)

        response = requests.get(url)

        descriptor, tmp_file = tempfile.mkstemp(
            dir=dst_dir, suffix=os.path.splitext(urllib.parse.urlparse(url).path)[1]
        )

        with open(descriptor, "wb") as dst_file:
            dst_file.write(response.content)

        return pathlib.Path(tmp_file)

    def _get_files(self) -> Iterator[pathlib.Path]:
        tmp_dir = tempfile.mkdtemp()

        for nft in db_session.query(NFT).filter(NFT.id.in_(self._ids)):
            logging.info("Downloading NFT %s", nft)

            yield self._download(nft.url, tmp_dir)

    def _upload(self) -> None:
        """
        Method should be implemented in the subclass

        Should contain a logic to perform an upload to a specific destination
        """
        raise NotImplementedError()

    def _mark_complete(self) -> None:
        """
        Mark all the nfts as uploaded, preventing other workers to grab them
        """

        for nft in db_session.query(NFT).filter(NFT.id.in_(self._ids)):
            logging.info("Marking %s upload as complete", nft)
            nft.uploaded = True

        db_session.commit()

    def upload(self) -> None:
        self._upload()
        self._mark_complete()


@dataclass
class OpenseaAutomaticUploaderAuthData:
    password: str = ""
    recovery_phrase: str = ""
    private_key: str = ""
    user_data: str = ""
    profile: str = ""
    two_captcha_key: str = ""


@dataclass
class OpenseaAutomaticUploaderParams:
    collection: str
    uploader_dir: str
    auth_data: OpenseaAutomaticUploaderAuthData


class UploaderBase(abc.ABC, Generic[_UploaderParams]):
    """
    Uploaded has an implementation of a specific upload logic to a specific platform
    """

    _params: _UploaderParams

    def __init__(self, params: _UploaderParams) -> None:
        self._params = params

    def upload(self, files: Iterator[pathlib.Path]) -> None:
        """
        To be implemented in a subclass
        """
        raise NotImplementedError()


class OpenseaAutomaticUploader(UploaderBase):
    def __init__(self, params: OpenseaAutomaticUploaderParams) -> None:
        super().__init__(params)

    def _get_nfts(
        self, image_files: List[ImageFileOpenseaUploaderStuct], collection: str = ""
    ) -> Iterator[NFTOpenseaUploaderStuct]:
        for _, image_file in enumerate(image_files):
            yield NFTOpenseaUploaderStuct(
                file_path=image_file.file_path,
                nft_name="Mem",
                collection=collection,
                description=image_file.description,
            )

    def upload(self, files: Iterator[pathlib.Path]) -> None:
        # Write json file with the list of nft needed by the nft uploader
        result = ResultOpenseaUploaderStuct(
            list(
                self._get_nfts(
                    [ImageFileOpenseaUploaderStuct(str(file), "") for file in files],
                    self._params.collection,
                )
            )
        )

        logging.info("Generated upload file for opensea uploader %s", result)

        # Write image list
        with open(
            self._params.uploader_dir + "/data/test.json", "w", encoding="utf-8"
        ) as file:
            file.write(json.dumps(asdict(result)))

        # Write auth data
        with open(
            self._params.uploader_dir + "/assets/data.json", "w", encoding="utf-8"
        ) as file:
            file.write(json.dumps(asdict(self._params.auth_data)))

        # Run the uploader
        process = subprocess.Popen(
            "python main.py",
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            shell=True,
            cwd=self._params.uploader_dir,
        )
        stdout, stderr = process.communicate(input=b"\n2\n1\n1\n1\n4\n2\n\n")
        exit_code = process.wait()

        logging.info(stdout)
        logging.info(stderr)
        logging.info(exit_code)

        if exit_code != 0:
            raise RuntimeError(
                f"Upload failed with exit code {exit_code}, "
                f"stdout: {stdout}, "
                f"stderr: {stderr}"
            )


class OpenseaAutomaticWorker(WorkerBase[OpenseaAutomaticUploaderParams]):
    def __init__(
        self, ids: List[int], uploader_params: OpenseaAutomaticUploaderParams
    ) -> None:
        super().__init__(ids, uploader_params)

        self._uploader = OpenseaAutomaticUploader(uploader_params)

    def _upload(self) -> None:
        self._uploader.upload(self._get_files())