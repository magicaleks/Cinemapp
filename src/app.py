import pickle
import uuid

from fastapi import (APIRouter, Depends, FastAPI, HTTPException, Query,
                     Response, status)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from passlib.context import CryptContext

from src.auth import JWTBearer, signJWT
from src.data import (MongoClient, RedisClient, get_cache_session,
                      get_db_session)
from src.validate import FilmIn, FilmOut, LikeIn, TokenOut, UserIn, UserOut

jwt_scheme = JWTBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="Cinemapp")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
    allow_credentials=True,
)

api = APIRouter(prefix="/api")


@api.post("/user/signup")
async def signup(user: UserIn, db: MongoClient = Depends(get_db_session)):

    data = {
        "_id": str(uuid.uuid4()),
        "username": user.username,
        "password_hash": pwd_context.hash(user.password),
        "likes": [],
    }

    u = await db.cinemapp.users.find_one({"username": data["username"]})
    if u:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with specified username already exists.",
        )

    await db.cinemapp.users.insert_one(data)

    return UserOut(**data)


@api.post("/user/signin")
async def signin(
    user: UserIn, db: MongoClient = Depends(get_db_session)
):

    user_from_db = await db.cinemapp.users.find_one({"username": user.username})

    if not user_from_db:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    _user = UserOut(**user_from_db)

    if not pwd_context.verify(user.password, _user.password_hash):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    token = signJWT(_user.uid)

    return TokenOut(access_token=token)


@api.post("/films")
async def upload_films(
    films: list[FilmIn], db: MongoClient = Depends(get_db_session)
):

    films_to_insert = [{"_id": str(uuid.uuid4()), "name": film.name} for film in films]

    await db.cinemapp.films.insert_many(films_to_insert)

    return JSONResponse(content={"ok": True})


@api.get("/films")
async def get_films(
    page: int = Query(ge=0, default=0),
    size: int = Query(ge=1, le=100),
    db: MongoClient = Depends(get_db_session),
) -> list[FilmOut]:

    cursor = await db.cinemapp.films.find({}).to_list((page + 1) * size)

    res = [FilmOut(**d) for d in cursor[page * size :]]

    return res


@api.post("/films/like")
async def like_film(
    like: LikeIn, user_id: str = Depends(jwt_scheme), db: MongoClient = Depends(get_db_session),
    cache: RedisClient = Depends(get_cache_session)
):

    await db.cinemapp.users.update_one(
        filter={"_id": user_id}, update={"$push": {"likes": like.uid}}
    )

    await cache.delete(user_id)

    return JSONResponse(content={"ok": True})


@api.delete("/films/like")
async def unlike_film(
    like: LikeIn,
    user_id: str = Depends(jwt_scheme),
    db: MongoClient = Depends(get_db_session),
    cache: RedisClient = Depends(get_cache_session)
) -> Response:

    await db.cinemapp.users.update_one(
        filter={"_id": user_id}, update={"$pull": {"likes": like.uid}}
    )

    await cache.delete(user_id)

    return JSONResponse(content={"ok": True})


@api.get("/films/like")
async def get_liked_films(
    db: MongoClient = Depends(get_db_session),
    user_id: str = Depends(jwt_scheme),
    cache: RedisClient = Depends(get_cache_session),
) -> list[FilmOut]:

    cached_res = await cache.lrange(user_id, 0, -1)
    if cached_res:
        return [FilmOut(**pickle.loads(c)) for c in cached_res]

    user_from_db = await db.cinemapp.users.find_one({"_id": user_id})

    user = UserOut(**user_from_db)

    cursor = await db.cinemapp.films.find({"_id": {"$in": user.likes}}).to_list(None)

    res = [FilmOut(**d) for d in cursor]

    if res:

        await cache.lpush(user_id, *[pickle.dumps(d) for d in cursor])
        await cache.expire(user_id, 300)

    return res


app.include_router(api)
