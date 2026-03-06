from enum import Enum
import random
from collections import Counter
import time
import yaml


with open("Code/Python/config.yaml", "r") as f:
    config = yaml.safe_load(f)


class SensorState(Enum):
    # gives the state + led color
    OK = ("ok", "green")
    WARNING = ("near danger", "orange")
    DANGER = ("danger", "blinking red")
    FAILED = ("failed", "red")

    def __init__(self, label, color):
        self.label = label
        self.color = color


# need to think if i want arming in the simulation
class SystemState(Enum):
    RUNNING = ("running", "green")
    WARNING = ("warning", "blinking orange")
    DANGER = ("danger", "blinking red")
    IDLE = ("idle", "red")
    ARMING = ("arming", "blinking green")

    def __init__(self, label, color):
        self.label = label
        self.color = color


class Sensor:
    def __init__(self, name, config):
        self.name = name
        self.min_value = config.get("min", 0)
        self.max_value = config.get("max", 100)
        self.noise = config.get("noise", 0.0)
        self.warningvalue = config.get("warning", None)
        self.failrate = config.get("failrate", 0.0)
        self.state = SensorState.OK

    def read(self):
        raise NotImplementedError("Must be defined in subclass")

    def simulate(self):
        raise NotImplementedError("Must be defined in sublass")


class UltraSonicSensor(Sensor):
    def __init__(self, name, config):
        super().__init__(name, config)
        self.currentValue = (self.min_value + self.max_value) / 2

    def simulate(self):
        # simulates a change in the value
        self.currentValue += random.uniform(-0.5, 1)

    def read(self):
        # reads the sensor
        if random.random() < 0.01:
            self.state = SensorState.FAILED
            return None
        # update sensor
        if self.state == SensorState.FAILED:
            return
        value = self.currentValue + random.uniform(-self.noise, self.noise)
        if value < self.min_value or value > self.max_value:
            self.state = SensorState.DANGER
        elif (
            self.warningvalue is not None and self.warningvalue < value < self.max_value
        ):
            self.state = SensorState.WARNING

        else:
            self.state = SensorState.OK
        # do i need to return value?
        return value


class SensorGroup:

    def __init__(self, name):
        self.name = name
        self.sensors = []
        self.state = SensorState.OK

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
        elif count[SensorState.WARNING] >= 2:
            self.state = SensorState.WARNING
        else:
            self.state = SensorState.OK


class System:
    def __init__(self):
        self.groups = []
        self.state = SystemState.IDLE

    def add_group(self, group):
        self.groups.append(group)

    def simulate(self):
        # simulate groups
        for group in self.groups:
            group.simulate()
        # read the sensor groups
        for group in self.groups:
            group.read_all()

        self.update_state()

    def update_state(self):
        # collect the groupstates
        group_states = [g.state for g in self.groups]

        if any(state == SensorState.DANGER for state in group_states):
            self.state = SystemState.DANGER
        elif any(state == SensorState.FAILED for state in group_states):
            self.state = SystemState.DANGER
        elif any(state == SensorState.WARNING for state in group_states):
            self.state = SystemState.WARNING
        else:
            self.state = SystemState.RUNNING


if __name__ == "__main__":
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
    while True:
        system.simulate()

        print(f"System state: {system.state.label} ({system.state.color})")
        for group in system.groups:
            print(f"  Group {group.name}: {group.state.label}")
            for sensor in group.sensors:
                print(f"    {sensor.name}: {sensor.state.label}, {sensor.currentValue}")

        print("-" * 40)
        if system.state == SystemState.DANGER:
            break
        time.sleep(0.5)
