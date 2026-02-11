from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, Enum as SqlEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
from .models import LeadStatus, InteractionType

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
    
    # Scoring Data (Embedded for simplicity, could be separate table)
    demographic_score = Column(Float, default=0.0)
    behavioral_score = Column(Float, default=0.0)
    intent_score = Column(Float, default=0.0)
    total_score = Column(Float, default=0.0)
    score_breakdown = Column(JSON, default=dict)
    last_scored_at = Column(DateTime, nullable=True)

    tags = Column(JSON, default=list)
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
