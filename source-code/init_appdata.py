from appdirs import *
import os


name = "app-1.0"
author = "HomeLoanCalculatorbyJackYeo"
appdata_folder = user_data_dir(name, author).replace("\\", "/")

if not os.path.exists(appdata_folder):
    os.makedirs(appdata_folder)
