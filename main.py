from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import os
import os.path
from WS_api import sabi_share, get_search_result, destroy
import time
import requests
import configparser
from pathlib import Path

import ui_main

class MainApp(QtWidgets.QMainWindow, ui_main.Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainApp , self).__init__(parent)
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)

        self.config=configparser.ConfigParser()
        self.config.read('config.ini')
        self.readLocation()
        self.download_finished = False

        self.progressBar.hide()
        self.pushButton_2.hide()
        self.label_4.hide()
        self.pushButton.clicked.connect(self.newitems)
        self.pushButton_2.clicked.connect(self.download)
        self.pushButton_3.clicked.connect(self.handleBrowse)
        self.pushButton_4.clicked.connect(self.select)

        self.movie = QtGui.QMovie(":/icons/834.gif")     
        self.label.setMovie(self.movie)

        self.workerThread = WorkerThread(self)
        self.workerThread.change_value.connect(self.downloadbar)
        self.workerThread.change_string.connect(self.stopAnimation)
        self.workerThread.error_string.connect(self.catchError)

    def closeEvent(self,event, *args, **kwargs):
        super(MainApp, self).closeEvent(event, *args, **kwargs)
        if self.progressBar.value() > 0:
            quit_msg = "Download in Progress, Are you sure you want to exit?"
            reply = QtWidgets.QMessageBox.question(self, 'Message', quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
        elif self.download_finished is False: 
            destroy()
            self.workerThread.quit()
            QtWidgets.QApplication.processEvents()

    def catchError(self, e):
        if e:
            self.movie.stop()
            self.label_4.show()
            self.label_4.setText(e)
            self.label.setHidden(True) 

    def select(self):

        if self.comboBox.currentText() == "EDGE":
            self.config['DRIVER']['BROWSER'] = 'EDGE'

        elif self.comboBox.currentText() == "FIREFOX":
            self.config['DRIVER']['BROWSER'] = 'FIREFOX'
        
        elif self.comboBox.currentText() == "CHROME":
            self.config['DRIVER']['BROWSER'] = 'CHROME'

        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)
        QtWidgets.QMessageBox.warning(self, "Warning", "RESTART TO APPLY")



    def readLocation(self):

        self.location = self.config['LOCATION']['PATH']
        self.label_3.setText(self.location)

        self.path = self.config['DRIVER']['BROWSER']
        index = self.comboBox.findText(self.path, QtCore.Qt.MatchFixedString)
        self.comboBox.setCurrentIndex(index)

    def newitems(self):
        self.listWidget.clear()
        self.pushButton_2.show()
        self.label_4.hide()
        if self.lineEdit.text() == "":
            QtWidgets.QMessageBox.warning(self, "Data Error", "Enter name!!")
        else:
            try:
                
                srh_rst = get_search_result(self.lineEdit.text())
                for i in srh_rst:
                    name = i["name"]        
                    self.listWidget.addItem(name)
                self.surl = [i["url"] for i in srh_rst]
            except requests.exceptions.ConnectionError:
                self.surl = None
                self.label_4.show()
                self.label_4.setText("Check Internet Connection")

    def download(self):
        
        if self.surl:
            self.workerThread.start()
            self.idx = self.listWidget.currentRow()
            self.url = self.surl[self.idx]
            self.label.setHidden(False)
            self.label_4.hide()
            self.movie.start()
        else:
            pass
        

    def stopAnimation(self, filename):
        if filename:
            self.label_4.show()
            self.label_4.setText(filename)
            self.movie.stop()
            self.label.setHidden(True) 

    def downloadbar(self,dp):
        self.progressBar.show()
        self.progressBar.setValue(dp)
        self.pushButton_2.hide()
        if self.progressBar.value() == self.progressBar.maximum():
            self.progressBar.setValue(0)
            self.progressBar.hide()
            self.label_4.setText("Done")
            self.pushButton_2.show()
            

    def handleBrowse(self):
        self.save_location = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))

        if self.save_location == "":
            self.save_location = self.config['LOCATION']['PATH']

        self.config['LOCATION']['PATH'] = self.save_location

        self.label_3.setText(self.save_location)
        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)  


class WorkerThread(QtCore.QThread):
    change_value = QtCore.pyqtSignal(int)
    change_string = QtCore.pyqtSignal(str)
    error_string = QtCore.pyqtSignal(str)

    def __init__(self, main_window):
        self.main_window = main_window
        super(WorkerThread, self).__init__(main_window)
  
    def run(self):

        location = Path(self.main_window.config['LOCATION']['PATH'])

        try:
            if self.main_window.url:
                val = str(sabi_share(self.main_window.url))
                r = requests.get(val, stream = True)
                total_size = int(r.headers['Content-Length'])
                filename = r.headers['Content-Disposition'][22:-1]
                fullpath = location / filename
                is_file = Path(fullpath).is_file()

                if is_file:
                    file_size = Path(fullpath).stat().st_size
                else:
                    file_size = 0
                
                if is_file and total_size == file_size:
                    e = "File already exists"
                    self.main_window.download_finished = 1
                    self.error_string.emit(e)

                elif is_file and total_size != file_size:

                    ############--------###########

                    resume_header = {'Range':f'bytes={file_size}-'}
                    r = requests.get(val, stream = True, headers=resume_header)
                    message = "Resuming {}".format(filename)
                    self.change_string.emit(message) #send value back to main thread

                    with open(fullpath, 'ab') as f:
                        rd = file_size
                        block_size =int(1024)
                        for chunk in r.iter_content(chunk_size= block_size): 
                            rd += len(chunk)
                            if total_size > 0:
                                f.write(chunk)
                                dp = int(rd * 100 / total_size)
                                self.change_value.emit(dp)

                    self.main_window.download_finished = True

                else:
                    self.change_string.emit(filename) #send value back to main thread
                    fullpath = location / filename
                    with open(fullpath, 'wb') as f:
                        rd = 0
                        block_size =int(1024)
                        for chunk in r.iter_content(chunk_size= block_size): 
                            rd += len(chunk)
                            if total_size > 0:
                                f.write(chunk)
                                dp = int(rd * 100 / total_size)
                                self.change_value.emit(dp)
                    self.main_window.download_finished = True
            else:
                e = "ERROR"
                self.error_string.emit(e)

        except Exception as e:
            self.error_string.emit(str(e))
            self.main_window.label_4.hide()
            pass

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 