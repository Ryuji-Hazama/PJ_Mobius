"""
User management router.

Handles user CRUD operations and password updates.
"""

import maplex
from fastapi import APIRouter

import BaseModelData as BMD
from datadomain import UserInfo, UserPasswordUpdate

logger = maplex.Logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["users"])


@router.patch("/password", response_model=BMD.UpdatePasswordRequestResponse)
def putPassword(item: BMD.UpdatePasswordRequestItem):

    logger.info(f"Password update request received: {item.UserName}")
    retItem = BMD.UpdatePasswordRequestResponse()

    # If the old password is None, it is an higher-level user changing another user's password.
    # In this case, need to compare the token's user privilege with the target user's privilege.
    # First, check if the token is valid.

    try:

        userPasswordUpdate = UserPasswordUpdate(item.UserName, item.NewPassword, item.Token, item.OldPassword)
        retItem = userPasswordUpdate.Update()

    except Exception as e:

        logger.ShowError(e, "Failed to update password.")
        retItem.ErrorInfo.Error = True
        retItem.ErrorInfo.Message = f"{e}"

    finally:

        if 'userPasswordUpdate' in locals():

            userPasswordUpdate.close()

    return retItem


@router.post("/user", response_model=BMD.PostUserInfoResponse)
def postUserInfo(item: BMD.PostUserInfoRequestItem):

    logger.info(f"Post user info request received.")
    # No model dump for security reason
    retItem = BMD.PostUserInfoResponse()

    try:

        userInfo = UserInfo(item.Token)
        retDict = userInfo.addUser(
            item.UserName,
            item.Email,
            item.Password,
            item.InitialPassword,
            item.AccessLevel,
            item.UserStatus,
            item.CompanyID
            )
        retItem.Created = retDict["Created"]
        retItem.UserID = retDict["UserID"]
        retItem.ErrorInfo = BMD.errorInfo(**retDict["ErrorInfo"])

    except Exception as e:

        logger.ShowError(e, "Failed to post user information.")
        retItem.ErrorInfo.Error = True
        retItem.ErrorInfo.Message = f"{e}"

    finally:

        if 'userInfo' in locals():

            userInfo.close()

    return retItem


@router.get("/user", response_model=BMD.GetUserInfoResponse)
def getUserInfo(item: BMD.GetUserInfoRequestItem):

    logger.info(f"Get user info request received: {item.model_dump()}")
    retItem = BMD.GetUserInfoResponse()

    try:

        userInfo = UserInfo(item.Token)
        retItemDict = userInfo.getUserInfo(
            userId=item.UserID,
            userName=item.UserName,
            eMail=item.Email,
            accessLevel=item.AccessLevel,
            companyId=item.CompanyID,
            userStatus=item.UserStatus,
            active=item.Active
            )
        retItem.Users = [BMD.UserInfoResponseItem(**user) for user in retItemDict["Users"]]
        retItem.ErrorInfo = BMD.errorInfo(**retItemDict["ErrorInfo"])

    except Exception as e:

        logger.ShowError(e, "Failed to get user information.")
        retItem.ErrorInfo.Error = True
        retItem.ErrorInfo.Message = f"{e}"

    finally:
        
        if 'userInfo' in locals():

            userInfo.close()

    return retItem
