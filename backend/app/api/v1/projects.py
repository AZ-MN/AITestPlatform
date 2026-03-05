from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.project import Project, ProjectMember, Iteration
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut, IterationCreate, IterationOut
from typing import Optional

router = APIRouter()


@router.get("/", response_model=list[ProjectOut])
async def list_projects(
    skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Project).offset(skip).limit(limit))
    return result.scalars().all()


@router.post("/", response_model=ProjectOut)
async def create_project(
    data: ProjectCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = Project(**data.model_dump(), owner_id=current_user.id)
    db.add(project)
    await db.flush()
    return project


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: int, data: ProjectUpdate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(project, k, v)
    return project


@router.delete("/{project_id}")
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    await db.delete(project)
    return {"message": "删除成功"}


# Iterations
@router.get("/{project_id}/iterations", response_model=list[IterationOut])
async def list_iterations(project_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Iteration).where(Iteration.project_id == project_id))
    return result.scalars().all()


@router.post("/{project_id}/iterations", response_model=IterationOut)
async def create_iteration(
    project_id: int, data: IterationCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    iteration = Iteration(**data.model_dump(), project_id=project_id)
    db.add(iteration)
    await db.flush()
    return iteration
