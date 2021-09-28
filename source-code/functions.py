# import statements
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from functools import partial
from datetime import datetime
from threading import Thread
import webbrowser
from dbh import conn, cur
import os
import json
from init_appdata import appdata_folder


# initialize global variables for later use
first_calculated = False
theme = None
dummy_home = None
dummy_calc_page = None
loading = None


# check if json theme file is invalid, because there's a possibility where user can edit the theme json file
def check_theme_json_file():
    if os.path.isfile(f"{appdata_folder}/theme.json"):
        with open(f"{appdata_folder}/theme.json", "r") as theme_json_file:
            try:
                theme = json.load(theme_json_file)["theme"]
                if theme in ["dark", "light"]:
                    return True
            except (json.decoder.JSONDecodeError, KeyError) as e:
                pass
    return False


# just a function to change the global variable 'theme' here
def update_theme(current_theme):
    global theme
    theme = current_theme


# toggle dark theme on/off
def change_theme(master):
    # NOTE: The theme's real name is sun-valley-<mode>
    if master.call("ttk::style", "theme", "use") == "sun-valley-dark":
        # Set light theme
        theme = "light"
    else:
        # Set dark theme
        theme = "dark"
    master.call("set_theme", theme)

    if check_theme_json_file():
        with open(f"{appdata_folder}/theme.json", "r") as jsonFile:
            data = json.load(jsonFile)
        data["theme"] = theme
    else:
        data = {"theme": theme}
    with open(f'{appdata_folder}/theme.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    update_theme(theme)


# function to calculate monthly repayment
def calc_monthly_repayment(principal, monthly_interest_rate, number_of_payment):
    try:
        return principal * (monthly_interest_rate + (monthly_interest_rate / ((1 + monthly_interest_rate) ** number_of_payment - 1)))
    except OverflowError:
        return "Overflow error: Result is too large!"


# function to check if value is float or not
def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


# function to center the tkinter windows
def center(window):
    window.update_idletasks()
    app_width = window.winfo_width()
    app_height = window.winfo_height()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width / 2) - (app_width / 2)
    y = (screen_height / 2) - (app_height / 2)
    window.geometry(f"{app_width}x{app_height}+{int(x)}+{int(y)}")


# limit the number of character that can be inputted into the entry boxes
def character_limit(entry_text, mode):
    if len(entry_text.get()) > 0:
        if mode == "check_rm":
            entry_text.set(entry_text.get()[-13:])
        if mode == "check_cent" or mode == "check_month":
            entry_text.set(entry_text.get()[-2:])
        if mode == "check_percentage":
            entry_text.set(entry_text.get()[-10:])
        if mode == "check_year":
            entry_text.set(entry_text.get()[-3:])


# when the entrybox for loan amount cent is focused
def cent_focused_in(event, cent):
    if cent.get() == "00":
        cent.set("")

# when the # when the entrybox for loan amount cent is un-focused
def cent_focused_out(event, cent):
    if cent.get() == "":
        cent.set("00")
    elif len(cent.get()) == 1:
        cent.set(cent.get() + "0")


# when the entrybox for period month is focused
def month_focused_in(event, month):
    if month.get() == "0":
        month.set("")

# when the entrybox for period month is un-focused
def month_focused_out(event, month):
    if month.get() == "" or int(month.get()) == 0:
        month.set("0")

# when the entrybox for down payment rate is focused
def down_payment_rate_focused_in(event, down_payment_rate):
    if down_payment_rate.get() == "0":
        down_payment_rate.set("")

# when the entrybox for down payment rate is un-focused
def down_payment_rate_focused_out(event, down_payment_rate):
    if down_payment_rate.get() == "" or float(down_payment_rate.get()) == 0:
        down_payment_rate.set("0")


# a function to limit only numbers in entrybox
def num_only(P, month_mode=False):
    if str.isdigit(P) or P == "":
        if month_mode:
            if P != "":
                if int(P) < 12:
                    return True
                else:
                    return False
            else:
                return True
        else:
            return True
    else:
        return False

# a function to limit only legit rates in entrybox: x must be float and less then 100
def rate_legit(P):
    if isfloat(P) or P == "":
        try:
            if float(P) < 100:
                return True
            else:
                return False
        except ValueError:
            return True
    else:
        return False


