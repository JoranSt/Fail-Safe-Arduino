from enum import Enum
import random
from collections import Counter
import time


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
    def __init__(self, name, min_value, max_value, noise, warningvalue, failrate=0.0):
        self.name = name
        self.min_value = min_value
        self.max_value = max_value
        self.noise = noise
        self.failrate = failrate
        self.state = SensorState.OK
        self.warningvalue = warningvalue

    def read(self):
        raise NotImplementedError("Must be defined in subclass")

    def simulate(self):
        raise NotImplementedError("Must be defined in sublass")


class UltraSonicSensor(Sensor):
    def __init__(self, name, min_value, max_value, noise, warningvalue, failrate=0.0):
        super().__init__(name, min_value, max_value, noise, warningvalue, failrate)
        self.currentValue = (min_value + max_value) / 2

    def simulate(self):
        # simulates a change in the value
        self.currentValue += random.uniform(-0.5, 1)

    def read(self):
        # reads the sensor
        if random.random() < 0.01:
            self.state = SensorState.FAILED
            return None
        # update sensor
        value = self.currentValue + random.uniform(-self.noise, self.noise)
        if value < self.min_value or value > self.max_value:
            self.state = SensorState.DANGER
        elif self.warningvalue < value < self.max_value:
            self.state = SensorState.WARNING
        else:
            self.state = SensorState.OK

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

        if count[SensorState.DANGER] >= 2:
            self.state = SensorState.DANGER
        elif count[SensorState.WARNING] >= 2:
            self.state = SensorState.WARNING
        elif count[SensorState.Failed] >= 2:
            self.state = SensorState.FAILED
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
    distance_group = SensorGroup("Distance Sensors")
    distance_group.add_sensor(UltraSonicSensor("sensor1", 10, 30, 1, 20))
    distance_group.add_sensor(UltraSonicSensor("sensor2", 10, 30, 1, 20))
    distance_group.add_sensor(UltraSonicSensor("sensor3", 10, 30, 1, 20))
    system = System()
    system.add_group(distance_group)
    while True:
        system.simulate()

        print(f"System state: {system.state.label} ({system.state.color})")
        for group in system.groups:
            print(f"  Group {group.name}: {group.state.label}")
            for sensor in group.sensors:
                print(f"    {sensor.name}: {sensor.state.label}")

        print("-" * 40)
        if system.state == SystemState.DANGER:
            break
        time.sleep(0.5)
