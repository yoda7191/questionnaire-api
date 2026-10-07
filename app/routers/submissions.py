from fastapi import APIRouter, HTTPException, Response

from app.deps import ScaleDep, SessionDep
from app.models import Submission
from app.schemas import AnswerErrorResponse, SubmissionCreate, SubmissionDetail, SubmissionRead
from app.scoring import score

router = APIRouter(tags=["submissions"])


@router.post(
    "/scales/{scale_id}/submissions",
    response_model=SubmissionRead,
    status_code=201,
    responses={422: {"model": AnswerErrorResponse, "description": "Answers don't fit the scale"}},
    summary="Score and store answers",
)
def create_submission(
    payload: SubmissionCreate, scale: ScaleDep, session: SessionDep, response: Response
):
    # Scoring validates first, so invalid answers are never stored.
    scores = score(scale, payload.answers)
    submission = Submission(
        scale_id=scale.id,
        scale_version=scale.version,
        answers=payload.answers,
        scores=scores,
    )
    session.add(submission)
    session.commit()
    session.refresh(submission)
    response.headers["Location"] = f"/submissions/{submission.id}"
    return submission


@router.get(
    "/submissions/{submission_id}",
    response_model=SubmissionDetail,
    summary="Get one submission",
)
def get_submission(submission_id: int, session: SessionDep):
    submission = session.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail=f"Submission {submission_id} not found")
    return submission