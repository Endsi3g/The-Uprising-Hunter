from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, Enum as SqlEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
from .models import LeadStatus, LeadStage, LeadOutcome, InteractionType

class DBCompany(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    domain = Column(String, unique=True, index=True)
    industry = Column(String, nullable=True)
    size_range = Column(String, nullable=True)
    revenue_range = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    location = Column(String, nullable=True)
    tech_stack = Column(JSON, default=list) # Store as JSON array
    description = Column(String, nullable=True)

    leads = relationship("DBLead", back_populates="company")

class DBLead(Base):
    __tablename__ = "leads"

    id = Column(String, primary_key=True, index=True) # Using email as ID for compatibility
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    title = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    
    company_id = Column(Integer, ForeignKey("companies.id"))
    company = relationship("DBCompany", back_populates="leads")
    
    status = Column(SqlEnum(LeadStatus), default=LeadStatus.NEW)
    segment = Column(String, nullable=True)
    stage = Column(SqlEnum(LeadStage), default=LeadStage.NEW)
    outcome = Column(SqlEnum(LeadOutcome), nullable=True)
    
    # Legacy scoring columns (kept for compatibility with existing DBs)
    demographic_score = Column(Float, default=0.0)
    behavioral_score = Column(Float, default=0.0)
    intent_score = Column(Float, default=0.0)
    score_breakdown = Column(JSON, default=dict)

    # Current scoring model
    icp_score = Column(Float, default=0.0)
    heat_score = Column(Float, default=0.0)
    total_score = Column(Float, default=0.0)
    tier = Column(String, default="Tier D")
    heat_status = Column(String, default="Cold")
    next_best_action = Column(String, nullable=True)
    icp_breakdown = Column(JSON, default=dict)
    heat_breakdown = Column(JSON, default=dict)
    last_scored_at = Column(DateTime, nullable=True)

    tags = Column(JSON, default=list)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    interactions = relationship("DBInteraction", back_populates="lead")

class DBInteraction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(String, ForeignKey("leads.id"))
    type = Column(SqlEnum(InteractionType))
    timestamp = Column(DateTime, default=datetime.now)
    details = Column(JSON, default=dict)

    lead = relationship("DBLead", back_populates="interactions")

class DBTask(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    title = Column(String)
    status = Column(String, default="To Do")
    priority = Column(String, default="Medium")
    due_date = Column(DateTime, nullable=True)
    assigned_to = Column(String, default="You")
    lead_id = Column(String, ForeignKey("leads.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

class DBProject(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    status = Column(String, default="Planning", index=True)
    lead_id = Column(String, ForeignKey("leads.id"), nullable=True)
    due_date = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class DBAdminSetting(Base):
    __tablename__ = "admin_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False, index=True)
    value_json = Column(JSON, default=dict, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
