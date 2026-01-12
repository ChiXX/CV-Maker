from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from sqlalchemy import func
from app.db.session import get_db_dependency
from app.db.models import Application, ApplicationStatus
from .schemas import JobApplicationResponse, JobApplicationUpdate, ApplicationStats

router = APIRouter()

@router.get("/stats", response_model=ApplicationStats)
async def get_application_stats(
    db: Session = Depends(get_db_dependency)
):
    """
    Get statistics for applications
    """
    stats_query = db.query(
        Application.status, 
        func.count(Application.id)
    ).group_by(Application.status).all()
    
    stats_dict = {status.value: 0 for status in ApplicationStatus}
    for status, count in stats_query:
        stats_dict[status.value] = count
        
    return ApplicationStats(
        total=sum(stats_dict.values()),
        submitted=stats_dict.get("submitted", 0),
        interviewing=stats_dict.get("interviewing", 0),
        offered=stats_dict.get("offered", 0),
        failed=stats_dict.get("failed", 0),
        archive=stats_dict.get("archive", 0)
    )

@router.get("", response_model=List[JobApplicationResponse])
async def list_applications(
    skip: int = 0,
    limit: int = 20,
    status: Optional[List[ApplicationStatus]] = Query(None),
    search: Optional[str] = None,
    include_archived: bool = False,
    sort_by: str = "updated_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db_dependency)
):
    """
    List applications with pagination, filtering and sorting
    """
    query = db.query(Application)
    
    if status:
        query = query.filter(Application.status.in_(status))
    elif not include_archived:
        # Default: don't show archived
        query = query.filter(Application.status != ApplicationStatus.archive)
        
    if search:
        query = query.filter(
            (Application.company.ilike(f"%{search}%")) | 
            (Application.title.ilike(f"%{search}%"))
        )
        
    # Sorting
    sort_attr = getattr(Application, sort_by, Application.updated_at)
    if sort_order == "desc":
        query = query.order_by(sort_attr.desc())
    else:
        query = query.order_by(sort_attr.asc())
        
    return query.offset(skip).limit(limit).all()

@router.get("/{application_id}", response_model=JobApplicationResponse)
async def get_application(
    application_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Get a single application by ID
    """
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application

@router.patch("/{application_id}", response_model=JobApplicationResponse)
async def update_application(
    application_id: int,
    update_data: JobApplicationUpdate,
    db: Session = Depends(get_db_dependency)
):
    """
    Update an application status or comment
    """
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    update_dict = update_data.model_dump(exclude_unset=True)
    if not update_dict:
         return application

    for field, value in update_dict.items():
        setattr(application, field, value)
    
    # Update timestamp whenever we make a patch (user requirement to update on status change)
    application.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(application)
    return application

@router.delete("/{application_id}")
async def delete_application(
    application_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Delete an application by ID
    """
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    db.delete(application)
    db.commit()
    return {"detail": "Application deleted successfully"}
