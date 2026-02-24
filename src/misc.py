import subprocess
import sys
import os 
import json 
import time 
from pathlib import Path
from typing import Optional
import re 

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

class AccountManager():

    def __init__(self, account_path):
        self.account_path = account_path
        self._create_accounts_file_if_missing()

    def _create_accounts_file_if_missing(self) -> bool:
        if not os.path.exists(self.account_path):
            parent_dir = Path(self.account_path).parent
            
            parent_dir.mkdir(parents=True, exist_ok=True)
            with open(self.account_path, "w") as file:
                file.write("")
            return True 
        return False

    def get_accounts(self):
        if os.path.exists(self.account_path):
            try: 
                with open(self.account_path, 'r') as file:
                    return json.load(file)
            except Exception as e:
                print("An exception occurred:", e)
                return []

        else:
            self._create_accounts_file_if_missing(self.account_path)
            return []
    
    def get_account(self, label: str) -> Optional[dict]:
        accounts: list = self.get_accounts()
        for account in accounts:
            account: dict 
            acc_label: str = account.get("label", None)
            if self._is_label_valid_and_same(acc_label, label):
                return account 
        return None
    def get_account_labels(self) -> list :
        label_list: list = []
        for account in self.get_accounts():
            label = account.get("label", None)
            if label is not None:
                label_list.append(label)
        return label_list 
    # could be optimized to only change diffs, but we don't have that much data so this optimization is unnecessary
    def _update_accounts_file(self, accounts: list) -> bool:
        try:
            with open(self.account_path, "w") as file:
                file.write(json.dumps(accounts, indent=4))
            return True 
        except Exception as e:
            print("An exception occurred:", e)
            return False 
        
    def _is_label_valid_and_same(self, label1: str, label2: str) -> bool:
        if label1 is None or label2 is None:
            return False

        return label1.lower().strip() == label2.lower().strip()

    def get_current_account_data(self) -> dict:
        # git config user.name
        # git config user.email
        account_obj: dict = {
            "email": self.get_current_email(),
            "username": self.get_current_username()
        }

        return account_obj
    
    def change_username(self, username: str) -> bool:
        command = f"git config --global user.name \"{username}\""
        try:
            result_username = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE,
                                            )
            #print(result_username)
            return True 
        except subprocess.CalledProcessError as e:
            return False 
        
    def change_email(self, email: str) -> bool:
            command = f"git config --global user.email \"{email}\""
            try:
                result_email = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)
                return True 
            except subprocess.CalledProcessError as e:
                return False 
            
    def get_current_username(self) -> str | None:
        command = "git config user.name"
        try:
            result_username = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
            return result_username.stdout.strip()
        except subprocess.CalledProcessError as e:
            return None
        
    def get_current_email(self) -> str | None:
        command = "git config user.email"
        try:
            result_email = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
            return result_email.stdout.strip()
        except subprocess.CalledProcessError as e:
            return None

    def get_all_repos(self) -> list[str] | None:
        command = "gh api user/repos --paginate -q \".[] | .clone_url\""
        try:
            results = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
            return results.stdout.strip().split("\n")
        except subprocess.CalledProcessError as e:
            return None
    def get_github_username(self) -> str | None:
        try:
            username = subprocess.check_output(
                        ["gh", "api", "user", "--jq", ".login"],
                            text=True
                        ).strip()
            return username
        except subprocess.CalledProcessError as e:
            print(e)
            return None
        
    def get_owned_repos(self) -> list[str] | None:
        try:
            username = self.get_github_username()
            cmd = [
                    "gh", "api", "user/repos", "--paginate",
                    "--jq", f'.[] | select(.owner.login == "{username}") | .clone_url'
                ]
            results = subprocess.run(
                cmd, check=True, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
            return results.stdout.strip().split("\n")
        except subprocess.CalledProcessError as e:  
            print(e)
            return None
    def get_shared_repos(self) -> list[str] | None:
        try:
            # get owned repos
            owned_repos = self.get_owned_repos()
            all_repos = self.get_all_repos()
            return sorted(set(all_repos) - set(owned_repos))
        except subprocess.CalledProcessError as e:  
            print(e)
            return None
        
    def switch_to_github_account(self, username: str) -> bool:
        possible_usernames: list = self.get_all_github_accounts()
        username_to_use = username
        changed_username = False 
        for usr in possible_usernames:
            usr: str
            if usr.lower() == username.lower():
                username_to_use = usr 
                changed_username = True 
                break
        if not changed_username:
            return False 
        
        command= ["gh", "auth", "switch", "--user", username_to_use]
        try:
            output = subprocess.check_output(
                        command,
                            text=True,
                            stderr=subprocess.STDOUT
                        ).strip()
            
            #print(f"output: ", output)
            return "Switched active account" in output
        except subprocess.CalledProcessError as e:
            print(e)
            return None
    def get_all_github_accounts(self) -> list[str] | None:
        command= "gh auth status"
        try:
            status_string = subprocess.check_output(
                        command,
                            text=True
                        ).strip()
            
            #print(status_string)
            regex = re.findall(r"Logged in to github.com account\s*(.+?)\s*\(keyring\)", status_string)
            return regex 
        except subprocess.CalledProcessError as e:
            print(e)
            return None

    def add_account(self, label: str, username: str, email: str) -> bool:
        accounts: list = self.get_accounts()
        for account in accounts:
            account: dict
            account_label: str  = account.get("label", None)
            account_username: str = account.get("username", None)
            account_email: str = account.get("email", None)

            if account_username is None or account_email is None or label is None:
                continue 
            
            if self._is_label_valid_and_same(account_label, label):
                account["email"] = email
                account["username"] = username  
                self._update_accounts_file(accounts)
                return True  
        account_obj: dict = {
            "label": label,
            "email": email,
            "username": username
        }
        accounts.append(account_obj)

        return self._update_accounts_file(accounts)
        
    def remove_account(self, label: str) -> bool:
        accounts: list = self.get_accounts()
        for idx, account in enumerate(accounts):
            account: dict 
            account_label: str  = account.get("label", None)

            if self._is_label_valid_and_same(account_label, label):
                accounts.pop(idx)
                self._update_accounts_file(accounts)
                return True 
        
        return False 


