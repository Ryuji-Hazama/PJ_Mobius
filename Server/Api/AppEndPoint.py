"""
PJ_Mobius FastAPI Application.

Main application entry point that initializes FastAPI and registers all routers.
"""

import maplex
from fastapi import FastAPI
import sys

from routers import admin, auth, users, companies, health

############################################
# Logging objects

logger = maplex.Logger(__name__)
logger.info("Initializing AppEndPoint.")

try:

    ############################################
    # Initialize FastAPI instance

    logger.info("Initializing FastAPI.")
    app = FastAPI()
    logger.info("FastAPI initialized.")

    ############################################
    # Register routers

    app.include_router(admin.router)
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(companies.router)
    app.include_router(health.router)

    logger.info("All routers registered successfully.")

except Exception as e:

    logger.ShowError(e, "Failed to initialize AppEndPoint.")
    sys.exit(1)

logger.info("AppEndPoint initialized successfully.")