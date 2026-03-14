from enum import Enum
import random
from collections import Counter
import time
import yaml
import json
import serial

# ---------------- ENUMS ---------------- #

class SensorState(Enum):
    OK = ("ok", "green", False)
    WARNING = ("near danger", "orange", True)
    DANGER = ("danger", "red", True)
    FAILED = ("failed", "red", True)

    def __init__(self, label, color, blink):
        self.label = label
        self.color = color
        self.blink = blink

    @staticmethod
    def from_label(label: str):
        for state in SensorState:
            if state.label == label:
                return state
        raise ValueError(f"Unknown SensorState label: {label}")


class SystemState(Enum):
    RUNNING = ("running", "green", False)
    WARNING = ("warning", "orange", True)
    DANGER = ("danger", "red", True)
    IDLE = ("idle", "red", False)
    ARMING = ("arming", "green", True)

    def __init__(self, label, color, blink):
        self.label = label
        self.color = color
        self.blink = blink

    @staticmethod
    def from_label(label: str):
        for state in SystemState:
            if state.label == label:
                return state
        raise ValueError(f"Unknown SystemState label: {label}")


# ---------------- SENSORS ---------------- #

class Sensor:
    def __init__(self, name, config, min_value=None, max_value = None):
        self.name = name
        self.min_value = min_value if min_value is not None else config.get("min", 0)
        self.max_value = max_value if max_value is not None else config.get("max", 100)
        self.noise = config.get("noise", 0.0)
        self.warningvalue = config.get("warning", None)
        self.failrate = config.get("failrate", 0.0)
        self.state = SensorState.OK
        self.history_x = []
        self.history_y = []
    


    def read(self):
        raise NotImplementedError("Must be defined in subclass")

    def simulate(self):
        raise NotImplementedError("Must be defined in subclass")

class ArduinoSensor(Sensor):
    def __init__(self, name, config, value, min_value=0, max_value=0,):
        super().__init__(name, config, min_value, max_value)
        self.currentValue = value
        
    def read(self):
        if random.random() < self.failrate:
            self.state = SensorState.FAILED
            return

        if self.state == SensorState.FAILED:
            return
        if  self.currentValue < float(self.max_value):
            self.state = SensorState.DANGER
        elif (
            float(self.min_value) > self.currentValue > float(self.max_value)
        ):
            self.state = SensorState.WARNING
        else:
            self.state = SensorState.OK
        return
    def simulate(self):
        pass
    
class UltraSonicSensor(Sensor):
    def __init__(self, name, config):
        super().__init__(name, config)
        self.currentValue = (self.min_value + self.max_value) / 2

    def simulate(self):
        if self.state == SensorState.FAILED:
            return
        self.currentValue += random.uniform(-0.05, 0.1)

    def read(self):
        if random.random() < self.failrate:
            self.state = SensorState.FAILED
            return

        if self.state == SensorState.FAILED:
            return

        value = self.currentValue + random.uniform(-self.noise, self.noise)

        if value < self.min_value or value > self.max_value:
            self.state = SensorState.DANGER
        elif (
            self.warningvalue is not None
            and self.warningvalue < value < self.max_value
        ):
            self.state = SensorState.WARNING
        else:
            self.state = SensorState.OK

        return value


# ---------------- GROUPS ---------------- #

class SensorGroup:
    def __init__(self, name):
        self.name = name
        self.sensors = []
        self.state = SensorState.OK
        self.plots = []

    def add_sensor(self, sensor):
        self.sensors.append(sensor)

    def simulate(self):
        for s in self.sensors:
            s.simulate()

    def read_all(self):
        for s in self.sensors:
            s.read()
        self.update_state()

    def update_state(self):
        states = [s.state for s in self.sensors]
        count = Counter(states)

        if count[SensorState.DANGER] + count[SensorState.FAILED] >= 2:
            self.state = SensorState.DANGER
            return
        elif count[SensorState.WARNING] + count[SensorState.FAILED] >= 2:
            self.state = SensorState.WARNING
            return
        else:
            self.state = SensorState.OK


# ---------------- SYSTEM ---------------- #

