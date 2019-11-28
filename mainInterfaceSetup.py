from PyQt5 import QtCore, QtGui, QtWidgets
from streamInterface import StreamThread
import serial, numpy
import mainInterface
from PyQt5.QtWidgets import QTableWidgetItem
import serial.tools.list_ports as lp
from parser import Parser, list_available_parsers

from matplotlib.backends.qt_compat import QtCore, QtWidgets, is_pyqt5
if is_pyqt5():
    from matplotlib.backends.backend_qt5agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
else:
    from matplotlib.backends.backend_qt4agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure

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
        else:
            self.stopStream()
            self.StreamTypeSelection.setEnabled(True)
            #print(self.StreamTypeSelection.currentIndex())
            self.StartStopStreamButton.setText("Start Stream")

    def loadFileButtonClicked(self):
        self.startStream(self.StreamTypeSelection.currentIndex())

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
        self._raw_data_timer.start(100)

    # prototype for raw data tabel update
    def update_raw_data(self):
       # print("try to fetch data")
        with StreamThread.data_lock:
            # take max 500 byte
            end = min(self.rawDataIndex + 500 , len(StreamThread.data)-1) 
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
        self._parser_timer.start(100)

    def parse_packets(self):
        #print("parsing packets")
        protocol = self.comboBox_parser_list.currentText()
        packet_strings,time_series,meta_data = getattr(Parser,protocol)(None)
        self.listWidget_packets.addItems(packet_strings)
        self.protocol_meta_data = meta_data
        self.lineEdit_number_of_packets.setText(str(self.listWidget_packets.count()))
        if len(self.time_series_data)==0:
            self.time_series_data = time_series
        else:
            for column_index in range(0,len(time_series)):
                self.time_series_data[column_index].extend(time_series[column_index])
        #print(self.time_series_data)

    #------- Graph Interface ------------# 
    def setupGraphInterface(self):
        self.matplot_canvas = FigureCanvas(Figure())
        self.TabView.currentChanged.connect(self.tab_changed)
        self.horizontalLayout_4.addWidget(self.matplot_canvas)
        self._matplot_ax = self.matplot_canvas.figure.subplots()
        self.matplot_canvas.figure.subplots_adjust(left=0.1,right=0.8)
        self._timer = self.matplot_canvas.new_timer(100,[(self._update_canvas, (), {})])

    def _update_canvas(self):
        if len(self.time_series_data[0])>0:
            self._matplot_ax.clear()
            time_data = numpy.array(self.time_series_data[0]).astype(numpy.double)
            for series in range(1,len(self.time_series_data)):
                data = numpy.array(self.time_series_data[series])
                none_values_mask = numpy.isfinite(data)
                # print("Data: {}".format(data))
                # print("Mask: {}".format(none_values_mask))
                # print("Time: {}".format(time_data[none_values_mask]))
                self._matplot_ax.plot(time_data[none_values_mask],
                data[none_values_mask],label="{} [{}]".format(self.protocol_meta_data[series][0],
                self.protocol_meta_data[series][1]))
            self._matplot_ax.grid(True)
            self._matplot_ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
            self._matplot_ax.figure.canvas.draw()

    def tab_changed(self,num):
        if (num == 3) and self.StartStopStreamButton.isChecked():
            self._timer.start()
        else:
            self._timer.stop()