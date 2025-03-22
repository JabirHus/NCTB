import MetaTrader5 as mt5

def connect_mt5(login, password, server, path="C:/Program Files/MetaTrader 5/terminal64.exe"):
    """Connect to MetaTrader 5 with explicit terminal path."""
    try:
        if not mt5.initialize(path):
            return False, f"Initialization failed: {mt5.last_error()}"

        authorized = mt5.login(int(login), password=password, server=server)
        if not authorized:
            return False, f"Login failed: {mt5.last_error()}"

        account_info = mt5.account_info()
        if account_info is None:
            return False, "Failed to retrieve account info after login."
        
        return True, account_info._asdict()

    except Exception as e:
        return False, f"Exception occurred: {str(e)}"
