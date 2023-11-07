import sys
import pickle
import logging
from decimal import Decimal, setcontext, BasicContext, InvalidOperation
from datetime import datetime

from bank import Bank
from exceptions import OverdrawError, TransactionLimitError, TransactionSequenceError

import sqlalchemy
from sqlalchemy.orm.session import sessionmaker

from sqlalchemy import create_engine
from bank import Base



# context with ROUND_HALF_UP
setcontext(BasicContext)

logging.basicConfig(filename='bank.log', level=logging.DEBUG,
                    format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class BankCLI():
    """Driver class for a command-line REPL interface to the Bank application"""

    def __init__(self):
        self._session = Session()
      
        
        # Get the bank from the database
        self._bank = self._session.query(Bank).first()

        # If a bank does not exist, then initialize and save a new bank
        if not self._bank:
            self._bank = Bank()
            self._session.add(self._bank)
            self._session.commit()
            logging.debug("Saved to bank.db")
        else:
            logging.debug("Loaded from bank.db")
        
        self._selected_account = None

        self._choices = {
            "1": self._open_account,
            "2": self._summary,
            "3": self._select,
            "4": self._add_transaction,
            "5": self._list_transactions,
            "6": self._monthly_triggers,
            "7": self._quit,
        }

    def _display_menu(self):
        print(f"""--------------------------------
Currently selected account: {self._selected_account}
Enter command
1: open account
2: summary
3: select account
4: add transaction
5: list transactions
6: interest and fees
7: quit""")

    def run(self):
        """Display the menu and respond to choices."""

        while True:
            self._display_menu()
            choice = input(">")
            action = self._choices.get(choice)
            # expecting a digit 1-9
            if action:
                action()
            else:
                # not officially part of spec since we don't give invalid options
                print("{0} is not a valid choice".format(choice))

    def _summary(self):
        for account in self._bank.show_accounts():
            print(account)

    def _quit(self):
        self._session.close()
        sys.exit(0)

    def _add_transaction(self):
        amount = None
        while amount is None:
            try:
                amount = Decimal(input("Amount?\n>"))
            except InvalidOperation:
                print("Please try again with a valid dollar amount.")

        date = None
        while not date:
            try:
                date = datetime.strptime(
                    input("Date? (YYYY-MM-DD)\n>"), "%Y-%m-%d").date()
            except ValueError:
                print("Please try again with a valid date in the format YYYY-MM-DD.")

        try:
            self._selected_account.add_transaction(amount, self._session, date)
            self._session.commit()
            logging.debug("Saved to bank.db")
        except AttributeError:
            print("This command requires that you first select an account.")
        except OverdrawError:
            print(
                "This transaction could not be completed due to an insufficient account balance.")
        except TransactionLimitError as ex:
            print(
                f"This transaction could not be completed because this account already has {ex.limit} transactions in this {ex.limit_type}.")
        except TransactionSequenceError as ex:
            print(f"New transactions must be from {ex.latest_date} onward.")

    def _open_account(self):
        acct_type = input("Type of account? (checking/savings)\n>")

        try:
            self._bank.add_account(acct_type, self._session)
            self._session.commit()
            logging.debug("Saved to bank.db")
        except OverdrawError:
            print(
                "This transaction could not be completed due to an insufficient account balance.")

    def _select(self):
        num = int(input("Enter account number\n>"))
        self._selected_account = self._bank.get_account(num)

    def _monthly_triggers(self):
        try:
            self._selected_account.assess_interest_and_fees(self._session)
            logging.debug("Triggered interest and fees")
            logging.debug("Saved to bank.db")
        except AttributeError:
            print("This command requires that you first select an account.")
        except TransactionSequenceError as e:
            print(
                f"Cannot apply interest and fees again in the month of {e.latest_date.strftime('%B')}.")

    def _list_transactions(self):
        try:
            for t in self._selected_account.get_transactions():
                print(t)
        except AttributeError:
            print("This command requires that you first select an account.")


if __name__ == "__main__":
    try:
        engine = create_engine(f"sqlite:///bank.db")
        # Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        Session = sqlalchemy.orm.sessionmaker(bind=engine)
        BankCLI().run()

    except Exception as e:
        print("Sorry! Something unexpected happened. Check the logs or contact the developer for assistance.")
        logging.error(str(e.__class__.__name__) + ": " + repr(str(e)))


