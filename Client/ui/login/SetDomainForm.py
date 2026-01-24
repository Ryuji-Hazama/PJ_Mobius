import maplex
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ui import Dialog

class SetDomainForm(ttk.Frame):

    def __init__(self):

        self.master = ttk.Toplevel("Set Server Domain", resizable=(False, False))

        super().__init__(self.master, padding=(10, 10))
        self.pack(fill=BOTH, expand=YES)

        # Logging objects

        self.logger = maplex.Logger(__name__)

        # Config instance

        try:

            self.conf = maplex.MapleTree("config.mpl")

        except maplex.MapleFileNotFoundException as notFoundE:

            self.logger.ShowError(notFoundE, "config.mpl does not exists.")
            Dialog("Error", "Configuration file does not exists.").showDialog()

        except Exception as e:

            self.logger.ShowError(e, "Failed to read config.mpl")
            Dialog("Error", "Failed to read config.mpl\n"
                                      "Please recover configuration file or\n"
                                      "contact to support.").showDialog()

        # Title label

        hdTxt = "Please set server domain."
        hd = ttk.Label(master=self, text=hdTxt)
        hd.pack(fill=BOTH, pady=(10, 10), padx=5, expand=YES)

        # Form variable

        self.domainText = ttk.StringVar(value="")

        # Forms

        self.domainEntry(self.domainText)
        self.buttons()

        self.logger.info("Domain initialization form loaded.")

    def domainEntry(self, variable):

        # Generate domain entry form frame

        container = ttk.Frame(self)
        container.pack(fill=BOTH, expand=YES)

        # - - - - - - - - - - #
        # Generate entry form #
        # - - - - - - - - - - #

        # Label

        httpLbText = "https://"
        httpLb = ttk.Label(container, text=httpLbText)
        httpLb.pack(side=LEFT, fill=X, padx=5, expand=YES)

        # Entry

        ent = ttk.Entry(container, textvariable=variable, width=50)
        ent.pack(side=LEFT, fill=X, expand=YES, padx=5)

        # Get config (if exists)

        try:

            domainText = self.conf.readMapleTag("DOMAIN", "APPLICATION_SETTINGS", "HTTP_REQUEST")

            if domainText is None:

                domainText = ""

        except Exception as e:

            self.logger.ShowError(e, "Unexpected error occurred dualing generating entry form.")
            Dialog("Error", f"Unexpected error:\n"
                                      f"{e}\n\n"
                                      f"Please contact to support.").showDialog()
            self.master.destroy()
        
        ent.insert(0, domainText)
        ent.select_range(0, END)
        ent.focus_set()

    def buttons(self):

        # Generate button frame

        container = ttk.Frame(self)
        container.pack(fill=X, expand=YES, pady=(10, 15))

        # Buttons

        btConf = ttk.Button(
            container,
            text="Confirm",
            bootstyle=SUCCESS,
            command=self.confirmDomain,
            width=7
            )
        btConf.pack(side=RIGHT, padx=5)

        btCancel = ttk.Button(
            container,
            text="Cancel",
            bootstyle=DANGER,
            command=self.master.destroy
            )
        btCancel.pack(side=RIGHT, padx=5)

    def confirmDomain(self):

        domainText = self.domainText.get()

        if domainText == "":

            self.logger.warn("Domain text is empty.")
            Dialog("Info", "Entry is empty").showDialog()

        else:

            # Update config.mpl

            self.conf.saveValue("DOMAIN", domainText, "APPLICATION_SETTINGS", "HTTP_REQUEST", save=True)
            self.logger.info(f"Domain information saved: {domainText}")
            self.master.destroy()
