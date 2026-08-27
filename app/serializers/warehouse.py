def serialize_warehouse(warehouse) -> dict:
    return {
        "id": str(warehouse.id),
        "branch_id": str(warehouse.branch_id),
        "code": warehouse.code,
        "name": warehouse.name,
        "warehouse_type": warehouse.warehouse_type,
        "is_active": bool(warehouse.is_active),
    }
