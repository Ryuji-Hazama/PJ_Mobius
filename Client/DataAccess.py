import datetime
import maplex
import os
import PJ_Mobius_Dialog
import requests
import threading
import time

NONE_LIST = [None, "", "None"]

def requestToServer(method: str, url: str, json: dict, processWindow: PJ_Mobius_Dialog.ProcessRequest | None = None) -> requests.Response | None:

    """ Send a request to the server and return the response. """
    
    response = None
    conf = maplex.MapleTree("config.mpl")
    certPath = conf.readMapleTag("VERIFY", "APPLICATION_SETTINGS", "HTTP_REQUEST")
    timeoutStr = conf.readMapleTag("TIMEOUT", "APPLICATION_SETTINGS", "HTTP_REQUEST")

    try:

        timeout = int(timeoutStr)

    except ValueError:

        timeout = 30  # Default timeout

    for i in range(3):

        try:

            if method.upper() == "GET":

                response = requests.get(url, json=json, verify=certPath, timeout=timeout)

            elif method.upper() == "POST":

                response = requests.post(url, json=json, verify=certPath, timeout=timeout)

            elif method.upper() == "PUT":

                response = requests.put(url, json=json, verify=certPath, timeout=timeout)

            else:

                raise ValueError(f"Unsupported HTTP method: {method}")

            if response.status_code == 200:

                return response

            if i < 2:

                time.sleep(2)

                if processWindow:

                    try:

                        processWindow.master.after(0, lambda msg=f"Retrying... ({i+1}/2)": processWindow.PackLabel(msg))

                    except Exception:

                        pass

        except Exception as e:

            time.sleep(2)

    return response

class SessionInfo:

    def __init__(self):
        
        # Logging objects

        self.Logger = maplex.Logger("DataAccess.SessionInfo")

        # variables

        self.token = os.getenv("PJ_MOBIUS_TOKEN")

        try:

            self.conf = maplex.MapleTree("config.mpl")
            domain = self.conf.readMapleTag("DOMAIN", "APPLICATION_SETTINGS", "HTTP_REQUEST")
            self.domain = f"https://{domain}/session"

        except Exception as e:

            self.Logger.ShowError(e, "Failed to read configuration file.")
            raise

        # Process window

        self.processWindow = None

    def getSessionInfo(self) -> dict | None:

        """ Get session info from server. """

        retDict = None

        try:

            def worker():

                nonlocal retDict

                try:

                    requestJson = {
                        "Token": self.token
                    }

                    response = requestToServer("GET", self.domain, requestJson, self.processWindow)

                    if self.processWindow:

                        # Close the process window on the main thread

                        try:

                            self.processWindow.master.after(0, self.processWindow.closeWindow)

                        except Exception:

                            try:

                                self.processWindow.closeWindow()

                            except Exception:

                                pass

                        self.processWindow = None

                    if response.status_code != 200:

                        self.Logger.Error(f"Failed to get session info. Status code: {response.status_code}")
                        retDict = None
                        return

                    retDict = response.json()
                    self.Logger.Debug(f"Get session info response: {retDict}")

                    if retDict.get("ErrorInfo", {}).get("Error", False):

                        self.Logger.Error(f"Error in get session info response: {retDict.get('ErrorInfo', {}).get('Message', '')}")
                        retDict = None
                        return

                except Exception as e:

                    self.Logger.ShowError(e, "Failed to get session info from server.")
                    retDict = None

            self.processWindow = PJ_Mobius_Dialog.ProcessRequest("Getting session info from server...")
            thread = threading.Thread(target=worker)
            thread.start()
            self.processWindow.master.wait_window(self.processWindow)

            thread.join()
            return retDict

        except Exception as e:

            self.Logger.ShowError(e, "Failed to get session info from server.")
            return None
        
        finally:

            if self.processWindow:

                self.processWindow.closeWindow()
                self.processWindow = None

    def checkSession(self) -> bool:

        """ Check if the current session is valid. """

        try:

            # Parse the locally-stored logout time. The server stores times in UTC
            # but the string may not include timezone information. Treat the value
            # as UTC explicitly to avoid mixing naive/local times with UTC.

            stored_logout = os.getenv("PJ_MOBIUS_LOGOUT")

            if not stored_logout:

                return False

            sessionTimeout = datetime.datetime.strptime(stored_logout, "%Y-%m-%dT%H:%M:%S")

            # Treat the parsed time as UTC (server provides UTC times)

            sessionTimeout = sessionTimeout.replace(tzinfo=datetime.timezone.utc)
            now = datetime.datetime.now(datetime.timezone.utc)
            self.Logger.Debug(f"Current time: {now}, Session timeout(UTC): {sessionTimeout}")

            # If current UTC time is before the timeout, session is still valid

            if now < sessionTimeout:

                return True

            sessionInfo = self.getSessionInfo()

            if sessionInfo is None:

                return False

            if not sessionInfo.get("Session", False):

                return False

            logoutTimeStr = sessionInfo.get("SessionInfo", {}).get("LogoutTime", "")

            if not logoutTimeStr:

                return False

            # Parse logout time from server and treat it as UTC

            logoutTime = datetime.datetime.strptime(logoutTimeStr, "%Y-%m-%dT%H:%M:%S")
            logoutTime = logoutTime.replace(tzinfo=datetime.timezone.utc)
            self.Logger.Debug(f"Current time: {now}, Logout time(UTC): {logoutTime}")
            # If now is before logoutTime, session is valid. Update local stored
            # logout time and return True. Otherwise session is invalid.

            if now < logoutTime:
                os.environ["PJ_MOBIUS_LOGOUT"] = logoutTimeStr
                return True

            return False
        
        except Exception as e:

            self.Logger.ShowError(e, "Failed to check session validity.")
            return False

