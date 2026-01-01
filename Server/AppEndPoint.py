import datetime
import maplex
from fastapi import FastAPI
from pydantic import BaseModel

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

#####################################
# Error info class

class errorInfo(BaseModel):

    Error: bool = False
    ErrorMessage: str | None = None

############################################
# Request item class
############################################
# Init super user request item class

class InitSuperUserItem(BaseModel):

    Password: str | None = None
    SuperUserName: str | None = None
    SuperUserPassword: str | None = None

############################################
# Login request item class

class LoginRequestItem(BaseModel):

    UserName: str | None = None
    Password: str | None = None

############################################
# Logout/UpdateSessionTime request item class

class UpdateSessionTimeRequestItem(BaseModel):

    Token: str | None = None
    Update: str = "00:30:00"

############################################
# Update password request item class

class UpdatePasswordRequestItem(BaseModel):

    Token: str | None = None
    UserName: str | None = None
    OldPassword: str | None = None
    NewPassword: str | None = None

############################################
# Get user info request item class

class GetUserInfoRequestItem(BaseModel):

    Token: str | None = None
    UserID: int | None = None
    UserName: str | None = None
    Email: str | None = None
    AccessLevel: str | None = None
    CompanyID: int | None = None
    UserStatus: str | None = None
    Active: bool | None = None

############################################
# Post user info request item class

class PostUserInfoRequestItem(BaseModel):

    Token: str | None = None
    UserName: str | None = None
    Email: str | None = None
    Password: str | None = None
    InitialPassword: int | None = None
    AccessLevel: str | None = None
    UserStatus: str | None = None
    CompanyID: int | None = None

############################################
# Get company info request item class

class GetCompanyInfoRequestItem(BaseModel):

    Token: str | None = None
    CompanyID: int | None = None
    CompanyName: str | None = None
    ContractLevel: int | None = None

############################################
# Response item class
############################################
# Health check response item

class HealthCheckResponse(BaseModel):

    ResponseMessage: str

############################################
# Init super user response item class

class InitSuperResponse(BaseModel):

    Registered: bool | None = None
    ErrorInfo: errorInfo = errorInfo()

############################################
# Login request response item class

class loginResult(BaseModel):

    Login: bool = False
    Token: str | None = None
    Message: str | None = None
    InitialPassword: bool = False

class sessionInfo(BaseModel):

    UserID: int | None = None
    CompanyID: int | None = None
    AccessLevel: str | None = None
    LogoutTime: datetime.datetime | None = None

class LoginRequestResponse(BaseModel):

    LoginResult: loginResult = loginResult()
    SessionInfo: sessionInfo = sessionInfo()
    ErrorInfo: errorInfo = errorInfo()

############################################
# Logout/UpdateSessionTime request response item class

class UpdateSessionRequestResponse(BaseModel):

    Update: bool = False
    ErrorInfo: errorInfo = errorInfo()

############################################
# Update password request response item class

class UpdatePasswordRequestResponse(BaseModel):

    Update: bool = False
    Message: str | None = None
    ErrorInfo: errorInfo = errorInfo()

############################################
# Get session info response item class

class SessionInfoResponse(BaseModel):

    Session: bool = False
    SessionInfo: sessionInfo = sessionInfo()
    ErrorInfo: errorInfo = errorInfo()

############################################
# Get user info response item class

class UserInfoResponseItem(BaseModel):

    UserID: int | None = None
    UserName: str | None = None
    Email: str | None = None
    AccessLevel: str | None = None
    CompanyID: int | None = None
    UserStatus: str | None = None
    Active: bool | None = None

class GetUserInfoResponse(BaseModel):

    Users: list[UserInfoResponseItem] = []
    ErrorInfo: errorInfo = errorInfo()

############################################
# Post user info response item class

class PostUserInfoResponse(BaseModel):

    Created: bool = False
    UserID: int | None = None
    ErrorInfo: errorInfo = errorInfo()

############################################
# Get company info response item class

class CompanyInfoResponseItem(BaseModel):
    
    CompanyID: int | None = None
    CompanyName: str | None = None
    CompanyPhone: str | None = None
    CompanyZipCode: str | None = None
    CompanyAddress: str | None = None
    CompanyEmail: str | None = None
    ContractLevel: int | None = None

