
from django.contrib.auth.decorators import login_required
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
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

from django.contrib.auth.password_validation import (
    validate_password,
)

from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)

from django.conf import settings as dj_settings

from django.urls import reverse

import requests


from accounts.models import EmailVerification

from content.models import Content

from versions.models import ContentVersion

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

from services.ai.ai_review_service import (
    run_ai_review,
)

from services.content.diff_service import (
    compute_version_diff,
)

from services.workflow.assignment_service import (
    assign_reviewer,
)


# =========================================================
# DASHBOARD
# =========================================================

@login_required
def dashboard(request):

    user = request.user

    if user.is_superuser:
        dashboard_role = "Admin"

    elif user.groups.filter(
        name="Reviewer"
    ).exists():
        dashboard_role = "Reviewer"

    elif user.groups.filter(
        name="Editor"
    ).exists():
        dashboard_role = "Editor"

    elif user.groups.filter(
        name="Author"
    ).exists():
        dashboard_role = "Author"

    else:
        dashboard_role = "User"


    if dashboard_role == "Admin":

        contents = Content.objects.all()

    elif dashboard_role == "Author":

        contents = Content.objects.filter(
            created_by=user
        )

    elif dashboard_role == "Reviewer":

        contents = (
            Content.objects
            .filter(
                review_assignments__reviewer=user
            )
            .distinct()
        )

    elif dashboard_role == "Editor":

        contents = Content.objects.all()

    else:

        contents = Content.objects.filter(
            created_by=user
        )


    unread_notifications = (
        Notification.objects
        .filter(
            user=user,
            is_read=False,
        )
        .select_related("content")
        .order_by("-created_at")
    )


    review_queue = (
        ReviewAssignment.objects
        .filter(
            reviewer=user,
            status=ReviewAssignment.Status.PENDING,
        )
        .select_related(
            "content",
            "assigned_by",
        )
        .order_by("-assigned_at")
    )


    recent_activity = (
        AuditLog.objects
        .select_related(
            "content",
            "user",
        )
        .exclude(
            Q(
                action=AuditLog.Action.AI_REVIEW,
                details__startswith=(
                    "AI pre-review failed:"
                ),
            )
        )
    )


    if dashboard_role == "Author":

        recent_activity = (
            recent_activity
            .filter(
                content__created_by=user
            )
        )

    elif dashboard_role == "Reviewer":

        recent_activity = (
            recent_activity
            .filter(
                content__review_assignments__reviewer=user
            )
            .distinct()
        )


    recent_activity = (
        recent_activity
        .order_by("-created_at")[:10]
    )


    can_create = dashboard_role in [
        "Admin",
        "Author",
    ]

    can_assign = dashboard_role in [
        "Admin",
        "Author",
        "Editor",
    ]


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

        "unread_notifications": (
            unread_notifications
        ),

        "unread_notification_count": (
            unread_notifications.count()
        ),

        "review_queue": review_queue,

        "recent_activity": recent_activity,

        "current_username": user.username,

        "current_roles": list(
            user.groups.values_list(
                "name",
                flat=True,
            )
        ) or (
            ["Admin"]
            if user.is_superuser
            else []
        ),

        "can_create": can_create,

        "can_assign": can_assign,
    }


    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )


# =========================================================
# REVIEW CONTENT
# =========================================================

@login_required
def review_content(request, content_id):

    content = get_object_or_404(
        Content.objects.select_related("created_by"),
        id=content_id,
    )

    # Get the latest pending assignment for this reviewer.
    # Multiple assignments may exist for the same content,
    # so we use filter().first() instead of get().
    assignment = (
        ReviewAssignment.objects
        .filter(
            content=content,
            reviewer=request.user,
            status=ReviewAssignment.Status.PENDING,
        )
        .select_related("assigned_by", "content")
        .order_by("-assigned_at")
        .first()
    )

    if assignment is None:
        messages.error(
            request,
            "You do not have a pending review assignment for this content.",
        )
        return redirect("dashboard")

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

            messages.success(
                request,
                "Content approved.",
            )

            return redirect("dashboard")

        elif action == "reject":

            reject_content(
                content=content,
                user=request.user,
            )

            messages.success(
                request,
                "Content rejected.",
            )

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

