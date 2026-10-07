from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_session
from app.scales import Scale

def get_scales(request: Request) -> dict[str, Scale]:
    return request.app.state.scales

def get_scale_or_404(
        scale_id: str, scales: Annotated[dict[str, Scale], Depends(get_scales)]
) -> Scale:
    scale = scales.get(scale_id)
    if scale is None:
        raise HTTPException(status_code=404, detail=f"Scale {scale_id!r} not found")
    return scale

ScalesDep = Annotated[dict[str, Scale], Depends(get_scales)]
ScaleDep = Annotated[Scale, Depends(get_scale_or_404)]
SessionDep = Annotated[Session, Depends(get_session)]