import os

import uvicorn
from dotenv import load_dotenv

if __name__ == "__main__":

    load_dotenv(".env")

    uvicorn.run(
        "src.app:app", host=os.getenv("HOST"), port=int(os.getenv("PORT")), reload=True
    )
