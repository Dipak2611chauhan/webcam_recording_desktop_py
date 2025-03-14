import sys
import cv2
import os
import threading
import time
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, QSizePolicy, QSpacerItem
from PyQt6.QtGui import QImage, QPixmap, QFont
from PyQt6.QtCore import Qt, QPoint

class OrderVideoRecorder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Recording App")
        # self.setGeometry(100, 100, 700, 500)
        self.setStyleSheet("background-color: #2b2b2b; color: white;")
        self.showFullScreen()
        # self.resize(800, 600) 
        self.setMinimumSize(400, 300) 

        # Resizing & dragging variables
        self.resizing = False
        self.dragging = False
        self.mouse_pos = QPoint()
        self.resize_margin = 10  # Edge margin to detect resizing

        # UI Elements
        self.order_label = QLabel("")
        self.order_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.order_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.order_label.setStyleSheet("color: #FFA500;")
        self.order_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.order_label.setFixedHeight(30)

        self.video_label = QLabel(self)
        self.video_label.setText("<html><div style='text-align: center; font-size: 25px; font-weight: bold; color: #FFA500; padding: 10px;'>"
                         "Enter Order ID Below Text Box and Press <span style='color: #00FF00;'>\" Enter \"</span> to Start Recording"
                         "</div></html>")
        self.video_label.setFixedSize(1200, 650)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("border: 8px solid black;  border-radius: 10px;")

        self.order_id_input = QLineEdit(self)
        self.order_id_input.setPlaceholderText("Enter Order ID and press Enter")
        self.order_id_input.setStyleSheet("background-color: #3a3a3a; color: white; padding: 8px; border-radius: 10px;")
        self.order_id_input.setFixedHeight(40)
        self.order_id_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.stop_button = QPushButton("Stop", self)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("background-color: #d9534f; color: white; padding: 8px; border-radius: 10px;")
        self.stop_button.setFixedHeight(40)
        self.stop_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Layouts
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.addWidget(self.order_label)
        main_layout.addWidget(self.video_label, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addSpacerItem(QSpacerItem(20, 40))

        # Add margin above buttons
        main_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(15)
        bottom_layout.addWidget(self.order_id_input)
        bottom_layout.addWidget(self.stop_button)

        # Ensure buttons are aligned with video_label width
        bottom_container = QWidget()
        bottom_container.setLayout(bottom_layout)
        bottom_container.setMinimumWidth(self.video_label.width())  # Match width
        main_layout.addWidget(bottom_container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Add margin below the buttons
        main_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

        # Connect Events
        self.order_id_input.returnPressed.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_and_close_camera)

        # Webcam and Recording Variables
        self.cap = None
        self.recording = False
        self.video_writer = None
        self.current_order_id = None

        # Downloads Folder
        self.download_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(self.download_folder):
            os.makedirs(self.download_folder)

    def start_recording(self):
        order_id = self.order_id_input.text().strip()
        if not order_id:
            return

        # Stop and save the previous recording before starting a new one
        if self.recording:
            self.stop_and_download()

        self.current_order_id = order_id  # Set the new order ID
        self.order_label.setText(f"Current Order ID: {self.current_order_id}")  # Update label
        self.order_id_input.clear()  # Clear input field for new entry

        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
            self.show_webcam()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.video_filename = f"{self.current_order_id}_{timestamp}.mp4"
        video_path = os.path.join(self.download_folder, self.video_filename)

        self.recording = True
        self.stop_button.setEnabled(True)

        fourcc = cv2.VideoWriter_fourcc(*'H264')
        self.video_writer = cv2.VideoWriter(video_path, fourcc, 20.0, (640, 480))

        def record():
            while self.recording and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    timestamp_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    order_id_text = f"Order ID: {self.current_order_id}"

                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.4
                    font_thickness = 1
                    text_color = (255, 255, 255)  
                    background_color = (0, 0, 0)  

                    height, width, _ = frame.shape
                    timestamp_x, timestamp_y = width - 160, 20
                    order_id_x, order_id_y = 10, 20

                    cv2.putText(frame, order_id_text, (order_id_x, order_id_y), font, font_scale, text_color, font_thickness, cv2.LINE_AA)
                    cv2.putText(frame, timestamp_text, (timestamp_x, timestamp_y), font, font_scale, text_color, font_thickness, cv2.LINE_AA)

                    self.video_writer.write(frame)

                time.sleep(0.05)

        threading.Thread(target=record, daemon=True).start()


    def stop_and_download(self):
        if not self.recording:
            return

        self.recording = False
        self.stop_button.setEnabled(False)

        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
            print(f"Recording saved as {self.video_filename} in Downloads folder")

        self.current_order_id = None
        self.order_label.setText("")

    def stop_and_close_camera(self):
        self.stop_and_download()
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.video_label.clear()
        self.video_label.setText("Thank you, visit again!")
        self.video_label.setStyleSheet("color: #00FF00; font-size: 70px; font-weight: bold; border: 8px solid black; border-radius: 10px;")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def show_webcam(self):
        def update_frame():
            while self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    label_width = self.video_label.width()
                    label_height = self.video_label.height()
                    frame_resized = cv2.resize(frame, (label_width, label_height), interpolation=cv2.INTER_AREA)

                    height, width, channels = frame_resized.shape
                    bytes_per_line = channels * width
                    q_img = QImage(frame_resized.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
                    pixmap = QPixmap.fromImage(q_img)
                    self.video_label.setPixmap(pixmap)
                time.sleep(0.03)

        threading.Thread(target=update_frame, daemon=True).start()

    def closeEvent(self, event):
        self.stop_and_close_camera()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.recording:
                print("Escape key pressed while recording. Stopping and saving the video first...")
                self.stop_and_download()  # Stop and save the recording before closing
            self.close()  # Now close the application


    def mouseDoubleClickEvent(self, event):
        pass  # This prevents double-clicking from triggering any unintended behavior

    def mouseDoubleClickEvent(self, event):
        pass  # Prevent window from closing on double-click


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OrderVideoRecorder()
    window.show()
    sys.exit(app.exec())


# change readable font
# 