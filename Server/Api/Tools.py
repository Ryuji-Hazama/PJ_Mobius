import hashlib
import maplex
import os

class stringHasher:

    def __init__(self, hashType: str="sha256"):

        self.ITERATIONS = int(os.getenv("HASH_ITERATIONS"))
        self.HASH_TYPE = hashType

    def hashString(self, plainPassword: str, userName="") -> str:

        # Hash password

        binPassWd = plainPassword.encode()
        salt = hashlib.pbkdf2_hmac(self.HASH_TYPE, binPassWd, userName.encode(), self.ITERATIONS)
        hashedPw = hashlib.pbkdf2_hmac(self.HASH_TYPE, binPassWd, salt, self.ITERATIONS).hex()

        return hashedPw

def CheckPasswordPattern(passwordString: str) -> bool:

    # If bytes were passed accidentally, decode them to a string (UTF-8)

    if isinstance(passwordString, (bytes, bytearray)):

        try:

            passwordString = passwordString.decode("utf-8")

        except Exception:

            # Fallback: replace undecodable bytes

            passwordString = passwordString.decode("utf-8", errors="replace")

    if len(passwordString) < 8:

        return False

    hasUpper = False
    hasLower = False
    hasDigit = False
    hasSpeci = False

    # Iterate characters directly (handles multi-byte unicode properly)

    for c in passwordString:

        if c.islower():

            hasLower = True

        if c.isupper():

            hasUpper = True

        if c.isdigit():

            hasDigit = True

        if not c.isalnum():

            # Special character: not alphanumeric

            hasSpeci = True

    # All flags must be True

    return all((hasLower, hasUpper, hasDigit, hasSpeci))
