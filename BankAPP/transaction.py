from datetime import datetime, date
import decimal
# decimal.getcontext().rounding = decimal.ROUND_HALF_UP


class Transaction:
    decimal.setcontext(decimal.Context(rounding = decimal.ROUND_HALF_UP))
    """This class stores amount and transaction date"""

    def __init__(self, date, amount, is_interest=False, is_fee=False):
        self._date = date
        amount_str = amount.replace("$", "")  # Remove the dollar sign
        amount_str = amount_str.replace(",", "")
        self.amount = decimal.Decimal(amount_str)
        self.is_interest = is_interest
        self.is_fee = is_fee
       
    def __str__(self):
        """Formats the way transactions are printed in string"""
        return "{}, ${:,.2f}".format(self._date, self.amount)
    
    def get_amount(self):
        return self.amount