"""
Routers module for PJ_Mobius API endpoints.

This package contains FastAPI routers organized by functionality:
- admin: Administrative operations (super user initialization)
- auth: Authentication and session management
- users: User management operations
- companies: Company management operations
- health: Health check endpoints
"""

from . import admin, auth, users, companies, health

__all__ = ["admin", "auth", "users", "companies", "health"]