# when user presses enter or click to submit
def submit(event, home, master, result_button, entries, dummy):
    global first_calculated

    # check if all required entrybox is filled
    for i in range(len(entries)):
        if entries[i].name == "property price cent" or entries[i].name == "period month" or entries[i].name == "down payment rate":
            master.focus()  # just to set the focus to somewhere else, in this case the window, just so that the "00" or "0" can appear
        else:
            if entries[i].get() == "" or float(entries[i].get()) == 0:
                entries[i].delete(0, END)
                messagebox.showerror("Incomplete Form!", f"Please enter your {entries[i].name}!", parent=master)
                entries[i].focus()
                return  # terminate the function

    # store the input datas in a dictionary
    input_datas = {}
    for i in range(len(entries)):
        input_datas[entries[i].name] = entries[i].get()

    # fetching the inputs to variables
    property_price = float(input_datas['property price'] + "." + input_datas['property price cent'])
    down_payment_rate = float(input_datas['down payment rate'])
    down_payment = property_price * down_payment_rate / 100
    loan_amount = property_price * (1 - down_payment_rate / 100)
    interest_rate = float(input_datas['interest rate']) / 100
    period = int(input_datas['period year']) * 12 + int(input_datas['period month'])
    monthly_interest_rate = interest_rate / 12

    # results
    monthly_repayment = calc_monthly_repayment(loan_amount, monthly_interest_rate, period)
    if isinstance(monthly_repayment, str):  # meaning that error message is returned, which is the overflow error
        result_button['text'] = monthly_repayment   # show the error message
        dummy['text'] = ""
    else:
        if first_calculated:    # means not first time already
            # check if user calculated the same thing within 1 min to prevent spam
            cur.execute("SELECT * FROM Result WHERE resultId = (SELECT max(resultId) FROM Result);")
            data = cur.fetchone()
            if data is not None:    # means database not empty
                if not (f'{property_price} {down_payment} {interest_rate} {period} {monthly_repayment}' == data[1] and (datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S') - datetime.strptime(data[2], '%Y-%m-%d %H:%M:%S')).seconds < 60):
                    cur.executescript(f"INSERT INTO Result (data, dateCreated) VALUES ('{property_price} {down_payment} {interest_rate} {period} {monthly_repayment}', '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}')")
                    conn.commit()
                else:
                    return      # do nothing if user calculated the same thing within 1 minute
            else:   # means database is empty
                cur.executescript(f"INSERT INTO Result (data, dateCreated) VALUES ('{property_price} {down_payment} {interest_rate} {period} {monthly_repayment}', '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}')")
                conn.commit()
        
        else:   # means first time calculating after opening calculator window
            cur.executescript(f"INSERT INTO Result (data, dateCreated) VALUES ('{property_price} {down_payment} {interest_rate} {period} {monthly_repayment}', '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}')")
            conn.commit()
            first_calculated = True

        result_button['text'] = "Monthly Repayment: " + format(monthly_repayment, "0.02f")
        dummy['text'] = "Click for more details"

        result_button.bind("<Button-1>", partial(see_result_details, home=home, master=master, id=cur.execute("SELECT max(resultId) FROM Result;").fetchone()[0]))    # maybe need to bind param in the future, for now just leave it as it is first


# start the thread to launch chrome to see result details
def see_result_details(event, home, master, id):
    threading(home, master, id)


# button at home page: command functions
def calculator(home):
    def calc_page_callback():  # upon closing calculator page
        global first_calculated
        home.deiconify()
        calc_page.destroy()
        first_calculated = False

    home.withdraw()

    calc_page = Toplevel()
    calc_page.iconbitmap("./includes/icons/iphone-calculator-icon.ico")
    calc_page.title('Home Loan Calculator')
    calc_page.geometry("500x540")
    calc_page.resizable(0, 0)
    calc_page.protocol("WM_DELETE_WINDOW", calc_page_callback)

    # initialise result label first for later use
    result = ttk.Label(calc_page, text="", font=("-family", 'Bahnschrift SemiLight', "-size", 16), foreground="#38f21f")
    dummy = ttk.Label(calc_page, text="", font=("-family", 'Bahnschrift SemiLight', "-size", 10))

    # validatecommand functions for entry boxes
    numonly_vcmd = calc_page.register(num_only)
    rate_vcmd = calc_page.register(rate_legit)

    # widgets
    # label frames
    property_price_frame = ttk.LabelFrame(calc_page, text="Property Price", padding=(20, 10))
    down_payment_rate_frame = ttk.LabelFrame(calc_page, text="Down Payment", padding=(0, 10))
    interest_rate_frame = ttk.LabelFrame(calc_page, text="Interest rate", padding=(0, 10))
    period_frame = ttk.LabelFrame(calc_page, text="Period", padding=(0, 10))

    # stringvars
    property_price_rm = StringVar()
    property_price_cent = StringVar(value="00")
    down_payment_rate = StringVar(value="0")
    interest_rate = StringVar()
    period_year = StringVar()
    period_month = StringVar(value="0")

    # limit the character length in entry boxes with character_limit()
    property_price_rm.trace("w", lambda *args: character_limit(property_price_rm, mode="check_rm"))
    property_price_cent.trace("w", lambda *args: character_limit(property_price_cent, mode="check_cent"))
    interest_rate.trace("w", lambda *args: character_limit(interest_rate, mode="check_percentage"))
    period_year.trace("w", lambda *args: character_limit(period_year, mode="check_year"))
    period_month.trace("w", lambda *args: character_limit(period_month, mode="check_month"))

    # instruction
    ttk.Label(calc_page, text="Press Enter or click to calculate.", font=("-family", 'Bahnschrift SemiLight', "-size", 16), foreground="#38f21f").pack(pady=20)
    property_price_frame.pack()
    down_payment_rate_frame.pack()
    interest_rate_frame.pack()
    period_frame.pack()

    # property price
    ttk.Label(property_price_frame, text="RM: ", font=('-family', 'Bahnschrift SemiLight', '-size', 16)).pack(side="left")
    property_price_rm_entry = ttk.Entry(property_price_frame, width=13, textvariable=property_price_rm, validate='all', validatecommand=(numonly_vcmd, '%P'))
    property_price_rm_entry.pack(side="left")
    ttk.Label(property_price_frame, text=".", font=('-family', 'Bahnschrift SemiLight', '-size', 16)).pack(side="left")
    property_price_cent_entry = ttk.Entry(property_price_frame, width=2, textvariable=property_price_cent, validate='all', validatecommand=(numonly_vcmd, '%P'))
    property_price_cent_entry.pack()

    # down payment rate
    down_payment_rate_entry = ttk.Entry(down_payment_rate_frame, width=10, textvariable=down_payment_rate, validate='all', validatecommand=(rate_vcmd, '%P'))
    down_payment_rate_entry.pack(side="left", padx=(23, 0))
    ttk.Label(down_payment_rate_frame, text="%", font=('-family', 'Bahnschrift SemiLight', '-size', 16)).pack(padx=(3, 102))

    # interest rate
    interest_rate_entry = ttk.Entry(interest_rate_frame, width=10, textvariable=interest_rate, validate='all', validatecommand=(rate_vcmd, '%P'))
    interest_rate_entry.pack(side="left", padx=(23, 0))
    ttk.Label(interest_rate_frame, text="%", font=('-family', 'Bahnschrift SemiLight', '-size', 16)).pack(padx=(3, 102))

    # period (year and month)
    period_year_entry = ttk.Entry(period_frame, width=3, textvariable=period_year, validate='all', validatecommand=(numonly_vcmd, '%P'))
    period_year_entry.pack(side="left", padx=(23, 0))
    ttk.Label(period_frame, text="year", font=('-family', 'Bahnschrift SemiLight', '-size', 16)).pack(side="left", padx=3)
    period_month_entry = ttk.Entry(period_frame, width=3, textvariable=period_month, validate='all', validatecommand=(numonly_vcmd, '%P', True))
    period_month_entry.pack(side="left")
    ttk.Label(period_frame, text="month", font=('-family', 'Bahnschrift SemiLight', '-size', 16)).pack(padx=(3, 18))

    # set the extra attribute 'name' for each entry box for the use of showing erros in submit()
    property_price_rm_entry.name = "property price"
    property_price_cent_entry.name = "property price cent"
    down_payment_rate_entry.name = "down payment rate"
    interest_rate_entry.name = "interest rate"
    period_year_entry.name = "period year"
    period_month_entry.name = "period month"

    # list of entries
    entries = [property_price_rm_entry, property_price_cent_entry, down_payment_rate_entry, interest_rate_entry, period_year_entry, period_month_entry]
    # bind the entry boxes with the "press enter" event that triggers the submit function
    for entry in entries:
        entry.bind("<Return>", partial(submit, home=home, master=calc_page, result_button=result, entries=entries, dummy=dummy))  # bind submit() with all entry boxes

    # what happens when the entry boxes are focused in or out
    property_price_cent_entry.bind("<FocusIn>", partial(cent_focused_in, cent=property_price_cent))
    property_price_cent_entry.bind("<FocusOut>", partial(cent_focused_out, cent=property_price_cent))
    period_month_entry.bind("<FocusIn>", partial(month_focused_in, month=period_month))
    period_month_entry.bind("<FocusOut>", partial(month_focused_out, month=period_month))
    down_payment_rate_entry.bind("<FocusIn>", partial(down_payment_rate_focused_in, down_payment_rate=down_payment_rate))
    down_payment_rate_entry.bind("<FocusOut>", partial(down_payment_rate_focused_out, down_payment_rate=down_payment_rate))

    # pack the label frames
    property_price_frame.pack(pady=10)
    down_payment_rate_frame.pack(pady=10)
    interest_rate_frame.pack(pady=10)
    period_frame.pack(pady=10)

    # submit button
    ttk.Button(calc_page, text="Calculate", command=partial(submit, event=None, home=home, master=calc_page, result_button=result, entries=entries, dummy=dummy), width=15, style="Accent.TButton").pack(pady=5)

    # results label
    result.pack()
    dummy.pack()

    # center the window when the widgets are loaded
    center(calc_page)

    # focuses the first entry box upon opening this window (calc_page)
    calc_page.after(200, lambda: property_price_rm_entry.focus_force())


# the function to start the results page in a thread
def threading(home, master=None, id=None):
    global dummy_home, dummy_calc_page, loading
    dummy_home = home
    if id is None:
        dummy_home.withdraw()
        thread = Thread(target=results, daemon=True)
    else:
        dummy_calc_page = master
        dummy_calc_page.withdraw()
        thread = Thread(target=partial(results, id), daemon=True)

    # loading screen while chrome is opening
    loading = Toplevel()
    loading.iconbitmap("./includes/icons/loading.ico")
    loading.title("Loading...")
    loading.geometry("300x150")
    loading.resizable(0, 0)
    def disable_close():
        pass
    loading.protocol("WM_DELETE_WINDOW", disable_close)
    ttk.Label(loading, text="Launching Chrome...", font=("-size", 15)).pack(padx=20, pady=20)
    progress = DoubleVar(value=25)
    progressbar = ttk.Progressbar(loading, value=0, variable=progress, mode="determinate")
    progressbar.pack(pady=(10, 20))
    def restart():
        if messagebox.askokcancel("Relaunch Chrome?", "Are you sure you want to relaunch Chrome?\n\nMake sure to relaunch Chrome only if you have problems like: \n\n- Chrome not showing up\n- Main page not showing up after Chrome is closed\n\nNOTE: To avoid problems stated above from happening again, you have to wait patiently for Chrome to load everytime. Do not rush things as the app may not be able to detect it.", parent=loading, icon="warning"):
            loading.destroy()
            threading(home, None if id is None else master, None if id is None else id)
    relaunch_chrome_button = ttk.Button(loading, text="Something's wrong, relaunch Chrome", command=restart, style="Accent.TButton", state="disabled")
    relaunch_chrome_button.pack()

    def update_progress(progress):
        from time import sleep
        while True:
            sleep(0.6)
            progress.set(progress.get() + 25)
    update_progress_bar = Thread(target=partial(update_progress, progress), daemon=True)
    update_progress_bar.start()

    def enable_relaunch_chrome(relaunch_button):
        from time import sleep
        sleep(10)
        try:
            relaunch_button['state'] = 'normal'
        except Exception:
            pass    # means do nothing since the loading window is gone already after the chrome window successfully loaded
    enable_relaunch_chrome_button = Thread(target=partial(enable_relaunch_chrome, relaunch_chrome_button), daemon=True)
    enable_relaunch_chrome_button.start()

    # center the loading screen
    center(loading)
    loading.after(200, lambda: loading.focus_force())

    thread.start()


# main function to start results page in Chrome
def results(id=None):
    from results import main
    if id is None:
        main()
    else:
        main(id)


def help(home):
    def help_page_callback():
        home.deiconify()
        help_page.destroy()

    home.withdraw()

    help_page = Toplevel()
    help_page.iconbitmap("./includes/icons/help.ico")
    help_page.title('Help')
    help_page.resizable(0, 0)
    help_page.geometry("500x280")
    help_page.protocol("WM_DELETE_WINDOW", help_page_callback)

    # widgets
    user_manual_frame = ttk.LabelFrame(help_page, text="Don't know how to use this app?", padding=(20, 10))
    def see_user_manual():
        webbrowser.open("https://github.com/jPRO-22/home-loan-calculator/tree/main#usage")
    ttk.Button(user_manual_frame, text="See the user manual", style="Accent.TButton", command=see_user_manual).pack()
    user_manual_frame.pack(pady=(20, 0))

    help_or_report_frame = ttk.LabelFrame(help_page, text="Need help or want to report a problem?", padding=(20, 10))
    def create_issue():
        webbrowser.open("https://github.com/jPRO-22/home-loan-calculator/issues")
    ttk.Button(help_or_report_frame, text="Create an issue at this project's Github repo", style="Accent.TButton", command=create_issue).pack()
    ttk.Label(help_or_report_frame, text="or").pack()
    def contact_author():
        webbrowser.open("mailto:superjackxh@gmail.com")
    ttk.Button(help_or_report_frame, text="Contact the author: superjackxh@gmail.com", style="Accent.TButton", command=contact_author).pack()
    help_or_report_frame.pack(pady=20)

    # center the window when the widgets are loaded
    center(help_page)

    help_page.after(200, lambda: help_page.focus_force())


def website():
    webbrowser.open("https://jpro-22.github.io/home-loan-calculator")


def about(home):
    messagebox.showinfo("About", "Home Loan Calculator\nAuthor: Jack Yeo\nVersion: 1.0.0\nBuilt with: Tkinter and Eel", parent=home)
