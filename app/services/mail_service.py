import asyncio
import os
from mailjet_rest import Client

#MailJet Configuration
api_key = os.getenv("MAILJET_API_KEY")
api_secret = os.getenv("MAILJET_SECRET_KEY")
sender_email = os.getenv("SENDER_EMAIL")
sender_name = os.getenv("SENDER_NAME")

mailjet = Client(auth=(api_key, api_secret), version='v3.1')

async def send_email(to_email: str, subject: str, text: str, html: str):
    data = {
        'Messages': [
            {
                "From": {"Email": sender_email, "Name": sender_name},
                "To": [{"Email": to_email, "Name": to_email}],
                "Subject": subject,
                "TextPart": text,
                "HTMLPart": html
            }
        ]
    }
    result = await asyncio.to_thread(mailjet.send.create, data=data)
    return result.status_code