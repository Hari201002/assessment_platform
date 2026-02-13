import uuid
import time
from datetime import datetime
from typing import Optional, List, Dict

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from database import SessionLocal
from models import Student, Test, Attempt, AttemptScore, Flag
from utils import normalize_email, normalize_phone
from scoring import compute_score
from dedup import is_duplicate
from logger import logger
from schemas import AttemptEvent, FlagRequest


# =========================================================
# App Setup
# =========================================================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# Request Logging Middleware
# =========================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()

    logger.info(
        "request_started",
        extra={
            "channel": "http",
            "context": {"request_id": request_id},
            "extra_data": {
                "method": request.method,
                "path": request.url.path,
                "ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            },
        },
    )

    response = await call_next(request)

    duration = round((time.time() - start_time) * 1000, 2)

    logger.info(
        "request_completed",
        extra={
            "channel": "http",
            "context": {
                "request_id": request_id,
                "status_code": response.status_code,
            },
            "extra_data": {"latency_ms": duration},
        },
    )

    response.headers["X-Request-ID"] = request_id
    return response


# =========================================================
# DB Dependency
# =========================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()





# =========================================================
# Ingest Attempts
# =========================================================

@app.post("/api/ingest/attempts")
def ingest_attempts(payload: List[AttemptEvent], db: Session = Depends(get_db)):

    for event in payload:

        # Normalize student identity
        email = normalize_email(event.student.email)
        phone = normalize_phone(event.student.phone)

        student = db.query(Student).filter(
            (Student.email == email) | (Student.phone == phone)
        ).first()

        if not student:
            student = Student(
                full_name=event.student.full_name,
                email=email,
                phone=phone,
            )
            db.add(student)
            db.commit()
            db.refresh(student)

        # Create or fetch test
        test = db.query(Test).filter(Test.name == event.test.name).first()

        if not test:
            test = Test(
                name=event.test.name,
                max_marks=event.test.max_marks,
                negative_marking=event.test.negative_marking,
                answer_key=event.test.answer_key,
            )
            db.add(test)
            db.commit()
            db.refresh(test)

        # Parse timestamps safely
        try:
            started_at = datetime.fromisoformat(event.started_at.replace("Z", ""))
            submitted_at = (
                datetime.fromisoformat(event.submitted_at.replace("Z", ""))
                if event.submitted_at else None
            )
        except Exception:
            logger.info(
                "malformed_timestamp",
                extra={
                    "channel": "ingest",
                    "context": {"source_event_id": event.source_event_id},
                },
            )
            continue

        attempt = Attempt(
            student_id=student.id,
            test_id=test.id,
            source_event_id=event.source_event_id,
            started_at=started_at,
            submitted_at=submitted_at,
            answers=event.answers,
            raw_payload=event.dict(),
            status="INGESTED",
        )

        # Dedup
        existing_attempts = db.query(Attempt).filter(
            and_(
                Attempt.student_id == student.id,
                Attempt.test_id == test.id,
            )
        ).all()

        duplicate_found = False

        for existing in existing_attempts:
            similarity = is_duplicate(attempt, existing)
            if similarity:
                attempt.status = "DEDUPED"
                attempt.duplicate_of_attempt_id = existing.id
                duplicate_found = True

                logger.info(
                    "dedup_detected",
                    extra={
                        "channel": "dedup",
                        "context": {
                            "attempt_id": event.source_event_id,
                            "canonical_id": str(existing.id),
                        },
                    },
                )
                break

        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        # Scoring
        if not duplicate_found:
            start_score_time = time.time()

            score_data = compute_score(test, event.answers)

            logger.info(
                "score_computed",
                extra={
                    "channel": "scoring",
                    "context": {
                        "attempt_id": str(attempt.id),
                        "score": score_data["score"],
                    },
                    "extra_data": {
                        "duration_ms": round(
                            (time.time() - start_score_time) * 1000, 2
                        )
                    },
                },
            )

            db.add(
                AttemptScore(
                    attempt_id=attempt.id,
                    correct=score_data["correct"],
                    wrong=score_data["wrong"],
                    skipped=score_data["skipped"],
                    accuracy=score_data["accuracy"],
                    net_correct=score_data["net_correct"],
                    score=score_data["score"],
                    explanation=score_data["explanation"],
                )
            )

            attempt.status = "SCORED"
            db.commit()

    return {"message": "Ingested successfully"}


# =========================================================
# Recompute
# =========================================================

@app.post("/api/attempts/{attempt_id}/recompute")
def recompute_attempt(attempt_id: str, db: Session = Depends(get_db)):

    attempt = db.query(Attempt).filter(Attempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404)

    if attempt.status == "DEDUPED":
        raise HTTPException(status_code=400)

    test = db.query(Test).filter(Test.id == attempt.test_id).first()

    score_data = compute_score(test, attempt.answers)

    existing = db.query(AttemptScore).filter(
        AttemptScore.attempt_id == attempt.id
    ).first()

    if existing:
        for key in score_data:
            setattr(existing, key, score_data[key])
    else:
        db.add(AttemptScore(attempt_id=attempt.id, **score_data))

    attempt.status = "SCORED"
    db.commit()

    return {"message": "Recomputed successfully"}


# =========================================================
# Flag
# =========================================================

@app.post("/api/attempts/{attempt_id}/flag")
def flag_attempt(
    attempt_id: str,
    flag_data: FlagRequest,
    db: Session = Depends(get_db),
):

    attempt = db.query(Attempt).filter(Attempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404)

    db.add(Flag(attempt_id=attempt.id, reason=flag_data.reason))
    attempt.status = "FLAGGED"
    db.commit()

    return {"message": "Attempt flagged successfully"}


# =========================================================
# List Attempts
# =========================================================

@app.get("/api/attempts")
def list_attempts(
    test_id: Optional[str] = None,
    student_id: Optional[str] = None,
    status: Optional[str] = None,
    has_duplicates: Optional[bool] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
    db: Session = Depends(get_db),
):

    query = db.query(Attempt).options(
        joinedload(Attempt.student),
        joinedload(Attempt.test),
        joinedload(Attempt.score),
        joinedload(Attempt.flags),
    )

    if test_id:
        query = query.filter(Attempt.test_id == test_id)
    if student_id:
        query = query.filter(Attempt.student_id == student_id)
    if status:
        query = query.filter(Attempt.status == status)
    if has_duplicates is not None:
        query = query.filter(
            Attempt.duplicate_of_attempt_id.isnot(None)
            if has_duplicates
            else Attempt.duplicate_of_attempt_id.is_(None)
        )
    if date_from:
        query = query.filter(Attempt.started_at >= date_from)
    if date_to:
        query = query.filter(Attempt.started_at <= date_to)
    if search:
        query = query.join(Student).filter(
            or_(
                Student.full_name.ilike(f"%{search}%"),
                Student.email.ilike(f"%{search}%"),
                Student.phone.ilike(f"%{search}%"),
            )
        )

    total = query.count()

    attempts = (
        query.order_by(Attempt.started_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": [
            {
                "attempt_id": str(a.id),
                "student": a.student.full_name if a.student else None,
                "test": a.test.name if a.test else None,
                "status": a.status,
                "score": a.score.score if a.score else None,
                "has_duplicates": a.duplicate_of_attempt_id is not None,
            }
            for a in attempts
        ],
    }


# =========================================================
# Leaderboard
# =========================================================

@app.get("/api/leaderboard")
def leaderboard(
    test_id: str,
    page: int = Query(1),
    page_size: int = Query(10),
    db: Session = Depends(get_db),
):

    rows = (
        db.query(Attempt, AttemptScore)
        .join(AttemptScore, Attempt.id == AttemptScore.attempt_id)
        .filter(Attempt.test_id == test_id, Attempt.status == "SCORED")
        .all()
    )

    best = {}

    for attempt, score in rows:
        sid = attempt.student_id
        candidate = {"attempt": attempt, "score": score}

        if sid not in best:
            best[sid] = candidate
        else:
            existing = best[sid]
            if (
                score.score > existing["score"].score
                or (
                    score.score == existing["score"].score
                    and score.accuracy > existing["score"].accuracy
                )
                or (
                    score.score == existing["score"].score
                    and score.accuracy == existing["score"].accuracy
                    and score.net_correct > existing["score"].net_correct
                )
                or (
                    score.score == existing["score"].score
                    and score.accuracy == existing["score"].accuracy
                    and score.net_correct == existing["score"].net_correct
                    and attempt.submitted_at < existing["attempt"].submitted_at
                )
            ):
                best[sid] = candidate

    leaderboard_list = [
        {
            "student_id": str(v["attempt"].student_id),
            "attempt_id": str(v["attempt"].id),
            "score": v["score"].score,
            "accuracy": v["score"].accuracy,
            "net_correct": v["score"].net_correct,
            "submitted_at": v["attempt"].submitted_at,
        }
        for v in best.values()
    ]

    leaderboard_list.sort(
        key=lambda x: (-x["score"], -x["accuracy"], -x["net_correct"], x["submitted_at"])
    )

    total = len(leaderboard_list)
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": leaderboard_list[(page - 1) * page_size : page * page_size],
    }


# =========================================================
# List Tests
# =========================================================

@app.get("/api/tests")
def list_tests(db: Session = Depends(get_db)):
    return [
        {"id": str(t.id), "name": t.name}
        for t in db.query(Test).all()
    ]
