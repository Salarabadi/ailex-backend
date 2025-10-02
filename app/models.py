from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from .db import Base

# Tenants
class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    status = Column(String, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Users
class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(String, default="researcher")  # admin, researcher, sales_viewer
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Personas
class Persona(Base):
    __tablename__ = "personas"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)

# Plans
class Plan(Base):
    __tablename__ = "plans"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)

# Persona × Plan matrix
class PersonaPlanMatrix(Base):
    __tablename__ = "persona_plan_matrix"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("personas.id"))
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"))
    base_price_cents = Column(Integer, default=0)
    included_reports = Column(Integer, default=0)

# Sources
class Source(Base):
    __tablename__ = "sources"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False)
    category = Column(String, nullable=False)  # events/laws or person/entity
    status = Column(String, default="active")

# Subscriptions
class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    persona_id = Column(UUID(as_uuid=True), ForeignKey("personas.id"))
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"))
    status = Column(String, default="active")
    start_at = Column(DateTime(timezone=True), server_default=func.now())
    renew_at = Column(DateTime(timezone=True), nullable=True)

# Subscription Sources
class SubscriptionSource(Base):
    __tablename__ = "subscription_sources"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id"))
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"))
    provisioning_status = Column(String, default="active")
