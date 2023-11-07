from accounts import CheckingAccount, SavingsAccount, Accounts
from transaction import Transaction
import decimal
decimal.getcontext().rounding = decimal.ROUND_HALF_UP

class Bank:
    """Container class with information of accounts, transactions, and summary methods"""

    def __init__(self):
        """Initializes Bank List with an empty list."""
        self._accounts = []
       
    def create_account(self, account_type):
        """Create Account of type savings or checking"""
        if account_type == "checking":
            _account = CheckingAccount()
        elif account_type == "savings":
            _account = SavingsAccount()
        self._accounts.append(_account)
        return _account

    def _find_account(self, account_id):
        """Locate the account with the given id."""
        for account in self._accounts:
            if account.id_matches(account_id):
                return account
        return None
    
    def list_transactions(self, acc):
        """Function to sort transactions and print them"""
        sorted_transactions = sorted(acc._transactions, key = lambda t: (t._date, acc._transactions.index(t))) 
        for transaction in sorted_transactions:
            print(transaction)
    
    def summary(self):
        """Prints the summary of all accounts in the bank"""
        for account in self._accounts:
            formatted_balance = f"${account.balance:,.2f}"
            print(f"{account.get_id()},\tbalance: {formatted_balance}")
