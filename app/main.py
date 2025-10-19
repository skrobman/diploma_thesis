from authx.exceptions import AuthXException
from fastapi import FastAPI, HTTPException, Depends, Request
from dotenv import load_dotenv
from mailjet_rest import Client
import os

from app.config.auth import security
from app.routes import user

app = FastAPI()
app.include_router(user.router)

load_dotenv()

api_key = os.getenv("MAILJET_API_KEY")
api_secret = os.getenv("MAILJET_SECRET_KEY")
sender_email = os.getenv("SENDER_EMAIL")
sender_name = os.getenv("SENDER_NAME")

mailjet = Client(auth=(api_key, api_secret), version='v3.1')

@app.post("/send")
def send_email():
    data = {
        'Messages': [
            {
                "From": {
                    "Email": sender_email,
                    "Name": sender_name
                },
                "To": [
                    {
                        "Email": "mikhailskrobat@gmail.com",
                        "Name": "Получатель"
                    }
                ],
                "Subject": "Тестовое письмо через Mailjet + FastAPI",
                "TextPart": "Привет! Это тестовое письмо из FastAPI 🚀",
                "HTMLPart": "<h3>Привет 👋</h3><p>Письмо успешно отправлено через <b>Mailjet</b>!</p>"
            }
        ]
    }

    result = mailjet.send.create(data=data)
    return {
        "status": result.status_code,
        "response": result.json()
    }

@app.get("/protected", dependencies=[Depends(security.access_token_required)])
def protected():
    return {"message": "Hello World"}

@app.exception_handler(AuthXException)
async def authx_exception_handler(request: Request, exc: AuthXException):
    raise HTTPException(status_code=403, detail=str(exc))