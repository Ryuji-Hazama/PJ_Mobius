"""
Company table adapter.

Provides the CompanyTableAdapters class for company database operations.
"""

import maplex

from .connection import DbConnection


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

        try:

            # Insert new company info

            sql = f"INSERT INTO ContractCompanies "\
                f"(company_name, company_phone, company_zipcode, company_address, company_email, contract_level, created_user_id, updated_user_id) "\
                f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"
            self.cursor.execute(sql, (companyName, companyPhone, companyZipCode, companyAddress, companyEmail, contractLevel, createUserId, createUserId))
            self.connection.commit()
            self.Logger.Info("New company info created.")

            return True

        except Exception as e:

            self.Logger.ShowError(e, "Failed to insert new company info.")
            raise

    #################################
    # Select

    def selectCompany(self, companyId: int | None = None, companyName: str | None = None, contractLevel: int | None = None, orSearch: bool = False) -> tuple[tuple] | None:

        # Select companies by exact match
        
        if companyId is None and companyName is None and contractLevel is None:

            # If the parameters are all empty

            self.Logger.Warn("Selecting all Companies at once is not allowed.")
            return None

        try:

            # Generate sql

            nextOption = False
            replaceList = []
            connector = " OR " if orSearch else " AND "
            emptyStrs = {None, ""}
            sql = "SELECT * FROM ContractCompanies WHERE "

            if companyId is not None:

                sql += f"company_id=%s"
                replaceList.append(companyId)
                nextOption = True

            if companyName not in emptyStrs:

                if nextOption:

                    sql += connector

                sql += f"company_name=%s"
                replaceList.append(companyName)

                nextOption = True

            if contractLevel is not None:

                if nextOption:

                    sql += connector

                sql += f"contract_level=%s"
                replaceList.append(contractLevel)

            sql += ";"
            self.Logger.Debug(f"Select Company SQL: {sql} with {replaceList}")

            # Execute sql

            self.cursor.execute(sql, replaceList)
            return self.cursor.fetchall()

        except Exception as e:

            self.Logger.ShowError(e, "Failed to select company informantions.")
            raise

    def searchCompany(self, companyName: str | None = None, companyAddress: str | None = None, companyEmail: str | None = None, orSearch: bool = False) -> tuple[tuple] | None:

        # Search companies by partial match

        if companyName is None and companyAddress is None and companyEmail is None:

            # If the parameters are all empty

            self.Logger.Warn("Searching all Companies at once is not allowed.")
            return None

        try:

            # Generate sql

            nextOption = False
            replaceList = []
            connector = " OR " if orSearch else " AND "
            emptyStrs = {None, ""}
            sql = "SELECT * FROM ContractCompanies WHERE "

            if companyName not in emptyStrs:

                sql += f"company_name LIKE %s"
                replaceList.append(f"%{companyName}%")
                nextOption = True

            if companyAddress not in emptyStrs:

                if nextOption:

                    sql += connector

                sql += f"company_address LIKE %s"
                replaceList.append(f"%{companyAddress}%")
                nextOption = True

            if companyEmail not in emptyStrs:

                # Maybe not use this for security reason?

                self.Logger.Warn("Searching by company email is not recommended for security reason.")
                
                if nextOption:

                    sql += connector

                sql += f"company_email LIKE %s"
                replaceList.append(f"%{companyEmail}%")

            sql += ";"

            # Execute sql

            self.cursor.execute(sql, replaceList)
            return self.cursor.fetchall()

        except Exception as e:

            self.Logger.ShowError(e, "Failed to search company informantions.")
            raise
