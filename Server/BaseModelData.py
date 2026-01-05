from pydantic import BaseModel
import datetime

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
# Add company request item class

class AddCompanyRequestItem(BaseModel):

    Token: str | None = None
    CompanyName: str | None = None
    ContractLevel: int | None = None
    CompanyPhone: str | None = None
    CompanyZipCode: str | None = None
    CompanyAddress: str | None = None
    CompanyEmail: str | None = None

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
