from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QSize, QTimer
import pyqtgraph as pg
import numpy as np
from PyQt6.QtGui import QPixmap, QPainter, QColor, QIcon
import sys
sys.path.append("Code/Python")
from Simulation import *


system = System()
SENSOR_TYPES = {"UltraSonicSensor": UltraSonicSensor}
system = System()
for group_cfg in config["groups"]:
    group = SensorGroup(group_cfg["name"])
    typesensor = SENSOR_TYPES[group_cfg["type"]]

    for sensor_cfg in group_cfg["sensors"]:
        name = sensor_cfg["name"]
        sensor = typesensor(name, sensor_cfg)

        group.add_sensor(sensor)

    system.add_group(group)
    
    
    
class MainWindow(QWidget):
    def __init__(self, system):
        super().__init__()

        self.setWindowTitle("System Monitor")
        self.resize(1200, 800)
        self.system = system
        self.stacked = QStackedWidget()
        self.sensorAmount = sum(len(group.sensors) for group in self.system.groups)
        self.blink_on = True

        # ----------------------------------------------------
        # MAIN LAYOUT
        # ----------------------------------------------------
        main_layout = QHBoxLayout(self)

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

                curve = plot.plot(pen=pg.mkPen("cyan", width=2))

                plots[sensor] = {
                    "curve": curve,
                    "data": [],
                    "led": led
                }

                page_layout.addWidget(plot)

            page_layout.addStretch()
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
        self.info_state_text.setText(f"State: {state.label}")

        # blinking LED
        if state.blink:
            if self.blink_on:
                self.info_state_icon.setPixmap(self.make_state_circle(state.color).pixmap(14, 14))
            else:
                self.info_state_icon.setPixmap(self.make_state_circle("transparent").pixmap(14, 14))
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
    def toggle_blink(self):
        self.blink_on = not self.blink_on
    # ----------------------------------------------------
    # UPDATE GRAPHS (NO BLINKING)
    # ----------------------------------------------------
    def update_graphs(self):
        for group, plots in zip(self.system.groups, self.group_pages):
            for sensor in group.sensors:
                plot_info = plots[sensor]

                # add new value
                plot_info["data"].append(sensor.currentValue)
                if len(plot_info["data"]) > 200:
                    plot_info["data"].pop(0)

                # update curve (NO blinking)
                color = sensor.state.color
                pen = pg.mkPen(color=color, width=2)
                plot_info["curve"].setPen(pen)
                plot_info["curve"].setData(plot_info["data"])

                # update LED above graph (blinks)
                if sensor.state.blink:
                    if self.blink_on:
                        icon = self.make_state_circle(color)
                    else:
                        icon = self.make_state_circle("transparent")
                else:
                    icon = self.make_state_circle(color)

                plot_info["led"].setPixmap(icon.pixmap(14, 14))

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