# =========================================================
# CONTENT LIST
# =========================================================

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


# =========================================================
# CREATE CONTENT
# =========================================================

@login_required
def content_create(request):

    if not _user_has_role(
        request.user,
        "Author",
        "Admin",
    ):

        messages.error(
            request,
            "You don't have permission to create content.",
        )

        return redirect("content_list")


    if request.method == "POST":

        title = request.POST.get(
            "title",
            "",
        ).strip()

        body = request.POST.get(
            "body",
            "",
        ).strip()


        if not title:

            messages.error(
                request,
                "Title is required.",
            )

        else:

            content = create_content(
                title=title,
                body=body,
                user=request.user,
            )

            messages.success(
                request,
                "Draft created.",
            )

            return redirect(
                "content_edit",
                content_id=content.id,
            )


    return render(
        request,
        "dashboard/content_create.html",
        {},
    )


# =========================================================
# EDIT CONTENT
# =========================================================

@login_required
def content_edit(request, content_id):

    content = get_object_or_404(
        Content.objects.select_related(
            "created_by"
        ),
        id=content_id,
    )


    is_author = (
        content.created_by_id
        == request.user.id
    )

    is_reviewer = _user_has_role(
        request.user,
        "Reviewer",
        "Admin",
    )

    is_editor = _user_has_role(
        request.user,
        "Editor",
        "Admin",
    )


    can_edit = (
        is_author
        and content.status in (
            Content.Status.DRAFT,
            Content.Status.REJECTED,
        )
    )


    can_submit = (
        is_author
        and content.status
        == Content.Status.DRAFT
    )


    can_approve_reject = (
        is_reviewer
        and content.status
        == Content.Status.IN_REVIEW
    )


    can_publish = (
        is_editor
        and content.status
        == Content.Status.APPROVED
    )


    can_assign = (
        (is_author or is_editor)
        and content.status
        != Content.Status.PUBLISHED
    )


    if request.method == "POST":

        action = request.POST.get(
            "action"
        )


        try:

            if action == "save" and can_edit:

                title = request.POST.get(
                    "title",
                    "",
                ).strip()

                body = request.POST.get(
                    "body",
                    "",
                )


                if not title:

                    raise ValueError(
                        "Title can't be empty."
                    )


                update_content(
                    content=content,
                    title=title,
                    body=body,
                    user=request.user,
                )


                messages.success(
                    request,
                    "Version saved.",
                )


            elif (
                action == "run_ai"
                and can_edit
            ):

                latest_version = (
                    content.versions
                    .order_by("-version_number")
                    .first()
                )


                run_ai_review(
                    content=content,
                    user=request.user,
                    content_version=latest_version,
                )


                messages.success(
                    request,
                    "AI review complete.",
                )


            elif (
                action == "submit"
                and can_submit
            ):

                submit_for_review(
                    content=content,
                    user=request.user,
                )


                messages.success(
                    request,
                    "Submitted for review.",
                )


            elif (
                action == "approve"
                and can_approve_reject
            ):

                approve_content(
                    content=content,
                    user=request.user,
                )


                messages.success(
                    request,
                    "Content approved.",
                )


            elif (
                action == "reject"
                and can_approve_reject
            ):

                reject_content(
                    content=content,
                    user=request.user,
                )


                messages.success(
                    request,
                    "Content rejected.",
                )


            elif (
                action == "publish"
                and can_publish
            ):

                publish_content(
                    content=content,
                    user=request.user,
                )


                messages.success(
                    request,
                    "Content published.",
                )


            elif (
                action == "schedule"
                and can_publish
            ):

                raw = request.POST.get(
                    "scheduled_at",
                    "",
                )


                when = parse_datetime(raw)


                if when is None:

                    raise ValueError(
                        "Pick a valid date and time."
                    )


                if timezone.is_naive(when):

                    when = timezone.make_aware(
                        when
                    )


                schedule_content(
                    content=content,
                    user=request.user,
                    scheduled_at=when,
                )


                messages.success(
                    request,
                    (
                        "Scheduled to publish at "
                        f"{when.strftime('%d %b %Y, %I:%M %p')}."
                    ),
                )


            elif (
                action == "cancel_schedule"
                and can_publish
            ):

                cancel_scheduled_publish(
                    content=content,
                    user=request.user,
                )


                messages.success(
                    request,
                    "Scheduled publish cancelled.",
                )


            elif (
                action == "assign"
                and can_assign
            ):

                reviewer_id = request.POST.get(
                    "reviewer_id"
                )

                note = request.POST.get(
                    "note",
                    "",
                )


                User = get_user_model()


                reviewer = get_object_or_404(
                    User,
                    id=reviewer_id,
                )


                assign_reviewer(
                    content=content,
                    reviewer=reviewer,
                    assigned_by=request.user,
                    note=note,
                )


                messages.success(
                    request,
                    (
                        f"Assigned {reviewer.username} "
                        "as reviewer."
                    ),
                )


            elif action == "restore":

                version_id = request.POST.get(
                    "version_id"
                )


                version = get_object_or_404(
                    ContentVersion,
                    id=version_id,
                    content=content,
                )


                restore_version(
                    content=content,
                    version=version,
                    user=request.user,
                )


                messages.success(
                    request,
                    (
                        f"Restored from version "
                        f"{version.version_number}."
                    ),
                )


            else:

                messages.error(
                    request,
                    "That action isn't available right now.",
                )


        except ValueError as exc:

            messages.error(
                request,
                str(exc),
            )


        return redirect(
            "content_edit",
            content_id=content.id,
        )


    versions = content.versions.all()


    latest_ai_review = (
        content.ai_reviews
        .order_by("-created_at")
        .first()
    )


    assignments = (
        content.review_assignments
        .select_related("reviewer")
        .order_by("-assigned_at")
    )


    eligible_reviewers = []


    if can_assign:

        User = get_user_model()

        eligible_reviewers = (
            User.objects
            .filter(
                groups__name__in=[
                    "Reviewer",
                    "Admin",
                ]
            )
            .distinct()
        )


    context = {
        "content": content,
        "versions": versions,
        "latest_ai_review": latest_ai_review,
        "assignments": assignments,
        "eligible_reviewers": eligible_reviewers,
        "can_edit": can_edit,
        "can_submit": can_submit,
        "can_approve_reject": can_approve_reject,
        "can_publish": can_publish,
        "can_assign": can_assign,
    }


    return render(
        request,
        "dashboard/content_edit.html",
        context,
    )


