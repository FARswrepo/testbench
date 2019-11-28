import numpy as np
import time
import sys 


import mainInterfaceSetup
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import pyqtSlot
from streamInterface import StreamThread
from matplotlib.backends.qt_compat import QtCore, QtWidgets

class TestbenchWindow(QtWidgets.QMainWindow, mainInterfaceSetup.Ui_MainWindow_Setup):
    def __init__(self):
        super().__init__()
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)
        self.setupUi(self)
        self.addCustomSetup()
        self.tableWidget.setHorizontalHeaderLabels(["observable","unit","a","b"])
        self.tableWidget.setRowCount(1)
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setCellWidget(0,0,QCheckBox("sinus"))
        self.tableWidget.setItem(0,1,QTableWidgetItem("none"))
        self.tableWidget.setItem(0,2,QTableWidgetItem("0.0004"))
        self.tableWidget.setItem(0,3,QTableWidgetItem("-9.7600"))

    def closeEvent(self,event):
        self._timer.stop()
        self._raw_data_timer.stop()
        StreamThread.stop_thread = True
        StreamThread.close_thread = True
        self.streamThread.join()
        
        event.accept()

if __name__ == "__main__":
    qapp = QtWidgets.QApplication(sys.argv)
    app = TestbenchWindow()
    # app.TabView.setTabEnabled(5,False)
    app.show()
    qapp.exec_()