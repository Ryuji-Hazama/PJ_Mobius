"""
User table adapter.

Provides the UserTableAdapters class for user database operations.
"""

import datetime
from typing import Literal
import maplex

import Tools
from .connection import DbConnection


class UserTableAdapters:

    def __init__(self):

        # Logging objects

        self.logger = maplex.Logger(__name__)

        try:

            self.connection = DbConnection().connect()
            self.cursor = self.connection.cursor()
            self.logger.info("Database connection established.")

        except Exception as e:

            self.logger.ShowError(e, "Failed to connect database.")
            raise

    def closeConnection(self):

        try:

            self.cursor.close()
            self.connection.close()
            self.logger.info("Database connection closed.")

        except Exception as e:

            self.logger.ShowError(e, "Failed to close database connection.")
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
            self.logger.info("New user info created.")

            return True
        
        except Exception as e:

            self.logger.ShowError(e, "Failed to insert new user information.")
            raise

    ##########################################
    # Update

    def updateUserPassword(self, userId: int, newPassword: str, updateUserId: int):

        try:

            # Update user password

            sql = f"UPDATE Users SET password_hash=%s, initial_password=0, updated_user_id=%s, updated_at=CURRENT_TIMESTAMP WHERE user_id=%s;"
            self.cursor.execute(sql, (newPassword, updateUserId, userId))
            self.connection.commit()
            self.logger.info("User password updated.")

        except Exception as e:
            
            self.logger.ShowError(e, "Failed to update user password.")
            raise

    def updateLoginFailed(self, userId: int, failedCount: int, failedAt: datetime.datetime | None = None, userStatus: Literal['active', 'inactive', 'suspended'] = 'active'):

        try:

            # Update login failed info

            sql = f"UPDATE Users SET login_failed=%s, login_failed_at=%s, user_status=%s WHERE user_id=%s;"
            self.cursor.execute(sql, (failedCount, failedAt, userStatus, userId))
            self.connection.commit()
            self.logger.info("User login failed info updated.")

        except Exception as e:
            
            self.logger.ShowError(e, "Failed to update user login failed info.")
            raise

    ##########################################
    # Select

    def selectUser(self, userId: int | None = None, userName: str | None = None, eMail: str | None = None, accessLevel: Literal['super', 'admin', 'user', 'guest'] | None = None, companyId: int | None = None, userStatus: Literal['active', 'inactive', 'suspended'] | None = None) -> tuple[tuple]:

        if userId is None and userName is None and eMail is None and accessLevel is None and companyId is None and userStatus is None:

            # If the parameters are all empty

            self.logger.warn("Selecting all Users at once is not allowed.")
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

            self.logger.ShowError(e, "Failed to select user informantions.")
            raise
