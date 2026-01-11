import maplex
from fastapi import FastAPI

import BaseModelData as BMD
import Company
import initSuperUser
import Session
import User

############################################
# Logging objects

Logger = maplex.Logger("AppEndPoint")

############################################
# Initialize FastAPI instance
# and set SSL

Logger.Info("Initializing FastAPI.")
app = FastAPI()
Logger.Info("FastAPI initialized.")
v1Root = "/api/v1"

############################################
# Main methods
############################################
# Initialize super user data

@app.post(f"{v1Root}/initsuper", response_model=BMD.InitSuperResponse)
def initSuperReceived(item: BMD.InitSuperUserItem):

    Logger.Info("Init super user request received.")

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
        Logger.Error(f"Invalid request item.")
        return resultItem
    
    try:

        resultItem.Registered = initSuperUser.InitSuperUser(passWd, superUserName, superPassword).initSuperUser()

    except Exception as e:

        Logger.ShowError(e, "Exception occurred while registering the super user.")
        resultItem.ErrorInfo.Error = True
        resultItem.ErrorInfo.Message = f"{e}"

    return resultItem

#################################
# Login

@app.get(f"{v1Root}/login", response_model=BMD.LoginRequestResponse)
def getLogin(item: BMD.LoginRequestItem):

    Logger.Info(f"Login request received: {item.UserName}")
    retItem = BMD.LoginRequestResponse()

    if "" in {item.UserName, item.Password}:

        Logger.Warn(f"UserName or Password, or both are blank: [UserName: {item.UserName}, Password: {item.Password}]")
        retItem.LoginResult.Message = "Empty item."
        return retItem

    try:

        userLogin = User.UserLogin(item.UserName, item.Password)
        retItemDict = userLogin.Login()

        retItem.LoginResult = BMD.loginResult(**retItemDict["LoginResult"])
        retItem.SessionInfo = BMD.sessionInfo(**retItemDict["SessionInfo"])
        retItem.ErrorInfo = BMD.errorInfo(**retItemDict["ErrorInfo"])

    except Exception as e:

        Logger.ShowError(e, "Failed to login.")
        retItem.ErrorInfo.Error = True
        retItem.ErrorInfo.Message = f"{e}"

    finally:

        if 'userLogin' in locals():

            userLogin.close()

    return retItem

@app.patch(f"{v1Root}/session", response_model=BMD.UpdateSessionRequestResponse)
def patchSession(item: BMD.UpdateSessionTimeRequestItem):

    # Update session time
    # Also used to log out (set update time to 00:00:00)

    Logger.Info(f"Session update request received: {item.model_dump()}")
    retItem = BMD.UpdateSessionRequestResponse()

    try:

        retItem.Update = Session.SessionUpdate().Update(item.Token, item.Update)

    except Exception as e:

        Logger.ShowError(e, "Failed to update session information.")
        retItem.ErrorInfo.Error = True
        retItem.ErrorInfo.Message = f"{e}"

    return retItem

@app.get(f"{v1Root}/session", response_model=BMD.SessionInfoResponse)
def getSessionInfo(item: BMD.UpdateSessionTimeRequestItem):

    Logger.Info(f"Get session info request received: {item.model_dump()}")
    retItem = BMD.SessionInfoResponse()

    try:

        sessionInfo = Session.CheckSession(item.Token)

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

        Logger.ShowError(e, "Failed to get session information.")
        retItem.ErrorInfo.Error = True
        retItem.ErrorInfo.Message = f"{e}"

    finally:

        if 'sessionInfo' in locals():

            sessionInfo.close()

    return retItem

#####################################
# Update password

@app.patch(f"{v1Root}/password", response_model=BMD.UpdatePasswordRequestResponse)
def putPassword(item: BMD.UpdatePasswordRequestItem):

    Logger.Info(f"Password update request received: {item.UserName}")
    retItem = BMD.UpdatePasswordRequestResponse()

    # If the old password is None, it is an higher-level user changing another user's password.
    # In this case, need to compare the token's user privilege with the target user's privilege.
    # First, check if the token is valid.

    try:

        userPasswordUpdate = User.UserPasswordUpdate(item.UserName, item.NewPassword, item.Token, item.OldPassword)
        retItem = userPasswordUpdate.Update()

    except Exception as e:

        Logger.ShowError(e, "Failed to update password.")
        retItem.ErrorInfo.Error = True
        retItem.ErrorInfo.Message = f"{e}"

    finally:

        if 'userPasswordUpdate' in locals():

            userPasswordUpdate.close()

    return retItem

