from tkinter import messagebox

def show_error(title: str, message: str):
    messagebox.showerror(title, message)

def show_info(title: str, message: str):
    messagebox.showinfo(title, message)

def show_warning(title: str, message: str):
    messagebox.showwarning(title, message)