class GetCompanyInfoResponse(BaseModel):

    Companies: list[CompanyInfoResponseItem] = []
    ErrorInfo: errorInfo = errorInfo()

############################################
# Main methods
############################################
# Initialize super user data

@app.post(f"{v1Root}/initsuper", response_model=InitSuperResponse)
def initSuperReceived(item: InitSuperUserItem):

    Logger.Info("Init super user request received.")

    passWd = item.Password
    superUserName = item.SuperUserName
    superPassword = item.SuperUserPassword

    # Initialize response item

    resultItem = InitSuperResponse()
    resultItem.Registered = False
    resultItem.ErrorInfo.ErrorMessage = None

    if None in item or "" in item:

        resultItem.ErrorInfo.Error = True
        resultItem.ErrorInfo.ErrorMessage = "Invalid request."
        Logger.Error(f"Invalid request item.")
        return resultItem
    
    try:

        resultItem.Registered = initSuperUser.InitSuperUser(passWd, superUserName, superPassword).initSuperUser()

    except Exception as e:

        Logger.ShowError(e, "Exception occurred while registering the super user.")
        resultItem.ErrorInfo.Error = True
        resultItem.ErrorInfo.ErrorMessage = f"{e}"

    return resultItem

#################################
# Login

@app.get(f"{v1Root}/login", response_model=LoginRequestResponse)
def getLogin(item: LoginRequestItem):

    Logger.Info(f"Login request received: {item.UserName}")
    retItem = LoginRequestResponse()

    if "" in {item.UserName, item.Password}:

        Logger.Warn(f"UserName or Password, or both are blank: [UserName: {item.UserName}, Password: {item.Password}]")
        retItem.LoginResult.Message = "Empty item."
        return retItem

    try:

        userLogin = User.UserLogin(item.UserName, item.Password)
        retItemDict = userLogin.Login()

        retItem.LoginResult = loginResult(**retItemDict["LoginResult"])
        retItem.SessionInfo = sessionInfo(**retItemDict["SessionInfo"])
        retItem.ErrorInfo = errorInfo(**retItemDict["ErrorInfo"])

    except Exception as e:

        Logger.ShowError(e, "Failed to login.")
        retItem.ErrorInfo.Error = True
        retItem.ErrorInfo.ErrorMessage = f"{e}"

    finally:

        if 'userLogin' in locals():

            userLogin.close()

    return retItem

@app.patch(f"{v1Root}/session", response_model=UpdateSessionRequestResponse)
def patchSession(item: UpdateSessionTimeRequestItem):

    # Update session time
    # Also used to log out (set update time to 00:00:00)

    Logger.Info(f"Session update request received: {item.model_dump()}")
    retItem = UpdateSessionRequestResponse()

    try:

        retItem.Update = Session.SessionUpdate().Update(item.Token, item.Update)

    except Exception as e:

        Logger.ShowError(e, "Failed to update session information.")
        retItem.ErrorInfo.Error = True
        retItem.ErrorInfo.ErrorMessage = f"{e}"

    return retItem

@app.get(f"{v1Root}/session", response_model=SessionInfoResponse)
def getSessionInfo(item: UpdateSessionTimeRequestItem):

    Logger.Info(f"Get session info request received: {item.model_dump()}")
    retItem = SessionInfoResponse()

    try:

        sessionInfo = Session.CheckSession(item.Token)

        if not sessionInfo.IsValid(False):

            retItem.ErrorInfo.Error = True
            retItem.ErrorInfo.ErrorMessage = "Invalid session."
            return retItem

        sessionData = sessionInfo.GetSessionInfo()

        if not sessionData:

            retItem.ErrorInfo.Error = True
            retItem.ErrorInfo.ErrorMessage = "Session not found."
            return retItem

        retItem.Session = True
        retItem.SessionInfo.UserID = sessionData[0]
        retItem.SessionInfo.CompanyID = sessionData[1]
        retItem.SessionInfo.AccessLevel = sessionData[2]
        retItem.SessionInfo.LogoutTime = sessionData[3]

    except Exception as e:

        Logger.ShowError(e, "Failed to get session information.")
        retItem.ErrorInfo.Error = True
        retItem.ErrorInfo.ErrorMessage = f"{e}"

    finally:

        if 'sessionInfo' in locals():

            sessionInfo.close()

    return retItem

