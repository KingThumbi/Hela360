"""
Audit Actions

Central registry of audit event types used throughout Hela360.

Every audit record should use one of these values instead of
hard-coded strings.

Hela360 Enterprise Pharmacy POS & ERP
"""

from enum import StrEnum


class AuditAction(StrEnum):
    # ==========================================================
    # Authentication
    # ==========================================================

    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"

    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    PASSWORD_RESET_REQUESTED = "PASSWORD_RESET_REQUESTED"
    PASSWORD_RESET_COMPLETED = "PASSWORD_RESET_COMPLETED"

    SESSION_CREATED = "SESSION_CREATED"
    SESSION_REVOKED = "SESSION_REVOKED"

    REFRESH_TOKEN_ISSUED = "REFRESH_TOKEN_ISSUED"
    REFRESH_TOKEN_ROTATED = "REFRESH_TOKEN_ROTATED"
    REFRESH_TOKEN_REVOKED = "REFRESH_TOKEN_REVOKED"

    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    ACCOUNT_UNLOCKED = "ACCOUNT_UNLOCKED"

    MFA_ENABLED = "MFA_ENABLED"
    MFA_DISABLED = "MFA_DISABLED"

    # ==========================================================
    # User Management
    # ==========================================================

    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DELETED = "USER_DELETED"

    ROLE_ASSIGNED = "ROLE_ASSIGNED"
    ROLE_REMOVED = "ROLE_REMOVED"

    PERMISSION_GRANTED = "PERMISSION_GRANTED"
    PERMISSION_REVOKED = "PERMISSION_REVOKED"

    # ==========================================================
    # Authorization
    # ==========================================================

    AUTHORIZATION_DENIED = "AUTHORIZATION_DENIED"

    TENANT_ACCESS_DENIED = "TENANT_ACCESS_DENIED"

    BRANCH_ACCESS_DENIED = "BRANCH_ACCESS_DENIED"

    # ==========================================================
    # Customers
    # ==========================================================

    CUSTOMER_CREATED = "CUSTOMER_CREATED"
    CUSTOMER_UPDATED = "CUSTOMER_UPDATED"
    CUSTOMER_DELETED = "CUSTOMER_DELETED"

    # ==========================================================
    # Products
    # ==========================================================

    PRODUCT_CREATED = "PRODUCT_CREATED"
    PRODUCT_UPDATED = "PRODUCT_UPDATED"
    PRODUCT_DELETED = "PRODUCT_DELETED"

    PRICE_CHANGED = "PRICE_CHANGED"

    # ==========================================================
    # Inventory
    # ==========================================================

    STOCK_RECEIVED = "STOCK_RECEIVED"
    STOCK_TRANSFERRED = "STOCK_TRANSFERRED"
    STOCK_ADJUSTED = "STOCK_ADJUSTED"
    STOCK_WRITTEN_OFF = "STOCK_WRITTEN_OFF"

    INVENTORY_COUNT_STARTED = "INVENTORY_COUNT_STARTED"
    INVENTORY_COUNT_COMPLETED = "INVENTORY_COUNT_COMPLETED"

    # ==========================================================
    # Procurement
    # ==========================================================

    PURCHASE_ORDER_CREATED = "PURCHASE_ORDER_CREATED"
    PURCHASE_ORDER_APPROVED = "PURCHASE_ORDER_APPROVED"
    PURCHASE_ORDER_RECEIVED = "PURCHASE_ORDER_RECEIVED"

    # ==========================================================
    # Sales / POS
    # ==========================================================

    SALE_CREATED = "SALE_CREATED"
    SALE_COMPLETED = "SALE_COMPLETED"
    SALE_CANCELLED = "SALE_CANCELLED"

    REFUND_CREATED = "REFUND_CREATED"
    REFUND_APPROVED = "REFUND_APPROVED"

    SHIFT_OPENED = "SHIFT_OPENED"
    SHIFT_CLOSED = "SHIFT_CLOSED"

    # ==========================================================
    # Finance
    # ==========================================================

    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    PAYMENT_VOIDED = "PAYMENT_VOIDED"

    INVOICE_CREATED = "INVOICE_CREATED"

    # ==========================================================
    # Platform
    # ==========================================================

    TENANT_CREATED = "TENANT_CREATED"
    TENANT_UPDATED = "TENANT_UPDATED"
    TENANT_DEACTIVATED = "TENANT_DEACTIVATED"

    SUBSCRIPTION_CREATED = "SUBSCRIPTION_CREATED"
    SUBSCRIPTION_UPDATED = "SUBSCRIPTION_UPDATED"

    LICENSE_ACTIVATED = "LICENSE_ACTIVATED"
    LICENSE_EXPIRED = "LICENSE_EXPIRED"

    # ==========================================================
    # System
    # ==========================================================

    SETTINGS_UPDATED = "SETTINGS_UPDATED"

    DATA_IMPORTED = "DATA_IMPORTED"
    DATA_EXPORTED = "DATA_EXPORTED"

    BACKUP_CREATED = "BACKUP_CREATED"
    RESTORE_COMPLETED = "RESTORE_COMPLETED"