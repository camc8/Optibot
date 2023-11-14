#pyuic5 -x layout.ui -o ui.py

import sys
import random
import time
import os.path
import pyautogui

from datetime import datetime
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QPoint, QFileInfo, QObject, QThread, pyqtSignal, pyqtSlot
from ui import Ui_MainWindow
from PyQt5.QtWidgets import * 
from PyQt5.QtGui import *

def trap_exc_during_debug(*args):
    # when app raises uncaught exception, print info
    print(args)
sys.excepthook = trap_exc_during_debug

class color:
    PRIMARY = '#226fed'
    SECONDARY = '#0099ff'
    LIGHT = '#92d3ff'
    DARK = '#061f47'
    IMPORTANT = '#ed2280'

class Worker(QObject):
	sig_step = pyqtSignal(list)  # worker id, step description: emitted every step through work() loop
	sig_done = pyqtSignal(int)  # worker id: emitted at end of work()
	sig_msg = pyqtSignal(str)  # message to be shown to user

	def __init__(self, lines: list, delay: list, script_line: int):
		super().__init__()
		self.script_line = script_line
		self.__id = 1
		self.__abort = False
		self.lines = lines
		self.delay = delay

	@pyqtSlot()
	def work(self): #TODO: Keep this loop running constantly, and send it updates from main thread about whether to do stuff or not
		#thread_name = QThread.currentThread().objectName()
		#thread_id = int(QThread.currentThreadId())
		QThread.sleep(5)
		for sentence in self.lines: #Message sending loop

			app.processEvents()
			if sentence != self.lines[self.script_line]: #Saves script loop position
				continue
			self.script_line += 1
			if self.__abort:
				break
			if sentence != "":
				# sentence = sentence.format( #Placeholders
				# 	project="MBC", 
				# 	name="Masked Billionaire Club",
				# 	time=datetime.now().strftime("%-I:%-M")
				# )
				for letter in sentence:
					pyautogui.typewrite(letter)
					QThread.sleep(int(random.randint(12, 246)/1000)) #This is the time between keystrokes
				pyautogui.press("enter")
				delay=random.randint(self.delay[0]*1000, self.delay[1]*1000)/1000
				self.sig_step.emit([self.script_line, f"<span style='color: {color.PRIMARY};'>Sent \"<span style='color: {color.LIGHT};'>" + sentence + f"</span>\", waiting <span style='color: {color.LIGHT};'>" + str(round(delay, 1)) + "</span> seconds.</span>"])
				QThread.sleep(int(delay))

		self.sig_done.emit(self.__id)

	def abort(self):
		self.__abort = True

