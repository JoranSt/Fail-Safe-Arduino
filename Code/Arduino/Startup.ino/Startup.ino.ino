//www.kuongshun.com/
//2023.10.11


unsigned long lastMillisLed;
unsigned long lastMillisButton;
unsigned long timeButtonPressed;
int ledPinRed = 5;
int ledPinGreen = 3;
int buttonApin = 6;
unsigned int redbrightness;
unsigned int greenbrightness;
int buttonState = 0;
int lastButtonState = 1;
int ledState = LOW;
bool safeToStart = false;
bool isFading = true;
int redbase = 255;
int greenbase = 128;
float fadeFactor = 1;
bool isPressed = false;


void setup() {
  Serial.begin(9600);
  pinMode(ledPinRed, OUTPUT);
  pinMode(ledPinGreen, OUTPUT);
  pinMode(buttonApin, INPUT_PULLUP);
  analogWrite(ledPinRed, redbrightness);
  analogWrite(ledPinGreen, greenbrightness);
}

void loop() {



  if (safeToStart == false) {             // outer if
    if (millis() - lastMillisLed > 10) {  // inner fade timing
      lastMillisLed = millis();
      redbrightness = redbase * fadeFactor;
      greenbrightness = greenbase * fadeFactor;
      analogWrite(ledPinRed, redbrightness);
      analogWrite(ledPinGreen, greenbrightness);
      fadeFactor += (isFading == false) ? 0.01 : -0.01;
    }

    // fade direction logic
    if (fadeFactor >= 1.0) {
      fadeFactor = 1.0;
      isFading = true;
    } else if (fadeFactor <= 0.0) {
      fadeFactor = 0.0;
      isFading = false;
    }
  }

  buttonState = digitalRead(buttonApin);
  if (buttonState == LOW && buttonState != lastButtonState && safeToStart == false) {
    isPressed = true;
    Serial.println("pressed");
    timeButtonPressed = millis();
  }
  // long press check — only while button is pressed
  if (isPressed && !safeToStart) {
    if (millis() - timeButtonPressed >= 2000) {
      safeToStart = true;  // confirmed long press
      digitalWrite(ledPinRed, ledState);
      digitalWrite(ledPinGreen, !ledState);
      Serial.println("Long press detected!");
    }
  }

  // reset on release
  if (buttonState == HIGH) {
    isPressed = false;
  }

  else if(buttonState == LOW && safeToStart == true && millis() - lastMillisButton >= 1000 && isPressed == false ){
      ledState = !ledState;  // toggle LED
      digitalWrite(ledPinRed, ledState);
      digitalWrite(ledPinGreen, !ledState);
      Serial.println("Pressed");
      lastMillisButton = millis();
  }
  lastButtonState = buttonState;  // moved inside
  
}
