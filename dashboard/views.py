# from django.contrib.auth.decorators import login_required
# from django.shortcuts import get_object_or_404, redirect, render
# from django.db.models import Q
# from django.utils import timezone
# from django.utils.dateparse import parse_datetime
# from django.contrib import messages
# from django.contrib.auth import (
#     authenticate,
#     login as auth_login,
#     logout as auth_logout,
#     get_user_model,
# )
# from django.contrib.auth.models import Group
# from django.contrib.auth.password_validation import validate_password
# from django.core.exceptions import ValidationError as DjangoValidationError
# from django.conf import settings as dj_settings
# from django.core.mail import send_mail
# from django.urls import reverse

# from accounts.models import EmailVerification

# from content.models import Content
# from versions.models import ContentVersion
# from ai_review.models import AIReviewResult
# from notifications.models import Notification
# from workflow.models import ReviewAssignment
# from audit.models import AuditLog

# from services.content.content_service import (
#     create_content,
#     update_content,
#     restore_version,
#     submit_for_review,
#     approve_content,
#     reject_content,
#     publish_content,
#     schedule_content,
#     cancel_scheduled_publish,
# )
# from services.ai.ai_review_service import run_ai_review
# from services.content.diff_service import compute_version_diff
# from services.workflow.assignment_service import assign_reviewer


# @login_required
# def dashboard(request):
#     contents = Content.objects.all()

#     unread_notifications = (
#         Notification.objects
#         .filter(
#             user=request.user,
#             is_read=False,
#         )
#         .select_related("content")
#         .order_by("-created_at")
#     )

#     review_queue = (
#         ReviewAssignment.objects
#         .filter(
#             reviewer=request.user,
#             status=ReviewAssignment.Status.PENDING,
#         )
#         .select_related("content", "assigned_by")
#         .order_by("-assigned_at")
#     )

#     recent_activity = (
#         AuditLog.objects
#         .select_related("content", "user")
#         .exclude(
#             Q(
#                 action=AuditLog.Action.AI_REVIEW,
#                 details__startswith="AI pre-review failed:"
#             )
#         )
#     .order_by("-created_at")[:10]
# )

#     context = {
#         "total_content": contents.count(),

#         "draft_count": contents.filter(
#             status=Content.Status.DRAFT
#         ).count(),

#         "review_count": contents.filter(
#             status=Content.Status.IN_REVIEW
#         ).count(),

#         "approved_count": contents.filter(
#             status=Content.Status.APPROVED
#         ).count(),

#         "published_count": contents.filter(
#             status=Content.Status.PUBLISHED
#         ).count(),

#         "unread_notifications": unread_notifications,
#         "unread_notification_count": unread_notifications.count(),

#         "review_queue": review_queue,

#         "recent_activity": recent_activity,

#         "current_username": request.user.username,
#         "current_roles": list(
#             request.user.groups.values_list("name", flat=True)
#         ) or (["Admin"] if request.user.is_superuser else []),
#     }

#     return render(
#         request,
#         "dashboard/dashboard.html",
#         context,
#     )


# @login_required
# def review_content(request, content_id):

#     content = get_object_or_404(
#         Content.objects.select_related("created_by"),
#         id=content_id,
#     )

#     # Make sure this reviewer is actually assigned
#     assignment = get_object_or_404(
#         ReviewAssignment,
#         content=content,
#         reviewer=request.user,
#         status=ReviewAssignment.Status.PENDING,
#     )

#     latest_version = (
#         content.versions
#         .order_by("-version_number")
#         .first()
#     )

#     latest_ai_review = (
#         content.ai_reviews
#         .order_by("-created_at")
#         .first()
#     )

#     if request.method == "POST":

#         action = request.POST.get("action")

#         if action == "approve":
#             approve_content(
#                 content=content,
#                 user=request.user,
#             )
#             messages.success(request, "Content approved.")

#             return redirect("dashboard")

#         if action == "reject":
#             reject_content(
#                 content=content,
#                 user=request.user,
#             )
#             messages.success(request, "Content rejected.")

#             return redirect("dashboard")

#     context = {
#         "content": content,
#         "assignment": assignment,
#         "latest_version": latest_version,
#         "latest_ai_review": latest_ai_review,
#     }

#     return render(
#         request,
#         "dashboard/review_content.html",
#         context,
#     )


# @login_required
# def content_list(request):

#     search = request.GET.get(
#         "search",
#         "",
#     ).strip()

