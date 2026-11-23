from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.diagnosis import DiagnosisHistory
from app.models.detection import DetectionResult
from app.schemas.dashboard import DashboardStats, RecentDiagnosisItem
from app.api.presenters import display_label, map_for_crop

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Total diagnoses by this user
    total = db.query(func.count(DiagnosisHistory.id)).filter(
        DiagnosisHistory.user_id == current_user.id
    ).scalar() or 0
    
    # Detected count
    detected = db.query(func.count(DiagnosisHistory.id)).filter(
        DiagnosisHistory.user_id == current_user.id,
        DiagnosisHistory.status == "detected"
    ).scalar() or 0
    
    # No detection count
    no_detection = db.query(func.count(DiagnosisHistory.id)).filter(
        DiagnosisHistory.user_id == current_user.id,
        DiagnosisHistory.status == "no_detection"
    ).scalar() or 0
    
    # Disease distribution for this user with mapped labels
    distribution_rows = db.query(
        DiagnosisHistory.crop_code,
        DetectionResult.class_name,
        func.count(DetectionResult.id)
    ).join(
        DiagnosisHistory, DetectionResult.history_id == DiagnosisHistory.id
    ).filter(
        DiagnosisHistory.user_id == current_user.id
    ).group_by(DiagnosisHistory.crop_code, DetectionResult.class_name).all()
    
    disease_distribution: dict[str, int] = {}
    for crop_code, raw_name, count in distribution_rows:
        mapped = map_for_crop(crop_code, raw_name)
        disease_distribution[mapped] = disease_distribution.get(mapped, 0) + count

    crop_counts = dict(
        db.query(DiagnosisHistory.crop_code, func.count(DiagnosisHistory.id))
        .filter(DiagnosisHistory.user_id == current_user.id)
        .group_by(DiagnosisHistory.crop_code)
        .all()
    )
    
    # Recent 5 diagnoses
    recent_recs = db.query(DiagnosisHistory).filter(
        DiagnosisHistory.user_id == current_user.id
    ).order_by(DiagnosisHistory.created_at.desc()).limit(5).all()
    
    recent_list = []
    for r in recent_recs:
        det_count = len(r.detections)
        primary = None
        if det_count > 0:
            best = max(r.detections, key=lambda d: d.confidence)
            primary = display_label(r, best.class_name)
            
        recent_list.append(RecentDiagnosisItem(
            id=r.id,
            status=r.status,
            created_at=r.created_at.isoformat() if r.created_at else "",
            detection_count=det_count,
            primary_disease=primary,
            crop_code=r.crop_code,
            original_image_url=f"/api/images/{r.original_image_path}"
        ))
        
    return DashboardStats(
        total_diagnoses=total,
        detected_count=detected,
        no_detection_count=no_detection,
        disease_distribution=disease_distribution,
        crop_counts=crop_counts,
        recent_diagnoses=recent_list
    )
