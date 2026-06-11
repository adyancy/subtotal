import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter as tk
import os
import db

# Set CustomTkinter to dark mode with a dark-blue base theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Colour palette used throughout the app
BG           = "#0b0b0d"   # main window background
CARD         = "#161616"   # card / panel background
CARD2        = "#222222"   # input field background
CARD3        = "#2c2c2c"   # dropdown button / hover surface
TEXT         = "#ffffff"   # primary text colour
MUTED        = "#cfcfcf"   # secondary / label text
ACCENT       = "#8b0000"   # dark red accent (buttons, headings)
ACCENT_HOVER = "#b00020"   # hover state for accent buttons
RED          = "#ff3b3b"   # bright red used for stat values
BORDER       = "#3a3a3a"   # border colour for cards and inputs
DANGER       = "#b00020"   # delete / danger button colour
DANGER_HOVER = "#d0002a"   # hover state for danger buttons
WARNING      = "#ff6b6b"   # warning text in recommendations
SUCCESS      = "#ffffff"   # success / good text in recommendations
BTN          = "#2b2b2b"   # default button background
BTN_HOVER    = "#3a3a3a"   # default button hover background



def _setup_ttk_style():
    # Apply dark styling to the table widget used on the dashboard
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # Style the table rows and cells to match the dark theme
    style.configure("Treeview",
                    background=CARD, foreground=TEXT,
                    fieldbackground=CARD, rowheight=32,
                    font=("Arial", 12))

    # Style the column heading row with the accent red colour
    style.configure("Treeview.Heading",
                    background=ACCENT, foreground=TEXT,
                    font=("Arial", 11, "bold"), relief="flat")

    # Highlight selected rows with the accent colour
    style.map("Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", TEXT)])

    # Style the vertical scrollbar to blend with the dark background
    style.configure("Vertical.TScrollbar",
                    background=CARD3, troughcolor=CARD,
                    arrowcolor=TEXT, bordercolor=CARD)


# Widget factory functions reused across all pages

def _lbl(parent, text, size=13, bold=False, muted=False, colour=None):
    # Creates a CustomTkinter label with transparent background
    return ctk.CTkLabel(
        parent, text=text,
        font=("Arial", size, "bold" if bold else "normal"),
        text_color=colour if colour else (MUTED if muted else TEXT),
        fg_color="transparent",
    )


def _btn(parent, text, command, style="normal", width=140, height=36, big=False):
    # Creates a rounded CustomTkinter button   style can be accent, danger, or normal
    fgs = {
        "accent": (ACCENT,  ACCENT_HOVER),
        "danger": (DANGER,  DANGER_HOVER),
        "normal": (BTN,     BTN_HOVER),
    }
    fg, hover = fgs.get(style, fgs["normal"])
    weight = "bold" if style in ("accent", "danger") else "normal"
    return ctk.CTkButton(
        parent, text=text, command=command,
        fg_color=fg, hover_color=hover,
        text_color=TEXT, corner_radius=8,
        width=width, height=48 if big else height,
        font=("Arial", 15 if big else 13, weight),
        border_width=0,
    )


def _link_btn(parent, text, command):
    # Creates a transparent text-style button used for navigation links
    return ctk.CTkButton(
        parent, text=text, command=command,
        fg_color="transparent", hover_color=CARD3,
        text_color=MUTED, corner_radius=8,
        width=240, height=32,
        font=("Arial", 12),
    )


def _entry(parent, show=None, width=440, height=38):
    # Creates a rounded dark input field for text, passwords, dates, etc.
    return ctk.CTkEntry(
        parent, show=show or "",
        width=width, height=height,
        fg_color=CARD2, text_color=TEXT,
        border_color=BORDER, border_width=1,
        corner_radius=8,
        font=("Arial", 13),
    )


def _combo_ro(parent, values, width=440, height=38, command=None):
    # Creates a read-only rounded dropdown   used for Category, Billing Cycle, and filters
    kwargs = dict(
        values=values or [""],
        state="readonly",
        width=width, height=height,
        fg_color=CARD2, text_color=TEXT,
        border_color=BORDER, border_width=1,
        button_color=CARD3, button_hover_color=BTN_HOVER,
        dropdown_fg_color=CARD2, dropdown_text_color=TEXT,
        dropdown_hover_color=CARD3,
        corner_radius=8,
        font=("Arial", 12),
    )
    if command:
        kwargs["command"] = command
    cb = ctk.CTkComboBox(parent, **kwargs)
    # Set the initial displayed value to the first option
    if values:
        cb.set(values[0])
    return cb


def _combo_edit(parent, values, width=430, height=38):
    # Creates an editable rounded dropdown   used for Subscription Name
    # state="normal" allows the user to type a custom name not in the list
    cb = ctk.CTkComboBox(
        parent,
        values=values or [""],
        state="normal",
        width=width,
        height=height,
        fg_color=CARD2,
        text_color=TEXT,
        border_color=BORDER,
        border_width=1,
        button_color=CARD3,
        button_hover_color=BTN_HOVER,
        dropdown_fg_color=CARD2,
        dropdown_text_color=TEXT,
        dropdown_hover_color=CARD3,
        corner_radius=8,
        font=("Arial", 12),
    )
    # Start with a blank field so the user selects or types a name
    cb.set("")
    return cb


