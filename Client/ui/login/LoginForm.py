import maplex
import os
import requests
import threading
import time
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ui import Dialog, ProcessRequest
from .InitPasswordForm import InitPasswordForm
from .SetDomainForm import SetDomainForm
from lib.Logout import Logout

class LoginForm(ttk.Frame):

    def __init__(self, master, switchCallback):
        
        super().__init__(master, padding=(20, 10))
        self.pack(fill=BOTH, expand=YES)

        # Logging objects

        self.Logger = maplex.Logger("LogInForm")

        # Values

        self.id = ttk.StringVar(value="")
        self.passwd = ttk.StringVar(value="")
        self.callback = switchCallback

        try:

            self.conf = maplex.MapleTree("config.mpl")
            self.verify = self.conf.readMapleTag("VERIFY", "APPLICATION_SETTINGS", "HTTP_REQUEST")
            timeoutStr = self.conf.readMapleTag("TIMEOUT", "APPLICATION_SETTINGS", "HTTP_REQUEST")

            try:

                self.timeout = int(timeoutStr)
                self.Logger.Debug(f"Timeout set to {self.timeout} seconds.")

            except ValueError:

                self.Logger.Warn(f"Invalid timeout value: {timeoutStr}")
                self.timeout = 30  # Default timeout
                self.Logger.Debug(f"Timeout set to default: {self.timeout} seconds.")

        except Exception as e:

            self.Logger.ShowError(e, "Failed to read configuration file.")
            Dialog("Error", "Failed to read app configurations.").showDialog()

        # Header info

        hd_txt = "Please enter your ID and Password."
        hd = ttk.Label(master=self, text=hd_txt, width=50)
        hd.pack(fill=X, pady=10)

        # Form entries

        self.createIDEntry("ID", self.id)
        self.createPassWdEntry("Password", self.passwd)
        self.create_buttons()

        self.Logger.Info("Login form loaded.")

    def createIDEntry(self, label, variable):

        container = ttk.Frame(self)
        container.pack(fill=X, expand=YES, pady=5)

        lbl = ttk.Label(master=container, text=label.title(), width=10)
        lbl.pack(side=LEFT, padx=5)

        ent = ttk.Entry(master=container, textvariable=variable)
        ent.pack(side=LEFT, padx=5, fill=X, expand=YES)
        ent.focus_set()

    def createPassWdEntry(self, label, variable):

        container = ttk.Frame(self)
        container.pack(fill=X, expand=YES, pady=5)

        lbl = ttk.Label(master=container, text=label.title(), width=10)
        lbl.pack(side=LEFT, padx=5)

        ent = ttk.Entry(master=container, textvariable=variable, show="*")
        ent.pack(side=LEFT, padx=5, fill=X, expand=YES)

    def create_buttons(self):

        container = ttk.Frame(self)
        container.pack(fill=X, expand=YES, pady=(15, 10))

        sub_btn = ttk.Button(
            master=container,
            text="Login",
            command=self.buttonClicked,
            bootstyle=SUCCESS,
            width=6
        )
        sub_btn.pack(side=RIGHT, padx=5)

        set_btn = ttk.Button(
            master=container,
            text="Set Domain",
            command=self.buttonSetClicked,
            bootstyle=INFO,
            width=10
        )
        set_btn.pack(side=RIGHT, padx=5)

        cnl_btn = ttk.Button(
            master=container,
            text="Cancel",
            command=lambda: self.quit(),
            bootstyle=DANGER,
            width=6
        )
        cnl_btn.pack(side=RIGHT, padx=5)

    ###############################
    # Login button clicked

    def buttonClicked(self):

        try:

            config = maplex.MapleTree("config.mpl")
            domain = config.readMapleTag("DOMAIN", "APPLICATION_SETTINGS", "HTTP_REQUEST")

            if domain in {None, ""}:

                self.Logger.Error("No domain info.")
                Dialog("Error", "Server domain has not set.").showDialog()
                return

            # Send login request

            url = f"https://{domain}/login"
            requestPayload = {"UserName": self.id.get(), "Password": self.passwd.get()}

            if "" in {requestPayload["UserName"], requestPayload["Password"]}:

                # If one of the entry is empty

                self.Logger.Info("Empty entry.")
                Dialog("Warn", "The entry is empty!").showDialog()
                return
            
            processLogin = ProcessRequest("Logging in...")
            t = threading.Thread(target=self.login, args=(processLogin, url, requestPayload))
            t.start()

        except Exception as e:

            if "processLogin" in locals():

                processLogin.closeWindow()

            self.Logger.ShowError(e, "Failed to login.")
            Dialog("Error", f"Unexpected error: \n"
                                      f"{e}\n\n"
                                      f"Please contact to support.").showDialog()

    def login(self, processLogin, url: str, requestPayload: str):

        try:

            for i in range(3):
                
                self.master.update()
                response = requests.get(url, json=requestPayload, verify=self.verify, timeout=self.timeout)
                self.Logger.Info(f"Login attempt {i + 1} / 3 status code: {response.status_code}")

                if response.status_code == 200:

                    break

                self.Logger.Warn(f"Failed to request: {i + 1} / 3")

                if i < 2:

                    processLogin.PackLabel(f"Retry {i + 1}/2")
                    time.sleep(1)

            self.master.after(0, lambda: self.handleResponse(response))

        except Exception as e:

            self.Logger.ShowError(e, "Failed to login.")
            Dialog("Error", f"{e}").showDialog()
            return

        finally:

            processLogin.closeWindow()

    def handleResponse(self, response):

        if response.status_code != 200:

            self.Logger.Error(f"Request failed with status code: {response.status_code}")
            Dialog("Warn", f"Request failed with status code: {response.status_code}\n\n"
                                    "The server domain is wrong or the server is temporary not responding.\n"
                                    "Please try again later and contact to support if the problem will not solve.")\
                                        .showDialog()
            return
        
        responseJson = response.json()

        if responseJson["ErrorInfo"]["Error"]:

            self.Logger.Error(f"Error occrred while login: {responseJson["ErrorInfo"]["Message"]}")
            Dialog("Warn", f"Failed to login because of the following error:\n"
                                    f"{responseJson["ErrorInfo"]["Message"]}\n\n"
                                    "Please contact to the support and try later.").showDialog()
            return
        
        if not responseJson["LoginResult"]["Login"]:

            self.Logger.Info(f"Failed to login: {responseJson["LoginResult"]["Message"]}")
            Dialog("Info", f"Failed to login:\n{responseJson["LoginResult"]["Message"]}")\
                .showDialog()
            return

        os.environ["PJ_MOBIUS_TOKEN"] = responseJson["LoginResult"]["Token"]
        os.environ["PJ_MOBIUS_USER"] = f"{responseJson["SessionInfo"]["UserID"]}"
        os.environ["PJ_MOBIUS_COMPANY"] = f"{responseJson["SessionInfo"]["CompanyID"]}"
        os.environ["PJ_MOBIUS_ACCESS"] = responseJson["SessionInfo"]["AccessLevel"]
        os.environ["PJ_MOBIUS_LOGOUT"] = responseJson["SessionInfo"]["LogoutTime"]

        if responseJson["LoginResult"]["InitialPassword"]:

            # Change initial password

            if not InitPasswordForm(self.id.get(), self.passwd.get()).show():

                self.Logger.Info("Cancel initialization.")
                processLogin = ProcessRequest("Logging out...")
                t = threading.Thread(target=Logout(self.callback).logOut, args=(processLogin, False))
                t.start()
                return

        self.callback("Main")

    def buttonSetClicked(self):

        self.Logger.Info("Set Domain clicked.")
        SetDomainForm()