import datetime
from typing import Literal
import maplex
import os
import pymysql
import Tools

class DbConnection:

    def connect(self):

        database = "MobiusDB"

        # Get DB informations

        try:

            with open(os.getenv("DB_USER"), "r") as userNameFile:
            
                userName = userNameFile.read().strip()

            with open(os.getenv("DB_PASSWORD"), "r") as passWdFile:

                passWd = passWdFile.read().strip()

            # DB connection

            return pymysql.connect(user=userName, passwd=passWd, host="pj-mobius-db", database=database)

        except Exception:

            raise

class UserTableAdapters:

    def __init__(self):

        # Logging objects

        self.Logger = maplex.Logger("TableAdapters: Users")

        try:

            self.connection = DbConnection().connect()
            self.cursor = self.connection.cursor()
            self.Logger.Info("Database connection established.")

        except Exception as e:

            self.Logger.ShowError(e, "Failed to connect database.")
            raise

    def closeConnection(self):

        try:

            self.cursor.close()
            self.connection.close()
            self.Logger.Info("Database connection closed.")

        except Exception as e:

            self.Logger.ShowError(e, "Failed to close database connection.")
            raise

    #######################################
    # Insert

    def insertUser(self, userName: str, eMail: str, userPassword: str, initialPassword: int=1, accessLevel: str="user", companyId: int | None = None, userStatus: str | None = None, createUserId: int | None = None) -> bool:

        try:

            # Hash password

            hashedPassword = Tools.stringHasher().hashString(userPassword, userName)

            # Insert new user info

            sql = f"INSERT INTO Users " \
                f"(user_name, email, password_hash, initial_password, access_level, company_id, user_status, created_user_id,  updated_user_id) " \
                f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
            self.cursor.execute(sql, (userName, eMail, hashedPassword, initialPassword, accessLevel, companyId, userStatus, createUserId, createUserId))
            self.connection.commit()
            self.Logger.Info("New user info created.")

            return True
        
        except Exception as e:

            self.Logger.ShowError(e, "Failed to insert new user information.")
            raise

    ##########################################
    # Update

    def updateUserPassword(self, userId: int, newPassword: str, updateUserId: int):

        try:

            # Update user password

            sql = f"UPDATE Users SET password_hash=%s, initial_password=0, updated_user_id=%s, updated_at=CURRENT_TIMESTAMP WHERE user_id=%s;"
            self.cursor.execute(sql, (newPassword, updateUserId, userId))
            self.connection.commit()
            self.Logger.Info("User password updated.")

        except Exception as e:
            
            self.Logger.ShowError(e, "Failed to update user password.")
            raise

    def updateLoginFailed(self, userId: int, failedCount: int, failedAt: datetime.datetime | None = None, userStatus: Literal['active', 'inactive', 'suspended'] = 'active'):

        try:

            # Update login failed info

            sql = f"UPDATE Users SET login_failed=%s, login_failed_at=%s, user_status=%s WHERE user_id=%s;"
            self.cursor.execute(sql, (failedCount, failedAt, userStatus, userId))
            self.connection.commit()
            self.Logger.Info("User login failed info updated.")

        except Exception as e:
            
            self.Logger.ShowError(e, "Failed to update user login failed info.")
            raise

    ##########################################
    # Select

    def selectUser(self, userId: int | None = None, userName: str | None = None, eMail: str | None = None, accessLevel: Literal['super', 'admin', 'user', 'guest'] | None = None, companyId: int | None = None, userStatus: Literal['active', 'inactive', 'suspended'] | None = None) -> tuple[tuple]:

        if userId is None and userName is None and eMail is None and accessLevel is None and companyId is None and userStatus is None:

            # If the parameters are all empty

            self.Logger.Warn("Selecting all Users at once is not allowed.")
            return None

        try:

            # Generate sql

            nextOption = False
            replaceList = []
            emptyStrs = {None, ""}
            sql = "SELECT * FROM Users WHERE"

            if userId is not None:

                sql += f" user_id=%s"
                replaceList.append(userId)
                nextOption = True

            if userName not in emptyStrs:

                if nextOption:

                    sql += " AND"

                sql += f" user_name=%s"
                replaceList.append(userName)
                nextOption = True

            if eMail not in emptyStrs:

                if nextOption:

                    sql += " AND"

                sql += f" email=%s"
                replaceList.append(eMail)
                nextOption = True

            if accessLevel not in emptyStrs:

                if nextOption:

                    sql += " AND"

                sql += f" access_level=%s"
                replaceList.append(accessLevel)
                nextOption = True

            if companyId is not None:

                if nextOption:

                    sql += " AND"

                sql += f" company_id=%s"
                replaceList.append(companyId)
                nextOption = True

            if userStatus not in emptyStrs:

                if nextOption:

                    sql += " AND"

                sql += f" user_status=%s"
                replaceList.append(userStatus)

            sql += ";"

            # Execute sql

            self.cursor.execute(sql, replaceList)
            return self.cursor.fetchall()

        except Exception as e:

            self.Logger.ShowError(e, "Failed to select user informantions.")
            raise

