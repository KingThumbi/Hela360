from app.models import Till


def serialize_till(till: Till) -> dict:
    return {
        "id": str(till.id),
        "branch_id": str(till.branch_id),
        "warehouse_id": str(till.warehouse_id) if till.warehouse_id else None,
        "code": till.code,
        "name": till.name,
        "is_active": bool(till.is_active),
    }
