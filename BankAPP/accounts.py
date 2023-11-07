from datetime import datetime, date
import decimal
from exceptions import TransactionLimitError, TransactionSequenceError, OverdrawError
from transaction import Transaction



class Accounts:
    decimal.setcontext(decimal.Context(rounding = decimal.ROUND_HALF_UP))
    last_id = 1
    
    def __init__(self, transactions = None, balance = 0):
        """Initialize an account with no transactions and 0 balance."""

        self.balance = decimal.Decimal('0.00')
        self._transactions = []
        self._id = Accounts.last_id

        Accounts.last_id += 1

    def add_transaction(self, amount, date, is_interest=False, is_fees=False):
        """Method to add transaction to an account"""

        transaction_date = datetime.strptime(date, "%Y-%m-%d").date()
        
        if is_interest:
            for transaction in self._transactions:
                existing_transaction_date = datetime.strptime(transaction._date, "%Y-%m-%d").date()
                if (existing_transaction_date.month == transaction_date.month and existing_transaction_date.year == transaction_date.year and transaction.is_interest):
                    raise TransactionSequenceError(transaction_date.strftime('%B'))
        elif is_fees:
            for transaction in self._transactions:
                existing_transaction_date = datetime.strptime(transaction._date, "%Y-%m-%d").date()
                if (existing_transaction_date.month == transaction_date.month and existing_transaction_date.year == transaction_date.year and transaction.is_fee):
                    raise TransactionSequenceError(transaction_date.strftime('%B'))
            
        if self._transactions:
            latest_transaction = max(datetime.strptime(transaction._date, "%Y-%m-%d").date() for transaction in self._transactions)

            if transaction_date < latest_transaction:
                raise TransactionSequenceError(latest_transaction)

        self.set_balance(amount)
        self._add_transaction_history(date, amount, is_interest)
   

    def interest_and_fees(self, interest):
        """Method to apply interest and fees to an account by choosing the last day of the month of the last transaction date"""
    
        sorted_transactions = sorted(self._transactions, key = lambda t: (t._date, self._transactions.index(t)))

        if sorted_transactions:
            last_transaction_date = sorted_transactions[-1]
            last_transaction_date_str = last_transaction_date._date
            last_transaction_date = datetime.strptime(last_transaction_date_str, "%Y-%m-%d").date()
            last_transaction_year = last_transaction_date.year
            last_transaction_month = last_transaction_date.month
        

        if last_transaction_month in [1, 3, 5, 7, 8, 10, 12]:
            transaction_date = date(last_transaction_year, last_transaction_month, 31)
        elif last_transaction_month == 2:
            transaction_date = date(last_transaction_year, last_transaction_month, 28)
        else:
            transaction_date = date(last_transaction_year, last_transaction_month, 30)


        self.add_transaction(interest, str(transaction_date), True, False)

        
    def get_latest_transaction(self):
        return self._transactions[-1]
        

    def get_id(self):
        "Method returns id because its a private var"
        return self._id
    
    def set_balance(self, amount):
        "Adds/subtracts amount from the account balance"
        self.balance += decimal.Decimal(amount)
    
    def id_matches(self, account_id):
        "This method returns true if the provided ID matches the id of the account"
        if self._id == f"Savings#{account_id:09}" or self._id == f"Checking#{account_id:09}":
            return True
        return False
    
    def _add_transaction_history(self, date, amount, is_interest=False):
        "Keeps track of the transaction history of an account"
        formatted_amount = f"${amount:,.2f}"
        _transaction = Transaction(date, formatted_amount, is_interest=is_interest)

        self._transactions.append(_transaction)

        


