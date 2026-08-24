from rest_framework.permissions import BasePermission


class CanViewContent(BasePermission):
    """
    Object-level permission for read-only content sub-resources:
    versions, diff, ai-review, ai-review/latest, history.

    These expose draft text, AI feedback, and audit trail - not
    things a random authenticated user should see. Allowed:
    - The content's own author
    - Any Editor or Admin
    - A Reviewer who has an assignment on this specific content
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user

        if (
            user.is_superuser
            or user.groups.filter(name__in=["Admin", "Editor"]).exists()
        ):
            return True

        if obj.created_by_id == user.id:
            return True

        return obj.review_assignments.filter(reviewer=user).exists()


class CanAssignReviewer(BasePermission):
    """
    Object-level permission for assign_reviewer_action.

    - Editor / Admin: can assign a reviewer to any content.
    - Author: can only assign a reviewer to content they own.
      (Without this, any user in the Author group could assign
      reviewers to someone else's content.)
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.groups.filter(
                name__in=["Author", "Editor", "Admin"]
            ).exists()
        )

    def has_object_permission(self, request, view, obj):
        user = request.user

        if (
            user.is_superuser
            or user.groups.filter(name__in=["Admin", "Editor"]).exists()
        ):
            return True

        return obj.created_by_id == user.id


class CanSubmitForReview(BasePermission):
    """
    Object-level permission for submit_review.

    - Admin: can submit any content.
    - Author: can only submit content they own.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.groups.filter(
                name__in=["Author", "Admin"]
            ).exists()
        )

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.is_superuser or user.groups.filter(name="Admin").exists():
            return True

        return obj.created_by_id == user.id


class IsAuthor(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.groups.filter(name="Author").exists()
        )


class IsReviewer(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.groups.filter(name="Reviewer").exists()
        )


class IsEditor(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.groups.filter(name="Editor").exists()
        )


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (
                request.user.is_superuser
                or request.user.groups.filter(name="Admin").exists()
            )
        )

class CanApproveContent(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (
                request.user.is_superuser
                or request.user.groups.filter(
                    name__in=["Reviewer", "Admin"]
                ).exists()
            )
        )


class IsContentOwnerOrAdmin(BasePermission):
    """
    Object-level permission for ContentViewSet's default CRUD
    (retrieve/update/partial_update/destroy).

    - Read (GET): any authenticated user.
    - Update (PUT/PATCH): only the content's own author, and only
      while it's still a draft or rejected (matches the same rule
      dashboard/views.py already enforces for can_edit). Admins can
      always edit.
    - Delete: Admins only, and never for published content.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True

        is_admin = (
            request.user.is_superuser
            or request.user.groups.filter(name="Admin").exists()
        )

        if request.method in ("PUT", "PATCH"):
            if is_admin:
                return True
            is_owner = obj.created_by_id == request.user.id
            return is_owner and obj.status in (
                obj.Status.DRAFT,
                obj.Status.REJECTED,
            )

        if request.method == "DELETE":
            if not is_admin:
                return False
            return obj.status != obj.Status.PUBLISHED

        return False


class CanEditContent(BasePermission):
    """
    Object-level permission for actions that mutate a content's
    current draft (e.g. restore_version). Mirrors the can_edit
    rule already used in dashboard/views.py:

    - The content's own author, while it's draft or rejected.
    - Any Editor, as long as it isn't published yet.
    - Admin, always.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        is_admin = (
            request.user.is_superuser
            or request.user.groups.filter(name="Admin").exists()
        )
        if is_admin:
            return True

        is_author = obj.created_by_id == request.user.id
        if is_author and obj.status in (
            obj.Status.DRAFT,
            obj.Status.REJECTED,
        ):
            return True

        is_editor = request.user.groups.filter(name="Editor").exists()
        if is_editor and obj.status != obj.Status.PUBLISHED:
            return True

        return False