# =========================================================
# CONTENT DIFF
# =========================================================

@login_required
def content_diff(request, content_id):

    content = get_object_or_404(
        Content,
        id=content_id,
    )


    versions = list(
        content.versions
        .order_by("version_number")
    )


    diff = None


    from_id = request.GET.get(
        "from"
    )

    to_id = request.GET.get(
        "to"
    )


    if to_id:

        new_version = get_object_or_404(
            ContentVersion,
            id=to_id,
            content=content,
        )


        old_version = None


        if from_id:

            old_version = get_object_or_404(
                ContentVersion,
                id=from_id,
                content=content,
            )

        else:

            old_version = (
                content.versions
                .filter(
                    version_number=(
                        new_version.version_number
                        - 1
                    )
                )
                .first()
            )


        diff = compute_version_diff(
            old_version=old_version,
            new_version=new_version,
        )


    context = {
        "content": content,
        "versions": versions,
        "diff": diff,
        "from_id": from_id,
        "to_id": to_id,
    }


    return render(
        request,
        "dashboard/content_diff.html",
        context,
    )


# =========================================================
# ROLE HELPER
# =========================================================

def _user_has_role(user, *roles):

    if user.is_superuser:
        return True

    return user.groups.filter(
        name__in=roles
    ).exists()


# =========================================================
# LOGIN
# =========================================================

