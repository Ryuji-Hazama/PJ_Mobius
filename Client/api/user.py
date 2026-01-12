"""
User API client.

Provides the UserInfo class for user data operations.
"""

import maplex
import os

import threading

from .base import requestToServer
from .session import SessionInfo


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

        from ui import Dialog, ProcessRequest  # Lazy import to avoid circular dependency

        retDict = {"Created": False, "ErrorInfo": {"Error": False}}

        try:

            # Check user duplication before posting

            self.Logger.Info("Checking for existing user before posting new user info.")
            existingUser = self.getUserInfo(userName=userData.get("UserName"))

            if existingUser is not None and len(existingUser) > 0:

                self.Logger.Warn(f"User '{userData.get('UserName')}' already exists.")
                Dialog("Error", f"User '{userData.get('UserName')}' already exists. Please choose a different user name.").showDialog()
                return retDict
            
            existingUser = self.getUserInfo(eMail=userData.get("Email"))

            if existingUser is not None and len(existingUser) > 0:

                self.Logger.Warn(f"E-Mail '{userData.get('Email')}' is already registered.")
                Dialog("Error", f"E-Mail '{userData.get('Email')}' is already registered. Please use a different E-Mail address.").showDialog()
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

            self.processWindow = ProcessRequest("Posting user info to server...")
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

        from ui import Dialog, ProcessRequest  # Lazy import to avoid circular dependency

        try:

            # Check if the session is valid

            if not SessionInfo().checkSession():

                self.Logger.Warn("Session is invalid or expired.")
                Dialog("Warn", "Your session has expired. Please log in again.", "Session Expired").showDialog()
                return None

        except Exception as e:

            self.Logger.ShowError(e, "Failed to validate session.")
            Dialog("Error", "Failed to validate session. Please log in again.").showDialog()
            return None

        if userId is None and userName is None and eMail is None and accessLevel is None and companyID is None and userStatus is None and active is None:

            self.Logger.Warn("No parameters provided for getUserInfo.")
            Dialog("Error", "No parameters provided for getUserInfo.").showDialog()
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

            self.processWindow = ProcessRequest("Getting user info from server...")
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