class UserInfo:

    def __init__(self):

        # Logging objects

        self.Logger = maplex.Logger("DataAccess.UserInfo")

        # variables

        self.token = os.getenv("PJ_MOBIUS_TOKEN")

        try:

            self.conf = maplex.MapleTree("config.mpl")
            domain = self.conf.readMapleTag("DOMAIN", "APPLICATION_SETTINGS", "HTTP_REQUEST")
            self.domain = f"https://{domain}/user"

        except Exception as e:

            self.Logger.ShowError(e, "Failed to read configuration file.")
            raise

        # Process window

        self.processWindow = None

    def postUserInfo(self, userData: dict) -> dict | None:
        
        """ Post user info to server. """

        retDict = {"Created": False, "ErrorInfo": {"Error": False}}

        try:

            # Check user duplication before posting

            self.Logger.Info("Checking for existing user before posting new user info.")
            existingUser = self.getUserInfo(userName=userData.get("UserName"))

            if existingUser is not None and len(existingUser) > 0:

                self.Logger.Warn(f"User '{userData.get('UserName')}' already exists.")
                PJ_Mobius_Dialog.Dialog("Error", f"User '{userData.get('UserName')}' already exists. Please choose a different user name.").showDialog()
                return retDict
            
            existingUser = self.getUserInfo(eMail=userData.get("Email"))

            if existingUser is not None and len(existingUser) > 0:

                self.Logger.Warn(f"E-Mail '{userData.get('Email')}' is already registered.")
                PJ_Mobius_Dialog.Dialog("Error", f"E-Mail '{userData.get('Email')}' is already registered. Please use a different E-Mail address.").showDialog()
                return retDict
            
            self.Logger.Info("No existing user found. Proceeding to post new user info.")

            def worker():

                nonlocal retDict

                try:

                    requestJson = userData
                    requestJson["Token"] = self.token

                    response = requestToServer("POST", self.domain, requestJson, self.processWindow)

                    if self.processWindow:

                        try:

                            self.processWindow.master.after(0, self.processWindow.closeWindow)

                        except Exception:

                            try:

                                self.processWindow.closeWindow()

                            except Exception:

                                pass
                            
                        self.processWindow = None

                    if response.status_code != 200:

                        self.Logger.Error(f"Failed to post user info. Status code: {response.status_code}")
                        retDict = None
                        return

                    retDict = response.json()
                    self.Logger.Debug(f"Post user info response: {retDict}")

                    if retDict.get("ErrorInfo", {}).get("Error", False):

                        self.Logger.Error(f"Error in post user info response: {retDict.get('ErrorInfo', {}).get('Message', '')}")
                        return

                except Exception as e:

                    self.Logger.ShowError(e, "Failed to post user info to server.")
                    retDict = None

            self.processWindow = PJ_Mobius_Dialog.ProcessRequest("Posting user info to server...")
            thread = threading.Thread(target=worker)
            thread.start()
            self.processWindow.master.wait_window(self.processWindow)

            thread.join()
            return retDict

        except Exception as e:

            self.Logger.ShowError(e, "Failed to post user info to server.")
            return None
        
        finally:

            if self.processWindow:

                self.processWindow.closeWindow()
                self.processWindow = None

    def getUserInfo(self, userId: int | None = None, userName: str | None = None, eMail: str | None = None, accessLevel: str | None = None, companyID: int | None = None, userStatus: str | None = None, active: bool | None = None) -> dict | None:
        
        """ Get user info from server. """

        try:

            # Check if the session is valid

            if not SessionInfo().checkSession():

                self.Logger.Warn("Session is invalid or expired.")
                PJ_Mobius_Dialog.Dialog("Warn", "Your session has expired. Please log in again.", "Session Expired").showDialog()
                return None

        except Exception as e:

            self.Logger.ShowError(e, "Failed to validate session.")
            PJ_Mobius_Dialog.Dialog("Error", "Failed to validate session. Please log in again.").showDialog()
            return None

        if userId is None and userName is None and eMail is None and accessLevel is None and companyID is None and userStatus is None and active is None:

            self.Logger.Warn("No parameters provided for getUserInfo.")
            PJ_Mobius_Dialog.Dialog("Error", "No parameters provided for getUserInfo.").showDialog()
            return None

        retDict = None

        try:

            def worker():

                nonlocal retDict

                try:

                    requestJson = {
                        "Token": self.token,
                        "UserID": userId,
                        "UserName": userName,
                        "Email": eMail,
                        "AccessLevel": accessLevel,
                        "CompanyID": companyID,
                        "UserStatus": userStatus,
                        "Active": active
                    }

                    response = requestToServer("GET", self.domain, requestJson, self.processWindow)

                    if self.processWindow:

                        try:

                            self.processWindow.master.after(0, self.processWindow.closeWindow)

                        except Exception:

                            try:

                                self.processWindow.closeWindow()

                            except Exception:

                                pass
                            
                        self.processWindow = None

                    if response.status_code != 200:

                        self.Logger.Error(f"Failed to get user info. Status code: {response.status_code}")
                        retDict = None
                        return

                    retDict = response.json()
                    self.Logger.Debug(f"Get user info response: {retDict}")

                    if retDict.get("ErrorInfo", {}).get("Error", False):

                        self.Logger.Error(f"Error in get user info response: {retDict.get('ErrorInfo', {}).get('Message', '')}")
                        retDict = None
                        return

                except Exception as e:

                    self.Logger.ShowError(e, "Failed to get user info from server.")
                    retDict = None

            self.processWindow = PJ_Mobius_Dialog.ProcessRequest("Getting user info from server...")
            thread = threading.Thread(target=worker)
            thread.start()
            self.processWindow.master.wait_window(self.processWindow)

            thread.join()

            if retDict is not None:

                return retDict.get("Users", [])
            
            else:

                return None

        except Exception as e:

            self.Logger.ShowError(e, "Failed to get user info from server.")
            return None
        
        finally:

            if self.processWindow:

                self.processWindow.closeWindow()
                self.processWindow = None

