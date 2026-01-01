import datetime
import maplex
import Session
import TableAdapters
import Tools

class UserLogin:

    def __init__(self, userName: str, userPassword: str):

        # Logging objects

        self.Logger = maplex.Logger("UserLogin")

        # Variables

        self.userName = userName
        self.userPassword = Tools.stringHasher().hashString(userPassword, userName)
        self.userTableAdapter = TableAdapters.UserTableAdapters()

        self.Logger.Info(f"UserLogin instance created for user [{self.userName}].")

    def close(self):

        self.userTableAdapter.closeConnection()
        self.Logger.Info("Closed UserLogin object.")

    def updateLoginFailed(self, userId: int, failedCount: int, failedAt: datetime.datetime | None = None) -> str:

        try:

            status = "active"

            if failedAt is not None:

                self.Logger.Debug(f"Last failed login at {failedAt}, current failed count is {failedCount}.")
                suspendCount = failedCount - 2
                suspendTime = datetime.timedelta(minutes=30 * suspendCount)

                if datetime.datetime.now() < failedAt + suspendTime or suspendCount < 1:

                    if failedCount < 10:

                        failedCount += 1

                # Set as suspended if failed count reached 3

                if failedCount >= 3:

                    self.Logger.Info(f"User ID [{userId}] account suspended due to multiple failed login attempts.")
                    status = "suspended"

                # Update failed time

                failedAt = datetime.datetime.now()

            self.userTableAdapter.updateLoginFailed(userId, failedCount, failedAt, status)
            return status
        
        except Exception as e:

            self.Logger.ShowError(e, "Failed to update login failed info.")
            raise

    def checkSuspended(self, userId: int, failedCount: int, failedAt: datetime.datetime | None) -> str:

        try:

            status = "active"

            if failedAt is not None:

                self.Logger.Debug(f"Last failed login at {failedAt}, current failed count is {failedCount}.")
                suspendCount = failedCount - 2
                suspendTime = datetime.timedelta(minutes=30 * suspendCount)

                if datetime.datetime.now() < failedAt + suspendTime:

                    self.Logger.Info(f"User account is currently suspended due to multiple failed login attempts.")
                    status = "suspended"

                else:

                    self.Logger.Debug(f"Suspend time has passed. User account is no longer suspended.")
                    self.updateLoginFailed(userId, 0, None)

            return status
        
        except Exception as e:

            self.Logger.ShowError(e, "Failed to check suspended status.")
            raise

    def Login(self) -> dict:

        retDict = {
            "LoginResult": 
                   {
                       "Login": False,
                       "Token": None,
                       "Message": "Authentication failed.",
                       "InitialPassword": False
                   },
            "SessionInfo": 
                   {
                       "UserID": None,
                       "CompanyID": None,
                       "AccessLevel": None,
                       "LogoutTime": None
                   },
            "ErrorInfo": 
                   {
                       "Error": False,
                       "ErrorMessage": ""
                   }
        }

        if self.userName == "":

            self.Logger.Warn("User name is blank. (This log should not be outputed.)")
            retDict["LoginResult"]["Message"] = "User name is blank."
            return retDict

        try:

            userList = self.userTableAdapter.selectUser(userName=self.userName)

            if userList:

                if len(userList) > 1:

                    self.Logger.Warn("Invalid user info: Duplicate user name.")
                    return retDict
                
                userStatus = userList[0][9]

                if userStatus == "inactive":

                    # Treat inactive users as non-loginable
                    self.Logger.Warn(f"User account is inactive state.")
                    retDict["LoginResult"]["Message"] = f"User account is inactive state."
                    return retDict
                
                tablePassword = userList[0][3]
                
                if tablePassword != self.userPassword:

                    # Update login failed info

                    if userList[0][8] is None:

                        suspendDatetime = datetime.datetime.now()

                    else:

                        suspendDatetime = userList[0][8]

                    userStatus = self.updateLoginFailed(userList[0][0], userList[0][7], suspendDatetime)
                    
                    if userStatus == "suspended":

                        self.Logger.Info("Invalid user info: Invalid user password and account is suspended.")
                        retDict["LoginResult"]["Message"] = "User suspended due to multiple failed login attempts."
                        return retDict
                    
                    else:

                        self.Logger.Info("Invalid user info: Invalid user password.")

                    return retDict

                if userStatus == "suspended":

                    # Check login failed count and time

                    if self.checkSuspended(userList[0][0], userList[0][7], userList[0][8]) == "suspended":

                        self.Logger.Info("Invalid user info: User account is still suspended.")
                        retDict["LoginResult"]["Message"] = "User suspended due to multiple failed login attempts."
                        return retDict

                elif userList[0][7] != 0 or userList[0][8] is not None:

                    # Reset login failed count

                    self.updateLoginFailed(userList[0][0], 0, None)
                
                # Create and get new session

                sessionInfo = Session.SessionUpdate().CreateNewSession(userList[0])

                if not sessionInfo:

                    self.Logger.Warn("Invalid session info: Duplicate session.")
                    retDict["LoginResult"]["Message"] = "There is another session remains from another computer."
                    return retDict

                retDict["LoginResult"]["Login"] = True
                retDict["LoginResult"]["Token"] = sessionInfo["Token"]
                retDict["LoginResult"]["Message"] = "Login success."
                retDict["SessionInfo"]["UserID"] = sessionInfo["UserID"]
                retDict["SessionInfo"]["CompanyID"] = sessionInfo["CompanyID"]
                retDict["SessionInfo"]["AccessLevel"] = sessionInfo["AccessLevel"]
                retDict["SessionInfo"]["LogoutTime"] = sessionInfo["LogoutTime"]

                if userList[0][4] == 1:

                    retDict["LoginResult"]["InitialPassword"] = True

                return retDict

            else:

                self.Logger.Warn("User name not found.")

        except Exception as e:

            self.Logger.ShowError(e, "Failed to login.")
            retDict["ErrorInfo"]["Error"] = True
            retDict["ErrorInfo"]["ErrorMessage"] = f"{e}"
        
        return retDict

