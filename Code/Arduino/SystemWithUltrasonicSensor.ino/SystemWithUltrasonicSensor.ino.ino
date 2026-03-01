#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <NewPing.h>
//look into structs note for self
//Pin numbers
int ledPinRed = 5;
int ledPinGreen = 3;
int buttonApin = 6;
#define TRIG_PIN 12
#define ECHO_PIN 11
#define ENABLE 9
#define DIRA 8
#define DIRB 10

enum SystemState {
  ARMING,
  IDLE,
  RUNNING,
  WARNING,
  ERROR
};
SystemState State = ARMING;
SystemState lastState = State;
enum Warning : uint8_t { WARN_NONE = 0,
                         WARN_ULTRASONIC = 1 << 0  // 00000001

};
uint8_t warnings = WARN_NONE;
enum Error : uint8_t { ERROR_NONE = 0,
                       ERROR_ULTRASONIC = 1 << 0  //00000001
};
uint8_t errors = ERROR_NONE;
//Variables for time
unsigned long lastMillisLed;
unsigned long lastMillisButton;
unsigned long timeButtonPressed;
unsigned long timeSystemOff;
unsigned long timeSystemOn;
unsigned long startTime;
unsigned long readSensor;



//Variables for blinking
unsigned int redbrightness;
unsigned int greenbrightness;
int redbase = 255;
int greenbase = 128;
float fadeFactor = 0;

//Component states variables
int buttonState = 0;
int lastButtonState = 1;
int ledState = HIGH;

//Bools
bool safeToStart = false;
bool isFading = false;
bool isPressed = false;
bool startingMessageGone = false;
bool readyToArm = false;

//Variables for LCD
String startingMessage = "System powered";
LiquidCrystal_I2C lcd(0x27, 16, 2);

//Variable ultrasonic sensor
#define MAX_DISTANCE 200
NewPing sonar(TRIG_PIN, ECHO_PIN, MAX_DISTANCE);
double distance;
double safetyDistance = 30;
double unsafeDistance = 10;


void setup() {
  Serial.begin(9600);
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print(startingMessage);
  pinMode(ledPinRed, OUTPUT);
  pinMode(ledPinGreen, OUTPUT);
  pinMode(buttonApin, INPUT_PULLUP);
  pinMode(ENABLE, OUTPUT);
  pinMode(DIRA, OUTPUT);
  pinMode(DIRB, OUTPUT);
  startTime = millis();
}

void loop() {
  buttonState = digitalRead(buttonApin);
  if (!safeToStart && readyToArm && State == ARMING) {
    updateBlinkingAnimation(0, 255);
    handleArmingButton();

  } else if (timePassed(startTime, 5000) && !readyToArm && !safeToStart) {
    lcd.clear();
    displayMessage("Ready to arm", 0, 0);
    readyToArm = true;
  }
  if (millis() - readSensor >= 10) {
    readAllSensors();
    handleAllSensors();
    updateSystemState();
    updateLCD();
    readSensor = millis();
  }
  handleToggleButton();
  checkIdle();
  checkFan();
  lastButtonState = buttonState;
}
void readAllSensors() {
  distance = readUltraSonic();
}
void handleAllSensors() {
  handleUltrasonic(distance);
}
void checkFan(){
  if(State == RUNNING){
    digitalWrite(ENABLE,HIGH); // enable on
    digitalWrite(DIRA,HIGH); //one way
    return;
  }
  else if (State == WARNING){
    return;
  }
  digitalWrite(ENABLE, LOW);
  digitalWrite(DIRA, LOW);
}
void updateSystemState() {
  if (errors != ERROR_NONE) {
    State = ERROR;
    safeToStart = false;
    updateBlinkingAnimation(redbase, 0);
  } else if (warnings != WARN_NONE) {
    State = WARNING;
    updateBlinkingAnimation(redbase, greenbase);
  } else if (safeToStart && ledState == HIGH) {
    State = RUNNING;
  } else if (safeToStart && ledState == LOW) {
    State = IDLE;
  } else {
    State = ARMING;
  }
}
void updateLCD() {
  if (State == lastState) return;

  lcd.clear();

  lastState = State;
  switch (State) {
    case ERROR:
      displayMessage("ERROR!", 0, 0);
      displayMessage("Shutting down!", 0, 1);
      break;
    case WARNING:
      displayMessage("Warning:", 0, 0);
      showWarningMessages();
      break;
    case IDLE: displayMessage("System idle", 0, 0); break;
    case RUNNING: displayMessage("System running", 0, 0); break;
    case ARMING:
      displayMessage("Arm System &", 0, 0);
      displayMessage("Check safety", 0, 1);
      break;
  }
}
void handleToggleButton() {
  if (buttonState == HIGH) {
    isPressed = false;
  }
  //turn the system on/off after arming it
  if (buttonState == LOW && safeToStart == true && timePassed(lastMillisButton, 500) && lastButtonState == HIGH) {
    toggleSystem();
    lastMillisButton = millis();
  }
}
void updateBlinkingAnimation(int red, int green) {
  if (timePassed(lastMillisLed, 10)) {
    lastMillisLed = millis();
    redbrightness = red * fadeFactor;
    greenbrightness = green * fadeFactor;
    analogWrite(ledPinRed, redbrightness);
    analogWrite(ledPinGreen, greenbrightness);
    fadeFactor += (isFading == false) ? 0.01 : -0.01;
  }
  fadefactor();
}
void handleArmingButton() {
  // detects pressing button and logs when you started holding it
  if (buttonState == LOW && buttonState != lastButtonState) {
    isPressed = true;
    timeButtonPressed = millis();
  }

  // arms the system after holding the button for 2 seconds
  if (isPressed && timePassed(timeButtonPressed, 2000)) {
    safeToStart = true;
    toggleSystem();
  }
}
double readUltraSonic() {
  return sonar.ping_cm();
}
void handleUltrasonic(double distance) {
  if (distance >= unsafeDistance && distance <= safetyDistance) {
    warnings |= WARN_ULTRASONIC;
  } else if (unsafeDistance > distance) {
    errors |= ERROR_ULTRASONIC;
  } else {
    warnings &= ~WARN_ULTRASONIC;  // clear warning
    errors &= ~ERROR_ULTRASONIC;
  }
}
void checkIdle() {
  //checks if the system has been idle for too long and put it back in the arming state
  if (State == IDLE && timePassed(timeSystemOff, 5000)) {
    safeToStart = false;
    ledState = HIGH;
    State = ARMING;
  }
}

void toggleSystem() {
  //switches the led state
  ledState = !ledState;
  digitalWrite(ledPinRed, !ledState);
  digitalWrite(ledPinGreen, ledState);

  handleSystemStateChange(ledState);
}
void handleSystemStateChange(int buttonState) {
  //tracks if the system is off (needed for disarming)
  if (buttonState == LOW) {
    State = IDLE;
    timeSystemOff = millis();
  } else {
    State = RUNNING;
    timeSystemOn = millis();
  }
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

void showWarningMessages() {
  if (warnings & WARN_ULTRASONIC) { displayMessage("Ultrasonic", 0, 1); }
}
void displayMessage(String message, int col, int row) {
  lcd.setCursor(col, row);
  lcd.print(message);
}
bool timePassed(unsigned long startTime, unsigned long interval) {
  return millis() - startTime >= interval;
}
