from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, create_engine
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from datetime import datetime
import functools

Base = declarative_base()

from accounts import SavingsAccount, CheckingAccount, Base

SAVINGS = "savings"
CHECKING = "checking"

class Bank(Base):
    __tablename__ = "bank"

    _id = Column(Integer, primary_key=True) # a unique id for each bank (even if you only have one)
    
    
    # Relationships
    _accounts = relationship("Account", backref="bank")  # One-to-many relationship with Account

    

    def add_account(self, acct_type, session):
        """Creates a new Account object and adds it to this bank object. The Account will be a SavingsAccount or CheckingAccount, depending on the type given.

        Args:
            type (string): "Savings" or "Checking" to indicate the type of account to create
        """
        acct_num = self._generate_account_number()
        if acct_type == SAVINGS:
            a = SavingsAccount(acct_num)  # associate account with the bank
        elif acct_type == CHECKING:
            a = CheckingAccount(acct_num) # associate account with the bank
        else:
            return None
        self._accounts.append(a)
        session.add(a)  # add account to session for saving to database
        session.commit()  # commit changes to database

    def _generate_account_number(self):
        return len(self._accounts) + 1  # use the length of the accounts list to generate account number

    def show_accounts(self):
        "Accessor method to return accounts"
        return self._accounts

    def get_account(self, account_num):
        """Fetches an account by its account number.

        Args:
            account_num (int): account number to search for

        Returns:
            Account: matching account or None if not found
        """        
        for x in self._accounts:
            if x._account_number == account_num:
                return x
        return None



