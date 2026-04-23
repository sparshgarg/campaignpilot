"""SQL generation utilities for safe query construction.

Provides validation and sanitization functions to prevent SQL injection
and ensure only allowed queries are executed.
"""

import re
import logging
from typing import Any

logger = logging.getLogger(__name__)

ALLOWED_TABLES = frozenset([
    "campaigns",
    "campaign_briefs",
    "creatives",
    "performance_events",
    "optimization_recommendations",
    "eval_runs",
    "campaign_performance_summary"
])

ALLOWED_OPERATIONS = frozenset(["SELECT"])


def validate_sql(sql: str) -> tuple[bool, str]:
    """Validate SQL query for safety and allowed operations.

    Checks that:
    - Only SELECT statements are allowed (no INSERT/UPDATE/DELETE/DROP)
    - All table references are in ALLOWED_TABLES
    - No SQL injection patterns are detected

    Args:
        sql: SQL query string to validate.

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty.
    """
    sql_stripped = sql.strip()

    # Check operation type
    operation_match = re.match(r"^\s*(\w+)", sql_stripped, re.IGNORECASE)
    if not operation_match:
        return False, "Empty or invalid SQL query"

    operation = operation_match.group(1).upper()
    if operation not in ALLOWED_OPERATIONS:
        return False, f"Operation '{operation}' not allowed. Only SELECT is permitted."

    # Detect stacked queries (semicolon injection)
    if re.search(r";\s*(?:INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)", sql, re.IGNORECASE):
        return False, "Stacked query detected. Multiple SQL statements are not allowed."

    # Detect comment injection patterns
    if re.search(r"(?:--|/\*|\*/).*?(?:INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)", sql, re.IGNORECASE):
        return False, "Comment injection detected."

    # Extract table names from FROM and JOIN clauses
    table_pattern = r"(?:FROM|JOIN|INNER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|FULL\s+JOIN|CROSS\s+JOIN)\s+(\w+)"
    tables = re.findall(table_pattern, sql, re.IGNORECASE)

    for table in tables:
        if table.upper() not in ALLOWED_TABLES:
            return False, f"Table '{table}' is not in the allowed tables list."

    # Check for suspicious patterns
    if re.search(r"(?:UNION|INTERSECT|EXCEPT)", sql, re.IGNORECASE):
        # UNION queries are technically SELECT, but allow only if properly scoped
        # For now, allow them as they're part of SELECT operations
        pass

    # Check for xp_cmdshell or other dangerous stored procedures
    if re.search(r"xp_|sp_OA|\.xp_", sql, re.IGNORECASE):
        return False, "Dangerous stored procedures detected."

    # Check for WAITFOR or time-based attacks
    if re.search(r"WAITFOR|BENCHMARK|SLEEP", sql, re.IGNORECASE):
        return False, "Potential timing attack detected."

    logger.debug(f"SQL validation passed for query: {sql_stripped[:100]}...")
    return True, ""


def sanitize_identifier(identifier: str) -> str:
    """Sanitize a database identifier (table, column name).

    Only allows alphanumeric characters and underscores. Useful for
    dynamic table/column names after whitelist checking.

    Args:
        identifier: Identifier to sanitize.

    Returns:
        Sanitized identifier.

    Raises:
        ValueError: If identifier contains illegal characters.
    """
    if not re.match(r"^[a-zA-Z0-9_]+$", identifier):
        raise ValueError(
            f"Identifier '{identifier}' contains illegal characters. "
            "Only alphanumeric and underscores allowed."
        )

    return identifier
