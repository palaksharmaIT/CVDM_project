import requests
from django.conf import settings


def send_verification_email(username, recipient_email, verify_url):
    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json",
    }

    payload = {
        "sender": {
            "name": settings.BREVO_SENDER_NAME,
            "email": settings.BREVO_SENDER_EMAIL,
        },
        "to": [
            {
                "email": recipient_email,
            }
        ],
        "subject": "Verify your CVDM account",
        "textContent": (
            f"Hi {username},\n\n"
            "Click the link below to verify your email "
            "and activate your CVDM account:\n\n"
            f"{verify_url}\n\n"
            "If you didn't request this, ignore this email."
        ),
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=10,
    )

    response.raise_for_status()

    print(f"Verification email sent to {recipient_email}. Response: {response.json()}")

    return response.json()