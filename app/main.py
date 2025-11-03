from authx.exceptions import AuthXException
from fastapi import FastAPI, HTTPException, Depends, Request
from dotenv import load_dotenv
import os

from app.config.auth import security
from app.routes import user, project_route

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.include_router(user.router)

app.include_router(project_route.router)

load_dotenv()

api_key = os.getenv("MAILJET_API_KEY")
api_secret = os.getenv("MAILJET_SECRET_KEY")
sender_email = os.getenv("SENDER_EMAIL")
sender_name = os.getenv("SENDER_NAME")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/protected", dependencies=[Depends(security.access_token_required)])
def protected():
    return {"message": "Hello World"}

@app.exception_handler(AuthXException)
async def authx_exception_handler(request: Request, exc: AuthXException):
    raise HTTPException(status_code=403, detail=str(exc))