#     status_filter = request.GET.get(
#         "status",
#         "",
#     ).strip()

#     author_filter = request.GET.get(
#         "author",
#         "",
#     ).strip()


#     contents = (
#         Content.objects
#         .select_related("created_by")
#         .all()
#     )


#     # Search by title or body
#     if search:

#         contents = contents.filter(
#             Q(title__icontains=search)
#             | Q(body__icontains=search)
#         )


#     # Filter by status
#     if status_filter:

#         contents = contents.filter(
#             status=status_filter
#         )


#     # Filter by author
#     if author_filter:

#         contents = contents.filter(
#             created_by_id=author_filter
#         )


#     # Get users who have created content
#     User = get_user_model()

#     authors = (
#         User.objects
#         .filter(
#             created_content__isnull=False
#         )
#         .distinct()
#         .order_by("username")
#     )


#     context = {
#         "contents": contents,

#         "search": search,

#         "status_filter": status_filter,

#         "author_filter": author_filter,

#         "status_choices": Content.Status.choices,

#         "authors": authors,

#         "can_create": _user_has_role(
#             request.user,
#             "Author",
#             "Admin",
#         ),
#     }


#     return render(
#         request,
#         "dashboard/content_list.html",
#         context,
#     )

# @login_required
# def content_create(request):

#     if not _user_has_role(request.user, "Author", "Admin"):
#         messages.error(request, "You don't have permission to create content.")
#         return redirect("content_list")

#     if request.method == "POST":
#         title = request.POST.get("title", "").strip()
#         body = request.POST.get("body", "").strip()

#         if not title:
#             messages.error(request, "Title is required.")
#         else:
#             content = create_content(title=title, body=body, user=request.user)
#             messages.success(request, "Draft created.")
#             return redirect("content_edit", content_id=content.id)

#     return render(request, "dashboard/content_create.html", {})


# @login_required
# def content_edit(request, content_id):
#     """
#     The main workbench: edit + save version, run AI review, submit
#     for review, assign a reviewer, approve/reject, publish, or
#     schedule a publish. Which actions are shown depends on the
#     user's role and the content's current status.
#     """

#     content = get_object_or_404(
#         Content.objects.select_related("created_by"),
#         id=content_id,
#     )

#     is_author = content.created_by_id == request.user.id
#     is_reviewer = _user_has_role(request.user, "Reviewer", "Admin")
#     is_editor = _user_has_role(request.user, "Editor", "Admin")

#     can_edit = (
#         is_author
#         and content.status in (
#             Content.Status.DRAFT, Content.Status.REJECTED
#         )
#     ) or (
#         is_editor
#         and content.status != Content.Status.PUBLISHED
#     )
#     can_submit = is_author and content.status == Content.Status.DRAFT
#     can_approve_reject = is_reviewer and content.status == Content.Status.IN_REVIEW
#     can_publish = is_editor and content.status == Content.Status.APPROVED
#     can_assign = (is_author or is_editor) and content.status != Content.Status.PUBLISHED

#     if request.method == "POST":
#         action = request.POST.get("action")

#         try:
#             if action == "save" and can_edit:
#                 title = request.POST.get("title", "").strip()
#                 body = request.POST.get("body", "")
#                 if not title:
#                     raise ValueError("Title can't be empty.")
#                 update_content(content=content, title=title, body=body, user=request.user)
#                 messages.success(request, "Version saved.")

#             elif action == "run_ai" and can_edit:
#                 latest_version = content.versions.order_by("-version_number").first()
#                 run_ai_review(content=content, user=request.user, content_version=latest_version)
#                 messages.success(request, "AI review complete.")

#             elif action == "submit" and can_submit:
#                 submit_for_review(content=content, user=request.user)
#                 messages.success(request, "Submitted for review.")

#             elif action == "approve" and can_approve_reject:
#                 approve_content(content=content, user=request.user)
#                 messages.success(request, "Content approved.")

#             elif action == "reject" and can_approve_reject:
#                 reject_content(content=content, user=request.user)
#                 messages.success(request, "Content rejected.")

#             elif action == "publish" and can_publish:
#                 publish_content(content=content, user=request.user)
#                 messages.success(request, "Content published.")