class SessionInfoTableAdapters:

    def __init__(self):

        # Logging objects

        self.Logger = maplex.Logger(f"TableAdapters: Session")

        try:

            self.connection = DbConnection().connect()
            self.cursor = self.connection.cursor()
            self.Logger.Info("Database connection established.")

        except Exception as e:

            self.Logger.ShowError(e, "Failed to connect database.")
            raise

    def closeConnection(self):

        try:

            self.cursor.close()
            self.connection.close()
            self.Logger.Info("Database connection closed.")

        except Exception as e:

            self.Logger.ShowError(e, "Failed to close database connection.")
            raise

    #################################
    # Insert

    def CreateNewSession(self, userData: tuple) -> str:

        self.Logger.Info("Creating new session information.")
        selectSql = f"SELECT session_uuid FROM SessionInfo WHERE user_id=%s AND logout_datetime>%s;"
        self.cursor.execute(selectSql, (userData[0], f"{datetime.datetime.now():%Y/%m/%d %H:%M:%S}"))
        result = self.cursor.fetchall()
        
        if result:

            # Session from another computer is still remains

            self.Logger.Warn("There is another active session.")
            return None
        
        # Create session info

        sql = f"INSERT INTO SessionInfo (user_id, user_name, company_id, access_level) VALUES (%s, %s, %s, %s);"
        self.cursor.execute(sql, (userData[0], userData[1], userData[6], userData[5]))
        self.connection.commit()
        self.Logger.Info("Session info created.")
        
        # Recheck duplicate session

        self.cursor.execute(selectSql, (userData[0], f"{datetime.datetime.now():%Y/%m/%d %H:%M:%S}"))
        result = self.cursor.fetchall()

        if len(result) > 1:

            # Login with two computers at the same time!?

            self.Logger.Warn("Another computer took the session.")
            return None

        return result[0][0]

    ################################
    # Update

    def UpdateLogout(self, uuid: str, update: str):

        self.Logger.Info(f"Updating logout datetime: +{update}")

        sql = f"UPDATE SessionInfo SET logout_datetime=ADDTIME(CURRENT_TIMESTAMP, %s) WHERE session_uuid=%s;"
        self.cursor.execute(sql, (update, uuid))
        self.connection.commit()

        self.Logger.Info("Logout datetime updated.")

    ################################
    # Select

    def selectSessionInfo(self, uuid: str) -> tuple[tuple] | None:

        self.Logger.Info(f"Selecting session information: {uuid}")

        try:

            sql = f"SELECT user_id, company_id, access_level, logout_datetime FROM SessionInfo WHERE session_uuid=%s;"
            self.cursor.execute(sql, (uuid,))
            result = self.cursor.fetchall()

            return result if result else None
        
        except Exception as e:

            self.Logger.ShowError(e, f"Failed to select session information: {uuid}")
            raise

    def selectSessionInfoByTimeAndUser(self, userId: int, BeforeAfter: Literal['before', 'after'], logoutDatetime: datetime.datetime | None = None) -> tuple[tuple] | None:

        if logoutDatetime is None:

            logoutDatetime = datetime.datetime.now()

        logoutDatetimeString = f"{logoutDatetime:%Y/%m/%d %H:%M:%S}"
        timeSpan = f"{'<' if BeforeAfter == 'before' else '>'}"

        self.Logger.Info(f"Selecting session information by time and user: {userId}, {BeforeAfter}, {logoutDatetime:%Y/%m/%d %H:%M:%S}")

        try:

            sql = f"SELECT session_uuid, user_id, company_id, access_level, logout_datetime FROM SessionInfo WHERE user_id=%s AND logout_datetime{timeSpan}=%s;"
            self.cursor.execute(sql, (userId, logoutDatetimeString))
            result = self.cursor.fetchall()

            return result if result else None
        
        except Exception as e:

            self.Logger.ShowError(e, f"Failed to select session information by time and user: {userId}, {BeforeAfter}, {timeSpan}")
            raise

