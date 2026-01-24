"""
Company API client.

Provides the CompanyInfo class for company data operations.
"""

import maplex
import os
import threading

from .base import requestToServer, NONE_LIST
from .session import SessionInfo


class CompanyInfo:

    def __init__(self):

        # Logging objects

        self.logger = maplex.Logger(__name__)

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

            self.logger.ShowError(e, "Failed to read configuration file.")
            raise

        # Process window

        self.processWindow = None

    def postCompanyInfo(self, companyData: dict) -> dict | None:
        
        """ Post company info to server. """

        from ui import Dialog, ProcessRequest  # Lazy import to avoid circular dependency

        # Check if the session is valid

        try:

            if not SessionInfo().checkSession():

                self.logger.warn("Session is invalid or expired.")
                Dialog("Warn", "Your session has expired. Please log in again.", "Session Expired").showDialog()
                return None

        except Exception as e:

            self.logger.ShowError(e, "Failed to validate session.")
            Dialog("Error", "Failed to validate session. Please log in again.").showDialog()
            return None

        retDict = None

        try:

            def worker():

                nonlocal retDict

                try:

                    requestJson = companyData
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

                        self.logger.error(f"Failed to post company info. Status code: {response.status_code}")
                        retDict = None
                        return

                    retDict = response.json()
                    self.logger.debug(f"Post company info response: {retDict}")

                    if retDict.get("ErrorInfo", {}).get("Error", False):

                        self.logger.error(f"Error in post company info response: {retDict.get('ErrorInfo', {}).get('Message', '')}")
                        return

                except Exception as e:

                    self.logger.ShowError(e, "Failed to post company info to server.")
                    retDict = None

            self.processWindow = ProcessRequest("Posting company info to server...")
            thread = threading.Thread(target=worker)
            thread.start()
            self.processWindow.master.wait_window(self.processWindow)

            thread.join()
            return retDict

        except Exception as e:

            self.logger.ShowError(e, "Failed to post company info to server.")
            return None
        
        finally:

            if self.processWindow:

                self.processWindow.closeWindow()
                self.processWindow = None

    def getCompanyInfo(self, companyID: int | None = None, companyName: str | None = None, contractLevel: int | None = None) -> dict | None:
        
        """ Get company info from server. """

        from ui import Dialog, ProcessRequest  # Lazy import to avoid circular dependency

        try:

            # Check if the session is valid

            if not SessionInfo().checkSession():

                self.logger.warn("Session is invalid or expired.")
                Dialog("Warn", "Your session has expired. Please log in again.", "Session Expired").showDialog()
                return None

        except Exception as e:

            self.logger.ShowError(e, "Failed to validate session.")
            Dialog("Error", "Failed to validate session. Please log in again.").showDialog()
            return None

        # Overwrite companyID with environment variable if not provided

        if companyID is None:

            companyID = self.companyID

        if companyID is None and companyName is None and contractLevel is None:

            self.logger.warn("No parameters provided for getCompanyInfo.")
            Dialog("Error", "No parameters provided for getCompanyInfo.").showDialog()
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

                        self.logger.error(f"Failed to get company info. Status code: {response.status_code}")
                        retDict = None
                        return

                    retDict = response.json()
                    self.logger.debug(f"Get company info response: {retDict}")

                    if retDict.get("ErrorInfo", {}).get("Error", False):

                        self.logger.error(f"Error in get company info response: {retDict.get('ErrorInfo', {}).get('Message', '')}")
                        retDict = None
                        return

                    elif len(retDict.get("Companies", [])) == 0:

                        self.logger.warn(f"No company found: {retDict.get('ErrorInfo', {}).get('Message', 'Unknown reason')}")
                        retDict = None
                        return

                except Exception as e:

                    self.logger.ShowError(e, "Failed to get company info from server.")
                    retDict = None

            self.processWindow = ProcessRequest("Getting company info from server...")
            thread = threading.Thread(target=worker)
            thread.start()
            self.processWindow.master.wait_window(self.processWindow)

            thread.join()

            if retDict is not None:

                return retDict.get("Companies", [])
            
            else:

                return None
            
        except Exception as e:

            self.logger.ShowError(e, "Failed to get company info from server.")
            return None

        finally:

            if self.processWindow:

                self.processWindow.closeWindow()
                self.processWindow = None