#             elif action == "schedule" and can_publish:
#                 raw = request.POST.get("scheduled_at", "")
#                 when = parse_datetime(raw)
#                 if when is None:
#                     raise ValueError("Pick a valid date and time.")
#                 if timezone.is_naive(when):
#                     when = timezone.make_aware(when)
#                 schedule_content(content=content, user=request.user, scheduled_at=when)
#                 messages.success(request, f"Scheduled to publish at {when.strftime('%d %b %Y, %I:%M %p')}.")

#             elif action == "cancel_schedule" and can_publish:
#                 cancel_scheduled_publish(content=content, user=request.user)
#                 messages.success(request, "Scheduled publish cancelled.")

#             elif action == "assign" and can_assign:
#                 reviewer_id = request.POST.get("reviewer_id")
#                 note = request.POST.get("note", "")
#                 from django.contrib.auth import get_user_model
#                 User = get_user_model()
#                 reviewer = get_object_or_404(User, id=reviewer_id)
#                 assign_reviewer(content=content, reviewer=reviewer, assigned_by=request.user, note=note)
#                 messages.success(request, f"Assigned {reviewer.username} as reviewer.")

#             elif action == "restore":
#                 version_id = request.POST.get("version_id")
#                 version = get_object_or_404(ContentVersion, id=version_id, content=content)
#                 restore_version(content=content, version=version, user=request.user)
#                 messages.success(request, f"Restored from version {version.version_number}.")

#             else:
#                 messages.error(request, "That action isn't available right now.")

#         except ValueError as exc:
#             messages.error(request, str(exc))

#         return redirect("content_edit", content_id=content.id)

#     versions = content.versions.all()
#     latest_ai_review = content.ai_reviews.order_by("-created_at").first()
#     assignments = content.review_assignments.select_related("reviewer").order_by("-assigned_at")

#     eligible_reviewers = []
#     if can_assign:
#         from django.contrib.auth import get_user_model
#         User = get_user_model()
#         eligible_reviewers = User.objects.filter(
#             groups__name__in=["Reviewer", "Admin"]
#         ).distinct()

#     context = {
#         "content": content,
#         "versions": versions,
#         "latest_ai_review": latest_ai_review,
#         "assignments": assignments,
#         "eligible_reviewers": eligible_reviewers,
#         "can_edit": can_edit,
#         "can_submit": can_submit,
#         "can_approve_reject": can_approve_reject,
#         "can_publish": can_publish,
#         "can_assign": can_assign,
#     }

#     return render(request, "dashboard/content_edit.html", context)


# @login_required
# def content_diff(request, content_id):

#     content = get_object_or_404(Content, id=content_id)
#     versions = list(content.versions.order_by("version_number"))

#     diff = None
#     from_id = request.GET.get("from")
#     to_id = request.GET.get("to")

#     if to_id:
#         new_version = get_object_or_404(ContentVersion, id=to_id, content=content)
#         old_version = None
#         if from_id:
#             old_version = get_object_or_404(ContentVersion, id=from_id, content=content)
#         else:
#             old_version = content.versions.filter(
#                 version_number=new_version.version_number - 1
#             ).first()

#         diff = compute_version_diff(old_version=old_version, new_version=new_version)

#     context = {
#         "content": content,
#         "versions": versions,
#         "diff": diff,
#         "from_id": from_id,
#         "to_id": to_id,
#     }

#     return render(request, "dashboard/content_diff.html", context)


# def public_articles_list(request):
#     """
#     Public, no-login-required list of published articles. This is
#     the "readers" view of the site — separate from the internal
#     /dashboard/ workflow tool.
#     """

#     articles = Content.objects.filter(
#         status=Content.Status.PUBLISHED
#     ).order_by("-published_at")

#     return render(
#         request,
#         "dashboard/public_articles_list.html",
#         {"articles": articles},
#     )


# def public_article_detail(request, content_id):

#     article = get_object_or_404(
#         Content,
#         id=content_id,
#         status=Content.Status.PUBLISHED,
#     )

#     return render(
#         request,
#         "dashboard/public_article_detail.html",
#         {"article": article},
#     )


# def _user_has_role(user, *roles):
#     if user.is_superuser:
#         return True
#     return user.groups.filter(name__in=roles).exists()


# def login_view(request):

#     if request.user.is_authenticated:
#         return redirect("dashboard")

#     next_url = request.GET.get("next", "")
#     User = get_user_model()

#     if request.method == "POST":
#         username = request.POST.get("username", "").strip()
#         password = request.POST.get("password", "")
#         next_url = request.POST.get("next", "") or next_url

