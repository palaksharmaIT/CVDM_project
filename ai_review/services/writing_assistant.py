from google import genai
from django.conf import settings


def generate_writing_suggestion(content, action="improve"):

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY
    )

    prompt = f"""
You are an AI writing assistant.

The user wants to: {action}

Improve the following content while preserving
the original meaning.

Content:
{content}

Return only the improved content.
Do not explain the changes.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )

    return response.text