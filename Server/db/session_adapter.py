"""
Session table adapter.

Provides the SessionInfoTableAdapters class for session database operations.
"""

import datetime
from typing import Literal
import maplex

from .connection import DbConnection


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
