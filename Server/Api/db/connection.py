"""
Database connection management.

Provides the DbConnection class for establishing MySQL database connections.
"""

import os
import pymysql


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
