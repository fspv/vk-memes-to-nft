import hashlib
import logging
from functools import lru_cache, wraps
from html.parser import HTMLParser
from io import StringIO
from typing import Any, Callable, Tuple, Type, TypeVar

import requests


class MLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_data(self, data: str) -> None:
        self.text.write(data)

    def get_data(self) -> str:
        return self.text.getvalue()


def strip_tags(html: str) -> str:
    stripper = MLStripper()
    stripper.feed(html)
    return stripper.get_data()


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


_ReturnType = TypeVar("_ReturnType")


class Retry:
    _tries: int
    _retry_exceptions: Tuple[Type[BaseException]]

    def __init__(
        self, tries: int, retry_exceptions: Tuple[Type[BaseException]] = (Exception,)
    ) -> None:
        self._tries = tries
        self._retry_exceptions = retry_exceptions

    def __call__(self, func: Callable[..., _ReturnType]) -> Callable[..., _ReturnType]:
        @wraps(func)
        def wrapped(*args: Any, **kwargs: Any) -> _ReturnType:
            for _try in range(self._tries - 1):
                try:
                    result = func(*args, **kwargs)
                    break
                except self._retry_exceptions:
                    logging.exception(
                        "Func %s failed, retrying %s/%s",
                        func.__name__,
                        _try + 1,
                        self._tries,
                    )
            else:
                result = func(*args, **kwargs)

            return result

        return wrapped


def retry(tries: int) -> Retry:
    return Retry(tries)
