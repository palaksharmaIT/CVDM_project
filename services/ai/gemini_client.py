# import json
# import os

# from google import genai


# REVIEW_PROMPT_TEMPLATE = """
# You are an editorial assistant reviewing a draft before it goes to a
# human reviewer. Review the following content for grammar and clarity
# issues only. Do not comment on factual accuracy, tone, or opinions.

# Title: {title}

# Body:
# {body}

# Respond with ONLY valid JSON, no markdown fences, in this exact shape:
# {{
#   "score": <integer 0-100, overall grammar/clarity quality>,
#   "summary": "<one or two sentence summary of the writing quality>",
#   "issues": [
#     {{
#       "type": "grammar" | "clarity",
#       "message": "<what is wrong>",
#       "suggestion": "<how to fix it>"
#     }}
#   ]
# }}
# If there are no issues, return an empty issues list.
# """


# def _get_client():
#     api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

#     if not api_key:
#         raise RuntimeError(
#             "GEMINI_API_KEY (or GOOGLE_API_KEY) is not set. "
#             "Add it to your .env file to enable AI review."
#         )

#     return genai.Client(api_key=api_key)


# def _strip_markdown_fence(raw_text):
#     text = raw_text.strip()

#     if not text.startswith("```"):
#         return text

#     text = text.strip("`")

#     if "\n" in text:
#         first_line, rest = text.split("\n", 1)
#         if first_line.strip().lower() in ("json", ""):
#             return rest.strip()

#     return text.strip()


# def review_text(*, title, body, model="gemini-3.5-flash-lite"):
#     """
#     Calls Gemini to review the given title/body for grammar and
#     clarity issues. Returns a dict: {score, summary, issues}.
#     Raises RuntimeError / ValueError on failure — callers should
#     catch these and store the failure rather than let it propagate.
#     """

#     client = _get_client()

#     prompt = REVIEW_PROMPT_TEMPLATE.format(title=title, body=body)

#     response = client.models.generate_content(
#         model=model,
#         contents=prompt,
#     )

#     raw_text = _strip_markdown_fence(response.text or "")

#     try:
#         parsed = json.loads(raw_text)
#     except json.JSONDecodeError as exc:
#         raise ValueError(
#             f"AI response was not valid JSON: {raw_text[:200]}"
#         ) from exc

#     return {
#         "score": parsed.get("score"),
#         "summary": parsed.get("summary", ""),
#         "issues": parsed.get("issues", []),
#     }

import json
import os

from google import genai


REVIEW_PROMPT_TEMPLATE = """
You are an editorial assistant reviewing a draft before it goes to a
human reviewer. Review the following content for grammar and clarity
issues only. Do not comment on factual accuracy, tone, or opinions.

Title: {title}

Body:
{body}

Respond with ONLY valid JSON, no markdown fences, in this exact shape:
{{
  "score": <integer 0-100, overall grammar/clarity quality>,
  "summary": "<one or two sentence summary of the writing quality>",
  "issues": [
    {{
      "type": "grammar" | "clarity",
      "message": "<what is wrong>",
      "suggestion": "<how to fix it>"
    }}
  ]
}}
If there are no issues, return an empty issues list.
"""

CATEGORY_PROMPT_TEMPLATE = """
Classify the following piece of editorial content into exactly one
of these categories: tech, finance, marketing, health, general.

Title: {title}

Body:
{body}

Respond with ONLY the category id, lowercase, no punctuation, no
markdown fences — for example: tech
"""

VALID_CATEGORIES = {"tech", "finance", "marketing", "health", "general"}


def _get_client():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY (or GOOGLE_API_KEY) is not set. "
            "Add it to your .env file to enable AI review."
        )

    return genai.Client(api_key=api_key)


def _strip_markdown_fence(raw_text):
    text = raw_text.strip()

    if not text.startswith("```"):
        return text

    text = text.strip("`")

    if "\n" in text:
        first_line, rest = text.split("\n", 1)
        if first_line.strip().lower() in ("json", ""):
            return rest.strip()

    return text.strip()


def review_text(*, title, body, model="gemini-3.5-flash-lite"):
    """
    Calls Gemini to review the given title/body for grammar and
    clarity issues. Returns a dict: {score, summary, issues}.
    Raises RuntimeError / ValueError on failure — callers should
    catch these and store the failure rather than let it propagate.
    """

    client = _get_client()

    prompt = REVIEW_PROMPT_TEMPLATE.format(title=title, body=body)

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    raw_text = _strip_markdown_fence(response.text or "")

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"AI response was not valid JSON: {raw_text[:200]}"
        ) from exc

    return {
        "score": parsed.get("score"),
        "summary": parsed.get("summary", ""),
        "issues": parsed.get("issues", []),
    }


def detect_category(*, title, body, model="gemini-3.5-flash-lite"):
    """
    Calls Gemini to classify the content into one of VALID_CATEGORIES.
    Returns the category id (str). Raises RuntimeError / ValueError on
    failure or an unrecognized category — callers should catch these
    and treat detection as best-effort.
    """

    client = _get_client()

    prompt = CATEGORY_PROMPT_TEMPLATE.format(title=title, body=body)

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    category = _strip_markdown_fence(response.text or "").strip().lower()

    if category not in VALID_CATEGORIES:
        raise ValueError(f"Unrecognized category from AI: {category!r}")

    return category