#         candidate = User.objects.filter(username=username).first()

#         if (
#             candidate
#             and not candidate.is_active
#             and candidate.check_password(password)
#         ):
#             messages.error(
#                 request,
#                 "Please verify your email before signing in. "
#                 "Check your inbox for the verification link.",
#             )
#         else:
#             user = authenticate(request, username=username, password=password)

#             if user is not None:
#                 auth_login(request, user)
#                 return redirect(next_url or "dashboard")

#             messages.error(request, "Invalid username or password.")

#     return render(
#         request,
#         "dashboard/login.html",
#         {"next": next_url},
#     )


# def register_view(request):

#     if request.user.is_authenticated:
#         return redirect("dashboard")

#     User = get_user_model()

#     if request.method == "POST":
#         username = request.POST.get("username", "").strip()
#         email = request.POST.get("email", "").strip()
#         password = request.POST.get("password", "")
#         role = request.POST.get("role", "")

#         error = None

#         if not username or not password or not role:
#             error = "All fields are required."
#         elif not email:
#             error = "Email is required for verification."
#         elif User.objects.filter(username=username).exists():
#             error = "A user with that username already exists."
#         elif role not in dj_settings.CVDM_SELF_ASSIGNABLE_ROLES:
#             error = "Please choose a valid role."
#         else:
#             try:
#                 validate_password(password)
#             except DjangoValidationError as exc:
#                 error = " ".join(exc.messages)

#         if error:
#             messages.error(request, error)
#         else:
#             user = User.objects.create_user(
#                 username=username,
#                 email=email,
#                 password=password,
#                 is_active=False,
#             )

#             group, _ = Group.objects.get_or_create(name=role)
#             user.groups.add(group)

#             verification = EmailVerification.objects.create(user=user)

#             verify_url = request.build_absolute_uri(
#                 reverse("verify-email", args=[verification.token])
#             )

#             send_mail(
#                 subject="Verify your CVDM account",
#                 message=(
#                     f"Hi {username},\n\n"
#                     f"Click the link below to verify your email and "
#                     f"activate your CVDM account:\n\n{verify_url}\n\n"
#                     f"If you didn't request this, ignore this email."
#                 ),
#                 from_email=dj_settings.DEFAULT_FROM_EMAIL,
#                 recipient_list=[email],
#                 fail_silently=False,
#             )

#             return render(
#                 request,
#                 "dashboard/check_email.html",
#                 {"email": email},
#             )

#     return render(
#         request,
#         "dashboard/register.html",
#         {"roles": dj_settings.CVDM_SELF_ASSIGNABLE_ROLES},
#     )


# def verify_email_view(request, token):

#     verification = get_object_or_404(EmailVerification, token=token)

#     if not verification.is_verified:
#         verification.is_verified = True
#         verification.verified_at = timezone.now()
#         verification.save(update_fields=["is_verified", "verified_at"])

#         verification.user.is_active = True
#         verification.user.save(update_fields=["is_active"])

#         messages.success(
#             request,
#             "Email verified. You can now sign in.",
#         )
#     else:
#         messages.info(request, "This email was already verified.")

#     return redirect("login")


# def logout_view(request):
#     auth_logout(request)
#     return redirect("login")

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    login as auth_login,
    logout as auth_logout,
    get_user_model,
)
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.conf import settings as dj_settings
from django.core.mail import send_mail
from django.urls import reverse

from accounts.models import EmailVerification

from content.models import Content
from versions.models import ContentVersion
from ai_review.models import AIReviewResult
from notifications.models import Notification
from workflow.models import ReviewAssignment
from audit.models import AuditLog

from services.content.content_service import (
    create_content,
    update_content,
    restore_version,
    submit_for_review,
    approve_content,
    reject_content,
    publish_content,
    schedule_content,
    cancel_scheduled_publish,
)
from services.ai.ai_review_service import run_ai_review
from services.ai.reviewer_recommendation_service import get_recommended_reviewers
from services.content.diff_service import compute_version_diff
from services.workflow.assignment_service import assign_reviewer


