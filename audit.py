"""
PHI Access Audit Logger
HIPAA §164.312(b) requires audit controls — this module provides them.
Logs WHO accessed WHAT resource WHEN — never the PHI data itself.
In production: ship these logs to Microsoft Sentinel via Log Analytics workspace.
"""

import logging
import json
from datetime import datetime, timezone
from typing import Optional

# Dedicated audit logger — separate from app logger so it can be
# routed to a different sink (e.g., Azure Log Analytics)
audit_logger = logging.getLogger("phi_audit")
audit_logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(message)s'))
audit_logger.addHandler(handler)


def log_phi_access(
    caller: str,
    resource_type: str,
    resource_id: str,
    action: str,
    request_id: Optional[str] = None
) -> None:
    """
    Emit a structured HIPAA audit event.
    
    Fields logged:
    - timestamp (UTC ISO 8601)
    - caller identity (OID / service principal — never username/password)
    - resource type and ID (never the resource content)
    - action performed
    - request correlation ID
    
    NEVER log: actual PHI values, tokens, passwords, or full names.
    """
    audit_event = {
        "event_type": "PHI_ACCESS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "caller_oid": caller,
        "resource_type": resource_type,
        "resource_id_hash": hash(resource_id),   # hash, never raw ID in logs
        "action": action,
        "request_id": request_id or "not-provided",
        "hipaa_ref": "164.312(b)"
    }

    audit_logger.info(json.dumps(audit_event))
