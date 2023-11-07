
class TransactionLimitError(Exception):
    """Raised when interest in triggered twice in the same month"""
    def __init__(self, limit_type):
        super().__init__()
        self.limit_type = limit_type

class OverdrawError(Exception):
    """Raised when money from an account is overdrafted."""
    pass

class TransactionSequenceError(Exception):
    """Raised when the subsequent transaction date is before the latest transaction"""
    def __init__(self, latest_date):
        self.latest_date = latest_date