class Window(QMainWindow):

	sig_stopBot = pyqtSignal()

	def __init__(self):
		super(Window, self).__init__()
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)
		self.initUI()
		QThread.currentThread().setObjectName('main')
		self.fileSelected = False
		self.__workers_done = None
		self.__threads = None
		self.script_line = 0
		self.permission = False
		self.queued = False
		self.permissionTest = False
		self.keyTest = 0

	def initUI(self):
		stylesheet = """
		QLineEdit {
		qproperty-frame: false;
		border: none;
	 	}"""
		app.setStyleSheet(stylesheet)
		self.ui.statusbar.hide()
		self.opacity_effect = QGraphicsOpacityEffect()
		self.opacity_effect.setOpacity(1)
		self.ui.console.setGraphicsEffect(self.opacity_effect)
		flags = QtCore.Qt.WindowFlags(QtCore.Qt.FramelessWindowHint)
		self.setWindowFlags(flags)
		self.center()
		self.oldPos = self.pos()
		self.ui.messageDurationBox.setAttribute(Qt.WA_MacShowFocusRect, 0)
		self.ui.startBotButton.clicked.connect(lambda: self.clickStartBot())
		self.ui.scriptFileButton.clicked.connect(lambda: self.pickScriptFile())
		#self.ui.minimizeButton.clicked.connect(self.showMinimized) Not working on mac...
		self.ui.closeButton.clicked.connect(lambda: sys.exit(0))
		self.logConsole(f"<span style='color: {color.SECONDARY}; font-size: 24px;'>Welcome to OptiBot</span><br><span style='color: {color.LIGHT}'>Please select a script file to get started</span><br>")

	def center(self):
		qr = self.frameGeometry()
		cp = QDesktopWidget().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	def keyPressEvent(self, event):
		if self.queued :
			if event.key() == Qt.Key_Return:
				if self.permission == False:
					self.queued = False
					self.permissionTest = False
					self.keyTest == 0
					self.ui.startBotButton.setEnabled(True)
					self.ui.startBotButton.setText("Start Bot")
					self.ui.startBotButton.setStyleSheet("background-color: rgba(34, 111, 237, 0.7);")
					self.logConsole(f"""<span style='color: #ed2280; font-size: 20px;'>Please enable Accessibility Permissions</span><br>
					<span style='color: {color.LIGHT}; font-weight: bold;'?>System Preferences<span style="color: #ed2280; font-weight: normal;"> -> </span>
					Security and Privacy<span style="color: #ed2280; font-weight: normal;"> -> </span>
					Privacy<span style="color: #ed2280; font-weight: normal;"> -> </span>
					Accessibility<span style="color: #ed2280; font-weight: normal;"> -> </span>
					Check Optibot
					</span><br>
					""") #Mac
				else:
					self.permissionTest = False
					self.queued = False
					self.keyTest == 0
					self.startBot()
			if event.key() == Qt.Key_Escape:
				self.queued = False
				self.ui.startBotButton.setEnabled(True)
				self.ui.startBotButton.setText("Start Bot")
				self.ui.startBotButton.setStyleSheet("background-color: rgba(34, 111, 237, 0.7);")
				self.logConsole(f"<span style='color: {color.LIGHT}; font-size: 20px;'>Cancelled</span>")
		if self.permissionTest :
			if event.key() == Qt.Key_Shift:
				self.keyTest += 1
				if (self.keyTest > 4) :
					self.permissionTest = False
					self.keyTest == 0
					self.permission = True

	def permissionGranted(self):
		self.permission = False
		self.permissionTest = True
		for i in range(5):
			pyautogui.press("shift")

	def mousePressEvent(self, event):
		self.oldPos = event.globalPos()

	def mouseMoveEvent(self, event):
		delta = QPoint (event.globalPos() - self.oldPos)
		self.move(self.x() + delta.x(), self.y() + delta.y())
		self.oldPos = event.globalPos()

	def logConsole(self, message) :
		self.ui.console.append(message)

	def clickStartBot(self):
		self.delayBox = self.ui.messageDurationBox.text()

		if self.fileSelected == False:
			self.logConsole("<span style='color: #ed2280;'>Please select a script file first!</span>")
			return
		if not (self.delayBox.replace('-', '').isnumeric()):
			self.logConsole("<span style='color: #ed2280; font-size: 20px;'>Enter a valid delay!</span>")
			return
		else:
			self.permissionGranted()
			#self.logConsole(f"<span style='color: {color.LIGHT}; font-size: 20px;'>Starting Bot...</span>")
			self.logConsole(f"<br><span style='color: {color.SECONDARY}; font-size: 20px;'>Press \"<span style='color: #ed2280;'>Enter</span>\" once you have your desired message app opened, or press \"<span style='color: #ed2280;'>Esc</span>\" to cancel</span><br>")
			self.ui.startBotButton.setText("Starting...")
			self.ui.startBotButton.setStyleSheet("background-color: rgba(146, 211, 255, 0.7);")
			self.ui.startBotButton.setDisabled(True)
			self.queued = True

	def startBot(self):
			self.logConsole("<br><span style='color: #ed2280; font-size: 20px;'>You have 5 seconds to refocus the text input of your messaging app</span><br>")
			self.ui.messageDurationBox.setDisabled(True)
			self.ui.startBotButton.setEnabled(True)
			self.ui.startBotButton.setText("Stop Bot")
			self.ui.startBotButton.setStyleSheet("background-color: rgba(237, 34, 128, 0.7)")
			self.ui.startBotButton.clicked.disconnect()
			self.ui.startBotButton.clicked.connect(lambda: self.stopBot())
			lines = [line.rstrip() for line in self.fileSelected] #Ordered set, saves position even after bot is stopped using i

			input = self.delayBox.split("-")
			if len(input) == 2:
				delay = [int(input[0]), int(input[1])]
			else:
				delay = [int(input[0]), int(input[0])]

			self.__workers_done = 0
			self.__threads = []
			worker = Worker(lines, delay, self.script_line)
			thread = QThread(parent=self) #parent=self allows killing the thread before it is done. Killing the thread abruptly in this case is ok since it will be sleeping
			#thread.setTerminationEnabled()
			thread.setObjectName('thread_' + str(1))
			self.__threads.append((thread, worker))
			worker.moveToThread(thread)

			worker.sig_step.connect(self.on_worker_step)
			worker.sig_done.connect(self.on_worker_done)
			worker.sig_msg.connect(self.logConsole)

			self.sig_stopBot.connect(worker.abort)

			thread.started.connect(worker.work)
			thread.start()

	@pyqtSlot(list)
	def on_worker_step(self, data: list):
		self.script_line = data[0]
		self.logConsole(data[1])

	@pyqtSlot(int)
	def on_worker_done(self, worker_id):
		for thread, worker in self.__threads:
			thread.quit()

	@pyqtSlot()
	def stopBot(self):
		self.sig_stopBot.emit()
		for thread, worker in self.__threads:  # note nice unpacking by Python, avoids indexing
			thread.quit()  # this will quit **as soon as thread event loop unblocks**
			#thread.wait()  # <- so you need to wait for it to *actually* quit
		self.ui.messageDurationBox.setEnabled(True)
		self.ui.startBotButton.setText("Start Bot")
		self.ui.startBotButton.setStyleSheet("background-color: rgba(34, 111, 237, 0.7)")
		self.ui.startBotButton.clicked.disconnect()
		self.ui.startBotButton.clicked.connect(lambda: self.clickStartBot())
		self.logConsole("<br><span style='color: #ed2280; font-size: 20px;'>Stopped Bot at line " + str(self.script_line) + "</span><br>")

	def pickScriptFile(self):
		file = QFileDialog.getOpenFileName(self, "Select Script", '',"Text files (*.txt)")
		if os.path.isfile(file[0]):
			self.logConsole("Works")
			self.script_line = 0
			f = open(file[0], 'r')
			data = f.readlines()
			filename = QFileInfo(file[0]).fileName()
			filenamecrop = (filename[:5] + "..." + filename[-7:]) if len(filename) > 20 else filename
			self.ui.scriptFileButton.setText(filenamecrop)
			self.fileSelected = data
			self.logConsole(f"<span style='color: {color.SECONDARY};'>Selected \"<span style='color: {color.LIGHT};'>" + filename + f"</span><span style='color: {color.SECONDARY};'>\" as the script file</span><br>")

if __name__ == "__main__":
	app = QApplication(sys.argv)
	form = Window()
	form.show()
	sys.exit(app.exec_())