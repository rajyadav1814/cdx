"""
CDX — Database Connection Module

Provides a single thread-safe psycopg2 connection pool.
All other modules import `get_conn()` from here.

Environment variable: DATABASE_URL (standard libpq URI)
  e.g.  postgresql://user:pass@localhost:5432/cdx
"""

import os
from contextlib import contextmanager

from dotenv import load_dotenv
import psycopg2
from psycopg2 import pool as psycopg2_pool

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

_pool: psycopg2_pool.ThreadedConnectionPool | None = None


def _get_pool() -> psycopg2_pool.ThreadedConnectionPool:
    """Lazily create the connection pool on first call."""
    global _pool
    if _pool is None:
        dsn = os.environ.get('DATABASE_URL')
        if not dsn:
            raise RuntimeError(
                "DATABASE_URL is not set. Add it to ~/cdx/.env:\n"
                "  DATABASE_URL=postgresql://user:pass@localhost:5432/cdx"
            )
        _pool = psycopg2_pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=dsn,
        )
    return _pool


@contextmanager
def get_conn():
    """
    Context manager that yields a psycopg2 connection from the pool.
    Commits on exit, rolls back on exception, always returns conn to pool.

    Usage:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(...)
    """
    p = _get_pool()
    conn = p.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)


def close_pool():
    """Close all connections in the pool. Call at process shutdown."""
    global _pool
    if _pool:
        _pool.closeall()
        _pool = None
