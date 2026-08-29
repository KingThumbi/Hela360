"""
Hela360 Models Package

This module imports all SQLAlchemy models so they are registered
with Flask-SQLAlchemy metadata for runtime use and migrations.
"""

from app.models.tenant import Tenant, Branch
from app.models.auth import (
    Permission,
    Role,
    RolePermission,
    User,
    UserPermission,
    UserRole,
)
from app.models.product import ProductCategory, Brand, UnitOfMeasure, Product, ProductUnit, ProductCode
from app.models.master_catalogue import (
    MasterItem,
    CatalogueSupplier,
    MasterItemSupplierMapping,
    SupplierItemPrice,
)
from app.models.customer import Customer
from app.models.supplier import Supplier
from app.models.inventory import (
    GoodsReceipt,
    GoodsReceiptItem,
    InventoryBatch,
    InventoryMovement,
    StockBalance,
    StockAdjustment,
    StockAdjustmentItem,
    StockCount,
    StockCountItem,
    StockCountScopeProduct,
    Warehouse,
)
from app.models.pos import (
    Till,
    Shift,
    Sale,
    SaleItem,
    DispensingRecord,
    PaymentMethod,
    SalePayment,
    SaleRefundItem,
)
from app.models.audit import AuditLog
from .shift import TillShift
from .security import (
    UserSession,
    RefreshToken,
    LoginAttempt,
    PasswordResetToken,
)
from app.models.number_sequence import NumberSequence
from app.models.tax import TaxCode

__all__ = [
    "Tenant",
    "Branch",
    "User",
    "Role",
    "Permission",
    "RolePermission",
    "UserRole",
    "ProductCategory",
    "Brand",
    "UnitOfMeasure",
    "Product",
    "ProductUnit",
    "ProductCode",
    "MasterItem",
    "CatalogueSupplier",
    "MasterItemSupplierMapping",
    "SupplierItemPrice",
    "Customer",
    "Supplier",
    "Warehouse",
    "GoodsReceipt",
    "GoodsReceiptItem",
    "InventoryBatch",
    "StockBalance",
    "StockAdjustment",
    "StockAdjustmentItem",
    "StockCount",
    "StockCountItem",
    "StockCountScopeProduct",
    "InventoryMovement",
    "Till",
    "TillShift",
    "Shift",
    "Sale",
    "SaleItem",
    "DispensingRecord",
    "PaymentMethod",
    "SalePayment",
    "SaleRefundItem",
    "AuditLog",
    "UserSession",
    "RefreshToken",
    "LoginAttempt",
    "PasswordResetToken",
    "UserPermission",
    "NumberSequence",
    "TaxCode",
]