class UserPasswordUpdate:

    def __init__(self, userName: str, userPassword: str, token: str, userOldPassword: str | None = None):

        # Logging objects

        self.Logger = maplex.Logger("UserPasswordUpdate")

        # Variables

        self.userName = userName
        self.userPassword = userPassword
        self.userOldPassword = userOldPassword

        # Table adapters

        self.userTableAdapter = TableAdapters.UserTableAdapters()
        self.sessionTableAdapter = Session.CheckSession(token)

    def close(self):

        self.userTableAdapter.closeConnection()
        self.sessionTableAdapter.close()
        self.Logger.Info("Closed UserPasswordUpdate object.")

    def Update(self):

        retDict = {"Update": False, "Message": "", "ErrorInfo": {"Error": False, "ErrorMessage": ""}}
        accessLevel = {"super": 3, "admin": 2, "user": 1, "guest": 0}

        try:

            # Get session infos

            if not self.sessionTableAdapter.IsValid():

                retDict["Message"] = "Session time out."
                self.Logger.Error("User session time out.")
                return retDict

            sessionData = self.sessionTableAdapter.GetSessionInfo()
            sessionAccessLevel = accessLevel[sessionData[2]]

            # Check password pattern

            if not Tools.CheckPasswordPattern(self.userPassword):

                retDict["Message"] = "Bad password: Password must be at least 8 characters long and contain uppercase, lowercase, digit, and special character."
                self.Logger.Error("Bad password pattern.")
                return retDict
            
            # Get user data

            userDataList = self.userTableAdapter.selectUser(userName=self.userName)

            if not userDataList:

                retDict["Message"] = "User not found."
                self.Logger.Error("User not found.")
                return retDict

            if len(userDataList) > 1:

                retDict["Message"] = "Duplicate user name."
                self.Logger.Error("Duplicate user name.")
                return retDict
            
            userData = userDataList[0]

            ########################################################################
            # Authentication

            if self.userOldPassword is None:

                # Check authentication if this is an admin reset

                # Check company match (If not super)

                if sessionAccessLevel != accessLevel["super"] and sessionData[1] != userData[6]:

                    retDict["Message"] = "User has no authority to change the password."
                    self.Logger.Error("User has no authority to change password: Company mismatch.")
                    return retDict
                
                # Check access level

                userAccessLevel = accessLevel[userData[5]]

                if sessionAccessLevel <= userAccessLevel:

                    retDict["Message"] = "User has no authority to change the password."
                    self.Logger.Error(f"User has no authority to change password: [User: {sessionAccessLevel} / Target: {userAccessLevel}]")
                    return retDict

            else:

                # If this is an user reset, check the old password

                dbOldPassword = userData[3]
                userOldPasswordHash = Tools.stringHasher().hashString(self.userOldPassword, self.userName)

                if dbOldPassword != userOldPasswordHash:

                    retDict["Message"] = "Password incorrect."
                    self.Logger.Error("User old password did not match.")
                    return retDict

            # Authentication complete
            ########################################################################

            # Update password

            newPasswordHash = Tools.stringHasher().hashString(self.userPassword, self.userName)
            self.userTableAdapter.updateUserPassword(userData[0], newPasswordHash, sessionData[0])
            retDict["Update"] = True
            retDict["Message"] = "Password updated successfully."
            self.Logger.Info("User password updated successfully.")

        except Exception as e:

            self.Logger.ShowError(e, "Failed to update password.")
            retDict["ErrorInfo"]["Error"] = True
            retDict["ErrorInfo"]["ErrorMessage"] = f"{e}"

        return retDict