#####################################
# Post user info

@app.post(f"{v1Root}/user", response_model=BMD.PostUserInfoResponse)
def postUserInfo(item: BMD.PostUserInfoRequestItem):

    Logger.Info(f"Post user info request received.")
    # No model dump for security reason
    retItem = BMD.PostUserInfoResponse()

    try:

        userInfo = User.UserInfo(item.Token)
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

        Logger.ShowError(e, "Failed to post user information.")
        retItem.ErrorInfo.Error = True
        retItem.ErrorInfo.Message = f"{e}"

    finally:

        if 'userInfo' in locals():

            userInfo.close()

    return retItem

#####################################
# Get user info

@app.get(f"{v1Root}/user", response_model=BMD.GetUserInfoResponse)
def getUserInfo(item: BMD.GetUserInfoRequestItem):

    Logger.Info(f"Get user info request received: {item.model_dump()}")
    retItem = BMD.GetUserInfoResponse()

    try:

        userInfo = User.UserInfo(item.Token)
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

        Logger.ShowError(e, "Failed to get user information.")
        retItem.ErrorInfo.Error = True
        retItem.ErrorInfo.Message = f"{e}"

    finally:
        
        if 'userInfo' in locals():

            userInfo.close()

    return retItem

#####################################
# Post company informations

@app.post(f"{v1Root}/company", response_model=BMD.PostCompanyResponse)
def postCompanyInfo(item: BMD.PostCompanyRequestItem):

    Logger.Info(f"Post company info request received: {item.model_dump()}")
    retItem = BMD.PostCompanyResponse()

    try:

        companyManager = Company.CompanyManager(item.Token)
        retItem = companyManager.createCompany(
            item.CompanyName,
            item.ContractLevel,
            item.CompanyPhone,
            item.CompanyZipCode,
            item.CompanyAddress,
            item.CompanyEmail
            )

    except Exception as e:

        Logger.ShowError(e, "Failed to post company information.")
        retItem.ErrorInfo.Error = True
        retItem.ErrorInfo.Message = f"{e}"

    finally:

        if 'companyManager' in locals():

            companyManager.close()

    return retItem

#####################################
# Get company informations

@app.get(f"{v1Root}/company", response_model=BMD.GetCompanyInfoResponse)
def getCompanyInfo(item: BMD.GetCompanyInfoRequestItem):

    Logger.Info(f"Get company info request received: {item.model_dump()}")
    retItem = BMD.GetCompanyInfoResponse()

    try:

        companyManager = Company.CompanyManager(item.Token)
        retDict = companyManager.getCompanyList(str,item.CompanyID, item.CompanyName, item.ContractLevel)

        # Break down company list

        for company in retDict["CompanyList"]:

            companyItem = BMD.CompanyInfoResponseItem()
            companyItem.CompanyID = company[0]
            companyItem.CompanyName = company[1]
            companyItem.CompanyPhone = company[2]
            companyItem.CompanyZipCode = company[3]
            companyItem.CompanyAddress = company[4]
            companyItem.CompanyEmail = company[5]
            companyItem.ContractLevel = company[6]

            retItem.Companies.append(companyItem)

        retItem.ErrorInfo = BMD.errorInfo(**retDict["ErrorInfo"])

    except Exception as e:

        Logger.ShowError(e, "Failed to get company information.")
        retItem.ErrorInfo.Error = True
        retItem.ErrorInfo.Message = f"{e}"

    finally:

        if 'companyManager' in locals():

            companyManager.close()

    return retItem

#####################################
# Health check

@app.get("/healthcheck", response_model=BMD.HealthCheckResponse)
def HealthCheck():

    return {"ResponseMessage": "Hello from PJ_Mobius."}