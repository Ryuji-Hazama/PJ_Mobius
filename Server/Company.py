import maplex
import Session
import TableAdapters

class CompanyManager:

    def __init__(self, token: str):

        # Logging objects

        self.Logger = maplex.Logger("CompanyManager")

        # Table adapters

        self.CompanyAdapter = TableAdapters.CompanyTableAdapters()
        self.Session = Session.CheckSession(token)
        self.sessionToken = token

    def close(self):

        self.CompanyAdapter.closeConnection()
        self.Session.close()
        self.Logger.Info("Closed CompanyManager object.")

    def createCompany(self, companyName: str | None = None, contractLevel: int | None = None, companyPhone: str | None = None, companyZipCode: str | None = None, companyAddress: str | None = None, companyEmail: str | None = None) -> dict:

        # Create a new company

        retDict = {"Success": False, "CompanyID": None, "ErrorInfo": {"Error": False, "Message": ""}}
        
        try:

            # Check the session validity

            if not self.Session.IsValid():

                retDict["ErrorInfo"]["Error"] = True
                retDict["ErrorInfo"]["Message"] = "Invalid session."
                return retDict
            
            if companyName is None or contractLevel is None:

                retDict["ErrorInfo"]["Error"] = True
                retDict["ErrorInfo"]["Message"] = "Company name and contract level are required."
                self.Logger.Info("Company name and contract level are required to create a company.")
                return retDict

            # Check for existing company with the same name

            existingCompanies = self.CompanyAdapter.selectCompany(companyName=companyName)

            if existingCompanies:

                retDict["ErrorInfo"]["Error"] = True
                retDict["ErrorInfo"]["Message"] = f"Company named {companyName} already exists."
                self.Logger.Info(f"Company named {companyName} already exists.")
                return retDict

            # Insert the new company

            retDict["CompanyID"] = self.CompanyAdapter.insertCompany(companyName, contractLevel, companyPhone, companyZipCode, companyAddress, companyEmail)

            if not retDict["CompanyID"]:

                retDict["ErrorInfo"]["Error"] = True
                retDict["ErrorInfo"]["Message"] = "Failed to create company."
                self.Logger.Info("Failed to create a new company.")

            else:

                self.Logger.Info(f"Created new company with ID: {retDict['CompanyID']}")

        except Exception as e:

            self.Logger.ShowError(e, "Failed to create company.")
            retDict["ErrorInfo"]["Error"] = True
            retDict["ErrorInfo"]["Message"] = f"Failed to create company: {str(e)}"

        return retDict

    def getCompanyList(self, str,companyID: int | None = None, companyName: str | None = None, contractLevel: int | None = None) -> tuple[tuple] | None:
        
        # Get company list

        retDict = {"CompanyList": None, "ErrorInfo": {"Error": False, "Message": ""}}
        
        try:

            # Check the session validity

            if not self.Session.IsValid():

                retDict["ErrorInfo"]["Error"] = True
                retDict["ErrorInfo"]["Message"] = "Invalid session."
                return retDict

            retDict["CompanyList"] = self.CompanyAdapter.selectCompany(companyID, companyName, contractLevel)

            if not retDict["CompanyList"]:

                retDict["ErrorInfo"]["Error"] = True
                retDict["ErrorInfo"]["Message"] = "No company found."
                self.Logger.Info("No company found with the given criteria.")

            else:

                self.Logger.Debug(f"Found {len(retDict['CompanyList'])} companies with the given criteria.")

        except Exception as e:

            self.Logger.ShowError(e, "Failed to get company list.")
            retDict["ErrorInfo"]["Error"] = True
            retDict["ErrorInfo"]["Message"] = f"Failed to get company list: {str(e)}"

        return retDict