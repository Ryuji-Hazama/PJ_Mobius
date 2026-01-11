import maplex
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os

import DataAccess
import PJ_Mobius_Dialog

class AddCompanyForm(ttk.Frame):

    def __init__(self, parent: ttk.Frame):

        # Logging object

        self.logger = maplex.Logger("AddCompanyForm")

        # Initialize the AddCompanyForm UI

        self.destroyChildren(parent)
        super().__init__(parent)

        self.parent = parent
        self.companyNameVar = ttk.StringVar()
        self.contractLevelVar = ttk.IntVar(value=1)
        self.companyPhoneVar = ttk.StringVar()
        self.companyZipCodeVar = ttk.StringVar()
        self.companyAddressVar = ttk.StringVar()
        self.companyEmailVar = ttk.StringVar()

        self.userAccessLevel = os.getenv("PJ_MOBIUS_ACCESS")

        self.buildUI()
        self.generateButtons()
        self.logger.Info("Add Company form UI built.")

    def destroyChildren(self, master: ttk.Frame):

        # Destroy all child widgets

        for child in master.winfo_children():
            child.destroy()

    def buildUI(self):

        # Build the user interface for adding a company

        self.pack(fill=BOTH, expand=YES, padx=10, pady=10)

        # Form title

        titleLabel = ttk.Label(self, text="Add New Company".title(), font=("Helvetica", 16, "bold"))
        titleLabel.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # Check user access level

        if self.userAccessLevel == "Guest":

            PJ_Mobius_Dialog.Dialog("Error", "Guest users are not allowed to add companies.").showDialog()
            self.logger.Warn("Guest user attempted to access Add Company form.")
            self.destroy()
            return

        ttk.Label(self, text="Company Name:").grid(row=1, column=0, sticky=W, pady=5)
        ttk.Entry(self, textvariable=self.companyNameVar).grid(row=1, column=1, sticky=EW, pady=5)

        ttk.Label(self, text="Contract Level:").grid(row=2, column=0, sticky=W, pady=5)
        ttk.Spinbox(self, from_=1, to=10, textvariable=self.contractLevelVar).grid(row=2, column=1, sticky=EW, pady=5)

        ttk.Label(self, text="Phone:").grid(row=3, column=0, sticky=W, pady=5)
        ttk.Entry(self, textvariable=self.companyPhoneVar).grid(row=3, column=1, sticky=EW, pady=5)
        ttk.Label(self, text="Zip Code:").grid(row=4, column=0, sticky=W, pady=5)
        ttk.Entry(self, textvariable=self.companyZipCodeVar).grid(row=4, column=1, sticky=EW, pady=5)

        ttk.Label(self, text="Address:").grid(row=5, column=0, sticky=W, pady=5)
        ttk.Entry(self, textvariable=self.companyAddressVar).grid(row=5, column=1, sticky=EW, pady=5)

        ttk.Label(self, text="Email:").grid(row=6, column=0, sticky=W, pady=5)
        ttk.Entry(self, textvariable=self.companyEmailVar).grid(row=6, column=1, sticky=EW, pady=5)

        self.columnconfigure(1, weight=1)

    def generateButtons(self):

        # Generate action buttons

        buttonFrame = ttk.Frame(self)
        buttonFrame.grid(row=7, column=0, columnspan=2, pady=10)

        addButton = ttk.Button(buttonFrame, text="Add Company", command=self.addCompany)
        addButton.pack(side=LEFT, padx=5)

        clearButton = ttk.Button(buttonFrame, text="Clear", command=self.clearFields)
        clearButton.pack(side=LEFT, padx=5)

    def clearFields(self):

        # Clear all input fields

        self.companyNameVar.set("")
        self.contractLevelVar.set(1)
        self.companyPhoneVar.set("")
        self.companyZipCodeVar.set("")
        self.companyAddressVar.set("")
        self.companyEmailVar.set("")

    def addCompany(self):

        # Add a new company using the provided details

        requestDict = {
            "CompanyName": self.companyNameVar.get(),
            "ContractLevel": self.contractLevelVar.get(),
            "CompanyPhone": self.companyPhoneVar.get(),
            "CompanyZipCode": self.companyZipCodeVar.get(),
            "CompanyAddress": self.companyAddressVar.get(),
            "CompanyEmail": self.companyEmailVar.get()
        }

        # Send the request to the server

        response = DataAccess.CompanyInfo.postCompanyInfo(requestDict)

        if response is None:

            self.logger.Error("Failed to receive a response from the server.")
            PJ_Mobius_Dialog.showErrorDialog(self.parent, "Error", "No response from server.")
            return

        elif response.get("Success", False) is False:

            errorMessage = response.get("ErrorInfo", {}).get("Message", "Unknown error.")
            self.logger.Error(f"Failed to add company: {errorMessage}")
            PJ_Mobius_Dialog.showErrorDialog(self.parent, "Error", f"Failed to add company: {errorMessage}")
            return

        PJ_Mobius_Dialog.showInfoDialog(self.parent, "Info", "Company added successfully.")
        self.logger.Info("Company added successfully.")
        self.clearFields()


