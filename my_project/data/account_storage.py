import json
import os

FILE_PATH = "accounts.json"

def load_accounts():
    if not os.path.exists(FILE_PATH):
        return {"masters": [], "slaves": []}
    with open(FILE_PATH, "r") as f:
        return json.load(f)

def save_account(account_type, account):
    data = load_accounts()
    if account not in data[account_type]:
        data[account_type].append(account)
        with open(FILE_PATH, "w") as f:
            json.dump(data, f, indent=4)

def remove_account(account_type, login):
    data = load_accounts()
    data[account_type] = [acc for acc in data[account_type] if acc["login"] != login]
    with open(FILE_PATH, "w") as f:
        json.dump(data, f, indent=4)
        
def clear_all_accounts():
    with open(FILE_PATH, "w") as f:
        json.dump({"masters": [], "slaves": []}, f, indent=4)
