import eel
from dbh import cur, conn
from tkinter import *
from tkinter.filedialog import asksaveasfile
import uuid
from datetime import datetime
from functools import partial

results = None

is_reloaded = False

csv_content = None

eel.init('results')     # init results folder where the web page is

def close_callback(route, websockets, id=None):
    global is_reloaded
    
    if not websockets:
        if not is_reloaded:
            from functions import dummy_home, dummy_calc_page, loading
            loading.destroy()
            if id is None:
                dummy_home.deiconify()
                dummy_home.lift()
                dummy_home.attributes("-topmost", True)
                dummy_home.after_idle(dummy_home.attributes, "-topmost", False)
                dummy_home.update_idletasks()
            else:
                dummy_calc_page.deiconify()
                dummy_calc_page.lift()
                dummy_calc_page.attributes("-topmost", True)
                dummy_calc_page.after_idle(dummy_home.attributes, "-topmost", False)
                dummy_calc_page.update_idletasks()
    else:
        is_reloaded = False

@eel.expose
def loaded():
    from functions import loading
    loading.destroy()


@eel.expose
def reload():
    global is_reloaded
    is_reloaded = True
        

@eel.expose
def constructResultsTableContent(id=None):
    global results

    if id is None:
        table_content = ""

        for result in results:
            id = result[0]
            data = result[1].split(" ")
            time_created = result[2]

            table_content += f"""
                <div id="for-direct-details" class="row" onclick="seeDetails({data[0]}, {data[1]}, {data[2]}, {data[3]}, {data[4]})" data-id="{id}">
                    <div class="cell" data-title="Loan Amount (RM)">{format(float(data[0]) - float(data[1]), "0.02f")}</div>
                    <div class="cell" data-title="Interest Rate (%)">{float(data[2]) * 100}</div>
                    <div class="cell" data-title="Period (Month)">{data[3]}</div>
                    <div class="cell" data-title="Monthly Repayment (RM)">{format(float(data[4]), "0.02f")}</div>
                    <div class="cell" data-title="Time Created">{time_created}</div>
                </div>
            """

        return table_content
    else:
        return list(map(float, results[0][1].split(" ")))

    
@eel.expose
def constructTableContent(loan_amount, monthly_interest_rate, period, monthly_repayment):
    global csv_content

    # note: actually, we can straight away set the line chart's datas here in this function
    chart_period = [i for i in range(1, int(period) + 1)]
    chart_principal = []
    chart_interest = []
    chart_balance = []

    loan = loan_amount      # just for the use of the total principle message below...
    table_content = "<tbody>"   # initialise the table content with the starting body tag
    total_interest = 0

    csv_content = f"""Loan Amount: RM {loan_amount}
Interest: {format(monthly_interest_rate * 12 * 100, "0.02f")} %
Period: {period} month(s)
Monthly Repayment: RM {format(monthly_repayment, "0.02f")}\n\nPrincipal (RM),Monthly Interest (RM),Balance (RM)\n"""

    for i in range(1, int(period) + 1):
        monthly_interest = loan_amount * monthly_interest_rate
        total_interest = total_interest + monthly_interest
        principle = monthly_repayment - monthly_interest
        loan_amount -= principle
        
        # chart stuffs here
        chart_principal.append(float(format(principle, "0.02f")))
        chart_interest.append(float(format(monthly_interest, "0.02f")))
        chart_balance.append(float(format(loan_amount, "0.02f")) if i != int(period) else 0)

        csv_content += f'"=""{format(principle, "0.02f")}""","=""{format(monthly_interest, "0.02f")}""","=""{format(loan_amount, "0.02f") if i != int(period) else "0.00"}"""\n'

        table_content += f'<tr><td>{i}</td><td>{format(principle, "0.02f")}</td><td>{format(monthly_interest, "0.02f")}</td><td>{format(loan_amount, "0.02f") if i != int(period) else "0.00"}</td></tr>'
    else:
        table_content += f'<tr><td>Total</td><td>RM {loan}</td><td>RM {format(total_interest, "0.02f")}</td><td></td>'
        
        csv_content += f'Total principle: RM {loan}\nTotal interest: RM {format(total_interest, "0.02f")}\n\nGenerated at {datetime.now().strftime("%m/%d/%Y %H:%M:%S")} - Home Loan Calculator by Jack Yeo\n=HYPERLINK("https://jpro-22.github.io/home-loan-calculator")'

        return table_content, loan, total_interest, chart_period, chart_principal, chart_interest, chart_balance

