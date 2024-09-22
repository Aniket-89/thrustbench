import serial
import tkinter as tk
from tkinter import ttk
import threading
import serial.tools.list_ports

class ArduinoDataApp:
class CircularGauge(QWidget):
    def __init__(self, name, unit, min_value, max_value, color):
        super().__init__()
        self.name = name
        self.unit = unit
        self.min_value = min_value
        self.max_value = max_value
        self.color = color
        self.value = min_value
        self.setMinimumSize(200, 200)

    def update_value(self, value):
        try:
            self.value = max(self.min_value, min(self.max_value, float(value)))
        except ValueError:
            print(f"Invalid value for {self.name}: {value}")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background
        painter.setBrush(QColor("#34495e"))
        painter.drawEllipse(self.rect())

        # Draw gauge
        center = self.rect().center()
        radius = min(self.width(), self.height()) // 2 - 10
        start_angle = 225 * 16  # Start from 225 degrees (lower-left)
        span_angle = -270 * 16  # Span 270 degrees counter-clockwise

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self.color))
        span = int(((self.value - self.min_value) / (self.max_value - self.min_value)) * -270 * 16)
        painter.drawPie(QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2),
                        start_angle, span)

        # Draw text
        painter.setPen(QColor("#ecf0f1"))
        painter.setFont(QFont("Helvetica", 14, QFont.Weight.Bold))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self.value:.1f}\n{self.unit}")

        painter.setFont(QFont("Helvetica", 12))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, self.name)

        painter.end()  # Ensure the painter is ended

    def closeEvent(self, event):
        # Ensure any ongoing painting is finished before closing
        self.update()
        super().closeEvent(event)

    def find_arduino_port(self):
        ports = list(serial.tools.list_ports.comports())
        print(ports)
        for p in ports:
            if 'Arduino' in p.description or 'CH340' in p.description:  # CH340 is a common chip used in Arduino clones
                return p.device
        return None

    def update_data(self):
        while self.is_running:
            if self.serial_port.in_waiting:
                data = self.serial_port.readline().decode('utf-8').strip()
                self.master.after(0, self.update_display, data)

    def update_display(self, data):
        self.data_display.config(text=data)

    def on_closing(self):
        self.is_running = False
        if hasattr(self, 'serial_port'):
            self.serial_port.close()
        self.master.destroy()


root = tk.Tk()
app = ArduinoDataApp(root)
root.protocol("WM_DELETE_WINDOW", app.on_closing)
root.mainloop()