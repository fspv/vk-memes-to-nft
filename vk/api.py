import copy
import datetime
import json
import logging
from abc import ABC
from dataclasses import dataclass
from http.client import HTTPConnection
from typing import Any, Dict, List, Optional, Union, cast

import requests

from vk.utils import (
    int_to_bool,
    int_to_bool_optional,
    validate_type,
    validate_type_optional,
)

VK_API_URL = "https://api.vk.com/method/"
VK_API_VERSION = "5.131"


def _enable_requests_debug() -> None:
    HTTPConnection.debuglevel = 1

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


class VkApiError(Exception):
    error_code: int
    error_msg: str

    def __init__(self, error_code: int, error_msg: str) -> None:
        super().__init__(error_msg)

        self.error_code = error_code
        self.error_msg = error_msg

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"error_code={self.error_code}, "
            f"error_msg='{self.error_msg}'"
            f")"
        )


@dataclass
class VkApiClientParams:
    service_token: str
    version: str = VK_API_VERSION
    app_id: Optional[int] = None
    secure_key: Optional[str] = None


class VkApiBase:
    _api_url: str = VK_API_URL
    _client_params: VkApiClientParams

    def __init__(self, params: VkApiClientParams, debug: bool = True) -> None:
        self._client_params = params

        self._session = requests.Session()
        self._session.headers["Accept"] = "application/json"
        self._session.headers["Content-Type"] = "application/x-www-form-urlencoded"

        if debug:
            _enable_requests_debug()

    def query(self, method: str, request: Dict[str, Any]) -> Dict[str, Any]:
        logging.debug("Request: %s", request)

        # Add auth and version to the request
        tmp_request = copy.deepcopy(request)
        tmp_request["access_token"] = self._client_params.service_token
        tmp_request["v"] = self._client_params.version

        json_response = self._session.get(
            self._api_url + method, params=tmp_request
        ).text

        response = json.loads(json_response)

        api_error = response.get("error")
        api_response = response.get("response")

        if api_error:
            raise VkApiError(api_error["error_code"], api_error["error_msg"])

        return api_response

        # TODO FIXME remove
        # decoder = json.JSONDecoder(strict=False)
        # response_parsed = decoder.raw_decode(response)


@dataclass
class UtilsResolveScreenNameResult:
    type: str  # user, group, application
    object_id: int


class VkApiUtils(VkApiBase):
    def resolve_screen_name(self, screen_name: str) -> UtilsResolveScreenNameResult:
        result = self.query("utils.resolveScreenName", {"screen_name": screen_name})

        object_type, object_id = result["type"], result["object_id"]

        return UtilsResolveScreenNameResult(object_type, object_id)


ObjectIdType = int
UserIdType = int


@dataclass
class PostCommentsInfo:
    count: int
    can_post: bool
    groups_can_post: bool


@dataclass
class PostLikesInfo:
    count: int
    user_likes: bool
    can_like: bool
    can_publish: bool


@dataclass
class PostRepostsInfo:
    count: int
    user_reposted: bool


@dataclass
class PostSource:
    type: str  # vk, widget, api, rss, sms
    platform: Optional[str]  # android, iphone, wphone
    url: Optional[str]
    data: Optional[str]  # profile_activity, profile_photo, comments, like, poll


@dataclass
class PlaceDescription:
    id: int
    title: str
    latitude: int
    longtitude: int
    created: datetime.datetime
    icon: str
    country: str
    city: str
    type: Optional[int] = None
    group_id: Optional[int] = None
    group_photo: Optional[str] = None
    checkins: Optional[int] = None
    updated: Optional[datetime.datetime] = None
    address: Optional[int] = None


@dataclass
class PostGeoInfo:
    type: str
    coordinates: str
    place: PlaceDescription


@dataclass
class Attachment(ABC):
    pass


@dataclass
class AttachmentOwned(Attachment):
    id: ObjectIdType
    owner_id: UserIdType


