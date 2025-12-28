import maplex
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os

import DataAccess
import PJ_Mobius_Dialog

class AddUserForm(ttk.Frame):

    def __init__(self, master: ttk.Frame):

        # Logging objects

        self.Logger = maplex.Logger("AddUserForm")

        # Initialize frame

        self.destroyChildren(master)

        super().__init__(master, padding=(0, 0))
        self.pack(fill=BOTH, expand=YES)

        # variables

        self.userName = ttk.StringVar()
        self.email = ttk.StringVar()
        self.password = ttk.StringVar()
        self.confirmPassword = ttk.StringVar()
        self.initialPassword = ttk.BooleanVar(value=True)
        self.accessLevel = ttk.StringVar()
        self.userStatus = ttk.StringVar(value="active")
        self.company = ttk.StringVar()

        self.userAccessLevel = os.getenv("PJ_MOBIUS_ACCESS")
        self.companyList = {}

        # Generate form

        self.generateForm()
        self.generateButtons()

    def destroyChildren(self, master: ttk.Frame):

        for child in master.winfo_children():

            child.destroy()

    def clearForm(self):
        
        # Clear all form fields

        self.userName.set("")
        self.email.set("")
        self.password.set("")
        self.confirmPassword.set("")
        self.initialPassword.set(True)
        self.accessLevel.set("")
        self.combo_accessLevel.current(0)
        self.userStatus.set("active")

        if self.userAccessLevel == "super":

            self.company.set("")
            self.combo_company.current(0)

        self.Logger.Info("Add User form cleared.")

    def checkEntries(self) -> bool:

        # Check if all required fields are filled

        if not self.userName.get().strip():

            PJ_Mobius_Dialog.Dialog("Error", "User Name cannot be empty.").showDialog()
            self.entry_UserName.focus_set()
            return False

        if not self.email.get().strip():

            PJ_Mobius_Dialog.Dialog("Error", "E-Mail cannot be empty.").showDialog()
            self.entry_email.focus_set()
            return False

        if not self.password.get():

            PJ_Mobius_Dialog.Dialog("Error", "Password cannot be empty.").showDialog()
            self.entry_password.focus_set()
            return False

        if self.password.get() != self.confirmPassword.get():

            PJ_Mobius_Dialog.Dialog("Error", "Password and Confirm Password do not match.").showDialog()
            self.entry_confirmPassword.focus_set()
            return False

        # - - - - - - - - - - - - - - - - - - - - - - - - -*
        # Password pattern check will occur at server side *
        # - - - - - - - - - - - - - - - - - - - - - - - - -*

        if not self.accessLevel.get():

            PJ_Mobius_Dialog.Dialog("Error", "User access level must be selected.")
            self.combo_accessLevel.current(0)
            self.combo_accessLevel.focus_set()
            return False

        if self.userAccessLevel == "super" and self.accessLevel.get() != "Super":

            if not self.company.get():

                PJ_Mobius_Dialog.Dialog("Error", "Company must be selected for non-Super users.").showDialog()
                self.combo_company.current(0)
                self.combo_company.focus_set()
                return False

        return True

    def addUser(self):
        
        # Check the form entries

        if not self.checkEntries():

            return
        
        # Convert form values

        accessLevel = self.accessLevel.get().lower()

        if self.userAccessLevel == "super" and accessLevel != "super":

            companyId = self.companyList[self.company.get()]

        else:

            companyId = int(os.getenv("PJ_MOBIUS_COMPANY"))

        if self.initialPassword.get():

            initialPassword = 1

        else:

            initialPassword = 0

        # Generate post request JSON

        requestPayload = {
            "UserName": self.userName.get(),
            "Email": self.email.get(),
            "Password": self.password.get(),
            "InitialPassword": initialPassword,
            "AccessLevel": accessLevel,
            "UserStatus": self.userStatus.get(),
            "CompanyID": companyId
        }

        # Send request to server

        if not DataAccess.UserInfo().postUserInfo(requestPayload):

            self.Logger.Error("Failed to add new user.")
            PJ_Mobius_Dialog.Dialog("Error", "Failed to add new user. Please check the logs for details.").showDialog()
            return
        
        PJ_Mobius_Dialog.Dialog("Info", "New user added successfully.").showDialog()
        self.Logger.Info(f"New user '{self.userName.get()}' added successfully.")
        self.clearForm()

    def accessLevelChanged(self, event):

        # Handle access level change event

        self.Logger.Debug(f"Access level changed to {self.accessLevel.get()}.")

        if self.accessLevel.get() == "Super":

            # Disable company selection for Super users

            self.combo_company.configure(state="disabled")
            self.company.set("")

        elif self.userAccessLevel == "super":

            # Enable company selection for non-Super users

            self.combo_company.configure(state="readonly")

    def generateForm(self):

        try:

            # Form title

            lbTitle = ttk.Label(self, text="Add New User".title(), width=20)
            lbTitle.configure(font=("", 20))
            lbTitle.pack(pady=(10, 10))

            if self.userAccessLevel == "Guest":

                # Guests cannot add new user

                PJ_Mobius_Dialog.Dialog("Error", "You do not have permission to add new user.").showDialog()
                self.Logger.Warn("Guest user attempted to add new user.")
                self.destroy()
                return

            form_f = ttk.Frame(self)
            form_f.pack(side=TOP, pady=(0, 10), padx=(20, 10), anchor=NW)

            # User Name

            lbl_UserName = ttk.Label(form_f, text="User Name", width=15, anchor=W)
            lbl_UserName.grid(row=0, column=0, padx=(10, 5), pady=(5, 5))
            self.entry_UserName = ttk.Entry(form_f, width=30, textvariable=self.userName)
            self.entry_UserName.grid(row=0, column=1, padx=(5, 10), pady=(5, 5))

            # E-Mail

            lbl_email = ttk.Label(form_f, text="E-Mail", width=15, anchor=W)
            lbl_email.grid(row=1, column=0, padx=(10, 5), pady=(5, 5))
            self.entry_email = ttk.Entry(form_f, width=30, textvariable=self.email)
            self.entry_email.grid(row=1, column=1, padx=(5, 10), pady=(5, 5))

            # Password

            lbl_password = ttk.Label(form_f, text="Password", width=15, anchor=W)
            lbl_password.grid(row=2, column=0, padx=(10, 5), pady=(5, 5))
            self.entry_password = ttk.Entry(form_f, width=30, show="*", textvariable=self.password)
            self.entry_password.grid(row=2, column=1, padx=(5, 10), pady=(5, 5))

            # Confirm Password

            lbl_confirmPassword = ttk.Label(form_f, text="Confirm Password", width=15, anchor=W)
            lbl_confirmPassword.grid(row=3, column=0, padx=(10, 5), pady=(5, 5))
            self.entry_confirmPassword = ttk.Entry(form_f, width=30, show="*", textvariable=self.confirmPassword)
            self.entry_confirmPassword.grid(row=3, column=1, padx=(5, 10), pady=(5, 5))

            # Initial Password Checkbox (Default: checked)

            self.check_initialPassword = ttk.Checkbutton(form_f, text="User must change password on next login", variable=self.initialPassword, onvalue=True, offvalue=False)
            self.check_initialPassword.grid(row=4, column=1, padx=(5, 10), pady=(5, 5), sticky=W)

            # Access Level

            lbl_accessLevel = ttk.Label(form_f, text="Access Level", width=15, anchor=W)
            lbl_accessLevel.grid(row=5, column=0, padx=(10, 5), pady=(5, 5))
            self.combo_accessLevel = ttk.Combobox(form_f, width=28, state="readonly", textvariable=self.accessLevel)

            levelDict = {
                "super": -1,
                "admin": 0,
                "user": 2,
                "guest": 3
            }
            levelList = ["Super", "Admin", "User", "Guest"]

            self.combo_accessLevel['values'] = levelList[levelDict[self.userAccessLevel]+1:]
            self.combo_accessLevel.current(0)
            self.combo_accessLevel.grid(row=5, column=1, padx=(5, 10), pady=(5, 5))

            # Bind access level change event

            self.combo_accessLevel.bind("<<ComboboxSelected>>", self.accessLevelChanged)
            
            # User status: Active or Inactive
            # (Inactive users cannot log in)
            # Default: Active

            lbl_status = ttk.Label(form_f, text="User status", width=15, anchor=W)
            lbl_status.grid(row=6, column=0, padx=(10, 5), pady=(5, 5))

            self.radio_active = ttk.Radiobutton(form_f, text="Active", variable=self.userStatus, value="active")
            self.radio_active.grid(row=6, column=1, padx=(10, 5), pady=(5, 5), sticky=W)

            self.radio_inactive = ttk.Radiobutton(form_f, text="Inactive", variable=self.userStatus, value="inactive")
            self.radio_inactive.grid(row=7, column=1, padx=(10, 5), pady=(5, 5), sticky=W)

            # Super user can set company id

            if self.userAccessLevel == "super":

                companyList = DataAccess.CompanyInfo().getCompanyInfo(contractLevel=5)
                companyList.extend(DataAccess.CompanyInfo().getCompanyInfo(contractLevel=4))

                # Create company dictionary

                self.companyList = {company.get("CompanyName", "N/A"): company.get("CompanyID", None) for company in companyList}

                lbl_company = ttk.Label(form_f, text="Company", width=15, anchor=W)
                lbl_company.grid(row=8, column=0, padx=(10, 5), pady=(5, 5))
                
                # Add company names to combobox
                # Disable by default; enabled when access level is changed to non-Super

                self.combo_company = ttk.Combobox(form_f, width=28, state="disabled", textvariable=self.company)
                companyNames = [company.get("CompanyName", "N/A") for company in companyList]
                self.combo_company['values'] = companyNames
                self.combo_company.current(0)
                self.combo_company.grid(row=8, column=1, padx=(5, 10), pady=(5, 5))

            # Fix the width of the grid columns

            form_f.grid_columnconfigure(0, weight=1)
            form_f.grid_columnconfigure(1, weight=2)

        except Exception as e:

            self.Logger.ShowError(e, "Failed to generate Add User form.")
            PJ_Mobius_Dialog.Dialog("Error", f"Failed to generate Add User form.\n{e}").showDialog()
            self.destroy()
            return
        
    def generateButtons(self):

        button_f = ttk.Frame(self)
        button_f.pack(side=BOTTOM, pady=(0, 10), padx=(10, 10), anchor=SE)

        btn_clear = ttk.Button(
            master=button_f,
            text="Clear",
            command=self.clearForm,
            bootstyle=INFO,
            width=8
            )
        btn_clear.pack(side=LEFT, padx=(0, 5))

        btn_addUser = ttk.Button(
            master=button_f,
            text="Add User",
            command=self.addUser,
            bootstyle=SUCCESS,
            width=8
        )
        btn_addUser.pack(side=LEFT, padx=(5, 0))