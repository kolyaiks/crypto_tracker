import sys
import logging
import pandas as pd
import requests
import os
import configparser

from PyQt6.QtCore import QRunnable, pyqtSlot, QThreadPool, QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QPushButton, QVBoxLayout, QWidget, QFileDialog, \
    QTableWidgetItem

class WorkerSignal(QObject):
    output = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()

class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignal()

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs) # Initialising the runner function with passed args, kwargs
            if result:
                self.signals.output.emit((result, *self.args)) # Sends normal result as object (result, kraken_pair, sym)
        except Exception as e:
            self.signals.error.emit(str(e)) # Sends exception to GUI

class MyWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initLogging()
        self.initateThreadPool()
        self.setUI()
        self.readKrakenMapping()

    def initateThreadPool(self):
        # Creating ThreadPool
        self.threadPool = QThreadPool()
        thread_count = self.threadPool.maxThreadCount()
        self.logger.debug(f" Multithreading with maximum {thread_count} threads")

    def readKrakenMapping(self):
        # Parsing the config with currency names mapping
        self.config = configparser.ConfigParser()
        self.config.read(self.get_config_path())
        self.logger.debug(f"Config {self.config}")

    def get_config_path(self):
        # Getting absolute path that works in PyCharm and PyInstaller
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")

        self.logger.debug(f"Base path: {base_path}")
        self.logger.debug(f"Files in bundle: {os.listdir(base_path)}")
        return os.path.join(base_path, "config.ini")

    def initLogging(self):
        # Creating logger
        self.logger = logging.getLogger('CryptoTracker')
        self.logger.setLevel(logging.DEBUG)

        # Creating formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(threadName)s - %(message)s')

        # Creating file handler
        fileHandler = logging.FileHandler('app.log')
        fileHandler.setFormatter(formatter)
        fileHandler.setLevel(logging.DEBUG)

        # Creating stream handler to log to console
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(formatter)
        consoleHandler.setLevel(logging.DEBUG)

        # Adding handlers to the logger
        self.logger.addHandler(fileHandler)
        self.logger.addHandler(consoleHandler)

    def setUI(self):
        # Setting window title
        self.setWindowTitle("CryptoTracker")

        # Creating Pandas DataFrame that will be written to the table
        self.portfolio = pd.DataFrame(columns=["symbol", "amount", "price", "total_value"])

        # Setting up Qt widgets
        self.table = QTableWidget()
        self.btn_load = QPushButton("Load Portfolio CSV")
        self.btn_load.clicked.connect(self.load_portfolio)
        self.btn_refresh = QPushButton("Refresh Kraken Prices")
        self.btn_refresh.clicked.connect(self.refresh_prices)
        self.btn_export = QPushButton("Export to CSV")
        self.btn_export.clicked.connect(self.export_csv)

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        layout.addWidget(self.btn_load)
        layout.addWidget(self.btn_refresh)
        layout.addWidget(self.btn_export)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def load_portfolio(self):
        # Loading the file
        file_name, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if file_name:
            self.portfolio = pd.read_csv(file_name)
            self.logger.info(f"Loaded file {file_name}")
            self.update_table()
        else:
            self.logger.error("No file selected")

    def update_table(self):
        self.logger.debug(f"Update table {self.table}")

        # Setting up the table based on portfolio file
        self.table.setRowCount(len(self.portfolio))
        self.table.setColumnCount(len(self.portfolio.columns))
        self.table.setHorizontalHeaderLabels(self.portfolio.columns)

        # Updating table rows (used for initial setup and while updating)
        for i, row in self.portfolio.iterrows():
            for j, col in enumerate(self.portfolio.columns):
                self.table.setItem(i, j, QTableWidgetItem(str(row[col])))

    def refresh_prices(self):
        self.logger.debug(f"Refreshing prices")

        if self.portfolio.empty:
            self.logger.error("No data found in portfolio")
            return

        for sym in self.portfolio["symbol"]:
            kraken_pair = self.config['KrakenSymbols'][sym.upper()]
            worker = Worker(self.get_info, kraken_pair, sym)
            worker.signals.output.connect(self.parse_resp)
            worker.signals.error.connect(lambda err: self.logger.error(f"Worker error: {err}")) # quick inline handler for error in worker
            self.threadPool.start(worker)

    def get_info(self, kraken_pair, sym):
        # Sending request to Kraken
        url = "https://api.kraken.com/0/public/Ticker"
        params = {"pair": kraken_pair}
        resp = requests.get(url, params=params).json()

        self.logger.debug(f"For {sym} ({kraken_pair}) response: {resp}")
        return resp

    def parse_resp(self, data):
        resp, kraken_pair, sym = data # comes from worker output signal (self.signals.output.emit((result, *self.args)))
        # Update prices in Pandas DataFrame
        price = float(resp["result"].get(kraken_pair)["c"][0])  # "c" = last trade closed [price, lot volume]
        self.logger.debug(f"Sym {sym} ({kraken_pair}) price {price}")
        self.logger.debug(f"Dtype for Dataframe: {self.portfolio.dtypes}")

        portfolio_row_index = self.portfolio.index[self.portfolio["symbol"] == sym].tolist()[
            0]  # getting row number in DataFrame where we have symbol
        self.portfolio.loc[portfolio_row_index, "price"] = price  # setting price sell for this row
        self.portfolio.loc[portfolio_row_index, "total_value"] = price * self.portfolio.loc[
            portfolio_row_index, "amount"]  # setting total_value sell for this row
        self.update_table()

    def export_csv(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if file_name:
            self.portfolio.to_csv(file_name, index=False)


def window():
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())

window()