from typing import Optional, Dict, Any
from fastapi import Request
from sqlalchemy.orm import Session
from app.models import AuditLog

def write_audit(
    db: Session,
    action: str,
    request: Optional[Request] = None,
    actor: Optional[str] = None,
    resource: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
):
    ip = ua = None
    if request:
        ip = request.client.host if request.client else None
        ua = request.headers.get("user-agent")
    row = AuditLog(action=action, actor=actor, resource=resource, ip=ip, ua=ua, details=details or {})
    db.add(row)