class UserInfo:

    def __init__(self, token: str):

        # Logging objects

        self.Logger = maplex.Logger("UserInfo")

        # Table adapters

        self.userTableAdapter = TableAdapters.UserTableAdapters()
        self.sessionData = Session.CheckSession(token)

        # Variables

        self.token = token

    def close(self):

        self.userTableAdapter.closeConnection()
        self.sessionData.close()
        self.Logger.Info("Closed UserInfo object.")

    def getUserInfo(self, userId: int | None = None, userName: str | None = None, eMail: str | None = None, accessLevel: str | None = None, companyId: int | None = None, userStatus: str | None = None, active: bool | None = None) -> list[dict] | None:

        retDict = {"Users": [], "ErrorInfo": {"Error": False, "ErrorMessage": ""}}

        # Check parameters

        if userId is None and userName is None and eMail is None and accessLevel is None and companyId is None and userStatus is None:

            retDict["ErrorInfo"]["Error"] = True
            retDict["ErrorInfo"]["ErrorMessage"] = "At least one search condition must be specified."
            self.Logger.Error("At least one search condition must be specified.")
            return retDict

        try:

            # Get session infos

            if not self.sessionData.IsValid(True):

                retDict["ErrorInfo"]["Error"] = True
                retDict["ErrorInfo"]["ErrorMessage"] = "Session time out."
                self.Logger.Error("User session time out.")
                return retDict
            
            sessionInfo = self.sessionData.GetSessionInfo()
            sessionAccessLevel = sessionInfo[2]
            sessionCompanyId = sessionInfo[1]

            # Check access level

            if sessionAccessLevel not in ["super", "admin", "user"]:

                retDict["ErrorInfo"]["Error"] = True
                retDict["ErrorInfo"]["ErrorMessage"] = "User has no authority to get user information."
                self.Logger.Error(f"User has no authority to get user information: Access level [{sessionAccessLevel}]")
                return retDict
            
            if companyId is not None and sessionCompanyId != companyId and sessionAccessLevel != "super":

                retDict["ErrorInfo"]["Error"] = True
                retDict["ErrorInfo"]["ErrorMessage"] = "User has no authority to get user information.\nCannot search other company user."
                self.Logger.Error(f"User has no authority to get user information: Company mismatch. [Session: {sessionCompanyId} / Request: {companyId}]")
                return retDict
            
            if accessLevel is not None:
                
                accessLevelDict = {"super": 3, "admin": 2, "user": 1, "guest": 0}

                if accessLevel not in accessLevelDict:

                    retDict["ErrorInfo"]["Error"] = True
                    retDict["ErrorInfo"]["ErrorMessage"] = "Bad access level."
                    self.Logger.Error(f"Bad access level: {accessLevel}")
                    return retDict
                
                if accessLevelDict[sessionAccessLevel] <= accessLevelDict[accessLevel] and sessionAccessLevel != "super":

                    retDict["ErrorInfo"]["Error"] = True
                    retDict["ErrorInfo"]["ErrorMessage"] = "User has no authority to get user information.\nCannot search same or higher access level user."
                    self.Logger.Error(f"User has no authority to get user information: Access level too high. [Session: {sessionAccessLevel} / Request: {accessLevel}]")
                    return retDict
                
            # Get user info

            userList = self.userTableAdapter.selectUser(userId=userId, userName=userName, eMail=eMail, accessLevel=accessLevel, companyId=companyId, userStatus=userStatus)

            # Build return dict user list

            if userList:

                for user in userList:

                    try:

                        isActive = self.sessionData.isActive(user[0])

                    except Exception as e:

                        self.Logger.ShowError(e, "Failed to check if user is active.")
                        isActive = False

                    if active is not None and isActive != active:

                        continue

                    userDict = {
                        "UserID": user[0],
                        "UserName": user[1],
                        "Email": user[2],
                        "AccessLevel": user[5],
                        "CompanyID": user[6],
                        "UserStatus": user[9],
                        "Active": isActive
                    }
                    retDict["Users"].append(userDict)

            return retDict
        
        except Exception as e:

            self.Logger.ShowError(e, "Failed to get user information.")
            retDict["ErrorInfo"]["Error"] = True
            retDict["ErrorInfo"]["ErrorMessage"] = f"{e}"
            return retDict
        
    def addUser(self, userName: str, eMail: str, password: str, initialPassword: int, accessLevel: str, userStatus: str, companyId: int | None = None) -> dict:

        retDict = {"Created": False, "UserID": None, "ErrorInfo": {"Error": False, "ErrorMessage": ""}}

        try:

            # Get session infos

            if not self.sessionData.IsValid(True):

                retDict["ErrorInfo"]["Error"] = True
                retDict["ErrorInfo"]["ErrorMessage"] = "Session time out."
                self.Logger.Error("User session time out.")
                return retDict
            
            sessionInfo = self.sessionData.GetSessionInfo()
            sessionAccessLevel = sessionInfo[2]
            sessionUserId = sessionInfo[0]

            # Check access level

            if sessionAccessLevel not in ["super", "admin", "user"]:

                retDict["ErrorInfo"]["Error"] = True
                retDict["ErrorInfo"]["ErrorMessage"] = "Guest user has no authority to add user."
                self.Logger.Error(f"Guest user has no authority to add user: Access level [{sessionAccessLevel}]")
                return retDict
            
            if sessionAccessLevel != "super":

                if companyId is None:

                    companyId = sessionInfo[1]

                elif companyId != sessionInfo[1]:

                    retDict["ErrorInfo"]["Error"] = True
                    retDict["ErrorInfo"]["ErrorMessage"] = "User has no authority to add user.\nCannot add user to other company."
                    self.Logger.Error(f"User has no authority to add user: Company mismatch. [Session: {sessionInfo[1]} / Request: {companyId}]")
                    return retDict
                
            # Check value validity

            if accessLevel not in ["super", "admin", "user", "guest"]:

                retDict["ErrorInfo"]["Error"] = True
                retDict["ErrorInfo"]["ErrorMessage"] = "Bad access level."
                self.Logger.Error(f"Bad access level: {accessLevel}")
                return retDict

            if userStatus not in ["active", "inactive", "suspended"]:

                retDict["ErrorInfo"]["Error"] = True
                retDict["ErrorInfo"]["ErrorMessage"] = "Bad user status."
                self.Logger.Error(f"Bad user status: {userStatus}")
                return retDict
            
            if not Tools.CheckPasswordPattern(password):

                retDict["ErrorInfo"]["Error"] = True
                retDict["ErrorInfo"]["ErrorMessage"] = "Bad password: Password must be at least 8 characters long and contain uppercase, lowercase, digit, and special character."
                self.Logger.Error("Bad password pattern.")
                return retDict
            
            if accessLevel != "super" and companyId is None:

                retDict["ErrorInfo"]["Error"] = True
                retDict["ErrorInfo"]["ErrorMessage"] = "Company must be specified for non-Super users."
                self.Logger.Error("Company must be specified for non-Super users.")
                return retDict
            
            # Add user

            retDict["Created"] = self.userTableAdapter.insertUser(
                userName=userName,
                eMail=eMail,
                userPassword=password,
                initialPassword=initialPassword,
                accessLevel=accessLevel,
                companyId=companyId,
                userStatus=userStatus,
                createUserId=sessionUserId
            )

            if retDict["Created"]:

                retDict["UserID"] = self.userTableAdapter.selectUser(userName=userName)[0][0]
                self.Logger.Info(f"User [{userName}] added successfully. [UserID: {retDict['UserID']}]")

            return retDict
        
        except Exception as e:

            self.Logger.ShowError(e, "Failed to add user.")
            retDict["ErrorInfo"]["Error"] = True
            retDict["ErrorInfo"]["ErrorMessage"] = f"{e}"
            return retDict
