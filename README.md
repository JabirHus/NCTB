Must install these packages
pip install MetaTrader5
pip install duckdb
pip install tk

Must have python downloaded: https://www.python.org/downloads

Must have MetaTrader 5 installed:https://www.metatrader5.com/en/download

Must have at least 2 brokerage accounts, demo (master/slave). Can sign up with any brokerage and open 2 accouts and recieve credentials instantly. Open a 100k and 50k, raw ecn, 1:100 leverage. This is a link to Vantage broker: https://www.vantagemarkets.co.uk/open-demo-account/


Once everything is installed, there are some changes that must be made to the default MetaTrader. Once MetaTrader 5 is open, log in with the credentials of the 'master' (any one of the 2 accounts). This is done by right clicking 'Accounts' on the left hand side within the Navigator. Alternatively, on the bottom right corner, click the stop sign and you'll have an option to login. Once logged in, click Tools on the top, click Options. Navigate to the Expert Advisors tab, and you'll be met with checkboxes. Only have the first one checked, all other ones in the Expert Advisors tab should be unchecked.
Once this is complete, click Ok and everything will still look the same.
Now on the top left you should see some forex pairs. Scroll to the last forex pair and add these symbols: GBPCHF+, USDCAD+, EURUSD+, GBPUSD+, NZDUSD+, USDJPY+, EURGBP+, AUDUSD+
Still on MetaTrader 5, click the button on the top with a red square that says 'Algo Trading', it should turn get a green arrow. Now you are set up to have this automated trading bot running on your MetaTrader 5. The hard part is done, now log into your mt5 slave account and the only step you need to do is to add the same pairs mentioned above. Step 1 complete!

Now that you are fully logged into your accounts, you are ready to run the program. cd into the file that contains main.py and run the terminal command: python main.py

This should boot up the program and you'll be met with the homepage. You can navigate to strategy builder where you'll have the opportunity to select the indicators for your strategy as well as some of the values associated with them. When they are complete, you can head over to the account page and connect your demo accounts. You should be able to see the balance as well as other things appearing. Now that everything is saved, you can close the program and rerun and it will begin to automatically evaluate the currency pairs againast the strategy and place a trade when the conditions are met.
Your strategies and accounts are saved. You may close and relaunch the app at any time, and it will resume automatic trading and copying based on your saved settings.