"""
Base utilities for API client.

Provides shared HTTP request handling and constants.
"""

import maplex
import requests
import time

NONE_LIST = [None, "", "None"]


def requestToServer(method: str, url: str, json: dict, processWindow=None) -> requests.Response | None:

    """ Send a request to the server and return the response. """
    
    response = None
    conf = maplex.MapleTree("config.mpl")
    certPath = conf.readMapleTag("VERIFY", "APPLICATION_SETTINGS", "HTTP_REQUEST")
    timeoutStr = conf.readMapleTag("TIMEOUT", "APPLICATION_SETTINGS", "HTTP_REQUEST")

    try:

        timeout = int(timeoutStr)

    except ValueError:

        timeout = 30  # Default timeout

    for i in range(3):

        try:

            if method.upper() == "GET":

                response = requests.get(url, json=json, verify=certPath, timeout=timeout)

            elif method.upper() == "POST":

                response = requests.post(url, json=json, verify=certPath, timeout=timeout)

            elif method.upper() == "PUT":

                response = requests.put(url, json=json, verify=certPath, timeout=timeout)

            else:

                raise ValueError(f"Unsupported HTTP method: {method}")

            if response.status_code == 200:

                return response

            if i < 2:

                time.sleep(2)

                if processWindow:

                    try:

                        processWindow.master.after(0, lambda msg=f"Retrying... ({i+1}/2)": processWindow.PackLabel(msg))

                    except Exception:

                        pass

        except Exception as e:

            time.sleep(2)

    return response
