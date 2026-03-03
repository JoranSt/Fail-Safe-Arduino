from enum import Enum
import random


class SensorState(Enum):
    # gives the state + led color
    OK = ("ok", "green")
    THRESHOLDWARNING = ("near danger", "orange")
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
        if random.random(0, 1) < 0.01:
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


test = UltraSonicSensor("sensor", 10, 30, 1, 20)
