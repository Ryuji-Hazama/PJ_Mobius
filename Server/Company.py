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