@eel.expose
def exportCSV():
    global csv_content

    # w_csv = Toplevel()
    # w_csv.overrideredirect(True)
    # w_csv.geometry("0x0+0+0")
    # payment_schedule_csv = asksaveasfile(parent=w_csv, mode = "w", defaultextension = ".csv", initialfile = f"payment-schedule-{str(uuid.uuid4())}")
    # if payment_schedule_csv is None:
    #     w_csv.destroy()
    #     eel.enableCSVButton()
    #     return
    # w_csv.destroy()

    # get user computer downloads folder, for windows and for mac
    import os
    if os.name == 'nt':
        import ctypes
        from ctypes import windll, wintypes
        from uuid import UUID

        # ctypes GUID copied from MSDN sample code
        class GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", wintypes.DWORD),
                ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD),
                ("Data4", wintypes.BYTE * 8)
            ] 

            def __init__(self, uuidstr):
                uuid = UUID(uuidstr)
                ctypes.Structure.__init__(self)
                self.Data1, self.Data2, self.Data3, \
                    self.Data4[0], self.Data4[1], rest = uuid.fields
                for i in range(2, 8):
                    self.Data4[i] = rest>>(8-i-1)*8 & 0xff

        SHGetKnownFolderPath = windll.shell32.SHGetKnownFolderPath
        SHGetKnownFolderPath.argtypes = [
            ctypes.POINTER(GUID), wintypes.DWORD,
            wintypes.HANDLE, ctypes.POINTER(ctypes.c_wchar_p)
        ]

        def _get_known_folder_path(uuidstr):
            pathptr = ctypes.c_wchar_p()
            guid = GUID(uuidstr)
            if SHGetKnownFolderPath(ctypes.byref(guid), 0, 0, ctypes.byref(pathptr)):
                raise ctypes.WinError()
            return pathptr.value

        FOLDERID_Download = '{374DE290-123F-4565-9164-39C4925E467B}'

        def get_download_folder():
            return _get_known_folder_path(FOLDERID_Download)
    else:
        def get_download_folder():
            home = os.path.expanduser("~")
            return os.path.join(home, "Downloads")

    csv_file_code = str(uuid.uuid4())
    with open(f"{get_download_folder()}\payment-schedule-{csv_file_code}.csv",  "w") as f:
        f.write(csv_content)
    eel.enableCSVButton()
    eel.CSVSaved(csv_file_code)
    
# =================== new =======================


@eel.expose
def getResultsData(id=None):
    global results

    datasets = []

    if id is None:
        for result in results:
            resultId = result[0]
            data = result[1].split(" ")
            time_created = result[2]

            # datasets.append({
            #     'id': resultId,
            #     'property price': format(float(data[0]), "0.02f"),
            #     'down payment': format(float(data[1]), "0.02f"),
            #     'interest rate': format(float(data[2]) * 100, "0.02f"),
            #     'period': data[3], 
            #     'monthly repayment': format(float(data[4]), "0.02f"), 
            #     'time created': time_created
            # })

            datasets.append({
                'id': resultId,
                'property price': data[0],
                'down payment': data[1],
                'interest rate': float(data[2]) * 100,
                'period': data[3], 
                'monthly repayment': data[4], 
                'time created': time_created
            })

        return datasets
    else:
        return list(map(float, results[0][1].split(" ")))

@eel.expose
def deleteRecord(id):
    if isinstance(id, list):    # if its a list of multiple ids
        for each_id in id:
            cur.execute(f"DELETE FROM Result WHERE resultId = '{each_id}';")
            conn.commit()
    else:
        cur.execute(f"DELETE FROM Result WHERE resultId = '{id}';")
        conn.commit()
        
# ===============================================



def main(id=None):
    global results

    # theme of the webpage follows theme of python app
    from functions import theme
    dark = "dark" if theme == "dark" else ""

    # start the 'app'
    if id is None:
        # fetch data from database and send it to client js at index.html
        cur.execute("SELECT * FROM Result;")
        results = cur.fetchall()
        eel.start(f'results.html?{dark}', close_callback=close_callback, port=0, cmdline_args=['--start-maximized'], mode="chrome")
    else:
        dark = ("&" + dark) if dark == "dark" else ""
        cur.execute(f"SELECT * FROM Result WHERE resultId = '{id}';")
        results = cur.fetchall()
        eel.start(f'results.html?id={id}{dark}', close_callback=partial(close_callback, id=id), port=0, cmdline_args=['--start-maximized'], mode="chrome")
    

