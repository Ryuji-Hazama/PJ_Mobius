from getpass import getpass
import maplex
import requests

###################################
# Logging objects

Logger = maplex.Logger("InitSuperUser")

#
###################################
# Main method

Logger.Info("Start")

try:

    while True:

        connectionSuccess = False
        domain = input("Input domain name > https://")

        # Exit command

        if domain.upper() == "EXIT":

            break

        # Create request payload

        url = f"https://{domain}/initsuper"
        passWd = getpass("Password > ")
        print("\nCreating new super account.\n")
        newUserName = input("User name > ")

        while True:
                
            superPassWd = getpass("Password > ")
            confPassWd = getpass("Confirm password > ")

            if superPassWd not in {None, ""} and superPassWd == confPassWd:

                break

            print("Password does not match.\nPlease try again.")
            
        requestPayload = {
            "Password": passWd,
            "SuperUserName": newUserName,
            "SuperUserPassword": superPassWd
        }

        try:
                
            # Send request

            response = requests.post(url, json=requestPayload, verify="pj-mobius-cert.crt")

            if response.status_code == 200:

                result = response.json()

                if result["ErrorInfo"]["Error"]:

                    Logger.Error(f"Server returned error: {result["ErrorInfo"]["ErrorMessage"]}")
                    print(f"\nFailed to register supre user.")

                elif result["Registered"]:

                    Logger.Info(f"Super user registered as : {newUserName}")
                    print("\nSuper user successfully registered.")

                else:

                    Logger.Error(f"Failed to register super user.")
                    print("\nFailed to register super user because of the one of the following reasons:\n" \
                          " - System password incorrect.\n" \
                          " - Another super user already exists.\n")
                    
            else:

                Logger.Error("Failed to connect to the server.")
                Logger.Error(f"Status code: {response.status_code}")
                print(f"\nFailed to connect to the server: {domain}\n"
                      f"Status code: {response.status_code}"
                      f"Please check the server domain and try it later.")
                
        except Exception as e:

            Logger.ShowError(e, "Request failed.")

        print("\n input \"exit\" to exit application.\n")

except Exception as e:

    Logger.ShowError(e, "Unexpected error.", True)