@dataclass
class PhotoSize:
    type: str
    url: str
    width: int
    height: int

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, PhotoSize):
            raise ValueError("Can't compare photo size to something else")

        order: List[str] = ["s", "m", "o", "p", "q", "r", "x", "y", "z", "w"]

        return order.index(self.type) < order.index(other.type)


@dataclass
class Photo(AttachmentOwned):
    album_id: ObjectIdType
    user_id: Optional[UserIdType]
    text: str
    date: datetime.datetime
    sizes: List[PhotoSize]
    width: Optional[int]
    height: Optional[int]


@dataclass
class DirectlyUploadedPhoto(AttachmentOwned):
    photo_130: str
    photo_604: str


@dataclass
class Video(AttachmentOwned):
    title: str
    description: str
    duration: str
    photo_130: Optional[str]
    photo_320: Optional[str]
    photo_640: Optional[str]
    photo_800: Optional[str]
    date: datetime.datetime
    adding_date: Optional[datetime.datetime]
    views: int
    comments: int
    player: str
    access_key: str
    is_favourite: Optional[bool]
    processing: Optional[bool]
    live: Optional[bool]
    upcoming: Optional[bool]
    image: List[PhotoSize]


@dataclass
class Artist:
    id: str
    name: str
    domain: str


@dataclass
class Audio(AttachmentOwned):
    artist: str
    title: str
    duration: int
    is_explicit: bool
    is_focus_track: bool
    track_code: str
    url: str
    date: datetime.datetime
    album_id: int
    short_videos_allowed: bool
    stories_allowed: bool
    stories_cover_allowed: bool
    main_artists: List[Artist]


@dataclass
class Document(Attachment):
    def __init__(self) -> None:
        raise NotImplementedError("")


@dataclass
class Graffiti(AttachmentOwned):
    photo_130: str
    photo_604: str


@dataclass
class Product:
    def __init__(self) -> None:
        # TODO: implement
        raise NotImplementedError("")


@dataclass
class Button:
    def __init__(self) -> None:
        # TODO: implement
        raise NotImplementedError("")


@dataclass
class Link(Attachment):
    url: str
    title: str
    caption: Optional[str]
    description: Optional[str]
    photo: Optional[Photo]
    is_external: Optional[bool]
    product: Optional[Product]
    button: Optional[Button]
    preview_page: Optional[str]
    preview_url: Optional[str]
    type: str = "link"


@dataclass
class Note(Attachment):
    def __init__(self) -> None:
        # TODO: implement
        raise NotImplementedError("")


@dataclass
class ApplicationContent(AttachmentOwned):
    photo_130: str
    photo_604: str


@dataclass
class Poll(AttachmentOwned):
    def __init__(self) -> None:
        # TODO: implement
        raise NotImplementedError("")


@dataclass
class WikiPage(Attachment):
    def __init__(self) -> None:
        # TODO: implement
        raise NotImplementedError("")


@dataclass
class PhotoAlbum(AttachmentOwned):
    thumb: Photo
    title: str
    description: str
    created: datetime.datetime
    updated: datetime.datetime
    size: int


Photos = List[int]


@dataclass
class Currency:
    id: int
    name: str
    title: str


@dataclass
class Price:
    amount: str
    text: str
    currency: Currency


@dataclass
class MarketCategorySection:
    id: int
    name: str


@dataclass
class MarketCategory:
    id: int
    name: str
    section: MarketCategorySection


@dataclass
class Market(AttachmentOwned):
    availability: int
    description: str
    title: str
    thumb_photo: str
    category: MarketCategory
    price: Price


