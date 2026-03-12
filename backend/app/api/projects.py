from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.requirement import Requirement
from app.models.testcase import TestCase
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut, ProjectMemberAdd

router = APIRouter(prefix="/projects", tags=["项目管理"])


def _enrich_project(p: Project, db: Session) -> dict:
    d = {c.name: getattr(p, c.name) for c in p.__table__.columns}
    d["member_count"] = db.query(ProjectMember).filter(ProjectMember.project_id == p.id).count()
    d["case_count"] = db.query(TestCase).filter(TestCase.project_id == p.id).count()
    d["req_count"] = db.query(Requirement).filter(Requirement.project_id == p.id).count()
    return d


def _hard_delete_project(project_id: int, db: Session):
    db.query(TestCase).filter(TestCase.project_id == project_id).delete(synchronize_session=False)
    db.query(Requirement).filter(Requirement.project_id == project_id).delete(synchronize_session=False)
    db.query(ProjectMember).filter(ProjectMember.project_id == project_id).delete(synchronize_session=False)
    db.query(Project).filter(Project.id == project_id).delete(synchronize_session=False)
    db.commit()


@router.get("", summary="获取项目列表")
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "super_admin":
        projects = db.query(Project).order_by(Project.created_at.desc()).all()
    else:
        member_rows = db.query(ProjectMember).filter(ProjectMember.user_id == current_user.id).all()
        pids = [m.project_id for m in member_rows]
        projects = db.query(Project).filter(Project.id.in_(pids)).order_by(Project.created_at.desc()).all()
    return [_enrich_project(p, db) for p in projects]


@router.post("", summary="创建项目")
async def create_project(
    proj_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    proj = Project(
        name=proj_in.name,
        description=proj_in.description,
        icon=proj_in.icon,
        created_by=current_user.id,
    )
    db.add(proj)
    db.flush()
    # 创建者自动成为项目管理员
    member = ProjectMember(project_id=proj.id, user_id=current_user.id, role="project_admin")
    db.add(member)
    db.commit()
    db.refresh(proj)
    return _enrich_project(proj, db)


@router.get("/{project_id}", summary="获取项目详情")
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="项目不存在")
    return _enrich_project(proj, db)


@router.put("/{project_id}", summary="更新项目")
async def update_project(
    project_id: int,
    proj_in: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="项目不存在")
    for field, value in proj_in.model_dump(exclude_unset=True).items():
        setattr(proj, field, value)
    db.commit()
    db.refresh(proj)
    return _enrich_project(proj, db)


@router.delete("/{project_id}", summary="删除项目")
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="项目不存在")
    if current_user.role != "super_admin" and proj.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="仅项目创建者或系统管理员可删除项目")
    if proj.status == "archived":
        raise HTTPException(status_code=400, detail="已归档项目不可删除，请先取消归档")

    _hard_delete_project(project_id, db)
    return {"message": "项目已删除"}


@router.post("/{project_id}/purge", summary="永久删除项目")
async def purge_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="项目不存在")
    if current_user.role != "super_admin" and proj.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="仅项目创建者或系统管理员可删除项目")
    if proj.status == "archived":
        raise HTTPException(status_code=400, detail="已归档项目不可删除，请先取消归档")
    _hard_delete_project(project_id, db)
    return {"message": "项目已永久删除"}


@router.patch("/{project_id}/archive", summary="归档项目")
async def archive_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="项目不存在")
    if current_user.role != "super_admin" and proj.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="仅项目创建者或系统管理员可归档项目")
    proj.status = "archived"
    db.commit()
    return {"message": "项目已归档"}


@router.patch("/{project_id}/unarchive", summary="取消归档项目")
async def unarchive_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="项目不存在")
    if current_user.role != "super_admin" and proj.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="仅项目创建者或系统管理员可取消归档项目")
    proj.status = "active"
    db.commit()
    return {"message": "项目已取消归档"}


@router.get("/{project_id}/members", summary="获取项目成员")
async def get_members(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    members = (
        db.query(ProjectMember, User)
        .join(User, ProjectMember.user_id == User.id)
        .filter(ProjectMember.project_id == project_id)
        .all()
    )
    return [
        {"id": m.id, "user_id": u.id, "username": u.username,
         "full_name": u.full_name, "role": m.role, "joined_at": m.joined_at}
        for m, u in members
    ]


@router.post("/{project_id}/members", summary="添加项目成员")
async def add_member(
    project_id: int,
    member_in: ProjectMemberAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    exists = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == member_in.user_id
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="成员已存在")
    member = ProjectMember(project_id=project_id, user_id=member_in.user_id, role=member_in.role)
    db.add(member)
    db.commit()
    return {"message": "成员添加成功"}
