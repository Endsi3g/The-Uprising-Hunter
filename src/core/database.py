from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./prospect.db")

# Render.com gives postgres:// but SQLAlchemy 2.x requires postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

import socket
from urllib.parse import urlparse, urlunparse

# Force IPv4 resolution for PostgreSQL to avoid Render/Supabase IPv6 issues
if DATABASE_URL.startswith("postgresql://"):
    try:
        parsed = urlparse(DATABASE_URL)
        if parsed.hostname:
            # Resolve to IPv4 address
            ipv4 = socket.getaddrinfo(parsed.hostname, None, socket.AF_INET)[0][4][0]
            # Replace hostname with IPv4 in the URL
            netloc = parsed.netloc.replace(parsed.hostname, ipv4)
            parsed = parsed._replace(netloc=netloc)
            DATABASE_URL = urlunparse(parsed)
            print(f"Resolved database host {parsed.hostname} to IPv4: {ipv4}")
    except Exception as e:
        print(f"Warning: Failed to resolve database host to IPv4: {e}")

create_engine_kwargs: dict = {}
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
