"""
Hela360 Goods Receipt Workflow Policy
=====================================

Defines the canonical lifecycle and transition rules for tenant goods receipts.

This module contains workflow policy only. It does not perform persistence,
authorization, inventory mutation, or transaction management.
"""

from __future__ import annotations

from enum import StrEnum


class GoodsReceiptStatus(StrEnum):
    DRAFT = "draft"
    RECEIVING = "receiving"
    RECEIVED = "received"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    POSTED = "posted"
    CANCELLED = "cancelled"


GOODS_RECEIPT_TRANSITIONS: dict[
    GoodsReceiptStatus,
    frozenset[GoodsReceiptStatus],
] = {
    GoodsReceiptStatus.DRAFT: frozenset(
        {
            GoodsReceiptStatus.RECEIVING,
            GoodsReceiptStatus.CANCELLED,
        }
    ),
    GoodsReceiptStatus.RECEIVING: frozenset(
        {
            GoodsReceiptStatus.RECEIVED,
            GoodsReceiptStatus.CANCELLED,
        }
    ),
    GoodsReceiptStatus.RECEIVED: frozenset(
        {
            GoodsReceiptStatus.UNDER_REVIEW,

            # Compatibility transition:
            # the current production API approves directly from RECEIVED.
            GoodsReceiptStatus.APPROVED,

            GoodsReceiptStatus.CANCELLED,
        }
    ),
    GoodsReceiptStatus.UNDER_REVIEW: frozenset(
        {
            GoodsReceiptStatus.RECEIVED,
            GoodsReceiptStatus.APPROVED,
            GoodsReceiptStatus.CANCELLED,
        }
    ),
    GoodsReceiptStatus.APPROVED: frozenset(
        {
            GoodsReceiptStatus.POSTED,
            GoodsReceiptStatus.CANCELLED,
        }
    ),
    GoodsReceiptStatus.POSTED: frozenset(),
    GoodsReceiptStatus.CANCELLED: frozenset(),
}


GOODS_RECEIPT_EDITABLE_STATUSES = frozenset(
    {
        GoodsReceiptStatus.DRAFT,
        GoodsReceiptStatus.RECEIVING,
        GoodsReceiptStatus.RECEIVED,
        GoodsReceiptStatus.UNDER_REVIEW,
    }
)


GOODS_RECEIPT_TERMINAL_STATUSES = frozenset(
    {
        GoodsReceiptStatus.POSTED,
        GoodsReceiptStatus.CANCELLED,
    }
)


def parse_goods_receipt_status(
    value: str | GoodsReceiptStatus,
) -> GoodsReceiptStatus:
    """Resolve one persisted/API status to its canonical enum value."""

    if isinstance(value, GoodsReceiptStatus):
        return value

    return GoodsReceiptStatus(
        str(value).strip().lower()
    )


def goods_receipt_allowed_transitions(
    status: str | GoodsReceiptStatus,
) -> frozenset[GoodsReceiptStatus]:
    """Return the canonical outgoing transitions for one status."""

    current = parse_goods_receipt_status(status)
    return GOODS_RECEIPT_TRANSITIONS[current]


def goods_receipt_can_transition(
    current: str | GoodsReceiptStatus,
    target: str | GoodsReceiptStatus,
) -> bool:
    """Return whether a real state transition is allowed."""

    current_status = parse_goods_receipt_status(current)
    target_status = parse_goods_receipt_status(target)

    if current_status == target_status:
        return False

    return (
        target_status
        in GOODS_RECEIPT_TRANSITIONS[current_status]
    )


def goods_receipt_is_editable(
    status: str | GoodsReceiptStatus,
) -> bool:
    return (
        parse_goods_receipt_status(status)
        in GOODS_RECEIPT_EDITABLE_STATUSES
    )


def goods_receipt_is_terminal(
    status: str | GoodsReceiptStatus,
) -> bool:
    return (
        parse_goods_receipt_status(status)
        in GOODS_RECEIPT_TERMINAL_STATUSES
    )


__all__ = [
    "GOODS_RECEIPT_EDITABLE_STATUSES",
    "GOODS_RECEIPT_TERMINAL_STATUSES",
    "GOODS_RECEIPT_TRANSITIONS",
    "GoodsReceiptStatus",
    "goods_receipt_allowed_transitions",
    "goods_receipt_can_transition",
    "goods_receipt_is_editable",
    "goods_receipt_is_terminal",
    "parse_goods_receipt_status",
]
