"""
Administrative operations router.

Handles super user initialization and other admin-related endpoints.
"""

import maplex
from fastapi import APIRouter

import BaseModelData as BMD
import initSuperUser

logger = maplex.Logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["admin"])


@router.post("/initsuper", response_model=BMD.InitSuperResponse)
def initSuperReceived(item: BMD.InitSuperUserItem):

    logger.info("Init super user request received.")

    passWd = item.Password
    superUserName = item.SuperUserName
    superPassword = item.SuperUserPassword

    # Initialize response item

    resultItem = BMD.InitSuperResponse()
    resultItem.Registered = False
    resultItem.ErrorInfo.Message = None

    if None in item or "" in item:

        resultItem.ErrorInfo.Error = True
        resultItem.ErrorInfo.Message = "Invalid request."
        logger.error(f"Invalid request item.")
        return resultItem
    
    try:

        resultItem.Registered = initSuperUser.InitSuperUser(passWd, superUserName, superPassword).initSuperUser()

    except Exception as e:

        logger.ShowError(e, "Exception occurred while registering the super user.")
        resultItem.ErrorInfo.Error = True
        resultItem.ErrorInfo.Message = f"{e}"

    return resultItem
