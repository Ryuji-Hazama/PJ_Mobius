import maplex
import os
import requests
import time
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ui import Dialog

class Logout:

    def __init__(self, callback, master: ttk.Window | None = None):
        
        self.callback = callback
        self.master = master

        # Logging objects

        self.Logger = maplex.Logger("Logout")

        try:

            self.conf = maplex.MapleTree("config.mpl")
            domain = self.conf.readMapleTag("DOMAIN", "APPLICATION_SETTINGS", "HTTP_REQUEST")
            self.domain = f"https://{domain}"
            self.verify = self.conf.readMapleTag("VERIFY", "APPLICATION_SETTINGS", "HTTP_REQUEST")
            timeoutStr = self.conf.readMapleTag("TIMEOUT", "APPLICATION_SETTINGS", "HTTP_REQUEST")

            try:

                self.timeout = int(timeoutStr)

            except Exception as e:

                self.timeout = 30  # Default timeout

        except Exception as e:

            self.Logger.ShowError(e, "Failed to read configuration file.")
            Dialog("Error", "Failed to read app configurations.").showDialog()

    def logOut(self, processLogin, quit: bool):

        self.Logger.Info("Logging out.")

        try:

            # Send logout request

            response = None
            url = f"{self.domain}/session"
            requestPayload = {"Token": os.getenv("PJ_MOBIUS_TOKEN"), "Update": "00:00:00"}

            for i in range(3):

                self.Logger.Info(f"Logout request: {i + 1} / 3")
                response = requests.patch(url, json=requestPayload, verify=self.verify, timeout=self.timeout)

                if response.status_code == 200:

                    break

                self.Logger.Warn(f"Failed to logout.")
                self.Logger.Info(f"Status code: {response.status_code}")

                if i < 2:

                    processLogin.PackLabel(f"Retry logout: {i + 1} / 2")
                    time.sleep(1)

        except Exception as e:

            self.Logger.ShowError(e, "Failed to logout.")
            Dialog("Warn", "Failed to logout because of the following error:\n"
                                    f"{e}").showDialog()
            
        finally:

            try:

                # Clear environment variables

                os.environ.pop("PJ_MOBIUS_TOKEN")
                os.environ.pop("PJ_MOBIUS_USER")
                os.environ.pop("PJ_MOBIUS_COMPANY")
                os.environ.pop("PJ_MOBIUS_ACCESS")
                os.environ.pop("PJ_MOBIUS_LOGOUT")
                
            except KeyError as ke:

                self.Logger.Warn(f"Environment variable does not exists: {ke}")

            processLogin.closeWindow()

        if response is not None:

            if response.status_code != 200:

                self.Logger.Error(f"Failedt to logout.")
                Dialog("Warn", "Failed to logout.\n"
                                        f"Response status code: {response.status_code}").showDialog()
                
            elif not response.json()["Update"]:

                self.Logger.Error(f"Failed to logout: {response.json()["ErrorInfo"]["Message"]}")
                Dialog("Warn", "Failed to logout because of the following reason:\n"
                                        f"{response.json()["ErrorInfo"]["Message"]}").showDialog()

        if quit:

            self.master.quit()

        else:

            self.callback("Login")