@login_required
def dashboard(request):
    if request.user.is_superuser:
        dashboard_role = "Admin"
    elif request.user.groups.filter(name="Reviewer").exists():
        dashboard_role = "Reviewer"
    elif request.user.groups.filter(name="Editor").exists():
        dashboard_role = "Editor"
    elif request.user.groups.filter(name="Author").exists():
        dashboard_role = "Author"
    else:
        dashboard_role = "User"

    if dashboard_role in ("Admin", "Editor"):
        contents = Content.objects.all()
    elif dashboard_role == "Reviewer":
        contents = (
            Content.objects
            .filter(review_assignments__reviewer=request.user)
            .distinct()
        )
    else:
        contents = Content.objects.filter(created_by=request.user)

    unread_notifications = (
        Notification.objects
        .filter(
            user=request.user,
            is_read=False,
        )
        .select_related("content")
        .order_by("-created_at")
    )

    review_queue = (
        ReviewAssignment.objects
        .filter(
            reviewer=request.user,
            status=ReviewAssignment.Status.PENDING,
        )
        .select_related("content", "assigned_by")
        .order_by("-assigned_at")
    )

    recent_activity = (
        AuditLog.objects
        .select_related("content", "user")
        .exclude(
            Q(
                action=AuditLog.Action.AI_REVIEW,
                details__startswith="AI pre-review failed:"
            )
        )
    )

    if dashboard_role == "Author":
        recent_activity = recent_activity.filter(content__created_by=request.user)
    elif dashboard_role == "Reviewer":
        recent_activity = (
            recent_activity
            .filter(content__review_assignments__reviewer=request.user)
            .distinct()
        )

    recent_activity = recent_activity.order_by("-created_at")[:10]

    context = {
        "dashboard_role": dashboard_role,

        "total_content": contents.count(),

        "draft_count": contents.filter(
            status=Content.Status.DRAFT
        ).count(),

        "review_count": contents.filter(
            status=Content.Status.IN_REVIEW
        ).count(),

        "approved_count": contents.filter(
            status=Content.Status.APPROVED
        ).count(),

        "published_count": contents.filter(
            status=Content.Status.PUBLISHED
        ).count(),

        "unread_notifications": unread_notifications,
        "unread_notification_count": unread_notifications.count(),

        "review_queue": review_queue,

        "recent_activity": recent_activity,

        "current_username": request.user.username,
        "current_roles": list(
            request.user.groups.values_list("name", flat=True)
        ) or (["Admin"] if request.user.is_superuser else []),
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )


@login_required
def review_content(request, content_id):

    content = get_object_or_404(
        Content.objects.select_related("created_by"),
        id=content_id,
    )

    # Make sure this reviewer is actually assigned
    assignment = get_object_or_404(
        ReviewAssignment,
        content=content,
        reviewer=request.user,
        status=ReviewAssignment.Status.PENDING,
    )

    latest_version = (
        content.versions
        .order_by("-version_number")
        .first()
    )

    latest_ai_review = (
        content.ai_reviews
        .order_by("-created_at")
        .first()
    )

    if request.method == "POST":

        action = request.POST.get("action")

        if action == "approve":
            approve_content(
                content=content,
                user=request.user,
            )
            messages.success(request, "Content approved.")

            return redirect("dashboard")

        if action == "reject":
            reject_content(
                content=content,
                user=request.user,
            )
            messages.success(request, "Content rejected.")

            return redirect("dashboard")

    context = {
        "content": content,
        "assignment": assignment,
        "latest_version": latest_version,
        "latest_ai_review": latest_ai_review,
    }

    return render(
        request,
        "dashboard/review_content.html",
        context,
    )


@login_required
def content_list(request):

    status_filter = request.GET.get(
        "status",
        "",
    )

    contents = (
        Content.objects
        .select_related("created_by")
        .all()
    )

    if status_filter:

        contents = contents.filter(
            status=status_filter
        )

    context = {
        "contents": contents,
        "status_filter": status_filter,
        "status_choices": Content.Status.choices,
        "can_create": _user_has_role(
            request.user,
            "Author",
            "Admin",
        ),
    }


    return render(
        request,
        "dashboard/content_list.html",
        context,
    )

@login_required
def content_create(request):

    if not _user_has_role(request.user, "Author", "Admin"):
        messages.error(request, "You don't have permission to create content.")
        return redirect("content_list")

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        body = request.POST.get("body", "").strip()

        if not title:
            messages.error(request, "Title is required.")
        else:
            content = create_content(title=title, body=body, user=request.user)
            messages.success(request, "Draft created.")
            return redirect("content_edit", content_id=content.id)

    return render(request, "dashboard/content_create.html", {})