class CompanyTableAdapters:

    def __init__(self):
        
        # Logging objects

        self.Logger = maplex.Logger("CompanyTableAdapters")

        try:

            self.connection = DbConnection().connect()
            self.cursor = self.connection.cursor()
            self.Logger.Info("Database connection established.")

        except Exception as e:

            self.Logger.ShowError(e, "Failed to connect database.")
            raise

    def closeConnection(self):

        try:

            self.cursor.close()
            self.connection.close()
            self.Logger.Info("Database connection closed.")

        except Exception as e:

            self.Logger.ShowError(e, "Failed to close database connection.")
            raise

    #################################
    # Insert

    def insertCompany(self, companyName: str, companyPhone: str, companyZipCode: str, companyAddress: str, companyEmail: str, contractLevel: int, createUserId: int | None = None) -> bool:

        pass

    #################################
    # Select

    def selectCompany(self, companyId: int | None = None, companyName: str | None = None, contractLevel: int | None = None) -> tuple[tuple] | None:

        if companyId is None and companyName is None and contractLevel is None:

            # If the parameters are all empty

            self.Logger.Warn("Selecting all Companies at once is not allowed.")
            return None

        try:

            # Generate sql

            nextOption = False
            replaceList = []
            emptyStrs = {None, ""}
            sql = "SELECT * FROM ContractCompanies WHERE"

            if companyId is not None:

                sql += f" company_id=%s"
                replaceList.append(companyId)
                nextOption = True

            if companyName not in emptyStrs:

                if nextOption:

                    sql += " AND"

                sql += f" company_name=%s"
                replaceList.append(companyName)

                nextOption = True

            if contractLevel is not None:

                if nextOption:

                    sql += " AND"

                sql += f" contract_level=%s"
                replaceList.append(contractLevel)

            sql += ";"

            # Execute sql

            self.cursor.execute(sql, replaceList)
            return self.cursor.fetchall()

        except Exception as e:

            self.Logger.ShowError(e, "Failed to select company informantions.")
            raise

    def searchCompany(self, companyName: str | None = None, companyAddress: str | None = None, companyEmail: str | None = None) -> tuple[tuple] | None:

        # Search companies by partial match

        if companyName is None and companyAddress is None and companyEmail is None:

            # If the parameters are all empty

            self.Logger.Warn("Searching all Companies at once is not allowed.")
            return None

        try:

            # Generate sql

            nextOption = False
            replaceList = []
            emptyStrs = {None, ""}
            sql = "SELECT * FROM ContractCompanies WHERE"

            if companyName not in emptyStrs:

                sql += f" company_name LIKE %s"
                replaceList.append(f"%{companyName}%")
                nextOption = True

            if companyAddress not in emptyStrs:

                if nextOption:

                    sql += " AND"

                sql += f" company_address LIKE %s"
                replaceList.append(f"%{companyAddress}%")
                nextOption = True

            if companyEmail not in emptyStrs:

                # Maybe not use this for security reason?

                self.Logger.Warn("Searching by company email is not recommended for security reason.")
                
                if nextOption:

                    sql += " AND"

                sql += f" company_email LIKE %s"
                replaceList.append(f"%{companyEmail}%")

            sql += ";"

            # Execute sql

            self.cursor.execute(sql, replaceList)
            return self.cursor.fetchall()

        except Exception as e:

            self.Logger.ShowError(e, "Failed to search company informantions.")
            raise