class CompanyInfo:

    def __init__(self):

        # Logging objects

        self.Logger = maplex.Logger("DataAccess.CompanyInfo")

        # variables

        self.token = os.getenv("PJ_MOBIUS_TOKEN")

        if os.getenv("PJ_MOBIUS_COMPANY") not in NONE_LIST:

            self.companyID = int(os.getenv("PJ_MOBIUS_COMPANY"))

        else:

            self.companyID = None

        try:

            self.conf = maplex.MapleTree("config.mpl")
            domain = self.conf.readMapleTag("DOMAIN", "APPLICATION_SETTINGS", "HTTP_REQUEST")
            self.domain = f"https://{domain}/company"

        except Exception as e:

            self.Logger.ShowError(e, "Failed to read configuration file.")
            raise

        # Process window

        self.processWindow = None

    def getCompanyInfo(self, companyID: int | None = None, companyName: str | None = None, contractLevel: int | None = None) -> dict | None:
        
        """ Get company info from server. """

        try:

            # Check if the session is valid

            if not SessionInfo().checkSession():

                self.Logger.Warn("Session is invalid or expired.")
                PJ_Mobius_Dialog.Dialog("Warn", "Your session has expired. Please log in again.", "Session Expired").showDialog()
                return None

        except Exception as e:

            self.Logger.ShowError(e, "Failed to validate session.")
            PJ_Mobius_Dialog.Dialog("Error", "Failed to validate session. Please log in again.").showDialog()
            return None

        # Overwrite companyID with environment variable if not provided

        if companyID is None:

            companyID = self.companyID

        if companyID is None and companyName is None and contractLevel is None:

            self.Logger.Warn("No parameters provided for getCompanyInfo.")
            PJ_Mobius_Dialog.Dialog("Error", "No parameters provided for getCompanyInfo.").showDialog()
            return None

        retDict = None

        try:

            def worker():

                nonlocal retDict

                try:

                    requestJson = {
                        "Token": self.token,
                        "CompanyID": companyID,
                        "CompanyName": companyName,
                        "ContractLevel": contractLevel
                    }

                    response = requestToServer("GET", self.domain, requestJson, self.processWindow)

                    if self.processWindow:

                        try:

                            self.processWindow.master.after(0, self.processWindow.closeWindow)

                        except Exception:

                            try:

                                self.processWindow.closeWindow()

                            except Exception:

                                pass
                            
                        self.processWindow = None

                    if response.status_code != 200:

                        self.Logger.Error(f"Failed to get company info. Status code: {response.status_code}")
                        retDict = None
                        return

                    retDict = response.json()
                    self.Logger.Debug(f"Get company info response: {retDict}")

                    if retDict.get("ErrorInfo", {}).get("Error", False):

                        self.Logger.Error(f"Error in get company info response: {retDict.get('ErrorInfo', {}).get('Message', '')}")
                        retDict = None
                        return

                except Exception as e:

                    self.Logger.ShowError(e, "Failed to get company info from server.")
                    retDict = None

            self.processWindow = PJ_Mobius_Dialog.ProcessRequest("Getting company info from server...")
            thread = threading.Thread(target=worker)
            thread.start()
            self.processWindow.master.wait_window(self.processWindow)

            thread.join()

            if retDict is not None:

                return retDict.get("Companies", [])
            
            else:

                return None
            
        except Exception as e:

            self.Logger.ShowError(e, "Failed to get company info from server.")
            return None

        finally:

            if self.processWindow:

                self.processWindow.closeWindow()
                self.processWindow = None