"""
Hela360 Office Master Item Governance Service
=============================================

Controlled platform-governance mutations for Hela360 Master Items.

Architectural boundaries
------------------------
* MasterItem is global and platform-owned.
* No tenant Product records are mutated.
* Approval is an explicit ``draft`` -> ``approved`` transition.
* The service flushes mutations but never commits or rolls back.
* The caller owns the surrounding transaction.
* Governance actions are recorded through the common audit service.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.errors import ValidationError
from app.models import MasterItem
from app.services.common.audit_actions import AuditAction
from app.services.common.audit_modules import AuditModule
from app.services.common.audit_service import AuditService


class MasterItemGovernanceError(ValidationError):
    """
    Base error for Master Item governance failures.
    """


class MasterItemGovernanceNotFoundError(
    MasterItemGovernanceError
):
    """
    Raised when the requested MasterItem does not exist.
    """


class MasterItemApprovalConflictError(
    MasterItemGovernanceError
):
    """
    Raised when a MasterItem cannot perform the approval transition.
    """


@dataclass(frozen=True, slots=True)
class MasterItemApprovalResult:
    """
    Result of one successful Master Item approval.
    """

    master_item: MasterItem


class PlatformMasterItemGovernanceService:
    """
    Perform controlled Hela360 Office Master Item governance transitions.
    """

    def __init__(
        self,
        session: Session,
        *,
        audit_service: AuditService | None = None,
    ) -> None:
        self.session = session

        self.audit_service = (
            audit_service
            if audit_service is not None
            else AuditService()
        )

    def approve_item(
        self,
        *,
        master_item_id: str,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> MasterItemApprovalResult:
        """
        Approve one draft MasterItem.

        The caller owns the surrounding transaction.
        """

        normalized_id = (
            str(master_item_id).strip()
            if master_item_id is not None
            else ""
        )

        if not normalized_id:
            raise MasterItemGovernanceError(
                "Master item id is required."
            )

        item = (
            self.session.query(MasterItem)
            .filter(
                MasterItem.id == normalized_id
            )
            .first()
        )

        if item is None:
            raise MasterItemGovernanceNotFoundError(
                "Master Item not found."
            )

        if item.review_status != "draft":
            raise MasterItemApprovalConflictError(
                "Only draft Master Items can be approved."
            )

        old_status = item.review_status

        item.review_status = "approved"

        self.session.flush()

        self.audit_service.log(
            module=AuditModule.CATALOGUE,
            action=(
                AuditAction
                .MASTER_CATALOGUE_ITEM_APPROVED
            ),
            entity_type="MasterItem",
            tenant_id=None,
            entity_id=str(item.id),
            user_id=user_id,
            branch_id=None,
            session_id=session_id,
            old_values={
                "review_status": old_status,
            },
            new_values={
                "review_status": item.review_status,
            },
            details={
                "master_code": item.master_code,
                "source": "hela360_office",
            },
            commit=False,
        )

        return MasterItemApprovalResult(
            master_item=item,
        )


__all__ = [
    "MasterItemApprovalConflictError",
    "MasterItemApprovalResult",
    "MasterItemGovernanceError",
    "MasterItemGovernanceNotFoundError",
    "PlatformMasterItemGovernanceService",
]
