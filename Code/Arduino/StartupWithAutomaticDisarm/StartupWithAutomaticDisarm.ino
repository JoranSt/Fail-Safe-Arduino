//Variables for time
unsigned long lastMillisLed;
unsigned long lastMillisButton;
unsigned long timeButtonPressed;
unsigned long timeSystemOff;
unsigned long timeSystemOn;

//Pin numbers
int ledPinRed = 5;
int ledPinGreen = 3;
int buttonApin = 6;

//Variables for blinking
unsigned int redbrightness;
unsigned int greenbrightness;
int redbase = 255;
int greenbase = 128;
float fadeFactor = 1;

//Component states variables
int buttonState = 0;
int lastButtonState = 1;
int ledState = HIGH;

//Bools
bool safeToStart = false;
bool isFading = true;
bool isPressed = false;
bool idle = false;

void setup() {
  Serial.begin(9600);
  pinMode(ledPinRed, OUTPUT);
  pinMode(ledPinGreen, OUTPUT);
  pinMode(buttonApin, INPUT_PULLUP);
  analogWrite(ledPinRed, redbrightness);
  analogWrite(ledPinGreen, greenbrightness);
}

void fadefactor() {
  //reverses the fadefactor when maximum reached
  if (fadeFactor >= 1.0) {
    fadeFactor = 1.0;
    isFading = true;
  } else if (fadeFactor <= 0.0) {
    fadeFactor = 0.0;
    isFading = false;
  }
}
void blinkingLed() {
  //makes the led blink every 10 ms
  if (millis() - lastMillisLed > 10) {
    lastMillisLed = millis();
    redbrightness = redbase * fadeFactor;
    greenbrightness = greenbase * fadeFactor;
    analogWrite(ledPinRed, redbrightness);
    analogWrite(ledPinGreen, greenbrightness);
    fadeFactor += (isFading == false) ? 0.01 : -0.01;
  }
}
void toggleSystem() {
  //switches the led state
  digitalWrite(ledPinRed, ledState);
  digitalWrite(ledPinGreen, !ledState);
  ledState = !ledState;
  handleSystemStateChange(ledState);
}
void handleSystemStateChange(int state) {
  //tracks if the system is off (needed for disarming)
  if (state == LOW) {
    idle = true;
    timeSystemOff = millis();
  } else {
    idle = false;
    timeSystemOn = millis();
  }
}
bool timePassed(unsigned long startTime, unsigned long interval) {
  return millis() - startTime >= interval;
}

void loop() {
  buttonState = digitalRead(buttonApin);

  if (safeToStart == false) {
    blinkingLed();
    fadefactor();
    //detects when you start holding the button
    if (buttonState == LOW && buttonState != lastButtonState) {
      isPressed = true;
      timeButtonPressed = millis();
    }
    //arms the system after holding the button for 2 seconds
    if (isPressed && timePassed(timeButtonPressed, 2000)) {
      safeToStart = true;
      toggleSystem();
    }
  }

  if (buttonState == HIGH) {
    isPressed = false;
  }
  //turn the system on/off after arming it
  if (buttonState == LOW && safeToStart == true && timePassed(lastMillisButton, 500) && lastButtonState == HIGH) {
    toggleSystem();
    lastMillisButton = millis();
  }
  //disarms the system after being off for too long
  if (timePassed(timeSystemOff, 5000) && idle == true) {
    ledState = HIGH;
    idle = false;
    safeToStart = false;
  }
  lastButtonState = buttonState;
  Serial.print("ledState: ");
  Serial.println(ledState);
}