def _make_table(parent, columns, col_widths=None):
    # Builds a dark-styled table with a vertical scrollbar
    frame = tk.Frame(parent, bg=CARD)
    frame.pack(fill="both", expand=True, padx=2, pady=2)
    t = ttk.Treeview(frame, columns=columns, show="headings")

    # Set each column heading and width
    for i, col in enumerate(columns):
        t.heading(col, text=col)
        w = col_widths[i] if col_widths else 130
        t.column(col, width=w, anchor="w")

    # Attach a scrollbar to the right side of the table
    sy = ttk.Scrollbar(frame, orient="vertical", command=t.yview,
                        style="Vertical.TScrollbar")
    t.configure(yscrollcommand=sy.set)
    t.pack(side="left", fill="both", expand=True)
    sy.pack(side="right", fill="y")
    return t


# Subscription catalogue names and AUD prices grouped by category

SUBSCRIPTION_OPTIONS = {
    "Entertainment / Streaming": [
        {"name": "YouTube Premium Lite",          "price":  8.99},
        {"name": "YouTube Premium Individual",    "price": 16.99},
        {"name": "YouTube Premium Family",        "price": 39.99},
        {"name": "Spotify Premium Individual",    "price": 15.99},
        {"name": "Spotify Premium Duo",           "price": 22.99},
        {"name": "Spotify Premium Family",        "price": 27.99},
        {"name": "Apple Music Individual",        "price": 12.99},
        {"name": "Apple Music Family",            "price": 19.99},
        {"name": "Twitch Turbo",                  "price": 11.99},
        {"name": "Amazon Prime Music / Prime",    "price":  9.99},
    ],
    "Video Streaming": [
        {"name": "Netflix Standard with Ads",     "price":  9.99},
        {"name": "Netflix Standard",              "price": 20.99},
        {"name": "Netflix Premium",               "price": 28.99},
        {"name": "Amazon Prime Video",            "price":  9.99},
        {"name": "Disney+ Standard with Ads",     "price":  9.99},
        {"name": "Disney+ Standard",              "price": 17.99},
        {"name": "Disney+ Premium",               "price": 24.99},
        {"name": "HBO Max Basic with Ads",        "price": 11.99},
        {"name": "HBO Max Standard",              "price": 15.99},
        {"name": "HBO Max Premium",               "price": 21.99},
        {"name": "Stan Standard",                 "price": 17.00},
        {"name": "BINGE Standard",                "price": 19.00},
        {"name": "Paramount+ Standard",           "price":  7.99},
        {"name": "BritBox",                       "price": 13.99},
    ],
    "Work / Productivity": [
        {"name": "ChatGPT Plus",                  "price":  35.00},
        {"name": "ChatGPT Pro",                   "price": 350.00},
        {"name": "Canva Pro",                     "price":  17.99},
        {"name": "Canva Teams",                   "price":  13.50},
        {"name": "Adobe Photoshop",               "price":  34.99},
        {"name": "Adobe Lightroom",               "price":  19.99},
        {"name": "Adobe Acrobat Pro",             "price":  34.99},
        {"name": "Adobe Illustrator",             "price":  34.99},
        {"name": "Adobe Creative Cloud All Apps", "price":  89.99},
        {"name": "Affinity by Canva",             "price":   0.00},
    ],
    "Gaming": [
        {"name": "Xbox Game Pass Essential",                 "price": 12.95},
        {"name": "Xbox Game Pass Premium",                   "price": 17.95},
        {"name": "Xbox Game Pass Ultimate",                  "price": 35.95},
        {"name": "PC Game Pass",                             "price": 19.45},
        {"name": "PlayStation Plus Essential",               "price": 12.95},
        {"name": "PlayStation Plus Extra",                   "price": 20.95},
        {"name": "PlayStation Plus Deluxe",                  "price": 23.95},
        {"name": "Nintendo Switch Online Monthly",           "price":  5.95},
        {"name": "Nintendo Switch Online Annual",            "price": 29.95},
        {"name": "Nintendo Switch Online + Expansion Pack",  "price": 59.95},
    ],
    "Gym / Fitness": [
        {"name": "Anytime Fitness",  "price": 100.00},
        {"name": "Fitness First",    "price": 150.00},
        {"name": "Jetts Fitness",    "price":  75.00},
        {"name": "Plus Fitness",     "price":  75.00},
        {"name": "F45 Training",     "price": 250.00},
        {"name": "BFT",              "price": 250.00},
        {"name": "ClassPass",        "price":  29.00},
        {"name": "Strava",           "price":  15.00},
        {"name": "Apple Fitness+",   "price":  14.99},
        {"name": "Peloton App",      "price":  17.00},
    ],
    "Delivery / Shopping": [
        {"name": "Uber One",                  "price":  9.99},
        {"name": "Amazon Prime Shopping",     "price":  9.99},
        {"name": "Amazon Prime Annual",       "price": 79.00},
        {"name": "DoorDash DashPass",         "price":  9.99},
        {"name": "Costco Gold Star",          "price": 65.00},
        {"name": "Costco Executive",          "price": 130.00},
        {"name": "eBay Plus",                 "price":  4.99},
        {"name": "Woolworths Everyday Extra", "price":  7.00},
        {"name": "Coles Plus Saver",          "price":  7.00},
        {"name": "OnePass",                   "price":  4.00},
    ],
    "Tech / Cloud / Security": [
        {"name": "iCloud+ 50GB",         "price":  1.49},
        {"name": "iCloud+ 200GB",        "price":  4.49},
        {"name": "iCloud+ 2TB",          "price": 14.99},
        {"name": "Google One 100GB",     "price":  2.49},
        {"name": "Google One 200GB",     "price":  4.39},
        {"name": "Google One 2TB",       "price": 12.49},
        {"name": "NordVPN",              "price":  5.00},
        {"name": "ExpressVPN",           "price": 20.00},
        {"name": "Surfshark VPN",        "price":  5.00},
        {"name": "1Password Individual", "price":  8.00},
        {"name": "1Password Families",   "price": 13.00},
        {"name": "Bitwarden Premium",    "price": 15.00},
        {"name": "Dashlane Premium",     "price": 10.00},
    ],
    # Empty list means no predefined subscriptions user types a custom name
    "Extra / Other": [],
}