def login_view(request):

    if request.user.is_authenticated:
        return redirect("dashboard")


    next_url = request.GET.get(
        "next",
        "",
    )


    User = get_user_model()


    if request.method == "POST":

        username = request.POST.get(
            "username",
            "",
        ).strip()


        password = request.POST.get(
            "password",
            "",
        )


        next_url = (
            request.POST.get(
                "next",
                "",
            )
            or next_url
        )


        candidate = (
            User.objects
            .filter(
                username=username
            )
            .first()
        )


        if (
            candidate
            and not candidate.is_active
            and candidate.check_password(password)
        ):

            messages.error(
                request,
                (
                    "Please verify your email before "
                    "signing in. Check your inbox for "
                    "the verification link."
                ),
            )


        else:

            user = authenticate(
                request,
                username=username,
                password=password,
            )


            if user is not None:

                auth_login(
                    request,
                    user,
                )


                return redirect(
                    next_url or "dashboard"
                )


            messages.error(
                request,
                "Invalid username or password.",
            )


    return render(
        request,
        "dashboard/login.html",
        {
            "next": next_url
        },
    )


# =========================================================
# REGISTER
# =========================================================

def register_view(request):

    if request.user.is_authenticated:
        return redirect("dashboard")


    User = get_user_model()


    if request.method == "POST":

        username = request.POST.get(
            "username",
            "",
        ).strip()


        email = request.POST.get(
            "email",
            "",
        ).strip()


        password = request.POST.get(
            "password",
            "",
        )


        role = request.POST.get(
            "role",
            "",
        )


        error = None


        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if (
            not username
            or not password
            or not role
        ):

            error = (
                "All fields are required."
            )


        elif not email:

            error = (
                "Email is required for verification."
            )


        elif User.objects.filter(
            username=username
        ).exists():

            error = (
                "A user with that username "
                "already exists."
            )


        elif role not in (
            dj_settings.CVDM_SELF_ASSIGNABLE_ROLES
        ):

            error = (
                "Please choose a valid role."
            )


        else:

            try:

                validate_password(
                    password
                )

            except DjangoValidationError as exc:

                error = " ".join(
                    exc.messages
                )


        # -------------------------------------------------
        # VALIDATION ERROR
        # -------------------------------------------------

        if error:

            messages.error(
                request,
                error,
            )


        # -------------------------------------------------
        # CREATE USER
        # -------------------------------------------------

        else:

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_active=False,
            )


            # -------------------------------------------------
            # ASSIGN ROLE
            # -------------------------------------------------

            group, _ = (
                Group.objects.get_or_create(
                    name=role
                )
            )


            user.groups.add(group)


            # -------------------------------------------------
            # CREATE EMAIL VERIFICATION
            # -------------------------------------------------

            verification = (
                EmailVerification.objects.create(
                    user=user
                )
            )


            verify_url = (
                request.build_absolute_uri(
                    reverse(
                        "verify-email",
                        args=[
                            verification.token
                        ],
                    )
                )
            )


            # -------------------------------------------------
            # BREVO CONFIGURATION CHECK
            # -------------------------------------------------

            brevo_api_key = (
                dj_settings.BREVO_API_KEY
            )

            brevo_sender_email = (
                dj_settings.BREVO_SENDER_EMAIL
            )

            brevo_sender_name = (
                dj_settings.BREVO_SENDER_NAME
            )


            if not brevo_api_key:

                verification.delete()
                user.delete()


                messages.error(
                    request,
                    (
                        "Email service is not configured. "
                        "Please try again later."
                    ),
                )


                return render(
                    request,
                    "dashboard/register.html",
                    {
                        "roles": (
                            dj_settings
                            .CVDM_SELF_ASSIGNABLE_ROLES
                        )
                    },
                )


            if not brevo_sender_email:

                verification.delete()
                user.delete()


                messages.error(
                    request,
                    (
                        "Email service is not configured. "
                        "Please try again later."
                    ),
                )


                return render(
                    request,
                    "dashboard/register.html",
                    {
                        "roles": (
                            dj_settings
                            .CVDM_SELF_ASSIGNABLE_ROLES
                        )
                    },
                )


            # -------------------------------------------------
            # BREVO EMAIL PAYLOAD
            # -------------------------------------------------

            email_payload = {
                "sender": {
                    "name": brevo_sender_name,
                    "email": brevo_sender_email,
                },

                "to": [
                    {
                        "email": email,
                        "name": username,
                    }
                ],

                "subject": (
                    "Verify your CVDM account"
                ),

                "textContent": (
                    f"Hi {username},\n\n"
                    "Thanks for registering with CVDM.\n\n"
                    "Please click the link below "
                    "to verify your email and "
                    "activate your account:\n\n"
                    f"{verify_url}\n\n"
                    "If you didn't request this "
                    "account, you can ignore this email.\n\n"
                    "— CVDM"
                ),

                "htmlContent": f"""
                    <!DOCTYPE html>
                    <html>
                    <body style="
                        font-family: Arial, sans-serif;
                        color: #20283a;
                        line-height: 1.6;
                    ">

                        <h2>
                            Verify your CVDM account
                        </h2>

                        <p>
                            Hi {username},
                        </p>

                        <p>
                            Thanks for registering
                            with CVDM.
                            Please verify your
                            email address to
                            activate your account.
                        </p>

                        <p>
                            <a
                                href="{verify_url}"
                                style="
                                    display:inline-block;
                                    padding:10px 18px;
                                    background:#20283a;
                                    color:#ffffff;
                                    text-decoration:none;
                                    border-radius:6px;
                                "
                            >
                                Verify Email
                            </a>
                        </p>

                        <p>
                            If the button doesn't work,
                            copy this link into your browser:
                        </p>

                        <p>
                            {verify_url}
                        </p>

                        <p>
                            If you didn't request this
                            account, you can ignore this email.
                        </p>

                        <p>
                            — CVDM
                        </p>

                    </body>
                    </html>
                """,
            }


            # -------------------------------------------------
            # SEND EMAIL THROUGH BREVO API
            # -------------------------------------------------

            try:

                brevo_response = requests.post(
                    "https://api.brevo.com/v3/smtp/email",

                    headers={
                        "accept": "application/json",
                        "api-key": brevo_api_key,
                        "content-type": "application/json",
                    },

                    json=email_payload,

                    timeout=10,
                )


                # -------------------------------------------------
                # BREVO ERROR
                # -------------------------------------------------

                if not brevo_response.ok:

                    print(
                        "BREVO EMAIL ERROR:",
                        brevo_response.status_code,
                        brevo_response.text,
                    )


                    verification.delete()
                    user.delete()


                    messages.error(
                        request,
                        (
                            "We couldn't send the "
                            "verification email. "
                            "Please try again later."
                        ),
                    )


                    return render(
                        request,
                        "dashboard/register.html",
                        {
                            "roles": (
                                dj_settings
                                .CVDM_SELF_ASSIGNABLE_ROLES
                            )
                        },
                    )


            except requests.RequestException as exc:

                print(
                    "BREVO CONNECTION ERROR:",
                    repr(exc),
                )


                verification.delete()
                user.delete()


                messages.error(
                    request,
                    (
                        "Email service is temporarily "
                        "unavailable. Please try again later."
                    ),
                )


                return render(
                    request,
                    "dashboard/register.html",
                    {
                        "roles": (
                            dj_settings
                            .CVDM_SELF_ASSIGNABLE_ROLES
                        )
                    },
                )


            # -------------------------------------------------
            # EMAIL SENT SUCCESSFULLY
            # -------------------------------------------------

            return render(
                request,
                "dashboard/check_email.html",
                {
                    "email": email
                },
            )


    return render(
        request,
        "dashboard/register.html",
        {
            "roles": (
                dj_settings
                .CVDM_SELF_ASSIGNABLE_ROLES
            )
        },
    )


# =========================================================
# VERIFY EMAIL
# =========================================================

def verify_email_view(request, token):

    verification = get_object_or_404(
        EmailVerification,
        token=token,
    )


    if not verification.is_verified:

        verification.is_verified = True

        verification.verified_at = (
            timezone.now()
        )


        verification.save(
            update_fields=[
                "is_verified",
                "verified_at",
            ]
        )


        verification.user.is_active = True


        verification.user.save(
            update_fields=[
                "is_active"
            ]
        )


        messages.success(
            request,
            "Email verified. You can now sign in.",
        )


    else:

        messages.info(
            request,
            "This email was already verified.",
        )


    return redirect("login")


# =========================================================
# LOGOUT
# =========================================================

def logout_view(request):

    auth_logout(request)

    return redirect("login")

