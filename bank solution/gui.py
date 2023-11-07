import sys
import logging
from decimal import Decimal, InvalidOperation
from datetime import datetime
import tkinter as tk
from tkinter import DISABLED, messagebox
from tkinter import ttk
from tkcalendar import DateEntry
from pmw import ListBox
from transactions import Base
from bank import Bank

import sqlalchemy
from sqlalchemy.orm.session import sessionmaker
from accounts import OverdrawError, TransactionLimitError, TransactionSequenceError



logging.basicConfig(filename='bank.log', level=logging.DEBUG,
                    format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')


def handle_exception(exception, value, traceback):
    print("Sorry! Something unexpected happened. If this problem persists please contact our support team for assistance.")
    logging.error(f"{exception.__name__}: {repr(value)}")
    sys.exit(0)


class BankGUI:
    """Initialize the BankGUI."""
    def __init__(self):
        self.setup_session()
        self.setup_gui_elements()
        self._window.mainloop()

    def setup_session(self):
        """Setup the session, loading or creating a bank from the database."""
        self._session = Session()
        self._bank = self._session.query(Bank).first()
        if self._bank:
            logging.debug("Loaded from bank.db")     
        else:
            self._bank = Bank()
            self._session.add(self._bank)
            self._session.commit()
            logging.debug("Saved to bank.db") 
        self._selected_account = None
        self._all_accounts = []
        self._all_transactions = []

    def setup_gui_elements(self):
        """Setup all the GUI elements like the main window, options, account frames, etc."""
        self._window = self.initialize_main_window()
        self.make_options()
        self.initialize_account_frames()
        self.initialize_transaction_widgets()
        self._summary()

    def initialize_main_window(self):
        """Initialize the main window of the bank GUI with its settings and position."""
        window = tk.Tk()
        window.report_callback_exception = handle_exception 
        window.title("MY BANK")
        window.geometry("800x600")  # Width x Height in pixels
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - 800) / 2
        y = (screen_height - 600) / 2
        window.geometry(f"800x600+{int(x)}+{int(y)}")
        return window

    def initialize_account_frames(self):
        """Initialize frames for account-related operations, including a canvas and scrollbar for summary."""
        self._open_account_frame = tk.Frame(self._window)
        self._summary_frame = tk.Frame(self._window)
        self._list_transactions_frame = tk.Frame(self._window)
        self._add_transaction_frame = tk.Frame(self._window)

        # Create a canvas inside _summary_frame
        self.canvas = tk.Canvas(self._summary_frame)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add a scrollbar to _summary_frame
        self.scrollbar = tk.Scrollbar(self._summary_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure the canvas
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Create a frame inside the canvas
        self.account_buttons_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0,0), window=self.account_buttons_frame, anchor="nw")

        self._summary_frame.grid(row=2, column=0, sticky="nsew")
        self._list_transactions_frame.grid(row=2, column=1, sticky="nsew")


    def initialize_transaction_widgets(self):
        """Initialize the widgets related to transactions."""
        self._list_transactions_frame.tkraise()
        self._transaction_listbox = ListBox(self._list_transactions_frame, self._all_transactions)

    def make_options(self):
        """Create the options frame with buttons for add account, add transaction, and interest and fees."""
        self._options_frame = tk.Frame(self._window)
        self._options_frame.grid(row=0, column=0, sticky="nsew")
        
        self._options_frame.columnconfigure([0, 1, 2], weight=1)
        self._options_frame.rowconfigure(0, weight=1)
        
        self._open_account_btn = tk.Button(self._options_frame, text="Open Account", 
                                    activebackground='blue', command=self._open_account_gui)
        self._open_account_btn.grid(row=0, column=0, padx=5, pady=15, sticky="nsew")

        self._add_transaction_btn = tk.Button(self._options_frame, text="Add Transaction", 
                                        state=tk.NORMAL, command=self._add_transaction_gui)
        self._add_transaction_btn.grid(row=0, column=1, padx=5, pady=15, sticky="nsew")

        self._trigger_interest_btn = tk.Button(self._options_frame, text="Interest and Fees", 
                                        command=self._monthly_triggers)
        self._trigger_interest_btn.grid(row=0, column=2, padx=5, pady=15, sticky="nsew")

    

    def _add_transaction_gui(self):
        """Display widgets for adding a transaction, including amount and date entry fields."""

        # Disable add transaction button
        self._add_transaction_btn['state'] = tk.DISABLED

        # Check if any account is selected
        if self._selected_account is None:
            self._add_transaction_btn['state'] = tk.NORMAL
            messagebox.showwarning('An Account was not Selected', "This command requires that you first select an account.")
            return

        # Display frame
        self._add_transaction_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        # Check validity of amount
        def validation_check():
            try:
                amount = Decimal(e1.get())
            except InvalidOperation:
                messagebox.showwarning('Invalid Amount', 'Please try again with a valid dollar amount.')
            else:
                add_callback(amount)

        def on_entry_click(event):
            if event.widget.get() == event.widget.default_text:
                event.widget.delete(0, "end")
                event.widget.config(fg='black')

        def on_focusout(event):
            if not event.widget.get():
                event.widget.put(event.widget.default_text)
                event.widget.config(fg='grey')

        # Label and Entry for amount
        l1 = tk.Label(self._add_transaction_frame, text="Deposit Amount:")
        l1.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        e1 = tk.Entry(self._add_transaction_frame, width=15)
        e1.default_text = "Enter amount..."
        e1.insert(0, e1.default_text)
        e1.bind('<FocusIn>', on_entry_click)
        e1.bind('<FocusOut>', on_focusout)
        e1.config(fg='grey')
        e1.grid(row=0, column=1)

        # Label and DateEntry (from tkcalendar) for date
        l2 = tk.Label(self._add_transaction_frame, text="Date:")
        l2.grid(row=1, column=0, sticky="w", pady=(0, 10))

        date_entry = DateEntry(self._add_transaction_frame, width=15)
        date_entry.grid(row=1, column=1)

        def add_callback(amount):
            date = date_entry.get_date()
            self._add_transaction(amount, date)
            for widget in self._add_transaction_frame.winfo_children():
                widget.destroy()
            self._add_transaction_frame.grid_forget()
            self._list_transactions()
            self._summary()
            self._add_transaction_btn['state'] = tk.NORMAL

        b1 = tk.Button(self._add_transaction_frame, text="Enter", command=validation_check, bg="blue", fg="white")
        b1.grid(row=2, column=0, columnspan=2, pady=10)

    
    def _add_transaction(self, amount, date):
        """Process GUI input for adding a transaction and update the selected account."""
        try:
            self._selected_account.add_transaction(amount, self._session, date)
            self._session.commit()
            logging.debug("Saved to bank.db")
        except (OverdrawError, TransactionLimitError, TransactionSequenceError) as e:
            title, message = self._get_transaction_error_message(e)
            messagebox.showwarning(title, message)

    def _get_transaction_error_message(self, exception):
        """Get an error message based on the exception type."""
        error_messages = {
            OverdrawError: ('Insufficient Balance', 
                            "This transaction could not be completed due to an insufficient account balance."),
            TransactionLimitError: ('Transaction Limit reached', 
                                    "This transaction could not be completed because the account has reached a transaction limit."),
            TransactionSequenceError: ('Invalid Date', 
                                    f"New transactions must be from {exception.latest_date} onward.")
        }

        return error_messages.get(type(exception), ("Unknown Error", "An unknown error occurred."))



    def _open_account_gui(self):
        """Display widgets for opening a new account, including radio buttons for account type."""

        self._open_account_frame.grid(padx=10, pady=10)

        title_label = tk.Label(self._open_account_frame, text="Open New Account", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)

        instruction_label = tk.Label(self._open_account_frame, text="Choose the type of account you want to open:", font=("Arial", 12))
        instruction_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))

        account_type = tk.StringVar()
        account_type.set("savings")

        savings_radio = tk.Radiobutton(self._open_account_frame, text="Savings", variable=account_type, value="savings")
        savings_radio.grid(row=2, column=0)

        checking_radio = tk.Radiobutton(self._open_account_frame, text="Checking", variable=account_type, value="checking")
        checking_radio.grid(row=2, column=1)

        b1 = tk.Button(self._open_account_frame, text="Open Account", command=lambda: self._open_account_action(account_type.get()), bg="blue", fg="white")
        b1.grid(row=3, column=0, columnspan=2, pady=10)

    def _open_account_action(self, account_type_chosen):
        """Process GUI input for opening an account and update the UI."""
        self._open_account(account_type_chosen)
        for widget in self._open_account_frame.winfo_children():
            widget.destroy()
        self._open_account_frame.grid_forget()
        self._summary()

    def _open_account(self, acct_type):
        """Open an account of the specified type."""
        try:
            self._bank.add_account(acct_type, self._session)
            self._session.commit()
            logging.debug("Saved to bank.db")
        except OverdrawError:
            messagebox.showwarning('Account Creation Failed')

    def _select(self, num):
        """Select an account based on its account number."""
        self._selected_account = self._bank.get_account(num)
        self._list_transactions()

    def _list_transactions(self):
        """List transactions for the selected account."""

        self._transaction_listbox.destroyer()

        t = self._selected_account.get_transactions()
        self._list_transactions_frame.tkraise()
        self._transaction_listbox = ListBox(self._list_transactions_frame, t)

    
    def _monthly_triggers(self):
        """Process interest and fees for the selected account as triggered by the user."""
        try:
            self._selected_account.assess_interest_and_fees(self._session)
            self._session.commit()
            logging.debug("Triggered fees and interest")
            logging.debug("Saved to bank.db")
        except AttributeError:
            messagebox.showwarning('Account not selected', 'This command requires that you first select an account.')
        except TransactionSequenceError as e:
            messagebox.showwarning('Interest already applied', f"Cannot apply interest and fees again in the month of {e.latest_date.strftime('%B')}.")
        else:
            self._list_transactions()
            self._summary()


    def _summary(self):
        """Display a summary of available accounts and their buttons."""
        
        # Destroy old account buttons
        for x in self._all_accounts:
            x.destroy()
        self._all_accounts = []  #

        # Populate with new account buttons, figure out why is the frame moving
        for account in self._bank.show_accounts():
            account_btn = tk.Button(self.account_buttons_frame, text=str(account),
                                    command=lambda num=account._account_number: self._select(num),
                                    width=50, background="purple", activebackground='white')
            account_btn.pack(fill=tk.X, ipady=5, padx=5)
            self._all_accounts.append(account_btn)


if __name__ == "__main__":

    engine = sqlalchemy.create_engine("sqlite:///bank.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker()
    Session.configure(bind=engine)
    BankGUI()