@login_required
def content_edit(request, content_id):
    """
    The main workbench: edit + save version, run AI review, submit
    for review, assign a reviewer, approve/reject, publish, or
    schedule a publish. Which actions are shown depends on the
    user's role and the content's current status.
    """

    content = get_object_or_404(
        Content.objects.select_related("created_by"),
        id=content_id,
    )

    is_author = content.created_by_id == request.user.id
    is_reviewer = _user_has_role(request.user, "Reviewer", "Admin")
    is_editor = _user_has_role(request.user, "Editor", "Admin")

    can_edit = (
        is_author
        and content.status in (
            Content.Status.DRAFT, Content.Status.REJECTED
        )
    ) or (
        is_editor
        and content.status != Content.Status.PUBLISHED
    )
    can_submit = is_author and content.status == Content.Status.DRAFT
    can_approve_reject = is_reviewer and content.status == Content.Status.IN_REVIEW
    can_publish = is_editor and content.status == Content.Status.APPROVED
    can_assign = (is_author or is_editor) and content.status != Content.Status.PUBLISHED

    if request.method == "POST":
        action = request.POST.get("action")

        try:
            if action == "save" and can_edit:
                title = request.POST.get("title", "").strip()
                body = request.POST.get("body", "")
                if not title:
                    raise ValueError("Title can't be empty.")
                update_content(content=content, title=title, body=body, user=request.user)
                messages.success(request, "Version saved.")

            elif action == "run_ai" and can_edit:
                latest_version = content.versions.order_by("-version_number").first()
                run_ai_review(content=content, user=request.user, content_version=latest_version)
                messages.success(request, "AI review complete.")

            elif action == "submit" and can_submit:
                submit_for_review(content=content, user=request.user)
                messages.success(request, "Submitted for review.")

            elif action == "approve" and can_approve_reject:
                approve_content(content=content, user=request.user)
                messages.success(request, "Content approved.")

            elif action == "reject" and can_approve_reject:
                reject_content(content=content, user=request.user)
                messages.success(request, "Content rejected.")

            elif action == "publish" and can_publish:
                publish_content(content=content, user=request.user)
                messages.success(request, "Content published.")

            elif action == "schedule" and can_publish:
                raw = request.POST.get("scheduled_at", "")
                when = parse_datetime(raw)
                if when is None:
                    raise ValueError("Pick a valid date and time.")
                if timezone.is_naive(when):
                    when = timezone.make_aware(when)
                schedule_content(content=content, user=request.user, scheduled_at=when)
                messages.success(request, f"Scheduled to publish at {when.strftime('%d %b %Y, %I:%M %p')}.")

            elif action == "cancel_schedule" and can_publish:
                cancel_scheduled_publish(content=content, user=request.user)
                messages.success(request, "Scheduled publish cancelled.")

            elif action == "assign" and can_assign:
                reviewer_id = request.POST.get("reviewer_id")
                note = request.POST.get("note", "")
                from django.contrib.auth import get_user_model
                User = get_user_model()
                reviewer = get_object_or_404(User, id=reviewer_id)
                assign_reviewer(content=content, reviewer=reviewer, assigned_by=request.user, note=note)
                messages.success(request, f"Assigned {reviewer.username} as reviewer.")

            elif action == "restore":
                version_id = request.POST.get("version_id")
                version = get_object_or_404(ContentVersion, id=version_id, content=content)
                restore_version(content=content, version=version, user=request.user)
                messages.success(request, f"Restored from version {version.version_number}.")

            else:
                messages.error(request, "That action isn't available right now.")

        except ValueError as exc:
            messages.error(request, str(exc))

        return redirect("content_edit", content_id=content.id)

    versions = content.versions.all()
    latest_ai_review = content.ai_reviews.order_by("-created_at").first()
    assignments = content.review_assignments.select_related("reviewer").order_by("-assigned_at")

    eligible_reviewers = []
    reviewer_recommendations = []
    if can_assign:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        eligible_reviewers = User.objects.filter(
            groups__name__in=["Reviewer", "Admin"]
        ).distinct()

        reviewer_recommendations = get_recommended_reviewers(
            content=content,
            eligible_reviewers=eligible_reviewers,
        )

    context = {
        "content": content,
        "versions": versions,
        "latest_ai_review": latest_ai_review,
        "assignments": assignments,
        "eligible_reviewers": eligible_reviewers,
        "reviewer_recommendations": reviewer_recommendations,
        "can_edit": can_edit,
        "can_submit": can_submit,
        "can_approve_reject": can_approve_reject,
        "can_publish": can_publish,
        "can_assign": can_assign,
    }

    return render(request, "dashboard/content_edit.html", context)


