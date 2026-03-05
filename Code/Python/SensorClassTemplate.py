class Name(Sensor):
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
