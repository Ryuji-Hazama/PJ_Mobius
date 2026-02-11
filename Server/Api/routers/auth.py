"""
Authentication and session management router.

Handles login, logout, and session-related endpoints.
"""

import maplex
from fastapi import APIRouter

import BaseModelData as BMD
from datadomain import SessionUpdate, CheckSession, UserLogin

logger = maplex.Logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["authentication"])


@router.get("/login", response_model=BMD.LoginRequestResponse)
def getLogin(item: BMD.LoginRequestItem):

    logger.info(f"Login request received: {item.UserName}")
    retItem = BMD.LoginRequestResponse()

    if "" in {item.UserName, item.Password}:

        logger.warn(f"UserName or Password, or both are blank: [UserName: {item.UserName}, Password: {item.Password}]")
        retItem.LoginResult.Message = "Empty item."
        return retItem

    try:

        userLogin = UserLogin(item.UserName, item.Password)
        retItemDict = userLogin.Login()

        retItem.LoginResult = BMD.loginResult(**retItemDict["LoginResult"])
        retItem.SessionInfo = BMD.sessionInfo(**retItemDict["SessionInfo"])
        retItem.ErrorInfo = BMD.errorInfo(**retItemDict["ErrorInfo"])

    except Exception as e:

        logger.ShowError(e, "Failed to login.")
        retItem.ErrorInfo.Error = True
        retItem.ErrorInfo.Message = f"{e}"

    finally:

        if 'userLogin' in locals():

            userLogin.close()

    return retItem


@router.patch("/session", response_model=BMD.UpdateSessionRequestResponse)
def patchSession(item: BMD.UpdateSessionTimeRequestItem):

    # Update session time
    # Also used to log out (set update time to 00:00:00)

    logger.info(f"Session update request received: {item.model_dump()}")
    retItem = BMD.UpdateSessionRequestResponse()

    try:

        retItem.Update = SessionUpdate().Update(item.Token, item.Update)

    except Exception as e:

        logger.ShowError(e, "Failed to update session information.")
        retItem.ErrorInfo.Error = True
        retItem.ErrorInfo.Message = f"{e}"

    return retItem


@router.get("/session", response_model=BMD.SessionInfoResponse)
def getSessionInfo(item: BMD.UpdateSessionTimeRequestItem):

    logger.info(f"Get session info request received: {item.model_dump()}")
    retItem = BMD.SessionInfoResponse()

    try:

        sessionInfo = CheckSession(item.Token)

        if not sessionInfo.IsValid(False):

            retItem.ErrorInfo.Error = True
            retItem.ErrorInfo.Message = "Invalid session."
            return retItem

        sessionData = sessionInfo.GetSessionInfo()

        if not sessionData:

            retItem.ErrorInfo.Error = True
            retItem.ErrorInfo.Message = "Session not found."
            return retItem

        retItem.Session = True
        retItem.SessionInfo.UserID = sessionData[0]
        retItem.SessionInfo.CompanyID = sessionData[1]
        retItem.SessionInfo.AccessLevel = sessionData[2]
        retItem.SessionInfo.LogoutTime = sessionData[3]

    except Exception as e:

        logger.ShowError(e, "Failed to get session information.")
        retItem.ErrorInfo.Error = True
        retItem.ErrorInfo.Message = f"{e}"

    finally:

        if 'sessionInfo' in locals():

            sessionInfo.close()

    return retItem
