/*
  Particle Photon 2 - Web Controlled LEDs + LCD
  
  SAFE WIRING GUIDE (3.3V Logic):
  - LEDs: Connect Anodes (+) to Pins D0, D1, D2. 
          Connect Cathodes (-) to Resistors -> GND.
  
  - Buttons: Connect one leg to Pins A0, A1, A2.
             Connect the other leg to GND.
             
  - LCD:  VCC -> VUSB (5V)
          GND -> GND
          RS  -> D3
          EN  -> D4
          D4  -> D5
          D5  -> D6
          D6  -> D7
          D7  -> A4  
          RW  -> GND
*/

// 1. Include Particle Library (Required for Workbench, optional for Web IDE)
#include "Particle.h"

// 2. Include LiquidCrystal
// In the Web IDE, you must click the "Libraries" icon, search for 
// "LiquidCrystal", and click "INCLUDE IN PROJECT".
#include <LiquidCrystal.h>

// --- PIN DEFINITIONS (Photon 2 Mapped) ---

// LCD Pins
const int rs = D3, en = D4, d4 = D5, d5 = D6, d6 = D7, d7 = A4;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

// LED Pins
const int ledGreen = D0;
const int ledRed   = D1;
const int ledBlue  = D2;

// Button Pins (Using Analog pins as Digital Inputs)
const int btnBlue  = A0; 
const int btnGreen = A1; 
const int btnRed   = A2; 

// Potentiometer (Optional - for input reading)
const int potPin = A3;

// Global Variable for Status
int ledStatus = 4; 

// --- CLOUD FUNCTION ---
int setLedFromWeb(String command) {
    if(command == "blue") {
        ledStatus = 0;
        return 1; 
    }
    else if(command == "green") {
        ledStatus = 1;
        return 1;
    }
    else if(command == "red") {
        ledStatus = 2;
        return 1;
    }
    else {
        return -1; 
    }
}

void setup() {
  // --- CLOUD REGISTRATION ---
  // This exposes the function to the HTML file
  Particle.function("setStatus", setLedFromWeb);

  // --- LED SETUP ---
  pinMode(ledGreen, OUTPUT);
  pinMode(ledRed, OUTPUT);
  pinMode(ledBlue, OUTPUT);

  // --- BUTTON SETUP ---
  // INPUT_PULLUP is safe for Photon. 
  // It holds the pin at 3.3V until button connects it to GND.
  pinMode(btnBlue, INPUT_PULLUP);
  pinMode(btnGreen, INPUT_PULLUP);
  pinMode(btnRed, INPUT_PULLUP);

  // --- POTENTIOMETER SETUP ---
  pinMode(potPin, INPUT);

  // --- LCD SETUP ---
  lcd.begin(16, 2);
  lcd.print("Photon 2 Online");
  delay(1000);
  lcd.clear();
}

void loop() {
  // --- READ PHYSICAL BUTTONS ---
  // Low = Pressed (because of Pull-Up)
  if (digitalRead(btnBlue) == LOW) ledStatus = 0;
  else if (digitalRead(btnGreen) == LOW) ledStatus = 1;
  else if (digitalRead(btnRed) == LOW) ledStatus = 2;

  // --- UPDATE LCD TIMER ---
  lcd.setCursor(0, 1);
  lcd.print("Time: ");
  lcd.print(millis() / 1000);
  
  // Optional: Read Potentiometer
  // int potValue = analogRead(potPin); 

  // --- UPDATE LEDS ---
  // We check if status changed to avoid flickering, 
  // but for simplicity, we write every loop here.
  
  if(ledStatus == 0){
      digitalWrite(ledBlue, HIGH);
      digitalWrite(ledGreen, LOW);
      digitalWrite(ledRed, LOW);
      lcd.setCursor(0, 0);
      lcd.print("Blue Mode       "); 
      
  } else if(ledStatus == 1){
      digitalWrite(ledBlue, LOW);
      digitalWrite(ledGreen, HIGH);
      digitalWrite(ledRed, LOW);
      lcd.setCursor(0, 0);
      lcd.print("Green Mode      ");

  } else if(ledStatus == 2){
      digitalWrite(ledBlue, LOW);
      digitalWrite(ledGreen, LOW);
      digitalWrite(ledRed, HIGH);
      lcd.setCursor(0, 0);
      lcd.print("Red Mode        ");

  } else {
      digitalWrite(ledBlue, LOW);
      digitalWrite(ledGreen, LOW);
      digitalWrite(ledRed, LOW);
      lcd.setCursor(0, 0);
      lcd.print("Ready...        "); 
  }   
}