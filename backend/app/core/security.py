from fastapi import Depends


async def require_admin() -> None:
    # MVP placeholder. Replace with JWT/RBAC before exposing admin routes.
    return None


AdminRequired = Depends(require_admin)

