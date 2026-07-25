from enum import StrEnum


class AuditModule(StrEnum):
    AUTH = "AUTH"
    INVENTORY = "INVENTORY"
    PROCUREMENT = "PROCUREMENT"
    CUSTOMERS = "CUSTOMERS"
    SALES = "SALES"
    FINANCE = "FINANCE"
    PLATFORM = "PLATFORM"
    SYSTEM = "SYSTEM"