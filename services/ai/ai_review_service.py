from ai_review.models import AIReviewResult
from audit.models import AuditLog
from services.audit.audit_service import create_audit_log

from . import gemini_client


def run_ai_review(*, content, user, content_version=None):
    """
    Runs an AI grammar/clarity review on the given content and
    stores the result.

    This is best-effort: if the AI call fails (no API key, network
    issue, bad response, etc.) the failure is captured on the
    AIReviewResult record with status=FAILED instead of being
    raised. This is deliberate — a broken AI call should never
    block a human from submitting or reviewing content.
    """

    result = AIReviewResult.objects.create(
        content=content,
        content_version=content_version,
        status=AIReviewResult.Status.PENDING,
    )

    try:
        review = gemini_client.review_text(
            title=content.title,
            body=content.body,
        )

        result.status = AIReviewResult.Status.COMPLETED
        result.score = review.get("score")
        result.summary = review.get("summary", "")
        result.issues = review.get("issues", [])
        result.save()

        create_audit_log(
            content=content,
            user=user,
            action=AuditLog.Action.AI_REVIEW,
            details=(
                f"AI pre-review completed. Score: {result.score}. "
                f"{len(result.issues)} issue(s) flagged."
            ),
        )

    except Exception as exc:
        result.status = AIReviewResult.Status.FAILED
        result.error_message = str(exc)
        result.save()

        create_audit_log(
            content=content,
            user=user,
            action=AuditLog.Action.AI_REVIEW,
            details=f"AI pre-review failed: {exc}",
        )

    return result