import maplex
import os
import TableAdapters
import Tools

class InitSuperUser:

    def __init__(self, passWord: str, superUserName: str, superPassWd: str):

        # Logging class

        self.Logger = maplex.Logger("InitSuperUser")

        # Variables

        self.passWord = passWord
        self.superUserName = superUserName
        self.superPassWd = superPassWd

        # String hasher

        self.hasher = Tools.stringHasher()

        # Table adapter

        self.tableAdapter = TableAdapters.UserTableAdapters()

    def checkPassword(self) -> bool:

        self.Logger.Info("Checking system password.")

        try:

            with open(os.getenv("ADMIN_NAME"), "r") as envUserNameFile:

                envUserName = envUserNameFile.read().strip()

            with open(os.getenv("ADMIN_PASSWORD"), "r") as envPasswordFile:

                envPassword = envPasswordFile.read().strip()

            hashedPassword = self.hasher.hashString(self.passWord, envUserName)

        except Exception as e:

            self.Logger.ShowError(e, "Failed to get admin informations.")
            raise

        return hashedPassword == envPassword
    
    def checkFirstEntry(self):

        try:

            usersList = self.tableAdapter.selectUser(accessLevel="super")

            return usersList is None or len(usersList) == 0
        
        except Exception as e:

            self.Logger.ShowError(e)
            raise

    def initSuperUser(self) -> bool:

        try:
                
            if not self.checkPassword():

                self.Logger.Info("System password incorrect.")
                return False
            
            elif not self.checkFirstEntry():

                self.Logger.Info("Another user info already exists.")
                return False
            
            return self.tableAdapter.insertUser(self.superUserName, "default@default", self.superPassWd, accessLevel="super")
            
        except Exception as e:

            self.Logger.ShowError(e, "Failed to create super user data.")
            raise