import sqlite3
from init_appdata import appdata_folder


conn = sqlite3.connect(f"{appdata_folder}/results.sqlite", check_same_thread=False)
cur = conn.cursor()

sql = """
        CREATE TABLE IF NOT EXISTS Result (
            resultId INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            dateCreated DATETIME NOT NULL
        );
        """

cur.executescript(sql)
conn.commit()
