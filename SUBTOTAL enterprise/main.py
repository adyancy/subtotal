import customtkinter as ctk
import db
from app import SubtotalApp

if __name__ == "__main__":
    db.init_db()
    root = ctk.CTk()
    SubtotalApp(root)
    root.mainloop()