# Flat lists derived from the catalogue for use in dropdowns
CATEGORIES     = list(SUBSCRIPTION_OPTIONS.keys())
BILLING_CYCLES = ["Monthly", "Yearly", "Weekly", "Quarterly"]
FILTER_OPTIONS = ["All Categories"] + CATEGORIES


def _sub_names_for_category(category):
    # Returns a list of subscription names for the given category
    return [s["name"] for s in SUBSCRIPTION_OPTIONS.get(category, [])]


def _default_price_for(category, name):
    # Returns the AUD price for a known subscription, or None if not found
    for s in SUBSCRIPTION_OPTIONS.get(category, []):
        if s["name"] == name:
            return s["price"]
    return None


# Main application class

class SubtotalApp:

    def __init__(self, root):
        # Set up the main window and open the login page
        self.root = root
        self.root.title("SUBTOTAL: Subscription Budgeter")
        self.root.geometry("1380x880")
        self.root.minsize(1100, 720)
        self.root.configure(fg_color=BG)
        _setup_ttk_style()
        self.current_user     = None
        self._filter_category = "All Categories"
        self.show_login()

    def clear(self):
        # Removes all widgets from the window before loading a new page
        for w in self.root.winfo_children():
            w.destroy()

    # Top navigation bar

    def _topbar(self, back_cmd=None):
        # Builds the top bar with the app logo, optional back button, and logout
        bar = ctk.CTkFrame(self.root, fg_color=CARD, height=54, corner_radius=0)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.pack(side="left", padx=18, fill="y")

        # Show a back button only when navigating away from the dashboard
        if back_cmd:
            _btn(left, "← Back", back_cmd, width=96, height=32).pack(
                side="left", padx=(0, 14), pady=11)

        ctk.CTkLabel(left, text="Σ SUBTOTAL",
                      font=("Arial", 17, "bold"),
                      text_color=RED,
                      fg_color="transparent").pack(side="left", pady=11)

        # Show the username and logout button when a user is logged in
        if self.current_user:
            right = ctk.CTkFrame(bar, fg_color="transparent")
            right.pack(side="right", padx=18, fill="y")
            ctk.CTkLabel(right,
                          text=f"👤  {self.current_user['username']}",
                          font=("Arial", 12), text_color=MUTED,
                          fg_color="transparent").pack(side="left", padx=10, pady=11)
            _btn(right, "Logout", self._logout, width=86, height=30).pack(
                side="left", pady=11)

    def _logout(self):
        # Clears the current user session and returns to the login page
        self.current_user = None
        self.show_login()

    # Stat card widget used on both Dashboard and Report pages

    def _stat_card(self, parent, label, value, col):
        # Creates a dark card displaying a single statistic (label + value)
        card = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=12,
                             border_width=1, border_color=BORDER)
        card.grid(row=0, column=col, sticky="ew", padx=5, pady=4)
        ctk.CTkLabel(card, text=label,
                      font=("Arial", 10), text_color=MUTED,
                      fg_color="transparent").pack(anchor="w", padx=14, pady=(12, 0))
        # Display the value in bright red to make it stand out
        ctk.CTkLabel(card, text=value,
                      font=("Arial", 21, "bold"), text_color=RED,
                      fg_color="transparent").pack(anchor="w", padx=14, pady=(2, 12))

    # Page: Login                                

    def show_login(self):
        # Displays the login page with username and password fields
        self.clear()
        self.root.bind("<Return>", lambda _: self._handle_login())

        outer = ctk.CTkFrame(self.root, fg_color=BG)
        outer.pack(expand=True, fill="both")

        # Centre the login card in the middle of the window
        card = ctk.CTkFrame(outer, fg_color=CARD, corner_radius=18,
                             border_width=1, border_color=BORDER,
                             width=460, height=490)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        # App logo and tagline at the top of the card
        ctk.CTkLabel(card, text="Σ", font=("Arial", 46, "bold"),
                      text_color=ACCENT, fg_color="transparent").pack(pady=(28, 0))
        _lbl(card, "SUBTOTAL", 22, bold=True).pack()
        _lbl(card, "Track every subscription. Spend smarter.", 12, muted=True
             ).pack(pady=(4, 24))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=32)

        # Username input field
        _lbl(inner, "Username", 12).pack(anchor="w")
        self._login_user = _entry(inner, width=396, height=42)
        self._login_user.pack(pady=(4, 12))

        # Password input field   characters are hidden with asterisks
        _lbl(inner, "Password", 12).pack(anchor="w")
        self._login_pw = _entry(inner, show="*", width=396, height=42)
        self._login_pw.pack(pady=(4, 0))

        bf = ctk.CTkFrame(card, fg_color="transparent")
        bf.pack(fill="x", padx=32, pady=(20, 8))
        _btn(bf, "Login", self._handle_login, style="accent",
             width=396, height=46, big=True).pack(pady=(0, 8))
        _link_btn(bf, "Don't have an account?  Sign Up", self.show_register).pack()

        self._login_user.focus()

    def _handle_login(self):
        # Secret easter egg   type bfdi / battle for dream island to trigger it
        if (self._login_user.get().strip() == "bfdi" and
                self._login_pw.get() == "battle for dream island"):
            self.root.unbind("<Return>")
            self.show_easter_egg_page()
            return

        # Validates credentials against the database and loads the dashboard
        user = db.check_login(self._login_user.get().strip(), self._login_pw.get())
        if not user:
            messagebox.showerror("Login Failed", "Invalid username or password.")
            return
        self.current_user = user
        self.root.unbind("<Return>")
        self.show_dashboard()

    def show_easter_egg_page(self):
        # Secret BFDI page   only reachable via the hidden login credentials
        self.clear()

        outer = ctk.CTkFrame(self.root, fg_color="#1a1a2e")
        outer.pack(expand=True, fill="both")

        # Load the easter egg image from the assets folder
        img_path = os.path.join("assets", "easter_egg.png")
        try:
            from PIL import Image, ImageTk
            img = Image.open(img_path)
            img = img.resize((520, 520), Image.LANCZOS)
            # Keep a reference on self so the image isn't garbage collected
            self._easter_img = ImageTk.PhotoImage(img)
        except Exception:
            # Fall back to built-in PhotoImage if Pillow isn't installed
            self._easter_img = tk.PhotoImage(file=img_path)

        tk.Label(outer, image=self._easter_img, bg="#1a1a2e").pack(pady=(60, 10))
        tk.Label(outer, text="you found the secret :)",
                  font=("Arial", 18, "bold"),
                  bg="#1a1a2e", fg="#f5c518").pack(pady=(0, 6))
        tk.Label(outer, text="battle for dream island!!",
                  font=("Arial", 13),
                  bg="#1a1a2e", fg="#aaaaaa").pack(pady=(0, 24))

        # Back button returns the user to the normal login page
        tk.Button(outer, text="← go back",
                   command=self.show_login,
                   bg="#333355", fg="#f5c518",
                   activebackground="#555577", activeforeground="#ffffff",
                   relief="flat", font=("Arial", 13), cursor="hand2",
                   padx=18, pady=8).pack()

    # Page: Register

    def show_register(self):
        # Displays the account creation page
        self.clear()
        self.root.bind("<Return>", lambda _: self._handle_register())

        outer = ctk.CTkFrame(self.root, fg_color=BG)
        outer.pack(expand=True, fill="both")

        card = ctk.CTkFrame(outer, fg_color=CARD, corner_radius=18,
                             border_width=1, border_color=BORDER,
                             width=460, height=450)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        ctk.CTkLabel(card, text="Σ", font=("Arial", 40, "bold"),
                      text_color=ACCENT, fg_color="transparent").pack(pady=(24, 0))
        _lbl(card, "Create Account", 20, bold=True).pack()
        _lbl(card, "Start tracking your subscriptions.", 12, muted=True
             ).pack(pady=(4, 22))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=32)

        # Username and password fields for the new account
        _lbl(inner, "Username", 12).pack(anchor="w")
        self._reg_user = _entry(inner, width=396, height=42)
        self._reg_user.pack(pady=(4, 12))

        _lbl(inner, "Password", 12).pack(anchor="w")
        self._reg_pw = _entry(inner, show="*", width=396, height=42)
        self._reg_pw.pack(pady=(4, 0))

        bf = ctk.CTkFrame(card, fg_color="transparent")
        bf.pack(fill="x", padx=32, pady=(20, 8))
        _btn(bf, "Create Account", self._handle_register, style="accent",
             width=396, height=46, big=True).pack(pady=(0, 8))
        _link_btn(bf, "← Back to Login", self.show_login).pack()

        self._reg_user.focus()

    def _handle_register(self):
        # Validates the form and creates a new user account in the database
        username = self._reg_user.get().strip()
        password = self._reg_pw.get()
        if not username or not password:
            messagebox.showerror("Error", "Username and password are required.")
            return
        if len(password) < 4:
            messagebox.showerror("Error", "Password must be at least 4 characters.")
            return
        ok, err = db.register_user(username, password)
        if ok:
            messagebox.showinfo("Account Created",
                                 f"Welcome, {username}!\nYou can now log in.")
            self.root.unbind("<Return>")
            self.show_login()
        else:
            messagebox.showerror("Registration Failed", err)

    # Page: Dashboard

    def show_dashboard(self):
        # Main page shown after login   displays stats, filters, and the subscription table
        self.clear()
        self._topbar()

        # Title row with quick-access buttons for adding and reporting
        title_row = ctk.CTkFrame(self.root, fg_color="transparent")
        title_row.pack(fill="x", padx=20, pady=(14, 0))
        _lbl(title_row, "Dashboard", 22, bold=True).pack(side="left")
        _btn(title_row, "+ Add Subscription", self.show_add,
             style="accent", width=172, height=36).pack(side="right")
        _btn(title_row, "📊  Spending Report", self.show_report,
             width=160, height=36).pack(side="right", padx=8)

        # Calculate totals from the database for the stat cards
        totals = db.get_totals(self.current_user["id"])
        # Weekly is derived from monthly: monthly × 12 ÷ 52
        weekly = round(totals["monthly"] * 12 / 52, 2)

        # Row of 5 stat cards showing key spending figures
        stats = ctk.CTkFrame(self.root, fg_color="transparent")
        stats.pack(fill="x", padx=20, pady=(10, 0))
        self._stat_card(stats, "Weekly Total",  f"${weekly:.2f}",               0)
        self._stat_card(stats, "Monthly Total", f"${totals['monthly']:.2f}",    1)
        self._stat_card(stats, "Yearly Total",  f"${totals['yearly']:.2f}",     2)
        self._stat_card(stats, "Subscriptions", str(totals["count"]),           3)
        self._stat_card(stats, "Daily Cost",    f"${totals['monthly']/30:.2f}", 4)
        # Make each card column stretch equally across the row
        for i in range(5):
            stats.grid_columnconfigure(i, weight=1)

        # Category filter row   lets the user narrow the table by category
        filter_row = ctk.CTkFrame(self.root, fg_color="transparent")
        filter_row.pack(fill="x", padx=20, pady=(10, 4))
        _lbl(filter_row, "Filter by Category:", 12, muted=True).pack(
            side="left", padx=(0, 8))
        self._filter_cb = _combo_ro(filter_row, FILTER_OPTIONS, width=240, height=34,
                                     command=self._apply_filter)
        # Restore the last selected filter state when the page reloads
        self._filter_cb.set(self._filter_category)
        self._filter_cb.pack(side="left")
        _btn(filter_row, "Clear", self._clear_filter, width=76, height=34).pack(
            side="left", padx=8)

        # Subscription table card   takes up the remaining space on the page
        table_wrap = ctk.CTkFrame(self.root, fg_color=CARD, corner_radius=10,
                                   border_width=1, border_color=BORDER)
        table_wrap.pack(fill="both", expand=True, padx=20, pady=(4, 4))

        cols   = ("Name", "Category", "Cost", "Billing", "Monthly equiv.",
                  "Start Date", "End Date", "Notes")
        widths = (175, 130, 86, 100, 126, 98, 98, 165)
        self._dash_table = _make_table(table_wrap, cols, widths)
        # Double-clicking a row opens the Edit Subscription page
        self._dash_table.bind("<Double-1>", self._on_dash_double_click)
        self._reload_dash_table()

        # Action buttons below the table
        btn_row = ctk.CTkFrame(self.root, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(4, 12))
        _btn(btn_row, "✏  Edit Selected",   self._edit_selected,
             width=148, height=34).pack(side="left", padx=(0, 8))
        _btn(btn_row, "🗑  Delete Selected", self._delete_selected,
             style="danger", width=148, height=34).pack(side="left")
        _btn(btn_row, "⟳  Refresh",         self._reload_dash_table,
             width=96, height=34).pack(side="right")

    def _apply_filter(self, value=None):
        # Updates the active filter category and refreshes the table
        self._filter_category = value if value else self._filter_cb.get()
        self._reload_dash_table()

    def _clear_filter(self):
        # Resets the category filter back to showing all subscriptions
        self._filter_category = "All Categories"
        self._filter_cb.set("All Categories")
        self._reload_dash_table()

    def _reload_dash_table(self, *_):
        # Clears and repopulates the table, applying the active category filter
        for row in self._dash_table.get_children():
            self._dash_table.delete(row)
        subs = db.get_subscriptions(self.current_user["id"])
        # Only show subscriptions that match the selected category filter
        if self._filter_category and self._filter_category != "All Categories":
            subs = [s for s in subs if s["category"] == self._filter_category]
        for s in subs:
            # Convert cost to monthly equivalent for easy comparison
            monthly = db.to_monthly(s["cost"], s["billing_cycle"])
            self._dash_table.insert("", "end", iid=str(s["id"]), values=(
                s["name"],
                s["category"],
                f"${s['cost']:.2f}",
                s["billing_cycle"],
                f"${monthly:.2f}/mo",
                s.get("start_date") or " ",
                s.get("end_date")   or " ",
                s["notes"] or "",
            ))

    def _get_selected_sub_id(self):
        # Returns the database ID of the currently selected table row
        sel = self._dash_table.focus()
        if not sel:
            messagebox.showerror("No Selection", "Please click on a subscription first.")
            return None
        return int(sel)

    def _on_dash_double_click(self, _event):
        # Opens the Edit page when the user double-clicks a table row
        sub_id = self._get_selected_sub_id()
        if sub_id:
            self.show_edit(sub_id)

    def _edit_selected(self):
        # Opens the Edit page for the currently highlighted subscription
        sub_id = self._get_selected_sub_id()
        if sub_id:
            self.show_edit(sub_id)

    def _delete_selected(self):
        # Asks for confirmation then deletes the selected subscription
        sub_id = self._get_selected_sub_id()
        if not sub_id:
            return
        sub = db.get_subscription(sub_id, self.current_user["id"])
        if not sub:
            return
        if messagebox.askyesno("Delete",
                                f"Delete '{sub['name']}'?\nThis cannot be undone."):
            db.delete_subscription(sub_id, self.current_user["id"])
            self._reload_dash_table()

    # Shared form builder   used by both Add and Edit pages

    def _build_sub_form(self, parent, prefill=None):
        # Builds the subscription form fields and wires up the dynamic callbacks
        ff = ctk.CTkFrame(parent, fg_color="transparent")
        ff.pack(fill="x", padx=36, pady=(0, 4))

        def field_row(label_text):
            # Creates a labelled row container for each form field
            row = ctk.CTkFrame(ff, fg_color="transparent")
            row.pack(fill="x", pady=5)
            ctk.CTkLabel(row, text=label_text,
                          font=("Arial", 12), text_color=MUTED,
                          fg_color="transparent",
                          width=168, anchor="w").pack(side="left")
            return row

        # Category dropdown   read-only, drives the subscription name list
        cat_cb = _combo_ro(field_row("Category *"), CATEGORIES, width=430, height=38)
        cat_cb.pack(side="left")

        # Subscription Name   editable CTkComboBox styled to match other fields
        # The user can pick from the list or type a custom name
        name_cb = _combo_edit(field_row("Subscription Name *"), [], width=430, height=38)
        name_cb.pack(side="left")

        # Cost field   auto-fills when a known subscription is selected
        r2 = field_row("Cost ($) *")
        cost_entry = _entry(r2, width=430, height=38)
        cost_entry.pack(side="left")

        # Billing Cycle dropdown   read-only selection
        cycle_cb = _combo_ro(field_row("Billing Cycle *"), BILLING_CYCLES,
                              width=430, height=38)
        cycle_cb.pack(side="left")

        # Optional date and notes fields
        r4 = field_row("Start Date")
        start_entry = _entry(r4, width=430, height=38)
        start_entry.pack(side="left")

        r5 = field_row("End Date")
        end_entry = _entry(r5, width=430, height=38)
        end_entry.pack(side="left")

        r6 = field_row("Notes")
        notes_entry = _entry(r6, width=430, height=38)
        notes_entry.pack(side="left")

        # Dynamic callbacks

        def refresh_names(cat_value=None):
            # Loads subscription names for the selected category into the name dropdown
            cat   = cat_value if cat_value is not None else cat_cb.get()
            names = _sub_names_for_category(cat)
            # Update the name dropdown with the new list
            name_cb.configure(values=names if names else [""])
            if names:
                # Auto-select the first name and fill in its price
                name_cb.set(names[0])
                price = _default_price_for(cat, names[0])
                if price is not None:
                    cost_entry.delete(0, "end")
                    cost_entry.insert(0, str(price))
            else:
                # Extra / Other has no predefined names   blank both fields
                name_cb.set("")
                cost_entry.delete(0, "end")

        def autofill_cost(selected=None):
            # Auto-fills the cost field when a known subscription is picked from the list
            # If the name is custom (not in catalogue), cost is left unchanged
            name  = selected if selected is not None else name_cb.get()
            price = _default_price_for(cat_cb.get(), name)
            if price is not None:
                cost_entry.delete(0, "end")
                cost_entry.insert(0, str(price))

        # Wire category changes to refresh the name list
        cat_cb.configure(command=refresh_names)
        # Wire name selection to auto-fill cost   command= fires on dropdown pick
        name_cb.configure(command=autofill_cost)

        # Pre-fill saved values (edit mode) or set defaults (add mode)

        if prefill:
            # Restore the saved category, falling back to the first option if unknown
            saved_cat = prefill.get("category", CATEGORIES[0])
            cat_cb.set(saved_cat if saved_cat in CATEGORIES else CATEGORIES[0])
            # Populate name list for the restored category
            name_cb.configure(values=_sub_names_for_category(cat_cb.get()) or [""])
            name_cb.set(prefill.get("name", ""))
            cost_entry.delete(0, "end")
            cost_entry.insert(0, str(prefill.get("cost", "")))
            saved_cycle = prefill.get("billing_cycle", BILLING_CYCLES[0])
            cycle_cb.set(saved_cycle if saved_cycle in BILLING_CYCLES else BILLING_CYCLES[0])
            start_entry.insert(0, prefill.get("start_date") or "")
            end_entry.insert(0,   prefill.get("end_date")   or "")
            notes_entry.insert(0, prefill.get("notes")      or "")
        else:
            # New form   set first category and auto-fill its first subscription
            cat_cb.set(CATEGORIES[0])
            refresh_names(CATEGORIES[0])

        # Return widget references so the save function can read the values
        return {
            "category": cat_cb,
            "name":     name_cb,
            "cost":     cost_entry,
            "cycle":    cycle_cb,
            "start":    start_entry,
            "end":      end_entry,
            "notes":    notes_entry,
        }

    # Page: Add Subscription

    def show_add(self):
        # Displays the Add Subscription form centred in the window
        self.clear()
        self._topbar(back_cmd=self.show_dashboard)

        outer = ctk.CTkFrame(self.root, fg_color=BG)
        outer.pack(expand=True, fill="both")

        card = ctk.CTkFrame(outer, fg_color=CARD, corner_radius=16,
                             border_width=1, border_color=BORDER,
                             width=700, height=660)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        _lbl(card, "Add Subscription", 20, bold=True).pack(pady=(20, 2))
        _lbl(card, "Select a service or type a custom name.",
             12, muted=True).pack(pady=(0, 10))

        # Build the shared form   no prefill data means blank defaults
        w = self._build_sub_form(card, prefill=None)

        bf = ctk.CTkFrame(card, fg_color="transparent")
        bf.pack(pady=(14, 0))

        def save():
            # Reads all form fields, validates them, and saves to the database
            name  = w["name"].get().strip()
            cat   = w["category"].get()
            cost  = w["cost"].get().strip()
            cycle = w["cycle"].get()
            start = w["start"].get().strip()
            end   = w["end"].get().strip()
            notes = w["notes"].get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a Subscription Name.")
                return
            if not cost:
                messagebox.showerror("Error", "Cost is required.")
                return
            try:
                cost_val = float(cost)
                if cost_val < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Cost must be a valid number ≥ 0.")
                return
            # Save the new subscription to the SQLite database
            db.add_subscription(self.current_user["id"], name, cat,
                                  cost_val, cycle, start, end, notes)
            messagebox.showinfo("Saved", f"'{name}' added successfully.")
            self.show_dashboard()

        _btn(bf, "Save Subscription", save, style="accent",
             width=188, height=44, big=True).pack(side="left", padx=6)
        _btn(bf, "Cancel", self.show_dashboard,
             width=110, height=44).pack(side="left", padx=6)

    # Page: Edit Subscription

    def show_edit(self, sub_id):
        # Loads the existing subscription from the database and opens the edit form
        sub = db.get_subscription(sub_id, self.current_user["id"])
        if not sub:
            messagebox.showerror("Error", "Subscription not found.")
            return

        self.clear()
        self._topbar(back_cmd=self.show_dashboard)

        outer = ctk.CTkFrame(self.root, fg_color=BG)
        outer.pack(expand=True, fill="both")

        card = ctk.CTkFrame(outer, fg_color=CARD, corner_radius=16,
                             border_width=1, border_color=BORDER,
                             width=700, height=660)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        _lbl(card, "Edit Subscription", 20, bold=True).pack(pady=(20, 2))
        _lbl(card, f"Editing: {sub['name']}", 12, muted=True).pack(pady=(0, 10))

        # Build the shared form pre-filled with the subscription's saved values
        w = self._build_sub_form(card, prefill=sub)

        bf = ctk.CTkFrame(card, fg_color="transparent")
        bf.pack(pady=(14, 0))

        def save():
            # Reads the updated field values and writes them back to the database
            name  = w["name"].get().strip()
            cat   = w["category"].get()
            cost  = w["cost"].get().strip()
            cycle = w["cycle"].get()
            start = w["start"].get().strip()
            end   = w["end"].get().strip()
            notes = w["notes"].get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a Subscription Name.")
                return
            if not cost:
                messagebox.showerror("Error", "Cost is required.")
                return
            try:
                cost_val = float(cost)
                if cost_val < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Cost must be a valid number ≥ 0.")
                return
            # Update the existing subscription record in the database
            db.update_subscription(sub_id, self.current_user["id"],
                                    name, cat, cost_val, cycle, start, end, notes)
            messagebox.showinfo("Saved", "Changes saved.")
            self.show_dashboard()

        _btn(bf, "Save Changes", save, style="accent",
             width=188, height=44, big=True).pack(side="left", padx=6)
        _btn(bf, "Cancel", self.show_dashboard,
             width=110, height=44).pack(side="left", padx=6)

    # Page: Spending Report

    def show_report(self):
        # Displays the Spending Report with stat cards, a pie chart, and recommendations
        self.clear()
        self._topbar(back_cmd=self.show_dashboard)

        title_row = ctk.CTkFrame(self.root, fg_color="transparent")
        title_row.pack(fill="x", padx=20, pady=(14, 0))
        _lbl(title_row, "Spending Report", 22, bold=True).pack(side="left")

        # Load all data needed for the report from the database
        subs      = db.get_subscriptions(self.current_user["id"])
        totals    = db.get_totals(self.current_user["id"])
        breakdown = db.get_category_breakdown(self.current_user["id"])
        weekly    = round(totals["monthly"] * 12 / 52, 2)

        # 5 spending summary stat cards at the top of the report
        stats = ctk.CTkFrame(self.root, fg_color="transparent")
        stats.pack(fill="x", padx=20, pady=(10, 0))
        self._stat_card(stats, "Weekly Spend",  f"${weekly:.2f}",                           0)
        self._stat_card(stats, "Monthly Spend", f"${totals['monthly']:.2f}",                1)
        self._stat_card(stats, "Yearly Spend",  f"${totals['yearly']:.2f}",                 2)
        self._stat_card(stats, "Subscriptions", str(totals["count"]),                       3)
        self._stat_card(stats, "Daily Cost",
                         f"${totals['monthly']/30:.2f}" if totals["count"] else "$0.00",    4)
        for i in range(5):
            stats.grid_columnconfigure(i, weight=1)

        # Show a placeholder message if the user has no subscriptions yet
        if not subs:
            _lbl(self.root, "No subscriptions to report on yet.", 14, muted=True
                 ).pack(pady=40)
            return

        # Split the lower section into left (chart) and right (table + tips) panels
        panes = ctk.CTkFrame(self.root, fg_color="transparent")
        panes.pack(fill="both", expand=True, padx=20, pady=(10, 12))

        # Left panel: matplotlib pie chart
        left = ctk.CTkFrame(panes, fg_color=CARD, corner_radius=10,
                             border_width=1, border_color=BORDER)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        _lbl(left, "Spend by Category (monthly)", 11, muted=True).pack(
            anchor="w", padx=12, pady=(10, 0))

        try:
            import matplotlib
            matplotlib.use("TkAgg")
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            import matplotlib.pyplot as plt

            # Dark red and grey colour palette to match the app theme
            PALETTE = ["#8b0000", "#b00020", "#d32f2f", "#ff3b3b", "#5a5a5a",
                        "#737373", "#9a9a9a", "#cfcfcf", "#3a3a3a", "#ffffff"]

            # Create the pie chart figure with a dark background
            fig, ax = plt.subplots(figsize=(4.2, 3.8), facecolor=CARD)
            ax.set_facecolor(CARD)
            labels = list(breakdown.keys())
            sizes  = list(breakdown.values())
            _, _texts, autotexts = ax.pie(
                sizes, labels=labels, autopct="%1.1f%%",
                colors=PALETTE[:len(labels)],
                textprops={"color": TEXT, "fontsize": 9},
                wedgeprops={"linewidth": 1.5, "edgecolor": BG},
                startangle=90,
            )
            # Make the percentage labels visible on the dark background
            for at in autotexts:
                at.set_color(TEXT)
            ax.axis("equal")
            fig.tight_layout()

            # Embed the matplotlib chart inside the Tkinter window
            canvas = FigureCanvasTkAgg(fig, master=left)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)
            plt.close(fig)
        except ImportError:
            _lbl(left,
                  "Install matplotlib to see charts:\npip install matplotlib",
                  12, muted=True).pack(expand=True, pady=20)

        # Right panel: category breakdown table and recommendations
        right = ctk.CTkFrame(panes, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        # Category breakdown table showing monthly cost and percentage per category
        cat_card = ctk.CTkFrame(right, fg_color=CARD, corner_radius=10,
                                 border_width=1, border_color=BORDER)
        cat_card.pack(fill="x", pady=(0, 8))
        _lbl(cat_card, "Category Breakdown", 12, bold=True).pack(
            anchor="w", padx=12, pady=(8, 4))
        cat_table = _make_table(cat_card,
                                 ("Category", "Monthly Cost", "% of Total"),
                                 (160, 130, 100))
        for cat, amt in breakdown.items():
            pct = f"{amt / totals['monthly'] * 100:.1f}%" if totals["monthly"] > 0 else "0%"
            cat_table.insert("", "end", values=(cat, f"${amt:.2f}", pct))

        # Recommendations panel   colour-coded tips based on cost and duplicates
        rec_card = ctk.CTkFrame(right, fg_color=CARD, corner_radius=10,
                                 border_width=1, border_color=BORDER)
        rec_card.pack(fill="both", expand=True)
        _lbl(rec_card, "Recommendations", 12, bold=True).pack(
            anchor="w", padx=12, pady=(8, 4))

        # Use a plain tk.Text widget so coloured tags can be applied per line
        rec_text = tk.Text(rec_card, bg=CARD2, fg=TEXT, font=("Arial", 11),
                            relief="flat", wrap="word",
                            highlightthickness=0, padx=12, pady=8)
        rec_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Generate a recommendation line for each subscription
        seen_cats = {}
        for s in subs:
            monthly = db.to_monthly(s["cost"], s["billing_cycle"])
            cat = s["category"]
            if cat in seen_cats:
                line = (f"⚠  {s['name']}: Same category as '{seen_cats[cat]}'. "
                         f"Possible duplicate.\n\n")
                tag  = "warn"
            elif monthly > 30:
                line = (f"⚠  {s['name']}: High cost (${monthly:.2f}/mo). "
                         f"Check for cheaper alternatives.\n\n")
                tag  = "warn"
            elif monthly > 15:
                line = (f"ℹ  {s['name']}: Moderate cost. "
                         f"Make sure you use this regularly.\n\n")
                tag  = "info"
            else:
                line = (f"✓  {s['name']}: Good value at ${monthly:.2f}/mo. "
                         f"Keep this subscription.\n\n")
                tag  = "good"
            rec_text.insert("end", line, tag)
            # Track the first subscription per category to detect duplicates
            seen_cats.setdefault(cat, s["name"])

        # Apply colour tags to each recommendation type
        rec_text.tag_config("warn", foreground=WARNING)
        rec_text.tag_config("info", foreground=TEXT)
        rec_text.tag_config("good", foreground=SUCCESS)
        # Make the text read-only so the user cannot accidentally edit it
        rec_text.config(state="disabled")
