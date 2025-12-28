import hashlib
import os
import pyperclip

HASH_TYPE = "sha256"
ITERATIONS = 1023

userName = input("Enter user name: ")
strPassWd = pyperclip.paste()

# Hash password

binPassWd = strPassWd.encode()
salt = hashlib.pbkdf2_hmac(HASH_TYPE, binPassWd, userName.encode(), ITERATIONS)
hashedPw = hashlib.pbkdf2_hmac(HASH_TYPE, binPassWd, salt, ITERATIONS).hex()

pyperclip.copy(hashedPw)
print(hashedPw)