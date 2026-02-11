import maplex
import os
from db import UserTableAdapters
import Tools

class InitSuperUser:

    def __init__(self, passWord: str, superUserName: str, superPassWd: str):

        # Logging class

        self.logger = maplex.Logger(__name__)

        # Variables

        self.passWord = passWord
        self.superUserName = superUserName
        self.superPassWd = superPassWd

        # String hasher

        self.hasher = Tools.stringHasher()

        # Table adapter

        self.tableAdapter = UserTableAdapters()

    def checkPassword(self) -> bool:

        self.logger.info("Checking system password.")

        try:

            with open(os.getenv("ADMIN_NAME"), "r") as envUserNameFile:

                envUserName = envUserNameFile.read().strip()

            with open(os.getenv("ADMIN_PASSWORD"), "r") as envPasswordFile:

                envPassword = envPasswordFile.read().strip()

            hashedPassword = self.hasher.hashString(self.passWord, envUserName)

        except Exception as e:

            self.logger.ShowError(e, "Failed to get admin informations.")
            raise

        return hashedPassword == envPassword
    
    def checkFirstEntry(self):

        try:

            usersList = self.tableAdapter.selectUser(accessLevel="super")

            return usersList is None or len(usersList) == 0
        
        except Exception as e:

            self.logger.ShowError(e)
            raise

    def initSuperUser(self) -> bool:

        try:
                
            if not self.checkPassword():

                self.logger.info("System password incorrect.")
                return False
            
            elif not self.checkFirstEntry():

                self.logger.info("Another user info already exists.")
                return False
            
            return self.tableAdapter.insertUser(self.superUserName, "default@default", self.superPassWd, accessLevel="super")
            
        except Exception as e:

            self.logger.ShowError(e, "Failed to create super user data.")
            raise