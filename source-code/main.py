# import statements
from tkinter import *
from tkinter import ttk
from functools import partial
import json
from functions import check_theme_json_file, center, calculator, threading, help, website, about, change_theme, update_theme
from init_appdata import appdata_folder


# home page
home = Tk()
home.iconbitmap('logo.ico')
home.title("Home Loan Calculator")
home.resizable(0, 0)

# this main frame is needed as a solution of theme changings in the sun valley theme: https://github.com/rdbende/Sun-Valley-ttk-theme#switching-themes
main_frame = ttk.Frame(home)
main_frame.pack(fill="both", expand=True, ipady=10)

# app name
ttk.Label(main_frame, text="Home Loan Calculator", font=("-family", "Segoe Print", "-size", 30),).grid(row=0, column=0, columnspan=2, padx=10)
ttk.Label(main_frame, text="by Jack Yeo", font=("-family", "Segoe Print", "-size", 15),).grid(row=1, column=0, columnspan=2)

# frame for main functions: calculator and results
home_frame = ttk.LabelFrame(main_frame, text="Home", padding=(20, 10))
home_frame.grid(row=2, column=0, padx=10, pady=5, sticky="e")

# about frame for about, link to website, and also help
about_frame = ttk.LabelFrame(main_frame, text="About", padding=(20, 10))
about_frame.grid(row=2, column=1, rowspan=2, padx=10, pady=5, sticky="w")

# settings frame for changing themes: light or dark mode
settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding=(20, 10))
settings_frame.grid(row=3, column=0, padx=10, pady=5, sticky="e")

# pack the widgets for home and about frame
ttk.Button(home_frame, text = "Calculator", command = partial(calculator, home), style="Accent.TButton").pack(pady=5)
ttk.Button(home_frame, text = "Results", command = partial(threading, home), style="Accent.TButton").pack(pady = 5)
ttk.Button(about_frame, text = "About", command = partial(about, home)).pack(pady = 5)
ttk.Button(about_frame, text = "Website", command = website).pack(pady = 5)
ttk.Button(about_frame, text = "Help", command = partial(help, home)).pack(pady = 5)

if check_theme_json_file():
    with open(f"{appdata_folder}/theme.json", "r") as theme_json_file:
        theme = json.load(theme_json_file)["theme"]
else:
    theme = "light"
update_theme(theme)
checked = BooleanVar(value=0 if theme == "light" else 1)
home.call("source", "sun-valley.tcl")
home.call("set_theme", theme)
# pack the dark mode checkbutton
ttk.Checkbutton(settings_frame, text="Dark theme", command=partial(change_theme, home), style="Switch.TCheckbutton", variable=checked).pack(pady=5)

# make all buttons' width 15
for widget in home_frame.winfo_children() + about_frame.winfo_children() + settings_frame.winfo_children():
    if isinstance(widget, ttk.Button):
        widget['width'] = 15

# center the window once home page when widgets are loaded
center(home)

home.mainloop()
