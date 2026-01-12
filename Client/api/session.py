"""
Session API client.

Provides the SessionInfo class for session management operations.
"""

import datetime
import maplex
import os

import threading

from .base import requestToServer


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

        from ui import Dialog  # Lazy import to avoid circular dependency

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

            self.processWindow = Dialog.ProcessRequest("Getting session info from server...")
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