@login_required
def content_diff(request, content_id):

    content = get_object_or_404(Content, id=content_id)
    versions = list(content.versions.order_by("version_number"))

    diff = None
    from_id = request.GET.get("from")
    to_id = request.GET.get("to")

    if to_id:
        new_version = get_object_or_404(ContentVersion, id=to_id, content=content)
        old_version = None
        if from_id:
            old_version = get_object_or_404(ContentVersion, id=from_id, content=content)
        else:
            old_version = content.versions.filter(
                version_number=new_version.version_number - 1
            ).first()

        diff = compute_version_diff(old_version=old_version, new_version=new_version)

    context = {
        "content": content,
        "versions": versions,
        "diff": diff,
        "from_id": from_id,
        "to_id": to_id,
    }

    return render(request, "dashboard/content_diff.html", context)


def public_articles_list(request):
    """
    Public, no-login-required list of published articles. This is
    the "readers" view of the site — separate from the internal
    /dashboard/ workflow tool.
    """

    articles = Content.objects.filter(
        status=Content.Status.PUBLISHED
    ).order_by("-published_at")

    return render(
        request,
        "dashboard/public_articles_list.html",
        {"articles": articles},
    )


def public_article_detail(request, content_id):

    article = get_object_or_404(
        Content,
        id=content_id,
        status=Content.Status.PUBLISHED,
    )

    return render(
        request,
        "dashboard/public_article_detail.html",
        {"article": article},
    )


def _user_has_role(user, *roles):
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=roles).exists()


def login_view(request):

    if request.user.is_authenticated:
        return redirect("dashboard")

    next_url = request.GET.get("next", "")
    User = get_user_model()

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        next_url = request.POST.get("next", "") or next_url

        candidate = User.objects.filter(username=username).first()

        if (
            candidate
            and not candidate.is_active
            and candidate.check_password(password)
        ):
            messages.error(
                request,
                "Please verify your email before signing in. "
                "Check your inbox for the verification link.",
            )
        else:
            user = authenticate(request, username=username, password=password)

            if user is not None:
                auth_login(request, user)
                return redirect(next_url or "dashboard")

            messages.error(request, "Invalid username or password.")

    return render(
        request,
        "dashboard/login.html",
        {"next": next_url},
    )


def register_view(request):

    if request.user.is_authenticated:
        return redirect("dashboard")

    User = get_user_model()

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        role = request.POST.get("role", "")

        error = None

        if not username or not password or not role:
            error = "All fields are required."
        elif not email:
            error = "Email is required for verification."
        elif User.objects.filter(username=username).exists():
            error = "A user with that username already exists."
        elif role not in dj_settings.CVDM_SELF_ASSIGNABLE_ROLES:
            error = "Please choose a valid role."
        else:
            try:
                validate_password(password)
            except DjangoValidationError as exc:
                error = " ".join(exc.messages)

        if error:
            messages.error(request, error)
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_active=False,
            )

            group, _ = Group.objects.get_or_create(name=role)
            user.groups.add(group)

            verification = EmailVerification.objects.create(user=user)

            verify_url = request.build_absolute_uri(
                reverse("verify-email", args=[verification.token])
            )

            send_mail(
                subject="Verify your CVDM account",
                message=(
                    f"Hi {username},\n\n"
                    f"Click the link below to verify your email and "
                    f"activate your CVDM account:\n\n{verify_url}\n\n"
                    f"If you didn't request this, ignore this email."
                ),
                from_email=dj_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            return render(
                request,
                "dashboard/check_email.html",
                {"email": email},
            )

    return render(
        request,
        "dashboard/register.html",
        {"roles": dj_settings.CVDM_SELF_ASSIGNABLE_ROLES},
    )


def verify_email_view(request, token):

    verification = get_object_or_404(EmailVerification, token=token)

    if not verification.is_verified:
        verification.is_verified = True
        verification.verified_at = timezone.now()
        verification.save(update_fields=["is_verified", "verified_at"])

        verification.user.is_active = True
        verification.user.save(update_fields=["is_active"])

        messages.success(
            request,
            "Email verified. You can now sign in.",
        )
    else:
        messages.info(request, "This email was already verified.")

    return redirect("login")


def logout_view(request):
    auth_logout(request)
    return redirect("login")