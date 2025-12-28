import maplex
import os
import requests
import threading
import time
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

import DataAccess
import PJ_Mobius_Dialog

class SetDomainForm(ttk.Frame):

    def __init__(self):

        self.master = ttk.Toplevel("Set Server Domain", resizable=(False, False))

        super().__init__(self.master, padding=(10, 10))
        self.pack(fill=BOTH, expand=YES)

        # Logging objects

        self.Logger = maplex.Logger("SetDomainForm")

        # Config instance

        try:

            self.conf = maplex.MapleTree("config.mpl")

        except maplex.MapleFileNotFoundException as notFoundE:

            self.Logger.ShowError(notFoundE, "config.mpl does not exists.")
            PJ_Mobius_Dialog.Dialog("Error", "Configuration file does not exists.").showDialog()

        except Exception as e:

            self.Logger.ShowError(e, "Failed to read config.mpl")
            PJ_Mobius_Dialog.Dialog("Error", "Failed to read config.mpl\n"
                                      "Please recover configuration file or\n"
                                      "contact to support.").showDialog()

        # Title label

        hdTxt = "Please set server domain."
        hd = ttk.Label(master=self, text=hdTxt)
        hd.pack(fill=BOTH, pady=(10, 10), padx=5, expand=YES)

        # Form variable

        self.domainText = ttk.StringVar(value="")

        # Forms

        self.domainEntry(self.domainText)
        self.buttons()

        self.Logger.Info("Domain initialization form loaded.")

    def domainEntry(self, variable):

        # Generate domain entry form frame

        container = ttk.Frame(self)
        container.pack(fill=BOTH, expand=YES)

        # - - - - - - - - - - #
        # Generate entry form #
        # - - - - - - - - - - #

        # Label

        httpLbText = "https://"
        httpLb = ttk.Label(container, text=httpLbText)
        httpLb.pack(side=LEFT, fill=X, padx=5, expand=YES)

        # Entry

        ent = ttk.Entry(container, textvariable=variable, width=50)
        ent.pack(side=LEFT, fill=X, expand=YES, padx=5)

        # Get config (if exists)

        try:

            domainText = self.conf.readMapleTag("DOMAIN", "APPLICATION_SETTINGS", "HTTP_REQUEST")

            if domainText is None:

                domainText = ""

        except Exception as e:

            self.Logger.ShowError(e, "Unexpected error occurred dualing generating entry form.")
            PJ_Mobius_Dialog.Dialog("Error", f"Unexpected error:\n"
                                      f"{e}\n\n"
                                      f"Please contact to support.").showDialog()
            self.master.destroy()
        
        ent.insert(0, domainText)
        ent.select_range(0, END)
        ent.focus_set()

    def buttons(self):

        # Generate button frame

        container = ttk.Frame(self)
        container.pack(fill=X, expand=YES, pady=(10, 15))

        # Buttons

        btConf = ttk.Button(
            container,
            text="Confirm",
            bootstyle=SUCCESS,
            command=self.confirmDomain,
            width=7
            )
        btConf.pack(side=RIGHT, padx=5)

        btCancel = ttk.Button(
            container,
            text="Cancel",
            bootstyle=DANGER,
            command=self.master.destroy
            )
        btCancel.pack(side=RIGHT, padx=5)

    def confirmDomain(self):

        domainText = self.domainText.get()

        if domainText == "":

            self.Logger.Warn("Domain text is empty.")
            PJ_Mobius_Dialog.Dialog("Info", "Entry is empty").showDialog()

        else:

            # Update config.mpl

            self.conf.saveTagLine("DOMAIN", domainText, True, "APPLICATION_SETTINGS", "HTTP_REQUEST")
            self.Logger.Info(f"Domain information saved: {domainText}")
            self.master.destroy()

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
            PJ_Mobius_Dialog.Dialog("Error", "Failed to read app configurations.").showDialog()

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
            PJ_Mobius_Dialog.Dialog("Warn", "Failed to logout because of the following error:\n"
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
                PJ_Mobius_Dialog.Dialog("Warn", "Failed to logout.\n"
                                        f"Response status code: {response.status_code}").showDialog()
                
            elif not response.json()["Update"]:

                self.Logger.Error(f"Failed to logout: {response.json()["ErrorInfo"]["ErrorMessage"]}")
                PJ_Mobius_Dialog.Dialog("Warn", "Failed to logout because of the following reason:\n"
                                        f"{response.json()["ErrorInfo"]["ErrorMessage"]}").showDialog()

        if quit:

            self.master.quit()

        else:

            self.callback("Login")

class InitPasswordForm(ttk.Frame):

    def __init__(self, userName: str, oldPassword: str):

        # Logging objects

        self.Logger = maplex.Logger("InitPassword")

        # Variables

        self.Password = ttk.Variable(value="")
        self.PassConf = ttk.Variable(value="")
        self.targetUser = userName
        self.oldPassword = oldPassword
        self.success = False

    def generateForms(self):

        containerForms = ttk.Frame(self.master, padding=(0, 0))
        containerForms.pack(fill=X, expand=YES)

        # Password entry

        containerPass = ttk.Frame(containerForms, padding=(5, 5))
        containerPass.pack(fill=X, expand=YES)

        passLb = ttk.Label(containerPass, text="Password", width=10)
        passLb.pack(side=LEFT, padx=5)

        self.passEnt = ttk.Entry(master=containerPass, textvariable=self.Password, show="*")
        self.passEnt.pack(side=LEFT, padx=5, fill=X, expand=YES)
        self.passEnt.focus_set()

        # Confirm entry

        containerConf = ttk.Frame(containerForms, padding=(5, 5))
        containerConf.pack(fill=X, expand=YES)

        confLb = ttk.Label(containerConf, text="Confirm", width=10)
        confLb.pack(side=LEFT, padx=5)

        confEnt = ttk.Entry(master=containerConf, textvariable=self.PassConf, show="*")
        confEnt.pack(side=LEFT, padx=5, fill=X, expand=YES)

    def generateButtons(self):

        container = ttk.Frame(self.master, padding=(15, 10))
        container.pack(fill=X, expand=YES)

        btOk = ttk.Button(
            container,
            text="OK",
            command=self.okButtonClicked,
            bootstyle=SUCCESS,
            width=6
            )
        btOk.pack(side=RIGHT, padx=5)

        btCn = ttk.Button(
            container,
            text="Cancel",
            command=self.cancelButtonClicked,
            bootstyle=DANGER,
            width=6
        )
        btCn.pack(side=RIGHT, padx=5)

    def handleResponse(self, response: requests.Response):

        self.Logger.Info(f"Response received: {response.status_code}")

        try:

            if response.status_code != 200:

                self.Logger.Error(f"Request failed with status code: {response.status_code}")
                PJ_Mobius_Dialog.Dialog("Warn", f"Request failed with status code: {response.status_code}\n\n"
                                        "Please try again later and contact to support if the problem will not solve.")\
                                            .showDialog()
                return
            
            responseJson = response.json()

            if responseJson["ErrorInfo"]["Error"]:

                self.Logger.Error(f"Error occurred while updating password: {responseJson["ErrorInfo"]["ErrorMessage"]}")
                PJ_Mobius_Dialog.Dialog("Warn", f"Failed to update password because of the following error:\n"
                                        f"{responseJson["ErrorInfo"]["ErrorMessage"]}\n\n"
                                        "Please contact to the support and try later.").showDialog()
                self.passEnt.focus_set()
                self.passEnt.select_range(0, END)
                return
            
            if not responseJson["Update"]:

                self.Logger.Info(f"Failed to update password: {responseJson["Message"]}")
                PJ_Mobius_Dialog.Dialog("Info", f"Failed to update password:\n{responseJson["Message"]}")\
                    .showDialog()
                self.passEnt.focus_set()
                self.passEnt.select_range(0, END)
                return

            PJ_Mobius_Dialog.Dialog("Info", "Password updated successfully.").showDialog()
            self.Logger.Info("Password updated successfully.")
            self.master.destroy()
            self.success = True

        except Exception as e:

            self.Logger.ShowError(e, "Failed to handle response.")
            PJ_Mobius_Dialog.Dialog("Error", f"Unexpected error:\n"
                                      f"{e}\n\n"
                                      f"Please contact to support.").showDialog()

    def updatePassword(self, processDialog: PJ_Mobius_Dialog.ProcessRequest):

        try:

            # Configurations

            conf = maplex.MapleTree("config.mpl")
            domain = conf.readMapleTag("DOMAIN", "APPLICATION_SETTINGS", "HTTP_REQUEST")
            verify = conf.readMapleTag("VERIFY", "APPLICATION_SETTINGS", "HTTP_REQUEST")
            timeoutStr = conf.readMapleTag("TIMEOUT", "APPLICATION_SETTINGS", "HTTP_REQUEST")

            try:

                timeout = int(timeoutStr)

            except Exception as e:

                timeout = 30  # Default timeout

        except Exception as e:

            self.Logger.ShowError(e, "Failed to read configurations.")
            self.master.destroy()
            return False
        
        url = f"https://{domain}/password"
        requestPayload = {"Token": os.getenv("PJ_MOBIUS_TOKEN"), "UserName": self.targetUser, "OldPassword": self.oldPassword, "NewPassword": self.Password.get()}

        try:

            for i in range(3):

                response = requests.patch(url=url, json=requestPayload, verify=verify, timeout=timeout)

                if response.status_code == 200:

                    break

                if i < 2:

                    processDialog.PackLabel(f"Retry update: {i + 1} / 2")

            self.master.after(0, lambda: self.handleResponse(response))

        except Exception as e:

            self.Logger.ShowError(e, "Failed to request update user password.")
            PJ_Mobius_Dialog.Dialog("Error", f"Request failed:\n{e}").showDialog()
            return False
        
        finally:

            processDialog.closeWindow()

    def okButtonClicked(self):

        # Check password

        if self.Password.get() in {None, ""} or self.PassConf.get() in {None, ""}:

            self.Logger.Warn("One of the entry is empty.")
            PJ_Mobius_Dialog.Dialog("Warn", "One of the entry is empty!").showDialog()
            self.passEnt.focus_set()
            self.passEnt.select_range(0, END)
            return
        
        if self.Password.get() != self.PassConf.get():

            self.Logger.Warn("Password does not match.")
            PJ_Mobius_Dialog.Dialog("Warn", "Password does not match!").showDialog()
            self.passEnt.focus_set()
            self.passEnt.select_range(0, END)
            return
        
        # - - - - - - - - - - - - - - - - - - - - - - - - -*
        # Password pattern check will occur at server side *
        # - - - - - - - - - - - - - - - - - - - - - - - - -*

        # Send request

        processDialog = PJ_Mobius_Dialog.ProcessRequest("Updating password...")
        t = threading.Thread(target=self.updatePassword, args=(processDialog,))
        t.start()

    def cancelButtonClicked(self):

        self.master.destroy()
        return False

    def show(self) -> bool:

        # Generate window

        self.master = ttk.Toplevel("Initialize password", resizable=(False, False))
        self.master.geometry("+%d+%d"%(300, 300))

        super().__init__(self.master, padding=(10, 10))
        self.pack(fill=BOTH, expand=YES)

        self.generateForms()
        self.generateButtons()

        self.master.protocol("WM_DELETE_WINDOW", lambda: self.cancelButtonClicked())
        self.Logger.Info("Password initialization window loaded.")

        # Wait till end

        self.master.grab_set()
        self.master.wait_window()

        return self.success

class LogInForm(ttk.Frame):

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
            PJ_Mobius_Dialog.Dialog("Error", "Failed to read app configurations.").showDialog()

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
                PJ_Mobius_Dialog.Dialog("Error", "Server domain has not set.").showDialog()
                return

            # Send login request

            url = f"https://{domain}/login"
            requestPayload = {"UserName": self.id.get(), "Password": self.passwd.get()}

            if "" in {requestPayload["UserName"], requestPayload["Password"]}:

                # If one of the entry is empty

                self.Logger.Info("Empty entry.")
                PJ_Mobius_Dialog.Dialog("Warn", "The entry is empty!").showDialog()
                return
            
            processLogin = PJ_Mobius_Dialog.ProcessRequest("Logging in...")
            t = threading.Thread(target=self.login, args=(processLogin, url, requestPayload))
            t.start()

        except Exception as e:

            if "processLogin" in locals():

                processLogin.closeWindow()

            self.Logger.ShowError(e, "Failed to login.")
            PJ_Mobius_Dialog.Dialog("Error", f"Unexpected error: \n"
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
            PJ_Mobius_Dialog.Dialog("Error", f"{e}").showDialog()
            return

        finally:

            processLogin.closeWindow()

    def handleResponse(self, response):

        if response.status_code != 200:

            self.Logger.Error(f"Request failed with status code: {response.status_code}")
            PJ_Mobius_Dialog.Dialog("Warn", f"Request failed with status code: {response.status_code}\n\n"
                                    "The server domain is wrong or the server is temporary not responding.\n"
                                    "Please try again later and contact to support if the problem will not solve.")\
                                        .showDialog()
            return
        
        responseJson = response.json()

        if responseJson["ErrorInfo"]["Error"]:

            self.Logger.Error(f"Error occrred while login: {responseJson["ErrorInfo"]["ErrorMessage"]}")
            PJ_Mobius_Dialog.Dialog("Warn", f"Failed to login because of the following error:\n"
                                    f"{responseJson["ErrorInfo"]["ErrorMessage"]}\n\n"
                                    "Please contact to the support and try later.").showDialog()
            return
        
        if not responseJson["LoginResult"]["Login"]:

            self.Logger.Info(f"Failed to login: {responseJson["LoginResult"]["Message"]}")
            PJ_Mobius_Dialog.Dialog("Info", f"Failed to login:\n{responseJson["LoginResult"]["Message"]}")\
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
                processLogin = PJ_Mobius_Dialog.ProcessRequest("Logging out...")
                t = threading.Thread(target=Logout(self.callback).logOut, args=(processLogin, False))
                t.start()
                return

        self.callback("Main")

    def buttonSetClicked(self):

        self.Logger.Info("Set Domain clicked.")
        SetDomainForm()