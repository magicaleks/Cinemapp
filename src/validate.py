from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field


class BaseModel(PydanticBaseModel):

    model_config = {"extra": "ignore", "frozen": False}


class FilmIn(BaseModel):

    name: str


class FilmOut(BaseModel):

    uid: str = Field(validation_alias="_id")
    name: str


class LikeIn(BaseModel):

    uid: str


class UserIn(BaseModel):

    username: str
    password: str


class UserOut(BaseModel):

    uid: str = Field(validation_alias="_id")
    username: str
    password_hash: str
    likes: list[str]


class TokenOut(BaseModel):

    access_token: str
