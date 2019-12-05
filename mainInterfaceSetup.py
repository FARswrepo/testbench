from parser import Parser, list_available_parsers

import numpy
import serial, time
import serial.tools.list_ports as lp
from matplotlib.backends.qt_compat import QtCore, QtWidgets, is_pyqt5
from matplotlib.figure import Figure
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QTableWidgetItem

import mainInterface
from streamInterface import StreamThread

if is_pyqt5():
    from matplotlib.backends.backend_qt5agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
else:
    from matplotlib.backends.backend_qt4agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)

class Ui_MainWindow_Setup(mainInterface.Ui_MainWindow):
    # main initialization function for testbench
    def addCustomSetup(self):
        self.setupStreamInterface()
        self.setupRawDataInterface()
        self.setupParserInterface()
        self.setupGraphInterface()
    #---- Stream Interface Functions -----#
    def setupStreamInterface(self):
        # general stream setup
        self.StreamTypeSelection.addItems(["From File","From Serial","From HTTPServer"])
        self.StreamTypeSelection.currentIndexChanged.connect(self.changeStreamType)
        self.StreamTabWidget.setTabEnabled(1,False)
        self.StreamTabWidget.setTabEnabled(2,False)
        self.StartStopStreamButton.clicked.connect(self.streamButtonClicked)
        self.pushButton_Load_File.clicked.connect(self.loadFileButtonClicked)
        self.pushButton_Clear_Data.clicked.connect(self.clear_all_data)
        self.streamThread = StreamThread()
        self.streamThread.start()

        # serial setup
        port_objects = lp.comports()
        port_names = [port.device for port in port_objects]
        self.comboBox_serial_ports.addItems(port_names)

        # file setup
        self.pushButton_browse_files.clicked.connect(self.browse_file)
        
    def browse_file(self):
        path = QtWidgets.QFileDialog.getOpenFileName(self,caption="Choose Data File")
        self.lineEdit_file_path.setText(path[0])

    def clear_all_data(self):
        self._raw_data_timer.stop()
        self._parser_timer.stop()
        time.sleep(0.2)
        with StreamThread.data_lock:
            StreamThread.data.clear()
            self.rawDataTable.clear()
            self.time_series_data.clear()
    
        # reset raw data interface variables
        self.rawDataTable.setColumnCount(10)
        self.rawDataTable.setRowCount(1)
        self.rawDataIndex = 0
        self.temp_data = bytearray()
        self.RawData_BYTES_NUM_Text.setPlainText("0")
        #self._raw_data_timer.start(100)

        # reset parser settings
        self.listWidget_packets.clear()
        self.lineEdit_number_of_packets.setText("0")
        Parser.seeker_position = 0
        Parser.packet = bytearray()
        self._parser_timer.start(10)


    def changeStreamType(self,index):
        lindex = [0,1,2]
        lindex.remove(index)
        for i in lindex:
            self.StreamTabWidget.setTabEnabled(i,False)
        self.StreamTabWidget.setTabEnabled(index,True)
        if index == 0:
            self.pushButton_Load_File.setEnabled(True)
            self.StartStopStreamButton.setEnabled(False)
        else:
            self.pushButton_Load_File.setEnabled(False)
            self.StartStopStreamButton.setEnabled(True)

    def streamButtonClicked(self):
        if self.StartStopStreamButton.isChecked():
            self.startStream(self.StreamTypeSelection.currentIndex())
            #print(self.StreamTypeSelection.currentIndex())
            self.StreamTypeSelection.setEnabled(False)
            self.StartStopStreamButton.setText("Stop Stream")
            self.update_graph_table()
        else:
            self.stopStream()
            self.StreamTypeSelection.setEnabled(True)
            #print(self.StreamTypeSelection.currentIndex())
            self.StartStopStreamButton.setText("Start Stream")

    def loadFileButtonClicked(self):
        self.startStream(self.StreamTypeSelection.currentIndex())
        self.update_graph_table()

    def startStream(self,streamIndex):
        if streamIndex == 0:
            self.streamThread.stream_file_path = self.lineEdit_file_path.text()
            self.streamThread.stream_type = "FileStream"
            StreamThread.stop_thread = False
        elif streamIndex == 1:
            stream_serial_setup = {}
            stream_serial_setup["baudrate"] = int(self.comboBox_serial_baud_rate.currentText())
            stream_serial_setup["parity"] = getattr(serial,self.comboBox_serial_parity.currentText())
            stream_serial_setup["bytesize"] = getattr(serial,self.comboBox_serial_byte_size.currentText())
            stream_serial_setup["timeout"] = float(self.lineEdit_serial_timeout.text())
            stream_serial_setup["stopbits"] = getattr(serial,self.comboBox_serial_stop_bits.currentText())
            stream_serial_setup["xonxoff"] = self.checkBox_serial_xonxoff.isChecked()
            stream_serial_setup["rtscts"] = self.checkBox_serial_rtsdts.isChecked()
            stream_serial_setup["dsrdtr"] = self.checkBox_serial_dtrdsr.isChecked()
            if self.checkBox_manual_port.isChecked():
                stream_serial_setup["port"] = self.lineEdit_manual_port.text()
            else:
                stream_serial_setup["port"] = self.comboBox_serial_ports.currentText()

            self.streamThread.stream_type = "SerialStream"
            self.streamThread.stream_serial_setup = stream_serial_setup
            StreamThread.stop_thread = False

    def stopStream(self):
        StreamThread.stop_thread = True


    #------Raw Data Interface Functions -----#
    def setupRawDataInterface(self):
        self.rawDataTable.setColumnCount(10)
        self.rawDataTable.setRowCount(1)
        self.rawDataIndex = 0
        self.temp_data = bytearray()
        self.rawDataTable.itemSelectionChanged.connect(self.translateRawData)
        self.RawData_GOTO_Text.returnPressed.connect(self.gotoRawDataItem)

        # timer for table update
        self._raw_data_timer = QtCore.QTimer(self)
        self._raw_data_timer.timeout.connect(self.update_raw_data)
        #self._raw_data_timer.start(100)

    # prototype for raw data tabel update
    def update_raw_data(self):
       # print("try to fetch data")
        with StreamThread.data_lock:
            # take max 10000 byte
            end = min(self.rawDataIndex + 10000 , len(StreamThread.data)) 
            self.temp_data = StreamThread.data[self.rawDataIndex:end]
           # print("fetching data successfull:{}".format(self.temp_data))
        for num in self.temp_data:
            char = "{0:02X}".format(num)
            row = self.rawDataTable.rowCount()
            if (((self.rawDataIndex+1)%10) == 0):
                self.rawDataTable.setRowCount(row+1)

            self.rawDataTable.setItem(row-1,((self.rawDataIndex)%10),QTableWidgetItem(char))
            self.rawDataIndex += 1
            self.RawData_BYTES_NUM_Text.setPlainText(str(self.rawDataIndex))



    def translateRawData(self):
        if len(self.rawDataTable.selectedItems())==0:
            pass
        else:
            item = self.rawDataTable.selectedItems()[0].text()
            #print(item)
            num = int(item,16)
            self.RawData_BIN_Text.setPlainText("{0:08b}".format(num))
            self.RawData_DEC_Text.setPlainText("{0:}".format(num))
            self.RawData_ASCII_Text.setPlainText(repr(chr(num)))

    def gotoRawDataItem(self):
        from math import ceil
        try:
            byteNum = int(self.RawData_GOTO_Text.text())
            row = int(ceil(byteNum/10)) - 1
            col = byteNum % 10
            if col == 0:
                col = 9
            else:
                col -= 1
            self.rawDataTable.setCurrentCell(row,col)
            #self.rawDataTable.setRangeSelected(QTableWidgetSelectionRange(row,col,row,col),True)
            self.rawDataTable.setFocus()
        except:
            pass

    #--------- Parser Interface Functions ----------#
    def setupParserInterface(self):
        parsers = list_available_parsers()
        self.comboBox_parser_list.addItems(parsers)
        self.time_series_data = []
         # timer for table update
        self._parser_timer = QtCore.QTimer(self)
        self._parser_timer.timeout.connect(self.parse_packets)
        self._parser_timer.start(10)

    def parse_packets(self):
        #print("parsing packets")
        protocol = self.comboBox_parser_list.currentText()
        packet_strings,time_series = getattr(Parser,protocol)(None)
        self.listWidget_packets.addItems(packet_strings)
        self.lineEdit_number_of_packets.setText(str(self.listWidget_packets.count()))
        if len(self.time_series_data)==0:
            self.time_series_data = time_series
        else:
            for series in range(0,len(time_series)):
                for index in range(0,2):
                    self.time_series_data[series][index].extend(time_series[series][index])
        #print(self.time_series_data)

    #------- Graph Interface ------------# 
    def setupGraphInterface(self):
        self.matplot_canvas = FigureCanvas(Figure())
        
        self.TabView.currentChanged.connect(self.tab_changed)
        self.horizontalLayout_4.addWidget(self.matplot_canvas)
        self.matplot_toolbar = NavigationToolbar(self.matplot_canvas, self)
        self.addToolBar(self.matplot_toolbar)
        self._matplot_ax = self.matplot_canvas.figure.subplots()
        self.matplot_canvas.figure.subplots_adjust(left=0.1,right=0.8)
        self._timer = self.matplot_canvas.new_timer(100,[(self._update_canvas, (), {})])
        self.tableWidget_graph.setHorizontalHeaderLabels(["observable","unit","bias","scale","𝞂","µ","filter"])
        self.matplot_canvas.mpl_connect('draw_event',self.drawing_init)
        self.update_graph_table()

    def drawing_init(self,event):
        if len(self.time_series_data)>0:
            if len(self.time_series_data[0])>0:
                for series in range(0,len(self.time_series_data)):
                    if self.tableWidget_graph.cellWidget(series,0).isChecked():
                        # get x limits and calculate std and mean
                        xlim = self._matplot_ax.get_xlim()
                        indmin, indmax = numpy.searchsorted(self.time_series_data[series][0], xlim)
                        indmax = min(len(self.time_series_data[series][0]) - 1, indmax)
                        data = self.time_series_data[series][1][indmin:indmax]

                        std = numpy.std(data)
                        mean = numpy.mean(data)
                        self.tableWidget_graph.item(series,4).setText(str(std))
                        self.tableWidget_graph.item(series,5).setText(str(mean))


    def _update_canvas(self):
        if len(self.time_series_data)>0:
            if len(self.time_series_data[0])>0:
                self._matplot_ax.clear()
                
                for series in range(0,len(self.time_series_data)):
                    if self.tableWidget_graph.cellWidget(series,0).isChecked():
                        bias, scale = self.get_calibration_values(series)
                        
                        time_data = numpy.array(self.time_series_data[series][0])
                        data = numpy.array(self.time_series_data[series][1])
                        data = (data + bias) * scale
                        self._matplot_ax.plot(time_data,
                        data,label="{} [{}]".format(self.tableWidget_graph.cellWidget(series,0).text(),
                        self.tableWidget_graph.item(series,1).text()))
                
    
                self._matplot_ax.grid(True)
                self._matplot_ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
                self._matplot_ax.figure.canvas.draw()
            else:
                self._matplot_ax.clear()
                self._matplot_ax.figure.canvas.draw()

    def get_calibration_values(self,series):
        try:
            bias = float(self.tableWidget_graph.item(series,2).text())
        except:
            self.tableWidget_graph.item(series,2).setText("0.0")
            bias = 0.0
        try:
            scale = float(self.tableWidget_graph.item(series,3).text())
        except:
            self.tableWidget_graph.item(series,3).setText("1.0")
            scale = 1.0
        
        return (bias,scale)

    def apply_filter(self):
        pass

    def update_graph_table(self):
        # get active protocol
        protocol = self.comboBox_parser_list.currentText()
        protocol_func = getattr(Parser,protocol)
        protocol_meta = protocol_func.__code__.co_consts[1] # the meta data in every protocol shall be in line one
        #print(protocol_meta) 
        self.tableWidget_graph.setRowCount(len(protocol_meta)-1)

        for num in range(1,len(protocol_meta)):
            self.tableWidget_graph.setCellWidget(num-1,0,QCheckBox(protocol_meta[num][0]))
            self.tableWidget_graph.setItem(num-1,1,QTableWidgetItem(protocol_meta[num][1]))
            self.tableWidget_graph.setItem(num-1,2,QTableWidgetItem("0.00"))
            self.tableWidget_graph.setItem(num-1,3,QTableWidgetItem("1.0"))
            self.tableWidget_graph.setItem(num-1,4,QTableWidgetItem("0.00"))
            self.tableWidget_graph.setItem(num-1,5,QTableWidgetItem("0.00"))

    def tab_changed(self,num):
        if (num == 3) and self.StartStopStreamButton.isChecked():
            self._timer.start()
        elif (num == 3):
            self._update_canvas()
        else:
            self._timer.stop()
