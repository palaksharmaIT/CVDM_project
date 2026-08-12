from audit.models import AuditLog


def create_audit_log(*, content, user, action, details=""):
    return AuditLog.objects.create(
        content=content,
        user=user,
        action=action,
        details=details,
    )