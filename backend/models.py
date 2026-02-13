import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    DateTime,
    JSON,
    Float,
    Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


# ==============================
# Student
# ==============================

class Student(Base):
    __tablename__ = "students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    attempts = relationship("Attempt", back_populates="student")


# ==============================
# Test
# ==============================

class Test(Base):
    __tablename__ = "tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    max_marks = Column(Integer, nullable=False)
    negative_marking = Column(JSON, nullable=False)
    answer_key = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    attempts = relationship("Attempt", back_populates="test")


# ==============================
# Attempt
# ==============================

class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"))
    test_id = Column(UUID(as_uuid=True), ForeignKey("tests.id"))

    source_event_id = Column(String, nullable=False)

    started_at = Column(DateTime(timezone=True))
    submitted_at = Column(DateTime(timezone=True), nullable=True)

    answers = Column(JSON, nullable=False)
    raw_payload = Column(JSON, nullable=False)

    status = Column(String, default="INGESTED")

    duplicate_of_attempt_id = Column(
        UUID(as_uuid=True),
        ForeignKey("attempts.id"),
        nullable=True
    )

    # Relationships
    student = relationship("Student", back_populates="attempts")
    test = relationship("Test", back_populates="attempts")

    score = relationship(
        "AttemptScore",
        back_populates="attempt",
        uselist=False
    )

    flags = relationship(
        "Flag",
        back_populates="attempt"
    )


# ==============================
# AttemptScore
# ==============================

class AttemptScore(Base):
    __tablename__ = "attempt_scores"

    attempt_id = Column(
        UUID(as_uuid=True),
        ForeignKey("attempts.id"),
        primary_key=True
    )

    correct = Column(Integer, nullable=False)
    wrong = Column(Integer, nullable=False)
    skipped = Column(Integer, nullable=False)
    accuracy = Column(Float, nullable=False)
    net_correct = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)

    explanation = Column(JSON, nullable=False)

    computed_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # 🚨 THIS WAS MISSING (CRITICAL)
    attempt = relationship("Attempt", back_populates="score")


# ==============================
# Flag
# ==============================

class Flag(Base):
    __tablename__ = "flags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id = Column(UUID(as_uuid=True), ForeignKey("attempts.id"))

    reason = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    attempt = relationship("Attempt", back_populates="flags")