#####################################
# Update password

@app.patch(f"{v1Root}/password", response_model=UpdatePasswordRequestResponse)
def putPassword(item: UpdatePasswordRequestItem):

    Logger.Info(f"Password update request received: {item.UserName}")
    retItem = UpdatePasswordRequestResponse()

    # If the old password is None, it is an higher-level user changing another user's password.
    # In this case, need to compare the token's user privilege with the target user's privilege.
    # First, check if the token is valid.

    try:

        userPasswordUpdate = User.UserPasswordUpdate(item.UserName, item.NewPassword, item.Token, item.OldPassword)
        userPasswordUpdate.Update()

    except Exception as e:

        Logger.ShowError(e, "Failed to update password.")
        retItem.ErrorInfo.Error = True
        retItem.ErrorInfo.ErrorMessage = f"{e}"

    finally:

        if 'userPasswordUpdate' in locals():

            userPasswordUpdate.close()

    return retItem

#####################################
# Post user info

@app.post(f"{v1Root}/user", response_model=PostUserInfoResponse)
def postUserInfo(item: PostUserInfoRequestItem):

    Logger.Info(f"Post user info request received.")
    # No model dump for security reason
    retItem = PostUserInfoResponse()

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
        retItem.ErrorInfo = errorInfo(**retDict["ErrorInfo"])

    except Exception as e:

        Logger.ShowError(e, "Failed to post user information.")
        retItem.ErrorInfo.Error = True
        retItem.ErrorInfo.ErrorMessage = f"{e}"

    finally:

        if 'userInfo' in locals():

            userInfo.close()

    return retItem

#####################################
# Get user info

@app.get(f"{v1Root}/user", response_model=GetUserInfoResponse)
def getUserInfo(item: GetUserInfoRequestItem):

    Logger.Info(f"Get user info request received: {item.model_dump()}")
    retItem = GetUserInfoResponse()

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
        retItem.Users = [UserInfoResponseItem(**user) for user in retItemDict["Users"]]
        retItem.ErrorInfo = errorInfo(**retItemDict["ErrorInfo"])

    except Exception as e:

        Logger.ShowError(e, "Failed to get user information.")
        retItem.ErrorInfo.Error = True
        retItem.ErrorInfo.ErrorMessage = f"{e}"

    finally:
        
        if 'userInfo' in locals():

            userInfo.close()

    return retItem

#####################################
# Get company informations

@app.get(f"{v1Root}/company", response_model=GetCompanyInfoResponse)
def getCompanyInfo(item: GetCompanyInfoRequestItem):

    Logger.Info(f"Get company info request received: {item.model_dump()}")
    retItem = GetCompanyInfoResponse()

    try:

        companyManager = Company.CompanyManager(item.Token)
        retDict = companyManager.getCompanyList(str,item.CompanyID, item.CompanyName, item.ContractLevel)

        # Break down company list

        for company in retDict["CompanyList"]:

            companyItem = CompanyInfoResponseItem()
            companyItem.CompanyID = company[0]
            companyItem.CompanyName = company[1]
            companyItem.CompanyPhone = company[2]
            companyItem.CompanyZipCode = company[3]
            companyItem.CompanyAddress = company[4]
            companyItem.CompanyEmail = company[5]
            companyItem.ContractLevel = company[6]

            retItem.Companies.append(companyItem)

        retItem.ErrorInfo = errorInfo(**retDict["ErrorInfo"])

    except Exception as e:

        Logger.ShowError(e, "Failed to get company information.")
        retItem.ErrorInfo.Error = True
        retItem.ErrorInfo.ErrorMessage = f"{e}"

    finally:

        if 'companyManager' in locals():

            companyManager.close()

    return retItem

#####################################
# Health check

@app.get("/healthcheck", response_model=HealthCheckResponse)
def HealthCheck():

    return {"ResponseMessage": "Hello from PJ_Mobius."}