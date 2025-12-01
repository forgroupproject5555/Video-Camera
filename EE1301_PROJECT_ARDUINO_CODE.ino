/*
  LiquidCrystal - Hello World + LEDs + Passive Buzzer
  
  Hardware Setup:
  - LCD RS:     Pin 7
  - LCD Enable: Pin 8
  - LCD D4-D7:  Pins 9-12
  
  - LED 1-3:    Pins 28, 29, 30
  - Buzzer:     Pin 31 (Passive)
*/

#include <LiquidCrystal.h>

// LCD Pin Mapping
const int rs = 7, en = 8, d4 = 9, d5 = 10, d6 = 11, d7 = 12;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

// LED Pin Definitions
const int ledGreen = 28;
const int ledRed = 29;
const int ledBlue = 30;

// Buzzer Pin Definition
const int buzzerPin = 31;

void setup() {
  // --- LED SETUP ---
  pinMode(ledGreen, OUTPUT);
  pinMode(ledRed, OUTPUT);
  pinMode(ledBlue, OUTPUT);

  // --- BUZZER SETUP ---
  pinMode(buzzerPin, OUTPUT);

  // Turn LEDs ON
  digitalWrite(ledGreen, HIGH);
  digitalWrite(ledRed, HIGH);
  digitalWrite(ledBlue, HIGH);

  // --- LCD SETUP ---
  lcd.begin(16, 2);
  lcd.print("hello, world!");

  // --- MAKE NOISE ---
  // Syntax: tone(pin, frequency_in_hz, duration_in_ms)
  // 1000 Hz is a standard "beep" pitch.
  tone(buzzerPin, 5000, 1000); 
}

void loop() {
  int ledStatus=0;
  lcd.setCursor(0, 1);
  lcd.print(millis() / 1000);
    if(ledStatus==0){
      digitalWrite(ledBlue, HIGH);
      digitalWrite(ledGreen, LOW);
      digitalWrite(ledRed, LOW);
    }else if(ledStatus==1){
      digitalWrite(ledBlue, LOW);
      digitalWrite(ledGreen, HIGH);
      digitalWrite(ledRed, LOW);
   }else if(ledStatus==2){
      digitalWrite(ledBlue, LOW);
      digitalWrite(ledGreen, LOW);
      digitalWrite(ledRed, HIGH);
   }else{
    lcd.setCursor(0,0);
    lcd.print("LED_STATUS_ERROR");
    digitalWrite(ledBlue, LOW);
    digitalWrite(ledGreen, LOW);
    digitalWrite(ledRed, LOW);
   }
}

  







