from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.compat import isoformat
from app.api.deps import get_auth_context, get_session
from app.domain.auth.schemas import AuthContext
from app.infrastructure.db.models.team import Department, TeamMember

router = APIRouter()


@router.get("/departments")
async def list_departments(
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, object]]:
    rows = (
        await session.scalars(
            select(Department).options(selectinload(Department.members)).order_by(Department.created_at.desc())
        )
    ).all()
    return [
        {
            "id": row.id,
            "name": row.name,
            "description": row.description,
            "email": row.email,
            "_count": {"members": len(row.members)},
            "createdAt": isoformat(row.created_at),
            "updatedAt": isoformat(row.updated_at),
        }
        for row in rows
    ]


@router.post("/departments", status_code=status.HTTP_201_CREATED)
async def create_department(
    payload: dict,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    row = Department(name=payload.get("name", ""), description=payload.get("description", ""), email=payload.get("email", ""))
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return {"id": row.id, "name": row.name, "description": row.description, "email": row.email, "_count": {"members": 0}, "createdAt": isoformat(row.created_at), "updatedAt": isoformat(row.updated_at)}


@router.put("/departments/{department_id}")
async def update_department(
    department_id: str,
    payload: dict,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    row = await session.get(Department, department_id)
    if not row:
        return {"error": "Department not found"}
    for field in ("name", "description", "email"):
        if field in payload:
            setattr(row, field, payload[field])
    await session.commit()
    count = await session.scalar(select(func.count()).select_from(TeamMember).where(TeamMember.department_id == row.id)) or 0
    return {"id": row.id, "name": row.name, "description": row.description, "email": row.email, "_count": {"members": count}, "createdAt": isoformat(row.created_at), "updatedAt": isoformat(row.updated_at)}


@router.delete("/departments/{department_id}")
async def delete_department(
    department_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    row = await session.get(Department, department_id)
    if not row:
        return {"success": False}
    await session.delete(row)
    await session.commit()
    return {"success": True}


@router.get("/members")
async def list_members(
    department_id: str | None = Query(default=None, alias="departmentId"),
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, object]]:
    stmt = select(TeamMember).options(selectinload(TeamMember.department)).order_by(TeamMember.created_at.desc())
    if department_id:
        stmt = stmt.where(TeamMember.department_id == department_id)
    rows = (await session.scalars(stmt)).all()
    return [
        {
            "id": row.id,
            "name": row.name,
            "email": row.email,
            "phone": row.phone,
            "role": row.role,
            "expertise": row.expertise,
            "departmentId": row.department_id,
            "department": {
                "id": row.department.id,
                "name": row.department.name,
            } if row.department else None,
            "isAvailable": row.is_available,
            "createdAt": isoformat(row.created_at),
            "updatedAt": isoformat(row.updated_at),
        }
        for row in rows
    ]


@router.post("/members", status_code=status.HTTP_201_CREATED)
async def create_member(
    payload: dict,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    row = TeamMember(
        name=payload.get("name", ""),
        email=payload.get("email", ""),
        phone=payload.get("phone", ""),
        role=payload.get("role", "member"),
        expertise=payload.get("expertise", ""),
        department_id=payload.get("departmentId", ""),
        is_available=payload.get("isAvailable", True),
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    department = await session.get(Department, row.department_id)
    return {
        "id": row.id,
        "name": row.name,
        "email": row.email,
        "phone": row.phone,
        "role": row.role,
        "expertise": row.expertise,
        "departmentId": row.department_id,
        "department": {"id": department.id, "name": department.name} if department else None,
        "isAvailable": row.is_available,
        "createdAt": isoformat(row.created_at),
        "updatedAt": isoformat(row.updated_at),
    }


@router.put("/members/{member_id}")
async def update_member(
    member_id: str,
    payload: dict,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    row = await session.get(TeamMember, member_id)
    if not row:
        return {"error": "Member not found"}
    mapping = {
        "name": "name",
        "email": "email",
        "phone": "phone",
        "role": "role",
        "expertise": "expertise",
        "departmentId": "department_id",
        "isAvailable": "is_available",
    }
    for src, dst in mapping.items():
        if src in payload:
            setattr(row, dst, payload[src])
    await session.commit()
    department = await session.get(Department, row.department_id)
    return {
        "id": row.id,
        "name": row.name,
        "email": row.email,
        "phone": row.phone,
        "role": row.role,
        "expertise": row.expertise,
        "departmentId": row.department_id,
        "department": {"id": department.id, "name": department.name} if department else None,
        "isAvailable": row.is_available,
        "createdAt": isoformat(row.created_at),
        "updatedAt": isoformat(row.updated_at),
    }


@router.delete("/members/{member_id}")
async def delete_member(
    member_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    row = await session.get(TeamMember, member_id)
    if not row:
        return {"success": False}
    await session.delete(row)
    await session.commit()
    return {"success": True}
