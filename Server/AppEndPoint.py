"""
PJ_Mobius FastAPI Application.

Main application entry point that initializes FastAPI and registers all routers.
"""

import maplex
from fastapi import FastAPI

from routers import admin, auth, users, companies, health

############################################
# Logging objects

Logger = maplex.Logger("AppEndPoint")

############################################
# Initialize FastAPI instance

Logger.Info("Initializing FastAPI.")
app = FastAPI()
Logger.Info("FastAPI initialized.")

############################################
# Register routers

app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(companies.router)
app.include_router(health.router)

Logger.Info("All routers registered successfully.")