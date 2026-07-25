import re
_SAFE_IDENTIFIER = re.compile('^[a-zA-Z_][a-zA-Z0-9_]{0,63}\\Z')

def is_safe_identifier(name: str) -> bool:
    return bool(_SAFE_IDENTIFIER.match(name))

def validate_sql_identifier(name: str) -> str:
    if not is_safe_identifier(name):
        raise ValueError(f'Unsafe SQL identifier rejected: {name!r}')
    return name

def quote_identifier(name: str) -> str:
    validate_sql_identifier(name)
    return f'"{name}"'