import tkinter as tk
from tkinter import font

class ListBox(tk.Frame):
    """
    A megawidget for displaying transactions using a Listbox.
    The transaction amount color is blue for positive values and red for negative values.
    """
    
    def __init__(self, parent, transaction_list, **kwargs):
        super().__init__(parent, **kwargs)
        self._transaction_list = transaction_list
        self._labels = []

        
        self.scrollbar = tk.Scrollbar(parent)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        
        self.listbox = tk.Listbox(
            parent,
            width=40,
            height=10,
            relief=tk.SUNKEN,
            bg="#F5F5F5",
            font=font.Font(size=12),
            yscrollcommand=self.scrollbar.set
        )

        for t in self._transaction_list:
            color = 'blue' if t._amt >= 0 else 'red'
            self.listbox.insert(tk.END, str(t))
            self.listbox.itemconfig(tk.END, {'fg': color})

        self.scrollbar.config(command=self.listbox.yview)
        
        self._labels.append(self.listbox)

        self.listbox.pack(padx=5, pady=5)


    def destroyer(self):
        """Method to destroy the megawidget"""
        for x in self._labels:
            x.destroy()

