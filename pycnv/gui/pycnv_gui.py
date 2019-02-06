
from .. import pycnv as pycnv
from .. import pycnv_sum_folder as pycnv_sum_folder
import sys
import os
import json
import logging
import argparse
import time
import locale

try:
    from PyQt5 import QtCore, QtGui, QtWidgets
except:
    from qtpy import QtCore, QtGui, QtWidgets


class get_valid_files(QtCore.QThread):
    """ A thread to search a directory for valid files
    """
    search_status = QtCore.pyqtSignal(object,int,int,str) # Create a custom signal
    def __init__(self,foldername):
        QtCore.QThread.__init__(self)
        self.foldername = foldername
        
    def __del__(self):
        self.wait()

    def run(self):
        # your logic here
        #pycnv_sum_folder.get_all_valid_files(foldername,status_function=self.status_function)
        #https://stackoverflow.com/questions/39658719/conflict-between-pyqt5-and-datetime-datetime-strptime
        locale.setlocale(locale.LC_TIME, "C")
        self.data = pycnv_sum_folder.get_all_valid_files(self.foldername,loglevel = logging.WARNING,status_function=self.status_function)
        
    def status_function(self,i,nf,f):
        self.search_status.emit(self,i,nf,f)

class mainWidget(QtWidgets.QWidget):
    def __init__(self,logging_level=logging.INFO):
        QtWidgets.QWidget.__init__(self)
        self.folder_dialog = QtWidgets.QLineEdit(self)
        self.folder_button = QtWidgets.QPushButton('Choose Datafolder')
        self.folder_button.clicked.connect(self.folder_clicked)
        self.search_button = QtWidgets.QPushButton('Search valid data')
        self.search_button.clicked.connect(self.search_clicked)
        self.search_opts_button = QtWidgets.QPushButton('Search options')
        self.search_opts_button.clicked.connect(self.search_opts_clicked)                
        self.file_table = QtWidgets.QTableWidget()
        self.file_table.setColumnCount(4)
        self.file_table.setHorizontalHeaderLabels("Date;Lon;Lat;File".split(";"))
        #self.file_table.horizontalHeaderItem().setTextAlignment(QtCore.Qt.AlignHCenter)
        self.file_table.horizontalHeader().setStretchLastSection(True)

        self.layout = QtWidgets.QGridLayout(self)
        self.layout.addWidget(self.folder_dialog,0,0)
        self.layout.addWidget(self.folder_button,0,1)
        self.layout.addWidget(self.search_button,1,0)
        self.layout.addWidget(self.search_opts_button,1,1)        
        self.layout.addWidget(self.file_table,2,0,1,2)
        
    def folder_clicked(self):
        foldername = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.folder_dialog.setText(foldername)

    def search_opts_clicked(self):
        self.search_opts_widget      = QtWidgets.QWidget()
        self.search_opts_widget.show()

    def search_clicked(self):
        foldername = self.folder_dialog.text()
        if(os.path.exists(foldername)):
            self.status_widget       = QtWidgets.QWidget()
            self.status_layout       = QtWidgets.QGridLayout(self.status_widget)
            self._progress_bar       = QtWidgets.QProgressBar(self.status_widget)
            self._thread_stop_button = QtWidgets.QPushButton('Stop')
            self._thread_stop_button.clicked.connect(self.search_stop)
            self._f_widget           = QtWidgets.QLabel('Hallo f')
            self._f_widget.setWordWrap(True)
            self.status_layout.addWidget(self._progress_bar,0,0)
            self.status_layout.addWidget(self._f_widget,1,0)
            self.status_layout.addWidget(self._thread_stop_button,2,0)
            self.status_widget.show()
            self.search_thread = get_valid_files(foldername)
            self.search_thread.start()
            self.search_thread.search_status.connect(self.status_function)
            self.search_thread.finished.connect(self.search_finished)
            #pycnv_sum_folder.get_all_valid_files(foldername,status_function=self.status_function)
        else:
            print('Enter a valid folder')

    def search_stop(self):
        self.search_thread.terminate()
        #self.status_widget.close()
        
    def search_finished(self):
        self.status_widget.close()
        self.data = self.search_thread.data
        # Fill the table
        for i in range(len(self.data['files'])):
            self.file_table.insertRow(i)

            date = self.data['dates'][i]
            self.file_table.setItem(i,0, QtWidgets.QTableWidgetItem( date.strftime('%Y-%m-%d %H:%M:%S' )))
            lon = self.data['lon'][i]
            self.file_table.setItem(i,1, QtWidgets.QTableWidgetItem( "{:6.3f}".format(lon)))
            lat = self.data['lat'][i]
            self.file_table.setItem(i,2, QtWidgets.QTableWidgetItem( "{:6.3f}".format(lat)))
            fname = self.data['files'][i]
            self.file_table.setItem(i,3, QtWidgets.QTableWidgetItem( fname ))            

    def status_function(self,call_object,i,nf,f):
        if(i == 0):
            self._progress_bar.setMaximum(nf)
            
        self._progress_bar.setValue(i)
        #tstr = str(i) +' of ' + str(nf)
        fstr = str(f)
        #self._i_widget.setText(tstr)
        self._f_widget.setText(fstr)


class pycnvMainWindow(QtWidgets.QMainWindow):
    def __init__(self,logging_level=logging.INFO):
        QtWidgets.QMainWindow.__init__(self)
        mainMenu = self.menuBar()
        self.setWindowTitle("pycnv")
        quitAction = QtWidgets.QAction("&Quit", self)
        quitAction.setShortcut("Ctrl+Q")
        quitAction.setStatusTip('Closing the program')
        quitAction.triggered.connect(self.close_application)

        chooseStreamAction = QtWidgets.QAction("&Streams", self)
        chooseStreamAction.setShortcut("Ctrl+S")
        chooseStreamAction.setStatusTip('Choose Streams')
        #chooseStreamAction.triggered.connect(self.choose_streams)        

        fileMenu = mainMenu.addMenu('&File')
        fileMenu.addAction(quitAction)
        #fileMenu.addAction(chooseStreamAction)




        self.mainwidget = mainWidget()
        self.setCentralWidget(self.mainwidget)        
        
        
        self.statusBar()

    def close_application(self):
        sys.exit()                                



def main():
    app = QtWidgets.QApplication(sys.argv)
    window = pycnvMainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()    
