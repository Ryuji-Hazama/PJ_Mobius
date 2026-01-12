"""
DEPRECATED: This file has been refactored into the api/ module.

This file is kept for backward compatibility but should not be used.
Please import from the api module instead:
    from api import SessionInfo
    from api import UserInfo
    from api import CompanyInfo
    from api import requestToServer
    from api import NONE_LIST

The new structure provides:
- api/base.py - Shared utilities and HTTP request handling
- api/session.py - Session management operations
- api/user.py - User data operations
- api/company.py - Company data operations
"""

# Re-export classes and functions from the new api module for backward compatibility
from api import (
    requestToServer,
    NONE_LIST,
    SessionInfo,
    UserInfo,
    CompanyInfo
)

__all__ = [
    "requestToServer",
    "NONE_LIST",
    "SessionInfo",
    "UserInfo",
    "CompanyInfo"
]
