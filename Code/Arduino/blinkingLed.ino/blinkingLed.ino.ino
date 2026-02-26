//www.kuongshun.com/
//2023.10.11

unsigned long myTime;
unsigned long lastMillis;
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


void setup() 
{
  Serial.begin(9600);
  pinMode(ledPinRed, OUTPUT);
  pinMode(ledPinGreen, OUTPUT);
  pinMode(buttonApin, INPUT_PULLUP);
  analogWrite(ledPinRed, redbrightness);
  analogWrite(ledPinGreen, greenbrightness);  
}

 void loop() 
{
  myTime = millis();

  
  if(safeToStart == false){

    if(myTime -lastMillis > 10){
      lastMillis = millis();

    
        redbrightness = redbase * fadeFactor;
        greenbrightness = greenbase * fadeFactor;
        analogWrite(ledPinRed, redbrightness);
        analogWrite(ledPinGreen, greenbrightness);
        
        
        fadeFactor += (isFading == false) ? 0.01:-0.01;
    }
    if(fadeFactor >= 1.0){
    fadeFactor = 1.0;
    isFading = true;   // start fading down
    delay(200);
  } 
  else if(fadeFactor <= 0.0){
    fadeFactor = 0.0;
    isFading = false;  // start fading up
    delay(200);
}
  }
  buttonState = digitalRead(buttonApin);
  // Detect button press (transition from HIGH to LOW)
  if (buttonState == LOW)
  {
    ledState = !ledState;  // toggle LED
    digitalWrite(ledPinRed, ledState);
    
    digitalWrite(ledPinGreen, !ledState);
    Serial.println("Pressed");
    delay(200); // simple debounce
  }
}

