# from . import gemini_client


# def detect_and_set_category(*, content):
#     """
#     Best-effort: detects the content's category via AI and saves it
#     on the content. If the AI call fails (no API key, network issue,
#     bad response, etc.) the category is simply left as-is — this
#     should never block a save.
#     """

#     try:
#         category = gemini_client.detect_category(
#             title=content.title,
#             body=content.body,
#         )
#         content.category = category
#         content.save(update_fields=["category"])

#     except Exception:
#         # Best-effort only — category detection failing should
#         # never block saving/submitting content.
#         pass