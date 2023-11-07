import sys
import pickle
from datetime import datetime, date
from bank import Bank
from accounts import Accounts, SavingsAccount, CheckingAccount
from transaction import Transaction
from exceptions import TransactionLimitError, TransactionSequenceError, OverdrawError
import decimal
import logging
decimal.getcontext().rounding = decimal.ROUND_HALF_UP





class NoAccountSelectedError(Exception):
    """Raised when an action requires an account to be selected, but an account is not selected."""
    pass

class BankCLI:
    """Display a BankCLI and respond to choices when run."""

    def __init__(self):
        self._bank = Bank()
        self.selected_acc = None
        self._choices = {
            "1": self._open_account,
            "2": self._summary,
            "3": self._select_account,
            "4": self._add_transaction,
            "5": self._list_transaction,
            "6": self._interest_and_fees,
            "7": self._save,
            "8": self._load,
            "9": self._quit,
        }

        self.display_account = None
        
    def _display_menu(self):
        print(
f"""--------------------------------
Currently selected account: {self.display_account}
Enter command
1: open account
2: summary
3: select account
4: add transaction
5: list transactions
6: interest and fees
7: save
8: load
9: quit
>""", end="")

    def run(self):
        """Display the BankCLI and respond to choices."""
        while True:
            self._display_menu()
            choice = input("")
            action = self._choices.get(choice)
            if action:
                try:
                    action()
                except NoAccountSelectedError:
                    print("This command requires that you first select an account.")
                except Exception as e:
                    print(f"An error occurred: {e}")
            else:
                print("{0} is not a valid choice".format(choice))

    def _open_account(self):
        account_type = input("Type of account? (checking/savings)\n>").lower()
        new_acc = self._bank.create_account(account_type)
        logging.debug(f"Created account: {new_acc.get_id()}")

    def _summary(self): 
        self._bank.summary()
        
    def _select_account(self):
        get_id = int(input("Enter account number\n>"))
        self.selected_acc = self._bank._find_account(get_id)

        if self.selected_acc is not None:
            formatted_balance = f"${self.selected_acc.balance:,.2f}"
            self.display_account = f"{self.selected_acc.get_id()},\tbalance: {formatted_balance}"

        else:
            self.display_account = None

    def valid_amount(self, amount):
        if amount >= (-1 * self.selected_acc.balance):
            pass
        else: 
            return False
    

    def _add_transaction(self):
        
        if self.selected_acc is None:
            raise NoAccountSelectedError

        while True:
            try:
                amount = float(input("Amount?\n>"))
                break  
            except ValueError:
                print("Please try again with a valid dollar amount.")
       
        while True:
            transaction_date = input("Date? (YYYY-MM-DD)\n>")
            try:                
                datetime.strptime(transaction_date, "%Y-%m-%d")
                break  
            except ValueError:
                print("Please try again with a valid date in the format YYYY-MM-DD.")
                
        try:
            
            self.selected_acc.add_transaction(amount, transaction_date)
            logging.debug(f"Created transaction: {self.selected_acc.get_id()}, {amount}")
            


        except OverdrawError:
            print("This transaction could not be completed due to an insufficient account balance.")
            return
        
        except TransactionSequenceError as tse:
            print(f"New transactions must be from {tse.latest_date.strftime('%Y-%m-%d')} onward.")
            return
        
        except TransactionLimitError as e:
            if e.limit_type == "daily":
                print("This transaction could not be completed because this account already has 2 transactions in this day.")
            elif e.limit_type == "monthly":
                print("This transaction could not be completed because this account already has 5 transactions in this month.")
            return

        formatted_balance = f"${self.selected_acc.balance:,.2f}"
        self.display_account = f"{self.selected_acc.get_id()},\tbalance: {formatted_balance}"


    
    
    def _interest_and_fees(self):
        if self.selected_acc is None:
            raise NoAccountSelectedError
        try:
            self.selected_acc.interest_and_fees()
            logging.debug("Triggered interest and fees")
            logging.debug(f"Created transaction: {self.selected_acc.get_id()}, {self.selected_acc.get_latest_transaction().get_amount()}")
        except TransactionSequenceError as e:
            print(f"Cannot apply interest and fees again in the month of {e.latest_date}.")
            return
         
        formatted_balance = f"${self.selected_acc.balance:,.2f}"
        self.display_account = f"{self.selected_acc.get_id()},\tbalance: {formatted_balance}"

        
    def _list_transaction(self):
        if self.selected_acc is None:
            raise NoAccountSelectedError
        self._bank.list_transactions(self.selected_acc)

    def _save(self):
        self.selected_acc = None
        with open("bank.pickle", "wb") as f:
            pickle.dump(self._bank, f)
        logging.debug("Saved to bank.pickle")
       

    def _load(self):
        with open("bank.pickle", "rb") as f:   
            self._bank = pickle.load(f)
        logging.debug("Loaded from bank.pickle")
    
    def _quit(self):
        sys.exit(0)
        
                        

if __name__ == "__main__":
    logging.basicConfig(filename='bank.log', level=logging.DEBUG, format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')


    try:
        BankCLI().run()
    except Exception as ex:
        print("Sorry! Something unexpected happened. Check the logs or contact the developer for assistance.")
        ex_type = type(ex).__name__
        ex_message = repr(ex.args[0]) if ex.args else "<no message>"  
        logging.error(f"{ex_type}: {ex_message}")
