import numpy as np
import time
import sys 
from matplotlib.backends.qt_compat import QtCore, QtWidgets, is_pyqt5
if is_pyqt5():
    from matplotlib.backends.backend_qt5agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
else:
    from matplotlib.backends.backend_qt4agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
import mainInterface
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
class TestbenchWindow(QtWidgets.QMainWindow, mainInterface.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)
        self.setupUi(self)
        self.tableWidget.setHorizontalHeaderLabels(["observable","unit","a","b"])
        self.tableWidget.setRowCount(1)
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setCellWidget(0,0,QCheckBox("sinus"))
        self.tableWidget.setItem(0,1,QTableWidgetItem("none"))
        self.tableWidget.setItem(0,2,QTableWidgetItem("0.0004"))
        self.tableWidget.setItem(0,3,QTableWidgetItem("-9.7600"))

        self.matplot_canvas = FigureCanvas(Figure())
        
        self.horizontalLayout_4.addWidget(self.matplot_canvas)
        self._matplot_ax = self.matplot_canvas.figure.subplots()
        self.matplot_canvas.figure.subplots_adjust(left=0.1,right=0.8)
        self._timer = self.matplot_canvas.new_timer(100,[(self._update_canvas, (), {})])
        self._timer.start()

    def _update_canvas(self):
        self._matplot_ax.clear()
        t = np.linspace(0, 10, 101)
        # Shift the sinusoid as a function of time.
        self._matplot_ax.plot(t, np.sin(t + time.time()),label="sinus")
        self._matplot_ax.grid(True)
        self._matplot_ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
        self._matplot_ax.figure.canvas.draw()

if __name__ == "__main__":
    qapp = QtWidgets.QApplication(sys.argv)
    app = TestbenchWindow()
    app.show()
    qapp.exec_()