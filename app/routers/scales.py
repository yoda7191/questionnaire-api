from statistics import mean, stdev

from fastapi import APIRouter
from sqlalchemy import select

from app.deps import ScaleDep, ScalesDep, SessionDep
from app.models import Submission
from app.schemas import ScalePublic, ScaleStats, ScaleSummary, SubscaleStats

router = APIRouter(prefix="/scales", tags=["scales"])

@router.get("", response_model=list[ScaleSummary], summary="List available scales")
def list_scales(scales: ScalesDep):
    return [
        ScaleSummary(id=s.id, name=s.name, item_count=len(s.items), subscales=s.subscales)
        for s in scales.values()
    ]

@router.get("/{scale_id}", response_model=ScalePublic, summary="Get one scale")
def get_scale(scale: ScaleDep):
    return scale

@router.get("/{scale_id}/stats", response_model=ScaleStats, summary="Subscale statistics")
def scale_stats(scale: ScaleDep, session: SessionDep):
    rows = session.scalars(
        select(Submission.scores).where(
            Submission.scale_id == scale.id,
            Submission.scale_version == scale.version
        )
    ).all()
    subscales = {}
    for name in scale.subscales:
        values = [row[name] for row in rows]
        subscales[name] = SubscaleStats(
            mean=round(mean(values), 2) if values else None,
            sd = round(stdev(values), 2) if len(values) >= 2 else None,
        )
    return ScaleStats(scale_id=scale.id, n=len(rows), subscales=subscales)