class System:
    def __init__(self, config):
        self.config = config
        self.mode = config["mode"]
        self.groups = []
        self.state = SystemState.IDLE
        self.start_time = time.time()
        self.time = 0
        self.buffer = ""

        self.SENSOR_TYPES = {
            "UltraSonicSensor": UltraSonicSensor
        }

        if self.mode == "replay":
            self._load_replay_data()
            
        elif self.mode == "arduino":
            self._connect_arduino()
        else:
            self._load_groups_from_config()

    # ---- config → groepen/sensoren (simulation/arduino) ---- #

    def _load_groups_from_config(self):
        for group_cfg in self.config["groups"]:
            group = SensorGroup(group_cfg["name"])
            typesensor = self.SENSOR_TYPES[group_cfg["type"]]

            for sensor_cfg in group_cfg["sensors"]:
                name = sensor_cfg["name"]

                if self.mode == "simulation":
                    sensor = typesensor(name, sensor_cfg)
                else:
                    sensor = Sensor(name, sensor_cfg)

                group.add_sensor(sensor)

            self.groups.append(group)

    # ---- replay data inladen ---- #

    def _load_replay_data(self):
        replay_cfg = self.config["replay"]
        if isinstance(replay_cfg, dict):
            replay_file = replay_cfg["file"]
        else:
            replay_file = replay_cfg

        with open(replay_file, "r") as f:
            self.replay_log = json.load(f)

        self.replay_index = 0

        # structuur uit eerste entry
        self.groups = []
        first = self.replay_log[0]["groups"]

        for g in first:
            group = SensorGroup(g["group"])
            for s in g["sensors"]:
                sensor = Sensor(s["name"], {})
                sensor.currentValue = s.get("value", 0)
                group.add_sensor(sensor)
            self.groups.append(group)

    # ---- arduino stub ---- #
    def parse_line(self,line):
            data = {}
            
            for part in line.strip().split(";"):
                key, value = part.split("=")
                data[key] = value
            return data
    
    def _connect_arduino(self):
        self.ser = serial.Serial(self.config["port"], self.config["baud"], timeout=1)
        time.sleep(5)
        self.ser.reset_input_buffer()
        self.arduino_setup()
        
    def arduino_setup(self):
        raw = self.ser.readline().decode().strip()
        if not raw:
            return  # lege regel
        data = self.parse_line(raw)

        if "GROUP" not in data:
            return  # incomplete regel, skip

        group = SensorGroup(data["GROUP"])
        if(group not in self.groups):
            s1 = float(data["S1"])
            s2 = float(data["S2"])
            s3 = float(data["S3"])
            group.add_sensor(ArduinoSensor("S1", self.config, s1, data["Min"], data["Max"]))
            group.add_sensor(ArduinoSensor("S2", self.config, s2, data["Min"], data["Max"]))
            group.add_sensor(ArduinoSensor("S3", self.config, s3, data["Min"], data["Max"]))
            self.groups.append(group)
        print(self.groups)
            
    def read_arduino(self):
        raw = self.ser.readline().decode(errors="ignore").strip()
        if not raw:
            return

        data = self.parse_line(raw)
        group_name = data["GROUP"]
        group = next((g for g in self.groups if g.name == group_name), None)

        # Update values from the objects
        group.sensors[0].currentValue = float(data["S1"])
        group.sensors[1].currentValue = float(data["S2"])
        group.sensors[2].currentValue = float(data["S3"])
        for i, key in enumerate(["S1", "S2", "S3"]):
            if key in data:
                value = float(data[key])
                sensor = group.sensors[i]

               

                sensor.currentValue = value
        # update de group
        group.read_all()
        
    # ---- main simulate ---- #

    def simulate(self):
        if self.mode == "replay":
            self._simulate_replay()
            return

        if self.mode == "simulation":
            self._simulate_live()
            for group in self.groups:
                group.simulate()
                group.read_all()

        elif self.mode == "arduino":
            self._simulate_arduino()
            for group in self.groups:
                group.read_all()

        self.update_state()

    def _simulate_live(self):
        self.time = time.time() - self.start_time
    def _simulate_arduino(self):
        self.time = time.time() - self.start_time
        self.read_arduino()
    def _simulate_replay(self):
        if self.replay_index >= len(self.replay_log):
            return

        entry = self.replay_log[self.replay_index]

        
        log_time = entry["time"]

        # first frame that displays directly
        if self.replay_index == 0:
            self.replay_start = time.time()
            self.log_start = log_time
        else:
            # time for plotting
            elapsed_log = log_time - self.log_start
            elapsed_real = time.time() - self.replay_start

            # wait if its too fast
            if elapsed_real < elapsed_log:
                return 
        self.time = log_time
        self.state = SystemState.from_label(entry["system_state"])

        for g_entry, group in zip(entry["groups"], self.groups):
            group.state = SensorState.from_label(g_entry["state"])

            for s_entry, sensor in zip(g_entry["sensors"], group.sensors):
                sensor.currentValue = s_entry["value"]
                sensor.state = SensorState.from_label(s_entry["state"])

        self.replay_index += 1
    # ---- state update (simulation/arduino) ---- #

    def update_state(self):
        if self.mode == "replay":
            # in replay the state comes from the log
            return

        group_states = [g.state for g in self.groups]
        self.time = time.time() - self.start_time

        if any(state == SensorState.DANGER for state in group_states):
            self.state = SystemState.DANGER
        elif any(state == SensorState.FAILED for state in group_states):
            self.state = SystemState.DANGER
        elif any(state == SensorState.WARNING for state in group_states):
            self.state = SystemState.WARNING
        else:
            self.state = SystemState.RUNNING


# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    with open("Code/Python/config.yaml", "r") as f:
        config = yaml.safe_load(f)

    system = System(config)

    while True:
        system.simulate()

        print(f"System state: {system.state.label} ({system.state.color})")
        for group in system.groups:
            print(f"  Group {group.name}: {group.state.label}")
            for sensor in group.sensors:
                print(f"    {sensor.name}: {sensor.state.label}, {sensor.currentValue}")

        print("-" * 40)

        if system.mode != "replay" and system.state == SystemState.DANGER:
            break

        time.sleep(0.5)