def attachment_factory(attachment: Dict[str, Any]) -> Attachment:
    logging.debug("Original attachment: %s", attachment)

    attachment_type = validate_type(attachment["type"], str)
    data = validate_type(attachment[attachment_type], dict)

    logging.debug("Detected type: %s", attachment_type)

    if attachment_type == "photo":
        photo = Photo(
            id=validate_type(data["id"], int),
            owner_id=validate_type(data["owner_id"], int),
            album_id=validate_type(data["album_id"], ObjectIdType),
            user_id=validate_type_optional(data.get("user_id"), UserIdType),
            text=validate_type(data["text"], str),
            date=datetime.datetime.fromtimestamp(validate_type(data["date"], int)),
            sizes=[],
            width=validate_type_optional(data.get("width"), int),
            height=validate_type_optional(data.get("height"), int),
        )

        for size_raw in data["sizes"]:
            size = PhotoSize(
                type=validate_type(size_raw["type"], str),
                url=validate_type(size_raw["url"], str),
                width=validate_type(size_raw["width"], int),
                height=validate_type(size_raw["height"], int),
            )

            photo.sizes.append(size)

        return photo

    if attachment_type == "posted_photo":
        return DirectlyUploadedPhoto(
            id=validate_type(data["id"], int),
            owner_id=validate_type(data["owner_id"], int),
            photo_130=validate_type(data["photo_130"], str),
            photo_604=validate_type(data["photo_604"], str),
        )

    if attachment_type == "link":
        product_raw = data.get("product")
        product: Optional[Product] = None

        if product_raw:
            product = Product()

        button_raw = data.get("button")
        button: Optional[Button] = None

        if button_raw:
            button = Button()

        return Link(
            url=validate_type(data["url"], str),
            title=validate_type(data["title"], str),
            caption=validate_type_optional(data.get("caption"), str),
            description=validate_type_optional(data.get("description"), str),
            photo=cast(
                Photo, attachment_factory({"type": "photo", "photo": data["photo"]})
            )
            if "photo" in data
            else None,
            is_external=validate_type_optional(data.get("is_external"), bool),
            product=product,
            button=button,
            preview_page=validate_type_optional(data.get("preview_page"), str),
            preview_url=validate_type_optional(data.get("preview_url"), str),
        )

    if attachment_type == "video":
        sizes_raw = data["image"] or []
        sizes: List[PhotoSize] = []

        for size_raw in sizes_raw:
            sizes.append(
                PhotoSize(
                    type="",
                    url=validate_type(size_raw["url"], str),
                    width=validate_type(size_raw["width"], int),
                    height=validate_type(size_raw["height"], int),
                )
            )

        adding_data_raw = validate_type_optional(data.get("adding_date"), int)

        return Video(
            id=validate_type(data["id"], int),
            owner_id=validate_type(data["owner_id"], int),
            title=validate_type(data["title"], str),
            description=validate_type(data["description"], str),
            duration=validate_type(data["duration"], int),
            photo_130=validate_type_optional(data.get("photo_130"), str),
            photo_320=validate_type_optional(data.get("photo_320"), str),
            photo_640=validate_type_optional(data.get("photo_640"), str),
            photo_800=validate_type_optional(data.get("photo_800"), str),
            date=datetime.datetime.fromtimestamp(validate_type(data["date"], int)),
            adding_date=datetime.datetime.fromtimestamp(adding_data_raw)
            if adding_data_raw
            else None,
            views=validate_type(data["views"], int),
            comments=validate_type_optional(data.get("comments"), int),
            player=validate_type_optional(data.get("player"), str),
            access_key=validate_type(data["access_key"], str),
            is_favourite=int_to_bool_optional(
                validate_type_optional(data.get("is_favourite"), int)
            ),
            processing=int_to_bool_optional(
                validate_type_optional(data.get("processing"), int)
            ),
            live=int_to_bool_optional(validate_type_optional(data.get("live"), int)),
            upcoming=int_to_bool_optional(
                validate_type_optional(data.get("upcoming"), int)
            ),
            image=sizes,
        )

    if attachment_type == "audio":
        return Audio(
            id=validate_type(data["id"], int),
            artist=validate_type(data["artist"], str),
            owner_id=validate_type(data["owner_id"], int),
            title=validate_type(data["title"], str),
            duration=validate_type(data["duration"], int),
            is_explicit=validate_type(data["is_explicit"], bool),
            is_focus_track=validate_type(data["is_focus_track"], bool),
            track_code=validate_type(data["track_code"], str),
            url=validate_type(data["url"], str),
            date=datetime.datetime.fromtimestamp(validate_type(data["date"], int)),
            album_id=validate_type(data["album_id"], int),
            main_artists=[
                Artist(
                    name=validate_type(artist["name"], str),
                    domain=validate_type(artist["domain"], str),
                    id=validate_type(artist["id"], str),
                )
                for artist in data["main_artists"]
            ],
            short_videos_allowed=validate_type(data["short_videos_allowed"], bool),
            stories_allowed=validate_type(data["stories_allowed"], bool),
            stories_cover_allowed=validate_type(data["stories_cover_allowed"], bool),
        )

    if attachment_type == "market":
        return Market(
            id=validate_type(data["id"], int),
            owner_id=validate_type(data["owner_id"], int),
            availability=validate_type(data["availability"], int),
            category=MarketCategory(
                id=validate_type(data["category"]["id"], int),
                name=validate_type(data["category"]["name"], str),
                section=MarketCategorySection(
                    id=validate_type(data["category"]["section"]["id"], int),
                    name=validate_type(data["category"]["section"]["name"], str),
                ),
            ),
            description=validate_type(data["description"], str),
            price=Price(
                amount=validate_type(data["price"]["amount"], str),
                text=validate_type(data["price"]["text"], str),
                currency=Currency(
                    id=validate_type(data["price"]["currency"]["id"], int),
                    name=validate_type(data["price"]["currency"]["name"], str),
                    title=validate_type(data["price"]["currency"]["title"], str),
                ),
            ),
            title=validate_type(data["title"], str),
            thumb_photo=validate_type(data["thumb_photo"], str),
        )

    raise NotImplementedError(
        f"Attachment of type {attachment_type} is not defined: {data}"
    )


