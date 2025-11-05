# services/project_service.py
from utils.firebase import db
from models.project import ProjectCreate, ProjectUpdate
from google.cloud.firestore_v1 import FieldFilter  # ← CORRECT
import google.cloud.firestore as firestore  # ← CORRECT

def create_project(user_id: str, project: ProjectCreate):
    proj_ref = db.collection('projects').document()
    proj_ref.set({
        'user_id': user_id,
        'name': project.name,
        'description': project.description,
        'sensor_type': project.sensor_type,
        'created_at': firestore.SERVER_TIMESTAMP  # Now works!
    })
    return {"project_id": proj_ref.id, **project.dict()}

def get_user_projects(user_id: str):
    projects = db.collection('projects') \
        .where(filter=FieldFilter('user_id', '==', user_id)) \
        .stream()
    return [{"id": p.id, **p.to_dict()} for p in projects]

def update_project(project_id: str, user_id: str, update: ProjectUpdate):
    proj_ref = db.collection('projects').document(project_id)
    proj = proj_ref.get()
    if not proj.exists or proj.to_dict()['user_id'] != user_id:
        return None
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if update_data:
        proj_ref.update(update_data)
    return {"message": "Updated"}

def delete_project(project_id: str, user_id: str):
    proj_ref = db.collection('projects').document(project_id)
    proj = proj_ref.get()
    if not proj.exists or proj.to_dict()['user_id'] != user_id:
        return None
    proj_ref.delete()
    return {"message": "Deleted"}