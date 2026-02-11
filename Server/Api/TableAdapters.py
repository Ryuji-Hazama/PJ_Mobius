"""
DEPRECATED: This file has been refactored into the db/ module.

This file is kept for backward compatibility but should not be used.
Please import from the db module instead:
    from db import UserTableAdapters
    from db import SessionInfoTableAdapters
    from db import CompanyTableAdapters
    from db import DbConnection

The new structure provides:
- db/connection.py - Database connection management
- db/user_adapter.py - User table operations
- db/session_adapter.py - Session table operations
- db/company_adapter.py - Company table operations
"""

# Re-export classes from the new db module for backward compatibility
from db import (
    DbConnection,
    UserTableAdapters,
    SessionInfoTableAdapters,
    CompanyTableAdapters
)

__all__ = [
    "DbConnection",
    "UserTableAdapters",
    "SessionInfoTableAdapters",
    "CompanyTableAdapters"
]
