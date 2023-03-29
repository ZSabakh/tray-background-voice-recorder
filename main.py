from datetime import datetime
import os
import subprocess
import sys
import threading

import lameenc
import pyaudio
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMainWindow, QTextEdit, QDialog, QVBoxLayout, QLabel, \
    QLineEdit, QButtonGroup, QRadioButton, QDialogButtonBox, QMessageBox, QPushButton, QComboBox


class TrayIcon(QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        QSystemTrayIcon.__init__(self, icon, parent)
        self.interval = 5
        self.textbox = None
        self.window = None
        self.recordingState = False
        self.currentRecording = None

        menu = QMenu(parent)
        startRecording = menu.addAction("Start Recording")
        stopRecording = menu.addAction("Stop Recording")
        showFileLocation = menu.addAction("Show File Location")
        readMe = menu.addAction("Read Me")
        options = menu.addMenu("Options")
        exitAction = menu.addAction("Exit")
        self.setContextMenu(menu)

        startRecording.triggered.connect(self.startRecording)
        stopRecording.triggered.connect(self.stopRecording)
        showFileLocation.triggered.connect(self.showFileLocation)
        exitAction.triggered.connect(self.exitAction)
        readMe.triggered.connect(self.readMe)
        options.addAction("Set Interval")

        options.triggered.connect(self.optionSelected)

    def optionSelected(self, action):
        if action.text() == "Set Interval":
            interval_dialog = QDialog()
            interval_dialog.setWindowTitle("Set Interval")

            layout = QVBoxLayout()

            instructions_label = QLabel("Enter a number from 0-60:")
            layout.addWidget(instructions_label)

            interval_input = QLineEdit()
            layout.addWidget(interval_input)

            time_units_selector = QComboBox()
            time_units_selector.addItem("Seconds")
            time_units_selector.addItem("Minutes")
            layout.addWidget(time_units_selector)

            submit_button = QPushButton("Submit")
            layout.addWidget(submit_button)

            submit_button.clicked.connect(
                lambda: self.handle_interval_input(interval_input, time_units_selector, interval_dialog))

            interval_dialog.setLayout(layout)
            interval_dialog.exec()

    def handle_interval_input(self, interval_input, time_units_selector, interval_dialog):
        try:
            interval = int(interval_input.text())

            if 0 <= interval <= 60:
                if time_units_selector.currentText() == "Minutes":
                    interval *= 60

                self.interval = interval
                interval_dialog.accept()
            else:
                QMessageBox.warning(interval_dialog, "Error", "Please enter a number from 0-60.")
        except ValueError:
            QMessageBox.warning(interval_dialog, "Error", "Please enter a valid integer.")


    def showFileLocation(self):
        current_location = os.path.dirname(os.path.abspath(__file__))
        if sys.platform == 'win32':
            subprocess.Popen(f'explorer "{current_location}"')
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', current_location])
        elif sys.platform == 'linux':
            subprocess.Popen(['xdg-open', current_location])
        else:
            print("Unsupported platform")


    def readMe(self):
        self.window = QMainWindow()
        self.window.setWindowTitle("Read Me")
        self.textbox = QTextEdit(self.window)
        self.textbox.setText("Audio files will be saved to the same directory as this application")
        self.textbox.setReadOnly(True)
        self.textbox.setGeometry(0, 0, 500, 500)
        self.textbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.textbox.setFontPointSize(20)
        self.textbox.setFontWeight(75)
        self.textbox.setStyleSheet("background-color: white")
        self.window.setWindowIcon(QIcon("green.png"))
        self.window.setGeometry(100, 100, 500, 500)
        self.window.setFixedSize(500, 500)
        self.window.show()

    def startRecording(self):
        self.setIcon(QIcon("red.png"))
        self.recordingState = True
        t = threading.Thread(target=self.recording)
        t.start()

    def stopRecording(self):
        self.setIcon(QIcon("green.png"))
        self.recordingState = False
        # check if there is any audio to save
        if self.currentRecording is not None:
            self.saveAndCompress()

    def recording(self):
        audio = pyaudio.PyAudio()
        stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
        frames = []

        while self.recordingState:
            for i in range(0, int(44100 / 1024 * self.interval)):
                data = stream.read(1024)
                frames.append(data)
            # save the audio
            self.currentRecording = frames
            self.saveAndCompress()
            frames = []


    def saveAndCompress(self):
        encoder = lameenc.Encoder()
        encoder.set_bit_rate(128)
        encoder.set_in_sample_rate(44100)
        encoder.set_channels(1)
        encoder.set_quality(2)
        mp3_data = bytearray()
        for frame in self.currentRecording:
            mp3_data += encoder.encode(frame)
        mp3_data += encoder.flush()
        filename = f"recording_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp3"
        directory = "recordings"
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(f"{directory}/{filename}", "wb") as f:
            f.write(mp3_data)
        self.currentRecording = None

    def exitAction(self):
        self.hide()
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    w = TrayIcon(QIcon("green.png"))
    w.show()
    sys.exit(app.exec())