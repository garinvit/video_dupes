from sqlalchemy import Column, Integer, String, Float, BigInteger, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base


class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    status = Column(String(32), default="queued")  # queued, running, done, error
    params = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)

    pairs = relationship("Pair", back_populates="job", cascade="all, delete-orphan")
    groups = relationship("Group", back_populates="job", cascade="all, delete-orphan")


class Pair(Base):
    __tablename__ = "pairs"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    similarity = Column(Float, index=True)
    label = Column(String(32))

    file_a = Column(Text, nullable=False)
    size_a = Column(BigInteger)
    duration_a = Column(Float)
    res_a = Column(String(32))

    file_b = Column(Text, nullable=False)
    size_b = Column(BigInteger)
    duration_b = Column(Float)
    res_b = Column(String(32))

    job = relationship("Job", back_populates="pairs")


class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    representative_path = Column(Text, nullable=False)
    count = Column(Integer, default=0)
    total_size = Column(BigInteger, default=0)  # сумма размеров файлов в группе

    job = relationship("Job", back_populates="groups")
    files = relationship("GroupFile", back_populates="group", cascade="all, delete-orphan")


class GroupFile(Base):
    __tablename__ = "group_files"
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    path = Column(Text, nullable=False)
    size = Column(BigInteger)
    duration = Column(Float)
    res = Column(String(32))
    is_representative = Column(Boolean, default=False)

    group = relationship("Group", back_populates="files")