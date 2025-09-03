import os
import socket
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def _ensure_ipv4_dsn(url: str) -> str:
    """Optionally add hostaddr to force IPv4 if NC_PG_FORCE_IPV4 is set.

    - If query already has hostaddr, return unchanged.
    - If NC_PG_FORCE_IPV4 is not truthy, return unchanged (allow IPv6).
    - Otherwise resolve A record and add hostaddr.
    """
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return url

        # Parse query params and bail if hostaddr already present
        query_params = dict(parse_qsl(parsed.query))
        if "hostaddr" in query_params:
            return url

        # Respect explicit opt-in to force IPv4
        if not os.getenv("NC_PG_FORCE_IPV4"):
            return url

        hostname = parsed.hostname
        if not hostname:
            return url

        # If the user provided an explicit IPv4, prefer it
        env_hostaddr = os.getenv("NC_PG_HOSTADDR")
        if env_hostaddr:
            query_params["hostaddr"] = env_hostaddr
            new_query = urlencode(query_params)
            new_parsed = parsed._replace(query=new_query)
            return urlunparse(new_parsed)

        # Resolve IPv4 address for the hostname
        ipv4_candidates = [
            ai[4][0] for ai in socket.getaddrinfo(hostname, None, socket.AF_INET)
        ]
        if not ipv4_candidates:
            return url

        query_params["hostaddr"] = ipv4_candidates[0]
        new_query = urlencode(query_params)
        new_parsed = parsed._replace(query=new_query)
        return urlunparse(new_parsed)
    except Exception:
        # Best-effort only: if anything goes wrong, fall back to the original URL
        return url


def get_engine(dsn: Optional[str] = None):
    url = (
        dsn
        or os.getenv("NC_PG_DSN")
        or "postgresql+psycopg://neuro:neuro@localhost:5432/neuro"
    )
    # Optionally force IPv4 hostaddr if requested via env (default allows IPv6)
    url = _ensure_ipv4_dsn(url)
    engine = create_engine(url, echo=False, future=True)
    return engine


def get_session_factory(dsn: Optional[str] = None):
    engine = get_engine(dsn)
    return sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
