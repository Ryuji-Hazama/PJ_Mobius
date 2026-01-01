import datetime
import maplex
import TableAdapters

class SessionUpdate:

    def __init__(self):

        # Logging objects

        self.Logger = maplex.Logger("UserLogout")

    def Update(self, token: str, update: str) -> bool:

        try:

            tableAdapter = TableAdapters.SessionInfoTableAdapters()
            tableAdapter.UpdateLogout(token, update)
            return True

        except Exception as e:

            self.Logger.ShowError(e, "Failed to logout.")
            raise

        finally:

            if 'tableAdapter' in locals():

                tableAdapter.closeConnection()

    def CreateNewSession(self, userInfo) -> tuple | None:

        ''' Create new session for the user '''

        try:

            tableAdapter = TableAdapters.SessionInfoTableAdapters()
            sessionId = tableAdapter.CreateNewSession(userInfo)

            if not sessionId:

                self.Logger.Error("Failed to create new session.")
                return None

            sessionInfo = tableAdapter.selectSessionInfo(sessionId)

            if not sessionInfo:

                self.Logger.Error("Failed to get new session info.")
                return None
            
            elif len(sessionInfo) > 1:

                self.Logger.Error("Duplicate new session info.")
                return None

            sessionInfoDict = {
                "Token": sessionId,
                "UserID": sessionInfo[0][0],
                "CompanyID": sessionInfo[0][1],
                "AccessLevel": sessionInfo[0][2],
                "LogoutTime": sessionInfo[0][3]
            }

            return sessionInfoDict
        
        except Exception as e:

            self.Logger.ShowError(e, "Failed to create new session.")
            raise

        finally:

            if 'tableAdapter' in locals():

                tableAdapter.closeConnection()

class CheckSession:

    def __init__(self, token):

        # Logging objects

        self.Logger = maplex.Logger("CheckSession")

        self.token = token

        # Table adapter

        self.tableAdapter = TableAdapters.SessionInfoTableAdapters()

    def close(self):

        self.tableAdapter.closeConnection()
        self.Logger.Info("Closed CheckSession object.")

    def IsValid(self, updateSessionTime=True):

        try:

            # Get session info

            sessionInfo = self.tableAdapter.selectSessionInfo(self.token)

            if not sessionInfo:

                self.Logger.Warn("Invalid session info: Session not found.")
                return False

            # Check expire time

            currentTime = datetime.datetime.now()

            if sessionInfo[0][3] < currentTime:

                self.Logger.Warn("Invalid session info: Session expired.")
                return False

            if updateSessionTime:

                self.tableAdapter.UpdateLogout(self.token, "00:30:00")

            return True

        except Exception as e:

            self.Logger.ShowError(e, "Failed to check session.")
            raise

    def GetSessionInfo(self):

        ''' Get session info: user_id, company_id, access_level, logout_time '''

        try:

            # Get session info

            sessionInfo = self.tableAdapter.selectSessionInfo(self.token)

            if not sessionInfo:

                self.Logger.Warn("Invalid session info: Session not found.")
                return None

            return sessionInfo[0]

        except Exception as e:

            self.Logger.ShowError(e, "Failed to get session info.")
            raise

    def isActive(self, userId: int) -> bool:

        """ Check if the user is active. """

        try:

            logoutDatetime = datetime.datetime.now()
            sessionInfo = self.tableAdapter.selectSessionInfoByTimeAndUser(userId, "after", logoutDatetime)

            if not sessionInfo:

                self.Logger.Info(f"User {userId} is not active.")
                return False
            
            self.Logger.Info(f"User {userId} is active.")
            return True
        
        except Exception as e:

            self.Logger.ShowError(e, "Failed to check if user is active.")
            raise