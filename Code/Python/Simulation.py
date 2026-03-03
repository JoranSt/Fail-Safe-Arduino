from enum import Enum


class SensorState(Enum):
    # gives the state + led color
    OK = ("ok", "green")
    WARNING = ("warning", "yellow")
    DANGER = ("danger", "blinking red")
    FAILED = ("failed", "red")

    def __init__(self, label, color):
        self.label = label
        self.color = color


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
    def __init__(self, name, min_value, max_value, noise, failrate=0.0):
        self.name = name
        self.min_value = min_value
        self.max_value = max_value
        self.noise = noise
        self.failrate = failrate
        self.state = SensorState.OK

    def read(self):
        raise NotImplementedError("Must be defined in subclass")

    def stimulate(self):
        raise NotImplementedError("Must be defined in sublass")
