# python envirometn with pyserial, pyyamlpyqt6
import serial
import yaml
from Code.Python.Simulation import *

SENSOR_TYPES = {"UltraSonicSensor", UltraSonicSensor}
with open("Code/Python/config.yaml", "r") as f:
    config = yaml.safe_load(f)

system = System()
mode = config["mode"]
# breakpoint config file to understand behaviour note to self
for group_cfg in config["groups"]:
    group = SensorGroup(group_cfg["name"])
    type = SENSOR_TYPES[group_cfg["type"]]

    for sensor_cfg in group_cfg["sensors"]:
        name = sensor_cfg["name"]

        if mode == "simulation":

            min_val = sensor_cfg["min"]
            max_val = sensor_cfg["max"]
            sensor = type(name, min_val=min_val, max_val=max_val)
        else:
            sensor = Sensor(name)  # fallback

        group.add_sensor(sensor)

    system.add_group(group)
