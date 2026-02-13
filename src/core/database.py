from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
import socket
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./prospect.db")

# Render.com gives postgres:// but SQLAlchemy 2.x requires postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

create_engine_kwargs: dict = {}

# Force IPv4 resolution for PostgreSQL to avoid Render/Supabase IPv6 issues
# We use 'hostaddr' in connect_args to force the IP connection while keeping the hostname in the URL for SSL verification.
if DATABASE_URL.startswith("postgresql://"):
    try:
        parsed = urlparse(DATABASE_URL)
        hostname = parsed.hostname
        ipv4 = None
        
        # Try resolving the hostname directly first
        try:
            ipv4 = socket.getaddrinfo(hostname, None, socket.AF_INET)[0][4][0]
            print(f"Resolved database host {hostname} to IPv4: {ipv4}")
        except socket.gaierror:
            # Fallback for Supabase: If project-specific hostname has no IPv4, try the generic pooler (US-East-1 default)
            # This is common for newer Supabase projects or specific Render DNS issues.
            fallback_host = "aws-0-us-east-1.pooler.supabase.com"
            print(f"Warning: Failed to resolve {hostname} to IPv4. Trying fallback: {fallback_host}")
            ipv4 = socket.getaddrinfo(fallback_host, None, socket.AF_INET)[0][4][0]
            print(f"Resolved fallback host {fallback_host} to IPv4: {ipv4}")

        if ipv4:
            # Helper to ensure connect_args exists
            if "connect_args" not in create_engine_kwargs:
                create_engine_kwargs["connect_args"] = {}
            
            # Pass hostaddr to libpq to force connection to this IP
            create_engine_kwargs["connect_args"]["hostaddr"] = ipv4
            
    except Exception as e:
        print(f"Warning: Failed to resolve database host to IPv4: {e}")

if DATABASE_URL.startswith("sqlite"):
    create_engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # For PostgreSQL: recover from stale connections automatically
    create_engine_kwargs["pool_pre_ping"] = True

engine = create_engine(DATABASE_URL, **create_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
