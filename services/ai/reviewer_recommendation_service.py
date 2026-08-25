from workflow.models import ReviewAssignment


def get_recommended_reviewers(*, content, eligible_reviewers):
    """
    Ranks eligible_reviewers for the given content by:
      1. expertise  — how many times this reviewer has completed a
         review for content in the same category (highest first)
      2. workload   — how many pending review assignments this
         reviewer currently has (lowest first, as a tiebreaker)

    Returns a list of dicts, sorted best-fit first:
        [{"reviewer": <User>, "workload": <int>,
          "expertise_count": <int>, "recommended": <bool>}, ...]

    Pure DB lookups only — no AI call here, so this never fails and
    stays fast at assignment time. The category itself is set
    earlier, best-effort, by detect_and_set_category().
    """

    ranked = []

    for reviewer in eligible_reviewers:
        workload = ReviewAssignment.objects.filter(
            reviewer=reviewer,
            status=ReviewAssignment.Status.PENDING,
        ).count()

        expertise_count = ReviewAssignment.objects.filter(
            reviewer=reviewer,
            status=ReviewAssignment.Status.COMPLETED,
            content__category=content.category,
        ).count()

        ranked.append({
            "reviewer": reviewer,
            "workload": workload,
            "expertise_count": expertise_count,
            "recommended": False,
        })

    ranked.sort(key=lambda r: (-r["expertise_count"], r["workload"]))

    if ranked:
        ranked[0]["recommended"] = True

    return ranked