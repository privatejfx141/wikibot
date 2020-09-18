import json

_CREDENTIALS_FILE = "./credentials.json"

USERNAME = ""
PASSWORD = ""
SITEURL = ""
try:
    with open(_CREDENTIALS_FILE, "r") as credentials_file:
        data = json.load(credentials_file)
        USERNAME = data["USERNAME"]
        PASSWORD = data["PASSWORD"]
        SITEURL = data["SITEURL"]
except FileNotFoundError:
    print("File 'credentials.json' is not found.")
