from __future__ import annotations

import pytest

from app.services.tenant.inventory.goods_receipt_workflow import (
    GOODS_RECEIPT_EDITABLE_STATUSES,
    GOODS_RECEIPT_TERMINAL_STATUSES,
    GoodsReceiptStatus,
    goods_receipt_allowed_transitions,
    goods_receipt_can_transition,
    goods_receipt_is_editable,
    goods_receipt_is_terminal,
    parse_goods_receipt_status,
)


def test_goods_receipt_status_catalogue_is_canonical():
    assert {status.value for status in GoodsReceiptStatus} == {
        "draft",
        "receiving",
        "received",
        "under_review",
        "approved",
        "posted",
        "cancelled",
    }


def test_goods_receipt_primary_workflow_transitions_are_allowed():
    assert goods_receipt_can_transition(
        GoodsReceiptStatus.DRAFT,
        GoodsReceiptStatus.RECEIVING,
    )
    assert goods_receipt_can_transition(
        GoodsReceiptStatus.RECEIVING,
        GoodsReceiptStatus.RECEIVED,
    )
    assert goods_receipt_can_transition(
        GoodsReceiptStatus.RECEIVED,
        GoodsReceiptStatus.UNDER_REVIEW,
    )
    assert goods_receipt_can_transition(
        GoodsReceiptStatus.UNDER_REVIEW,
        GoodsReceiptStatus.APPROVED,
    )
    assert goods_receipt_can_transition(
        GoodsReceiptStatus.APPROVED,
        GoodsReceiptStatus.POSTED,
    )


def test_goods_receipt_current_direct_approval_transition_remains_supported():
    assert goods_receipt_can_transition(
        GoodsReceiptStatus.RECEIVED,
        GoodsReceiptStatus.APPROVED,
    )


def test_goods_receipt_posted_and_cancelled_are_terminal():
    assert GOODS_RECEIPT_TERMINAL_STATUSES == {
        GoodsReceiptStatus.POSTED,
        GoodsReceiptStatus.CANCELLED,
    }

    assert goods_receipt_is_terminal("posted")
    assert goods_receipt_is_terminal("cancelled")

    assert goods_receipt_allowed_transitions(
        GoodsReceiptStatus.POSTED
    ) == frozenset()

    assert goods_receipt_allowed_transitions(
        GoodsReceiptStatus.CANCELLED
    ) == frozenset()


def test_goods_receipt_editability_stops_after_receiving():
    assert GOODS_RECEIPT_EDITABLE_STATUSES == {
        GoodsReceiptStatus.DRAFT,
        GoodsReceiptStatus.RECEIVING,
    }

    assert goods_receipt_is_editable("draft")
    assert goods_receipt_is_editable("receiving")
    assert not goods_receipt_is_editable("received")
    assert not goods_receipt_is_editable("under_review")

    assert not goods_receipt_is_editable("approved")
    assert not goods_receipt_is_editable("posted")
    assert not goods_receipt_is_editable("cancelled")


def test_goods_receipt_same_state_is_not_a_transition():
    for status in GoodsReceiptStatus:
        assert not goods_receipt_can_transition(
            status,
            status,
        )


def test_goods_receipt_invalid_status_is_rejected():
    with pytest.raises(ValueError):
        parse_goods_receipt_status("made_up_status")


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (GoodsReceiptStatus.DRAFT, True),
        (GoodsReceiptStatus.RECEIVING, True),
        (GoodsReceiptStatus.RECEIVED, False),
        (GoodsReceiptStatus.UNDER_REVIEW, False),
        (GoodsReceiptStatus.APPROVED, False),
        (GoodsReceiptStatus.POSTED, False),
        (GoodsReceiptStatus.CANCELLED, False),
    ],
)
def test_goods_receipt_editability_policy(status, expected):
    assert goods_receipt_is_editable(status) is expected
