
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

# For the map plotting
import pylab as pl
import cartopy.crs as ccrs
from cartopy.io import shapereader
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER    
import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

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


class casttableWidget(QtWidgets.QTableWidget):
    plot_signal = QtCore.pyqtSignal(object,str) # Create a custom signal for plotting
    def __init__(self):
        QtWidgets.QTableWidget.__init__(self)

    def contextMenuEvent(self, event):
        print('Event!')
        self.menu = QtWidgets.QMenu(self)
        plotAction = QtWidgets.QAction('Add to map', self)
        plotAction.triggered.connect(self.plot_map)
        remplotAction = QtWidgets.QAction('Rem from map', self)
        remplotAction.triggered.connect(self.rem_from_map)        
        print(QtGui.QCursor.pos())
        self.menu.addAction(plotAction)
        self.menu.addAction(remplotAction)        
        self.menu.popup(QtGui.QCursor.pos())
        self.menu.show()
        # Get selected rows (as information for plotting etc.)
        self.rows = set() # Needed for "unique" list
        for idx in self.selectedIndexes():
            self.rows.add(idx.row())

        self.rows = list(self.rows)
        print('Rows',self.rows)
        #action = self.menu.exec_(QtGui.QCursor.pos())#self.mapToGlobal(event))

    def plot_map(self):
        row_list = self.rows
        self.plot_signal.emit(row_list,'add to map') # Emit the signal with the row list and the command

    def rem_from_map(self):
        row_list = self.rows
        self.plot_signal.emit(row_list,'rem from map') # Emit the signal with the row list and the command        


        

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
        self.clear_table_button = QtWidgets.QPushButton('Clear')
        self.clear_table_button.clicked.connect(self.clear_table_clicked)                        
        self.file_table = casttableWidget() # QtWidgets.QTableWidget()
        self.file_table.plot_signal.connect(self.plot_signal) # Custom signal for plotting
        self._ncolumns = 5
        self.file_table.setColumnCount(self._ncolumns)
        self.file_table.setHorizontalHeaderLabels("Date;Lon;Lat;Station/Transect;File".split(";"))
        for i in range(self._ncolumns):
            self.file_table.horizontalHeaderItem(i).setTextAlignment(QtCore.Qt.AlignHCenter)
            
        self.file_table.horizontalHeader().setStretchLastSection(True)
        self.file_table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.layout = QtWidgets.QGridLayout(self)
        self.layout.addWidget(self.folder_dialog,0,0)
        self.layout.addWidget(self.folder_button,0,1)
        self.layout.addWidget(self.search_button,1,0)
        self.layout.addWidget(self.search_opts_button,1,1)
        self.layout.addWidget(self.file_table,2,0,1,2)
        self.layout.addWidget(self.clear_table_button,3,0)

    def plot_map(self):
        print('Plot map')
        try:
            self.data['lon']
            self.data['lat']
        except:
            print('No data')
            #return

        FIG_LON = [-170,180]
        FIG_LAT = [-89,90]
        #FIG_LON = [0,180]
        #FIG_LAT = [0,70]
        self.dpi       = 100
        #self.fig       = Figure((5.0, 4.0), dpi=self.dpi)
        self.fig       = Figure(dpi=self.dpi)
        self.figwidget = QtWidgets.QWidget()
        self.figwidget.setWindowTitle('pycnv map')
        self.canvas    = FigureCanvas(self.fig)
        self.canvas.setParent(self.figwidget)
        plotLayout = QtWidgets.QVBoxLayout()
        plotLayout.addWidget(self.canvas)
        self.figwidget.setLayout(plotLayout)
        self.canvas.setMinimumSize(self.canvas.size()) # Prevent to make it smaller than the original size
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.figwidget)
        plotLayout.addWidget(self.mpl_toolbar)
        #self.figs.append(fig)
        self.axes      = self.fig.add_subplot(111,projection=ccrs.Mercator())
        ax             = self.axes
        ax.set_extent([FIG_LON[0], FIG_LON[1], FIG_LAT[0], FIG_LAT[1]])
        #ax.coastlines()
        ax.coastlines('10m')

        #ax.draw()
        self.figwidget.show()

    def plot_signal(self,rows,command):
        if(command == 'add to map'):
            self.add_positions_to_map(rows)
        elif(command == 'rem from map'):
            self.rem_positions_from_map(rows)            

    def add_positions_to_map(self,rows):
        # Check if we have a map, if not call plot_map to create one
        try:
            self.axes
        except:
            self.plot_map()
            
        print('Add positions', rows)
        for row in rows:
            print(row)
            lon = self.data['lon'][row]
            lat = self.data['lat'][row]
            self.data['plot_map'][row].append(self.axes.plot(lon,lat,'o',transform=ccrs.PlateCarree()))

        self.canvas.draw()
        
    def rem_positions_from_map(self,rows):
        # Check if we have a map, if not call plot_map to create one
        try:
            self.axes
        except:
            return
            
        print('Remove positions', rows)
        for row in rows:
            while self.data['plot_map'][row]:
                tmpdata = self.data['plot_map'][row].pop()
                for line in tmpdata:
                    line.remove()
                
            #self.data['plot_map'][row].pop(0)[0].remove()

        self.canvas.draw()
        
    def clear_table_clicked(self):
        # Remove from plot
        for row in range(len(self.data['files'])):            
            while self.data['plot_map'][row]:
                tmpdata = self.data['plot_map'][row].pop()
                for line in tmpdata:
                    line.remove()
        try:
            self.canvas.draw()
        except:
            pass
        
        self.file_table.setRowCount(0)
        
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
            #self._thread_stop_button = QtWidgets.QPushButton('Stop')
            #self._thread_stop_button.clicked.connect(self.search_stop)
            self._f_widget           = QtWidgets.QLabel('Hallo f')
            self._f_widget.setWordWrap(True)
            self.status_layout.addWidget(self._progress_bar,0,0)
            self.status_layout.addWidget(self._f_widget,1,0)
            #self.status_layout.addWidget(self._thread_stop_button,2,0)
            self.status_widget.show()
            self.search_thread = get_valid_files(foldername)
            self.search_thread.start()
            self.search_thread.search_status.connect(self.status_function)
            self.search_thread.finished.connect(self.search_finished)
            #pycnv_sum_folder.get_all_valid_files(foldername,status_function=self.status_function)
        else:
            print('Enter a valid folder')

    def search_stop(self):
        """This doesnt work, if a stop is needed it the search function needs
        to have the functionality to be interrupted

        """
        self.search_thread.terminate()
        #self.status_widget.close()
        
    def search_finished(self):
        self.status_widget.close()
        self.data = self.search_thread.data
        # Add additional information
        self.data['plot_map'] = [[]] * len(self.data['files'])
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
            self.file_table.setItem(i,4, QtWidgets.QTableWidgetItem( fname ))

        # Resize the columns
        self.file_table.resizeColumnsToContents()        

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



        fileMenu = mainMenu.addMenu('&File')
        fileMenu.addAction(quitAction)
        #fileMenu.addAction(chooseStreamAction)

        self.mainwidget = mainWidget()
        self.setCentralWidget(self.mainwidget)

        plotMenu = mainMenu.addMenu('&Plot')
        plotmapAction = QtWidgets.QAction("&Plot map", self)
        plotmapAction.setShortcut("Ctrl+M")
        plotmapAction.setStatusTip('Plot a map')
        plotmapAction.triggered.connect(self.mainwidget.plot_map)
        plotMenu.addAction(plotmapAction)
        
        
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
