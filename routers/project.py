from fastapi import APIRouter, HTTPException
from models.project import ProjectCreate, ProjectUpdate
from services.project_service import create_project, get_user_projects, update_project, delete_project

router = APIRouter(prefix="/project", tags=["Projects"])

@router.post("/create-project/{user_id}")
def create(user_id: str, project: ProjectCreate):
    return create_project(user_id, project)

@router.get("/get-project/{user_id}")
def get_projects(user_id: str):
    return get_user_projects(user_id)

@router.put("/update-project/{project_id}/{user_id}")
def update(project_id: str, user_id: str, update: ProjectUpdate):
    res = update_project(project_id, user_id, update)
    if not res:
        raise HTTPException(404, "Project not found or unauthorized")
    return res

@router.delete("/delete-project/{project_id}/{user_id}")
def delete(project_id: str, user_id: str):
    res = delete_project(project_id, user_id)
    if not res:
        raise HTTPException(404, "Project not found or unauthorized")
    return res