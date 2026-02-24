import os
import subprocess
from appdirs import *
from misc import exit_program, AccountManager
from InquirerPy import inquirer
import typer
from typing_extensions import Annotated
from colorama import Fore, Style

appname = "git-account-switch"
author = "vindalyn"
appdata_path = user_data_dir(appname=appname, appauthor=author)
accounts_file_path = os.path.join(appdata_path, "accounts.json")
acc_man: AccountManager = AccountManager(accounts_file_path)
accounts = acc_man.get_accounts()
account_labels = acc_man.get_account_labels()

app: typer.Typer = typer.Typer()

@app.command()
def switch(
    label: Annotated[str | None, typer.Option("--label", "-l", "--l", help="Label of the account preset")] = None,
    github: Annotated[bool, typer.Option("--github", "-g", "--g", help="Attempt Github Account Switch")] = False
    ):
    #print(f"label: {label}")
    if label is None: 
        account_chosen = inquirer.select(
            message="Choose an account!",
            choices=account_labels
        ).execute()
    else:
        account_chosen = label
    # grab account from file 
    account = acc_man.get_account(account_chosen)

    # account hasn't been added yet
    if account is None:
        print("\n")
        print("Your accounts file doesn't have a user with that username!")
        exit_program(5, -2)

    try:
        # attempt to change git username and email
        change_user = acc_man.change_username(account["username"])
        change_email = acc_man.change_email(account["email"])

        if change_user and change_email:
            print(f"Changed git global config account to {account['username']}!!")
        else:
            print("Failed to change git config 3:")

        if github:
            # attempt to switch github account auth
            if not acc_man.switch_to_github_account(account['username']):
                print("Failed to change active github account")
            else:
                print("changed github config!! :3")


    except subprocess.CalledProcessError as e:
        print("Error executing Git command:", e)


@app.callback(invoke_without_command=True)
def account_switch(
    ctx: typer.Context, 
    label: Annotated[str | None, typer.Option("--label", "-l", "--l", help="Label of the account preset")] = None):
    #print("calling default command")

    if ctx.invoked_subcommand is None:
        switch(label)

@app.command()
def add(label: Annotated[str, typer.Argument()], username: Annotated[str, typer.Argument()], email: Annotated[str, typer.Argument()]):
    # TODO: separate add from edit
    res = acc_man.add_account(label, username, email)

    if res:
        print(f"Added user: {username} under label: {label}!! :3 ")
    else: 
        print("Couldn't add user... 3:")

@app.command()
def remove(label: Annotated[str, typer.Argument()]):
    res = acc_man.remove_account(label)

    if res:
        print("Removed user from config: ", label)
    else: 
        print("Couldn't remove label... 3:")

@app.command()
def config():
    print("Data is located under:", accounts_file_path)

@app.command()
def ps(
    label: Annotated[str | None, typer.Option("--label", "-l", "--l", help="Label of the account preset")] = None   
       ):
    current_data: dict = acc_man.get_current_account_data()
    current_email: str = current_data["email"]
    current_username: str = current_data["username"]
    found_one: bool = False 
    #print(acc_man.get_shared_repos())
    #print(current_data)
    for account in accounts:
        acc_label = account.get("label", None)
        username = account.get("username", None)
        email = account.get("email", None)

        if acc_label is None:
            continue

        if not acc_man._is_label_valid_and_same(label, acc_label) and label is not None:
            continue

        print_label_string: str = acc_label
        if current_email == email and current_username == username:
            print_label_string = f"{Fore.GREEN}{print_label_string}{Style.RESET_ALL}"

        print(print_label_string)
        if username is not None:
            print(f"\t{username}")
            if found_one is False:
                found_one = True
        if email is not None:
            print(f"\t{email}")
    
    if found_one is False:
        print("Sorry! 3: Couldn't find anything..")

@app.command()
def repos(
    all: Annotated[bool, typer.Option("--all", "-a", "--a", help="Boolean to check if all repos should be listed")] = False,  
    owned: Annotated[bool, typer.Option("--owned", "-o", "--o", help="Boolean to check if only owned repos should be listed")] = False,  
    shared: Annotated[bool, typer.Option("--shared", "-s", "--s", help="Boolean to check if only shared repos should be listed")] = False   
):
    display_repos: list = []
    #print(f"all: {all}, owned: {owned}, shared: {shared}")
    if owned or all:
        owned_repos += acc_man.get_owned_repos()
        if owned_repos:
            display_repos += owned_repos

    if shared or all:
        shared_repos = acc_man.get_shared_repos()
        if shared_repos:
            display_repos += shared_repos
    if display_repos:
        for i in display_repos:
            print(i)
    else:
        print("No repos to display!")


if __name__ == "__main__":
    app()