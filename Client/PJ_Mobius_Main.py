import maplex
import os
import threading
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

import DataAccess
import PJ_Mobius_Dialog
import PJ_Mobius_Login
import PJ_Mobius_User

NONE_LIST = [None, "", "None"]

class MainMenuForm(ttk.Frame):

    def __init__(self, master: ttk.Window, callback):

        # Logging objects

        self.Logger = maplex.Logger("MainMenu")

        self.callback = callback
        master.geometry("+%d+%d"%(50, 30))

        super().__init__(master, padding=(0, 0))
        self.pack(fill=BOTH, expand=YES)

        self.menuAndData()
        self.generateButtons()

        master.protocol("WM_DELETE_WINDOW", lambda: self.windowClosing(True))
        self.conf = maplex.MapleTree("config.mpl")

        try:

            domain = self.conf.readMapleTag("DOMAIN", "APPLICATION_SETTINGS")
            self.domain = f"https://{domain}"

        except Exception as e:

            self.Logger.ShowError(e, "Failed to read configuration file.")
            PJ_Mobius_Dialog.Dialog("Error", "Failed to read app configurations.").showDialog()

    def menuWindow(self, master):

        left_f = ttk.Frame(master)
        left_f.pack(side=LEFT, fill=BOTH, expand=YES)

        lbl = ttk.Label(left_f, text="MENU".title(), width=10)
        lbl.configure(font=("", 12))
        lbl.pack()

        mb_UserManagement = ttk.Menubutton(left_f, text="User Management", width=20)
        menu = ttk.Menu(mb_UserManagement, tearoff=0)
        mb_UserManagement["menu"] = menu
        menu.add_command(label="Add User", command=lambda: PJ_Mobius_User.AddUserForm(self.right_f))
        mb_UserManagement.pack(pady=5)

        master.add(left_f)

    def dataWindow(self, master):

        try:

            userId = int(os.getenv("PJ_MOBIUS_USER"))
            userData = DataAccess.UserInfo().getUserInfo(userId=userId)
            self.Logger.Info(f"User data: {userData}")  # Delete this line in production

            if userData is None or len(userData) != 1:

                raise Exception("Failed to get user data from server.")

        except Exception as e:

            self.Logger.ShowError(e, "Failed to get user data from server.")
            PJ_Mobius_Dialog.Dialog("Error", "Failed to get user data from server.").showDialog()
            userData = None

        self.right_f = ttk.Frame(master)
        self.right_f.pack(side=LEFT, fill=BOTH)

        # Title

        titleFrame = ttk.Frame(self.right_f)
        titleFrame.pack(fill=X)

        lblPjTitle = ttk.Label(titleFrame, text="PJ Mobius", width=20)
        lblPjTitle.configure(font=("", 20))
        lblPjTitle.pack(pady=(10, 20))

        if userData is not None:

            labelText = f"Hello there, {userData[0].get('UserName', 'User')}!" # Star Wars reference
            accessLevelText = f"Access Level: {userData[0].get('AccessLevel', 'N/A')}"

        else:

            # This should not happen
            # Unless someone is trying to hack the system

            lblError = ttk.Label(self.right_f, text="Failed to get user data.", width=30)
            lblError.configure(font=("", 8))
            lblError.pack(pady=(0, 20))
            labelText = "Ah, Mr. Anderson..." # Matrix reference
            accessLevelText = "Access Level: Intruder from Zion" # Could be a hack attempt

        # User info

        userFrame = ttk.Frame(self.right_f)
        userFrame.pack(padx=10, pady=(0, 20), fill=X)

        lblWelcome = ttk.Label(userFrame, text=labelText, width=30)
        lblWelcome.configure(font=("", 16))
        lblWelcome.grid(row=0, column=0, pady=(0, 5), sticky=W)

        lblAccessLevel = ttk.Label(userFrame, text=accessLevelText, width=30)
        lblAccessLevel.configure(font=("", 12))
        lblAccessLevel.grid(row=1, column=0, pady=(0, 5), sticky=W)

        # Company info (if it exists).

        if os.getenv("PJ_MOBIUS_COMPANY") not in NONE_LIST:

            companyList = DataAccess.CompanyInfo().getCompanyInfo()
            self.Logger.Info(f"Company info: {companyList}")

            if companyList is not None and len(companyList) == 1:

                companyName = companyList[0].get("CompanyName", "N/A")

                lblCompanyName = ttk.Label(userFrame, text=f"Company: {companyName}", width=30)
                lblCompanyName.configure(font=("", 12))
                lblCompanyName.grid(row=2, column=0, pady=(0, 5), sticky=W)

                self.Logger.Info(f"User is associated with company: {companyName}")

            elif companyList is not None and len(companyList) > 1:

                # Which should not happen normally

                lblCompanyName = ttk.Label(userFrame, text="Company: You are lost in multiple companies", width=30)
                lblCompanyName.configure(font=("", 12))
                lblCompanyName.grid(row=2, column=0, pady=(0, 5), sticky=W)

                self.Logger.Warn("User is associated with multiple companies.")

            else:
                
                lblCompanyName = ttk.Label(userFrame, text="Company: N/A", width=30)
                lblCompanyName.configure(font=("", 12))
                lblCompanyName.grid(row=2, column=0, pady=(0, 5), sticky=W)

                self.Logger.Info("User's company information is not found.")

        else:

            self.Logger.Info("User is not associated with any company.")

        master.add(self.right_f)

    def menuAndData(self):

        container = ttk.Frame(self, padding=(5, 5))
        container.pack(fill=BOTH, expand=YES)

        pw = ttk.Panedwindow(container, orient=HORIZONTAL, width=1000, height=500)
        pw.pack(fill=BOTH, expand=YES)

        self.menuWindow(pw)
        self.dataWindow(pw)

    def generateButtons(self):

        container = ttk.Frame(self, padding=(10, 5))
        container.pack(fill=BOTH, expand=YES)

        btBackToLogin = ttk.Button(
            container,
            command=self.logoutButtonClicked,
            text="Log Out",
            width=8,
            bootstyle=INFO
            )
        btBackToLogin.pack(side=RIGHT, padx=5)

        btQuit = ttk.Button(
            container,
            command=self.quitButtonClicked,
            text="Quit",
            width=8,
            bootstyle=DANGER
        )
        btQuit.pack(side=RIGHT, padx=5)

    def logoutButtonClicked(self):

        self.Logger.Info("Log out.")
        self.windowClosing(False)

    def quitButtonClicked(self):

        self.Logger.Info("Quitting from main menu.")
        self.windowClosing(True)

    def windowClosing(self, quit: bool = False):

        try:

            self.Logger.Info("Closing main menu window.")
            processLogin = PJ_Mobius_Dialog.ProcessRequest("Logging out...")
            t = threading.Thread(target=PJ_Mobius_Login.Logout(self.callback, self).logOut, args=(processLogin, quit))
            t.start()

        except Exception as e:

            self.Logger.ShowError(e)