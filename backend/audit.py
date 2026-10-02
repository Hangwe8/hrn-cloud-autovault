from sqlalchemy.orm import Session

import models


def create_audit_log(
    db: Session,
    business_id: int,
    user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    details: str | None = None
):
    audit_log = models.AuditLog(
        business_id=business_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details
    )

    db.add(audit_log)
    db.flush()

    return audit_log
