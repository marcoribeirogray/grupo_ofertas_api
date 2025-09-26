from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Boolean, JSON, Text, UniqueConstraint

from .database import Base


class TimestampMixin:\n    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)\n    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)\n\n\nclass User(TimestampMixin, Base):\n    __tablename__ = "users"\n\n    id = Column(Integer, primary_key=True, index=True)\n    email = Column(String(255), nullable=False, unique=True, index=True)\n    full_name = Column(String(120))\n    password_hash = Column(String(255), nullable=False)\n    role = Column(String(32), nullable=False, default="editor")\n    is_active = Column(Boolean, nullable=False, default=True)\n\n\nclass IntegrationSetting(TimestampMixin, Base):
    __tablename__ = "integration_settings"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(50), nullable=False, unique=True)
    label = Column(String(120), nullable=False)
    data = Column(JSON, default=dict)


class OfferTemplate(TimestampMixin, Base):
    __tablename__ = "offer_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    slug = Column(String(80), nullable=False, unique=True)
    description = Column(String(255))
    body = Column(Text, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)


class TransformationRule(TimestampMixin, Base):
    __tablename__ = "transformation_rules"
    __table_args__ = (UniqueConstraint("name", name="uq_rule_name"),)

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    description = Column(String(255))
    conditions = Column(JSON, default=dict)
    actions = Column(JSON, default=dict)
