from typing import Literal
import maplex
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import MessageDialog
from ttkbootstrap.icons import Icon
from ttkbootstrap.constants import *

class Dialog(MessageDialog):

    def __init__(self, dialogStyle: Literal['Info', "Question", 'Warn', 'Error'], dialogMessage: str, dialogTitle: str | None = None, buttons: list[Literal['OK', 'Yes', 'No', 'Confirm', 'Retry', 'Cancel']] = ['OK']):

        icons = {"Info": Icon.info, "Question": Icon.question, "Warn": Icon.warning, "Error": Icon.error}
        buttonStyle = {"OK": SUCCESS, "Yes": INFO, "No": "info-outline", 'Confirm': SECONDARY, 'Retry': "success-outline", 'Cancel': DANGER}
        buttonList = []

        # Button list generation

        for button in buttons:

            buttonList.append(f"{button}:{buttonStyle[button]}")

        # Default title setting

        if dialogTitle is None:

            dialogTitle = dialogStyle

        super().__init__(dialogMessage, dialogTitle, icon=icons[dialogStyle], buttons=buttonList, default=buttons[0], resizable=(False, False), topmost=True)

    def showDialog(self) -> str:

        DialogResult = self.show()
        return DialogResult

class ProcessRequest(ttk.Frame):

    def __init__(self, titleMessage):

        # Logging objects

        self.Logger = maplex.Logger("ProcessRequest")

        self.master = ttk.Toplevel(titleMessage, resizable=(False, False), topmost=True)

        super().__init__(self.master, padding=(10, 10))
        self.pack(fill=BOTH, expand=YES)

        self.labelContainer = ttk.Frame(self)
        self.labelContainer.pack(fill=X, expand=YES)

        self.messageLb = ttk.Label(self.labelContainer, text="Requesting...")
        self.messageLb.pack(fill=X, expand=YES)

        progressContainer = ttk.Frame(self, padding=(30, 0))
        progressContainer.pack(fill=X, expand=YES)

        self.progressBar = ttk.Progressbar(progressContainer, bootstyle=SUCCESS, mode="indeterminate", length=200)
        self.progressBar.pack(pady=10)
        self.progressBar.start()

        self.Logger.Info("Process window loaded.")

        self.master.grab_set()

    def PackLabel(self, messageText):

        self.messageLb.destroy()
        self.messageLb = ttk.Label(self.labelContainer, text=messageText)
        self.messageLb.pack(fill=X, expand=YES)

    def closeWindow(self):

        self.master.destroy()