@dataclass
class PostCopyHistoryItem:
    def __init__(self) -> None:
        # TODO: not specified in the doc, what this object should contain
        raise NotImplementedError()


@dataclass
class Post:
    id: ObjectIdType
    owner_id: UserIdType
    from_id: ObjectIdType
    date: datetime.datetime
    text: str
    comments: PostCommentsInfo
    likes: PostLikesInfo
    reposts: PostRepostsInfo
    post_type: str  # post, copy, reply, postpone, suggest
    post_source: PostSource
    attachments: List[Attachment]
    marked_as_ads: bool
    created_by: Optional[UserIdType]
    reply_owner_id: Optional[UserIdType]
    reply_post_id: Optional[ObjectIdType]
    friends_only: Optional[bool]
    geo: Optional[PostGeoInfo]
    signer_id: Optional[UserIdType]
    copy_history: Optional[List[PostCopyHistoryItem]]
    can_pin: Optional[bool]
    can_delete: Optional[bool]
    can_edit: Optional[bool]
    is_favourite: Optional[bool]
    is_pinned: Optional[bool]


@dataclass
class Wall:
    count: int
    items: List[Post]


class VkApiWall(VkApiBase):
    def get(
        self,
        domain: str,
        offset: int,
        count: int,
        owner_id: Optional[int] = None,
        _filter: Optional[str] = None,
        extended: Optional[bool] = None,
        fields: Optional[List[str]] = None,
    ) -> Wall:
        query: Dict[str, Union[int, str]] = {}

        if owner_id:
            query["owner_id"] = owner_id

        if _filter:
            query["filter"] = _filter

        if extended:
            query["extended"] = extended

        if fields:
            query["fields"] = ",".join(fields)

        query["domain"] = domain
        query["offset"] = offset
        query["count"] = count

        response = self.query("wall.get", query)

        result = Wall(response["count"], [])

        for post_raw in response["items"]:
            geo_raw = validate_type_optional(post_raw.get("geo"), dict)
            geo: Optional[PostGeoInfo] = None

            if geo_raw:
                geo = PostGeoInfo(
                    type=validate_type(geo_raw["type"], str),
                    coordinates=validate_type(geo_raw["coordinates"], int),
                    place=PlaceDescription(
                        id=validate_type(geo_raw["place"]["id"], ObjectIdType),
                        title=validate_type(geo_raw["place"]["tile"], str),
                        latitude=validate_type(geo_raw["place"]["latitude"], int),
                        longtitude=validate_type(geo_raw["place"]["longtitude"], int),
                        created=datetime.datetime.fromtimestamp(
                            validate_type(geo_raw["place"]["created"], int)
                        ),
                        icon=validate_type(geo_raw["place"]["icon"], str),
                        country=validate_type(geo_raw["place"]["country"], str),
                        city=validate_type(geo_raw["place"]["city"], str),
                        type=validate_type(geo_raw["place"]["type"], int),
                    ),
                )

            attachments_raw = post_raw.get("attachments", [])
            attachments: List[Attachment] = []

            for attachment_raw in attachments_raw:
                attachment = attachment_factory(attachment_raw)
                attachments.append(attachment)

            post = Post(
                id=validate_type(post_raw["id"], ObjectIdType),
                owner_id=validate_type(post_raw["owner_id"], UserIdType),
                from_id=validate_type(post_raw["from_id"], UserIdType),
                created_by=validate_type_optional(
                    post_raw.get("created_by"), UserIdType
                ),
                date=datetime.datetime.fromtimestamp(
                    validate_type(post_raw["date"], int)
                ),
                text=validate_type(post_raw["text"], str),
                reply_owner_id=validate_type_optional(
                    post_raw.get("reply_owner_id"), UserIdType
                ),
                reply_post_id=validate_type_optional(
                    post_raw.get("reply_post_id"), ObjectIdType
                ),
                friends_only=validate_type_optional(post_raw.get("friends_only"), bool),
                comments=PostCommentsInfo(
                    validate_type(
                        validate_type(post_raw["comments"], dict)["count"], int
                    ),
                    int_to_bool(validate_type(post_raw["comments"], dict)["can_post"]),
                    int_to_bool(
                        validate_type(post_raw["comments"], dict)["groups_can_post"]
                    ),
                ),
                likes=PostLikesInfo(
                    count=validate_type(
                        validate_type(post_raw["likes"], dict)["count"], int
                    ),
                    user_likes=int_to_bool(
                        validate_type(post_raw["likes"], dict)["user_likes"]
                    ),
                    can_like=int_to_bool(
                        validate_type(post_raw["likes"], dict)["can_like"]
                    ),
                    can_publish=int_to_bool(
                        validate_type(post_raw["likes"], dict)["can_publish"]
                    ),
                ),
                reposts=PostRepostsInfo(
                    count=validate_type(
                        validate_type(post_raw["reposts"], dict)["count"], int
                    ),
                    user_reposted=int_to_bool(
                        validate_type(post_raw["reposts"], dict)["user_reposted"]
                    ),
                ),
                post_type=validate_type(post_raw["post_type"], str),
                post_source=PostSource(
                    type=validate_type(
                        validate_type(post_raw["post_source"], dict)["type"], str
                    ),
                    platform=validate_type_optional(
                        validate_type(post_raw["post_source"], dict).get("platform"),
                        str,
                    ),
                    url=validate_type_optional(
                        validate_type(post_raw["post_source"], dict).get("url"), str
                    ),
                    data=validate_type_optional(
                        validate_type(post_raw["post_source"], dict).get("data"), str
                    ),
                ),
                attachments=attachments,
                geo=geo,
                signer_id=validate_type_optional(post_raw.get("signer_id"), UserIdType),
                copy_history=None,  # TODO FIXME
                can_pin=int_to_bool_optional(
                    validate_type_optional(post_raw.get("can_pin"), int)
                ),
                can_delete=int_to_bool_optional(
                    validate_type_optional(post_raw.get("can_delete"), int)
                ),
                can_edit=int_to_bool_optional(
                    validate_type_optional(post_raw.get("can_edit"), int)
                ),
                is_pinned=int_to_bool_optional(
                    validate_type_optional(post_raw.get("is_pinned"), int)
                ),
                marked_as_ads=int_to_bool(
                    validate_type(post_raw["marked_as_ads"], int)
                ),
                is_favourite=int_to_bool_optional(
                    validate_type_optional(post_raw.get("is_favourite"), int)
                ),
            )

            result.items.append(post)

        return result
