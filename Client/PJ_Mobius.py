import PJ_Mobius_Login
import PJ_Mobius_Main
import maplex
import ttkbootstrap as ttk

class App:

    def __init__(self):

        # Logging objects

        self.Logger = maplex.Logger("App")
        self.Logger.Info("Initializing App.")

        # Generate window form

        self.root = ttk.Window("Login Form", "darkly")
        self.current_frame = None
        self.switchWindow("Login")

        self.Logger.Info("App initialized.")

    def switchWindow(self, targetWindow):

        try:

            self.Logger.Info(f"Switching to [{targetWindow}] window.")

            if self.current_frame:

                self.current_frame.destroy()

            if targetWindow == "Login":

                self.root.title("Login Form")
                self.root.resizable(False, False)
                self.current_frame = PJ_Mobius_Login.LogInForm(self.root, self.switchWindow)

            elif targetWindow == "Main":

                self.root.title("Main Menu")
                self.root.resizable(True, True)
                self.current_frame = PJ_Mobius_Main.MainMenuForm(self.root, self.switchWindow)

        except Exception as e:

            self.Logger.ShowError(e, f"Failed to switch window to [{targetWindow}]", True)

    def run(self):

        self.root.mainloop()
        self.Logger.Info("Quitting App.")

if __name__ == "__main__":

    App().run()