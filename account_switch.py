import os
import json
import sys
import time
import subprocess
import pywintypes
import win32cred


def get_github_username():
    try:
        credentials = win32cred.CredEnumerate(None, 0)  # Fetch all credentials
        github_credentials = []

        for cred in credentials:
            # Check if the credential is related to GitHub
            if "github.com" in cred['TargetName'].lower():
                github_credentials.append(cred)

        if not github_credentials:
            return None  # No GitHub credentials found

        # Assuming the first GitHub credential is the one you want
        username = github_credentials[0]['UserName']
        return username
    except pywintypes.error as e:
        print(f"An error occurred: {e}")
        return None


def remove_github_credential():
    try:
        credentials = win32cred.CredEnumerate(None, 0)  # Fetch all credentials

        for cred in credentials:
            # Check if the credential is related to GitHub
            if "github.com" in cred['TargetName'].lower():
                try:
                    win32cred.CredDelete(cred['TargetName'], cred['Type'], 1)  # Use CRED_PERSIST_SESSION (1)
                    print(f"GitHub credential for {cred['TargetName']} removed.")
                except pywintypes.error as e:
                    print(f"Error removing GitHub credential for {cred['TargetName']}: {e}")

    except pywintypes.error as e:
        print(f"An error occurred: {e}")


def exit_program(seconds: int, error_id: int):
    print("------------------")
    print("exiting in")
    seconds = seconds

    for second in range(seconds).__reversed__():
        print(str(second + 1) + "...")
        time.sleep(1)

    print("exiting!")
    print("------------------")
    sys.exit(error_id)


directory = __file__[: __file__.rfind("\\") + 1]
accounts_path = directory + "accounts.json"
accounts = ""

if os.path.exists(accounts_path):
    with open(accounts_path, 'r') as file:
        accounts = json.load(file)
else:
    print("No accounts file!!! Save your accounts in a json file!")
    print("keys should be 'username' and 'email'. take a look at the example_accounts file for examples!")
    exit_program(5, -1)

print("\n")
print("Choose an account!")
print("------------------")
for account in accounts:
    print(account["username"])

print("------------------")

account_chosen = str(input())

account = {}

for account_object in accounts:
    if account_chosen.lower() == account_object["username"].lower():
        account = account_object
        break

if account == {}:
    print("\n")
    print("Your accounts file doesn't have a user with that username!")
    exit_program(5, -2)

git_username = f"git config --global user.name '{account['username']}'"
git_email = f"git config --global user.email {account['email']}"

try:
    result_username = subprocess.run(git_username, shell=True, check=True, text=True, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
    result_email = subprocess.run(git_email, shell=True, check=True, text=True, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
    print(f"Changed git global config account to {account['username']}!!")
    if get_github_username().lower() != account['username'].lower():
        remove_github_credential()
    else:
        print("Git config username is the same, so the windows credentials weren't erased.")


except subprocess.CalledProcessError as e:
    print("Error executing Git command:", e)

print("\n")
