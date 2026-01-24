import maplex
import os
import requests
import threading
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ui import Dialog, ProcessRequest

class InitPasswordForm(ttk.Frame):

    def __init__(self, userName: str, oldPassword: str):

        # Logging objects

        self.logger = maplex.Logger(__name__)

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

        self.logger.info(f"Response received: {response.status_code}")

        try:

            if response.status_code != 200:

                self.logger.error(f"Request failed with status code: {response.status_code}")
                Dialog("Warn", f"Request failed with status code: {response.status_code}\n\n"
                                        "Please try again later and contact to support if the problem will not solve.")\
                                            .showDialog()
                return
            
            responseJson = response.json()

            if responseJson["ErrorInfo"]["Error"]:

                self.logger.error(f"Error occurred while updating password: {responseJson["ErrorInfo"]["Message"]}")
                Dialog("Warn", f"Failed to update password because of the following error:\n"
                                        f"{responseJson["ErrorInfo"]["Message"]}\n\n"
                                        "Please contact to the support and try later.").showDialog()
                self.passEnt.focus_set()
                self.passEnt.select_range(0, END)
                return
            
            if not responseJson["Update"]:

                self.logger.info(f"Failed to update password: {responseJson["Message"]}")
                Dialog("Info", f"Failed to update password:\n{responseJson["Message"]}")\
                    .showDialog()
                self.passEnt.focus_set()
                self.passEnt.select_range(0, END)
                return

            Dialog("Info", "Password updated successfully.").showDialog()
            self.logger.info("Password updated successfully.")
            self.master.destroy()
            self.success = True

        except Exception as e:

            self.logger.ShowError(e, "Failed to handle response.")
            Dialog("Error", f"Unexpected error:\n"
                                      f"{e}\n\n"
                                      f"Please contact to support.").showDialog()

    def updatePassword(self, processDialog: ProcessRequest):

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

            self.logger.ShowError(e, "Failed to read configurations.")
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

            self.logger.ShowError(e, "Failed to request update user password.")
            Dialog("Error", f"Request failed:\n{e}").showDialog()
            return False
        
        finally:

            processDialog.closeWindow()

    def okButtonClicked(self):

        # Check password

        if self.Password.get() in {None, ""} or self.PassConf.get() in {None, ""}:

            self.logger.warn("One of the entry is empty.")
            Dialog("Warn", "One of the entry is empty!").showDialog()
            self.passEnt.focus_set()
            self.passEnt.select_range(0, END)
            return
        
        if self.Password.get() != self.PassConf.get():

            self.logger.warn("Password does not match.")
            Dialog("Warn", "Password does not match!").showDialog()
            self.passEnt.focus_set()
            self.passEnt.select_range(0, END)
            return
        
        # - - - - - - - - - - - - - - - - - - - - - - - - -*
        # Password pattern check will occur at server side *
        # - - - - - - - - - - - - - - - - - - - - - - - - -*

        # Send request

        processDialog = ProcessRequest("Updating password...")
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
        self.logger.info("Password initialization window loaded.")

        # Wait till end

        self.master.grab_set()
        self.master.wait_window()

        return self.success