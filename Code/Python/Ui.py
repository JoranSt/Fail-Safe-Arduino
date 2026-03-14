from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QSize, QTimer
import pyqtgraph as pg
import numpy as np
from PyQt6.QtGui import QPixmap, QPainter, QColor, QIcon
import sys
sys.path.append("Code/Python")
from Simulation import *
import json
import yaml
with open("Code/Python/config.yaml", "r") as f:
        config = yaml.safe_load(f)


system = System(config)

    
    
    
class MainWindow(QWidget):
    def __init__(self, system):
        super().__init__()

        self.setWindowTitle("System Monitor")
        self.resize(1200, 800)
        self.system = system
        self.stacked = QStackedWidget()
        self.sensorAmount = sum(len(group.sensors) for group in self.system.groups)
        self.blink_on = True
        self.logging_active = True          
        self.logging_stopped = False        
        self.logged_data = []
        self.log_filename = "logs/system_log.json" 
                      

        # ----------------------------------------------------
        # MAIN LAYOUT
        # ----------------------------------------------------
        main_layout = QHBoxLayout(self)

        # ----------------------------------------------------
        # LEFT SIDE: GROUP PAGES WITH GRAPHS
        # ----------------------------------------------------
        # ----------------------------------------------------
# LEFT SIDE: GROUP PAGES WITH GRAPHS
# ----------------------------------------------------
        self.group_pages = []  # store graph structures

        for group in self.system.groups:
            page = QWidget()
            page_layout = QVBoxLayout(page)

            title = QLabel(f"Page for {group.name}")
            title.setStyleSheet("font-size: 20px; font-weight: bold;")
            page_layout.addWidget(title)

            # store plots for this group
            plots = {}

            for sensor in group.sensors:

                # --- SENSOR STATE ROW ---
                row = QHBoxLayout()
                led = QLabel()
                led.setFixedSize(14, 14)
                name_label = QLabel(sensor.name)
                name_label.setStyleSheet("font-weight: bold;")

                row.addWidget(led)
                row.addWidget(name_label)
                row.addStretch()
                page_layout.addLayout(row)

                # --- GRAPH ---
                plot = pg.PlotWidget()
                plot.setBackground("#1e1e1e")
                plot.showGrid(x=True, y=True, alpha=0.3)

                curve = plot.plot(pen=pg.mkPen(sensor.state.color, width=2))

                plots[sensor] = {
                    "curve": curve,
                    "x": [],       # tijdstempels
                    "data": [],    # sensorwaarden
                    "led": led
                }

                page_layout.addWidget(plot)

            page_layout.addStretch()

            # ⬅️ BELANGRIJK: deze drie regels BUITEN de sensor-loop
            self.group_pages.append(plots)
            self.stacked.addWidget(page)


        # ----------------------------------------------------
        # RIGHT SIDE: INFO PANEL + SIDEBAR
        # ----------------------------------------------------
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)

        # INFO PANEL
        self.info_time = QLabel("Time: --:--")
        self.info_sensors = QLabel("Number of sensors: 0")
        self.info_warnings = QLabel("Warnings: 0")
        self.info_failed = QLabel("Failed sensors: 0")
        self.info_state_icon = QLabel()
        self.info_state_text = QLabel(f"State: {self.system.state.label}")

        self.info_state_icon.setPixmap(self.make_state_circle("green").pixmap(14, 14))
        self.info_state_icon.setFixedSize(14, 14)

        right_layout.addWidget(self.info_time)
        right_layout.addWidget(self.info_sensors)
        right_layout.addWidget(self.info_warnings)
        right_layout.addWidget(self.info_failed)

        row = QHBoxLayout()
        row.addWidget(self.info_state_icon)
        row.addWidget(self.info_state_text)
        right_layout.addLayout(row)

        # SIDEBAR
        sidebar_container = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_container)

        self.knoppen = []
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)

        for group in self.system.groups:
            knop = QPushButton(group.name)
            knop.setCheckable(True)
            knop.setProperty("group_obj", group)
            knop.setIcon(self.make_state_circle("#684444"))
            knop.setIconSize(QSize(12, 12))
            knop.setFixedHeight(32)

            sidebar_layout.addWidget(knop)
            self.knoppen.append(knop)
            self.group.addButton(knop)

        for index, knop in enumerate(self.knoppen):
            knop.clicked.connect(lambda _, idx=index: self.stacked.setCurrentIndex(idx))

        sidebar_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(sidebar_container)
        scroll.setWidgetResizable(True)

        right_layout.addWidget(scroll)

        main_layout.addWidget(self.stacked, stretch=3)
        main_layout.addWidget(right_container, stretch=1)

        # ----------------------------------------------------
        # TIMERS
        # ----------------------------------------------------
        self.fast_timer = QTimer()
        self.fast_timer.timeout.connect(self.system.simulate)
        self.fast_timer.timeout.connect(self.update_graphs)
        self.fast_timer.timeout.connect(self.update_all_group_icons)
        self.fast_timer.start(50)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_info_panels)
        self.timer.start(1000)

    # ----------------------------------------------------
    # UPDATE INFO PANEL
    # ----------------------------------------------------
    def update_info_panels(self):
        elapsed = int(self.system.time)
        mins = elapsed // 60
        secs = elapsed % 60

        warnings = sum(1 for g in self.system.groups for s in g.sensors if s.state == SensorState.WARNING)
        failures = sum(1 for g in self.system.groups for s in g.sensors if s.state == SensorState.FAILED)

        self.info_sensors.setText(f"Number of sensors: {self.sensorAmount}")
        self.info_warnings.setText(f"Warnings: {warnings}")
        self.info_failed.setText(f"Failed sensors: {failures}")
        self.info_time.setText(f"Time: {mins:02d}:{secs:02d}")

        state = self.system.state  
        # --- STOP LOGGING EN SCHRIJF JSON ---
        if state == SystemState.DANGER and self.logging_active and not system.mode == "replay":

            self.logging_active = False
            self.logging_stopped = True
            print("⚠️ Logging gestopt: systeem in DANGER")

            import json
            with open(self.log_filename, "w") as f:
                json.dump(self.logged_data, f, indent=4)

            print(f"📁 Log opgeslagen naar {self.log_filename}")

        self.info_state_text.setText(f"State: {state.label}")

        # blinking LED
        if state.blink:
            if self.blink_on:
                self.info_state_icon.setPixmap(self.make_state_circle("transparent").pixmap(14, 14))
            else:
                self.info_state_icon.setPixmap(self.make_state_circle(state.color).pixmap(14, 14))
            self.blink_on = not self.blink_on
        else:
            self.info_state_icon.setPixmap(self.make_state_circle(state.color).pixmap(14, 14))
            
            
    # ----------------------------------------------------
    # UPDATE GROUP ICONS IN SIDEBAR
    # ----------------------------------------------------
    def update_all_group_icons(self):
        for knop in self.knoppen:
            self.update_group_icon(knop)

    def update_group_icon(self, knop):
        group = knop.property("group_obj")
        state = group.state
        color = state.color

        if state.blink:
            if self.blink_on:
                knop.setIcon(self.make_state_circle(color))
            else:
                knop.setIcon(self.make_state_circle("transparent"))
        else:
            knop.setIcon(self.make_state_circle(color))
    # ----------------------------------------------------
    # UPDATE GRAPHS (NO BLINKING)
    # ----------------------------------------------------
    def update_graphs(self):
        for group, plots in zip(self.system.groups, self.group_pages):
            
            for sensor in group.sensors:
                plot_info = plots[sensor]

                current_time = self.system.time

                plot_info["data"].append(sensor.currentValue)
                plot_info["x"].append(current_time)

                if len(plot_info["data"]) > 200:
                    plot_info["data"].pop(0)
                    plot_info["x"].pop(0)

                plot_info["curve"].setPen(pg.mkPen(sensor.state.color, width=2))
                plot_info["curve"].setData(plot_info["x"], plot_info["data"])

                color = sensor.state.color
                icon_color = color if not sensor.state.blink or self.blink_on else "transparent"
                plot_info["led"].setPixmap(self.make_state_circle(icon_color).pixmap(14, 14))

        # --- LOGGING (1x per tick, NIET per sensor!) ---
        if self.logging_active:
            entry = {
                "time": self.system.time,
                "system_state" : self.system.state.label,
                "groups": []
            }

            for group in self.system.groups:
                group_data = {
                    "group": group.name,
                    "state" : group.state.label,
                    "sensors": []
                }

                for sensor in group.sensors:
                    group_data["sensors"].append({
                        "name": sensor.name,
                        "value": sensor.currentValue,
                        "state": sensor.state.label
                    })

                entry["groups"].append(group_data)
            self.logged_data.append(entry)

    # ----------------------------------------------------
    # DRAW CIRCLE ICON
    # ----------------------------------------------------
    def make_state_circle(self, kleur, diameter=12):
        pixmap = QPixmap(diameter, diameter)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(kleur))
        painter.setPen(Qt.GlobalColor.transparent)
        painter.drawEllipse(0, 0, diameter, diameter)
        painter.end()

        return QIcon(pixmap)


# ----------------------------------------------------
# START APP
# ----------------------------------------------------
app = QApplication(sys.argv)
window = MainWindow(system)
window.show()
sys.exit(app.exec())
