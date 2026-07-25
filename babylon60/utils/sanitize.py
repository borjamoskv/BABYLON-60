from __future__ import annotations
import re
import unicodedata
from typing import Final
__all__ = ['sanitize_project_name', 'sanitize_query', 'sanitize_tenant_id', 'validate_fact_type', 'validate_pagination']
_PROJECT_RE: Final = re.compile('^[a-zA-Z0-9][a-zA-Z0-9_\\-\\.]{0,127}$')
_TENANT_RE: Final = re.compile('^[a-z0-9_\\-]{1,64}$', re.IGNORECASE)
ALLOWED_FACT_TYPES: Final = frozenset({'knowledge', 'decision', 'error', 'rule', 'axiom', 'schema', 'idea', 'ghost', 'bridge', 'pattern', 'episode', 'metric', 'config'})
_DANGEROUS_CHARS: Final = frozenset({'\x00', '\r', '\n', '\t', '\x1b'})
MAX_QUERY_LENGTH: Final = 2048

def sanitize_project_name(project: str) -> str:
    if not project:
        raise ValueError('Project name cannot be empty')
    project = unicodedata.normalize('NFKC', project).strip()
    if any((c in project for c in _DANGEROUS_CHARS)):
        raise ValueError('Project name contains forbidden characters')
    if not _PROJECT_RE.match(project):
        raise ValueError(f"Invalid project name: '{project}'. Must be 1-128 chars, alphanumeric with _-. allowed, starting with alphanumeric.")
    return project

def sanitize_tenant_id(tenant_id: str) -> str:
    if not tenant_id:
        return 'default'
    tenant_id = unicodedata.normalize('NFKC', tenant_id).strip()
    if not _TENANT_RE.match(tenant_id):
        raise ValueError(f"Invalid tenant_id: '{tenant_id}'. Must be 1-64 chars, lowercase alphanumeric with _- allowed.")
    return tenant_id

def sanitize_query(query: str) -> str:
    if not query or not query.strip():
        raise ValueError('Search query cannot be empty')
    query = unicodedata.normalize('NFKC', query).strip()
    query = ''.join((c for c in query if c not in _DANGEROUS_CHARS))
    if len(query) > MAX_QUERY_LENGTH:
        raise ValueError(f'Query too long ({len(query)} chars, max {MAX_QUERY_LENGTH})')
    return query

def validate_fact_type(fact_type: str) -> str:
    fact_type = fact_type.strip().lower()
    if fact_type not in ALLOWED_FACT_TYPES:
        raise ValueError(f"Invalid fact_type: '{fact_type}'. Allowed: {', '.join(sorted(ALLOWED_FACT_TYPES))}")
    return fact_type

def validate_pagination(limit: int | None=None, offset: int | None=None, max_limit: int=1000) -> tuple[int, int]:
    if limit is not None:
        if limit < 1:
            limit = 1
        elif limit > max_limit:
            limit = max_limit
    else:
        limit = 50
    if offset is not None:
        if offset < 0:
            offset = 0
    else:
        offset = 0
    return (limit, offset)