class CheckingAccount(Accounts):
    """Creating a Checking Account"""

    def __init__(self, transactions=None, balance=0):
        super().__init__(transactions, balance)
        self._id = f"Checking#{self._id:09d}"
        self.interest_applied = False  # Flag to track whether interest has been applied
        self.fees_applied = False  # Flag to track whether fees have been applied
        self._last_interest_month = None  # Track the month when interest was last applied
        self._last_fees_month = None

    def add_transaction(self, amount, date, is_interest=False, is_fees=False):
        """Method to add transaction to a Checking Account, while checking if it's an interest or normal transaction"""

        if not is_interest and amount < (-1 * self.balance):
            raise OverdrawError

        # Reset interest and fees flags if a normal transaction is added
        if not is_interest and not is_fees:
            self.interest_applied = False
            self.fees_applied = False

        if is_interest:
            # Check if interest has already been applied for the current month
            if self.interest_applied:
                raise TransactionSequenceError(date)  
            self.interest_applied = True

        if is_fees:
            # Check if fees have already been applied for the current month
            if self.fees_applied:
                raise TransactionSequenceError(date)  
            self.fees_applied = True

        super().add_transaction(amount, date)


    def set_balance(self, amount):
        """Adds/subtracts balance from the checking account"""
        super().set_balance(amount)

    def interest_and_fees(self):
        """Applies interest and fees to the checking account"""

        current_month = date.today().month

        # Check if we've entered a new month since last applying interest
        if self._last_interest_month != current_month:
            
            self.interest_applied = False
        if self._last_fees_month != current_month:
            
            self.fees_applied = False

        # Now that the flags are reset, attempt to apply the interest
        try:
            super().interest_and_fees(self.balance * decimal.Decimal('0.0008'))
            self._last_interest_month = current_month
        except TransactionSequenceError as e:
            latest_date_str = e.latest_date  
            latest_date = datetime.strptime(latest_date_str, "%Y-%m-%d").date()  
            latest_month = latest_date.strftime('%B') 
           
            raise TransactionSequenceError(f"{latest_month}")
        
        # Logic for fees if balance < 100
        sorted_transactions = sorted(self._transactions, key=lambda t: (t._date, self._transactions.index(t)))
        if sorted_transactions:
            last_transaction_date = sorted_transactions[-1]
            last_transaction_date_str = last_transaction_date._date
            last_transaction_date = datetime.strptime(last_transaction_date_str, "%Y-%m-%d").date()
            if last_transaction_date.month in [1, 3, 5, 7, 8, 10, 12]:
                transaction_date = date(last_transaction_date.year, last_transaction_date.month, 31)
            elif last_transaction_date.month == 2:
                transaction_date = date(last_transaction_date.year, last_transaction_date.month, 28)
            else:
                transaction_date = date(last_transaction_date.year, last_transaction_date.month, 30)

            
    
        if self.balance < 100:
            try:
                self.add_transaction(decimal.Decimal('-5.44'), str(transaction_date), False, True)
                # After successfully applying fees, update the respective month
                self._last_fees_month = current_month
            except TransactionSequenceError:
                latest_date_str = e.latest_date
                latest_date = datetime.strptime(latest_date_str, "%Y-%m-%d").date()
                latest_month = latest_date.strftime('%B')
                
                raise TransactionSequenceError(f"{latest_month}")

       







class SavingsAccount(Accounts):
    """Create a savings account"""
    def __init__(self, transactions=None, balance=0):
        super().__init__(transactions, balance)
        self._id = f"Savings#{self._id:09d}" 

    def interest_and_fees(self):
        """Apply interest and fees to Savings Account"""
        super().interest_and_fees(self.balance * decimal.Decimal('0.0041'))

    def add_transaction(self, amount, date, is_interest=False, is_fees = False):
        """Adds transaction to a Savings Account, while checking if its an interest or normal transaction.
        It also checks whether the daily or monthly limit has exceeded"""

        if not is_interest and amount < (-1 * self.balance):
            raise OverdrawError

        if is_interest:
            super().add_transaction(amount, date, is_interest, is_fees=False)
            return
        
        months, days = 0, 0
        if len(self._transactions) >= 2:
            for each in self._transactions:
                if not(each.is_interest):
                    if each._date[5:7] == date[5:7] and each._date[0:4] == date[0:4]:
                        months += 1
                        if each._date[8:10] == date[8:10]:
                            days += 1
                if months >= 5:
                    raise TransactionLimitError("monthly")
                if days >= 2:
                    raise TransactionLimitError("daily")
        super().add_transaction(amount, date)

    
    def set_balance(self, amount):
            super().set_balance(amount)



 
       

     


   

