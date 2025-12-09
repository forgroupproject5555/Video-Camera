/*
 * PROJECT: Study Sergeant Hardware (Photon P2)
 * AUTHOR: Brendon, Jonah, Kincaid, Sagar
 * DATE: Dec 2025
 */

#include "Particle.h"
#include <LiquidCrystal.h>

// --- MQTT LIBRARIES ---
#include "Adafruit_MQTT/Adafruit_MQTT.h"
#include "Adafruit_MQTT/Adafruit_MQTT_SPARK.h"

// --- CONFIGURATION ---
#define AIO_SERVER      "io.adafruit.com"
#define AIO_SERVERPORT  1883                   
#define AIO_USERNAME    "groupproject5555"
#define AIO_KEY         "aio_aZzg25M75FBUOxiA6E8qpfUZZ9pn"

// Global Objects
TCPClient TheClient;
Adafruit_MQTT_SPARK mqtt(&TheClient, AIO_SERVER, AIO_SERVERPORT, AIO_USERNAME, AIO_KEY);
Adafruit_MQTT_Subscribe deviceStatus = Adafruit_MQTT_Subscribe(&mqtt, AIO_USERNAME "/feeds/devicestatus");

// --- HARDWARE PINS ---
const int ledGreen = D0; // Studying
const int ledRed   = D1; // Phone/Bad
const int ledyellow  = A0; // Neutral/Idle

// LCD Pins
const int rs = D2, en = D3, d4 = D4, d5 = D5, d6 = D6, d7 = D7;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

// --- TIMER VARIABLES ---
String currentStatus = "";
String lastStatus = "";
unsigned long lastStatusChangeTime = 0;
bool messageShown = false; // Prevents LCD flickering

void MQTT_connect();

void setup() {
  Serial.begin(115200);
  
  pinMode(ledGreen, OUTPUT);
  pinMode(ledRed, OUTPUT);
  pinMode(ledyellow, OUTPUT);
  
  lcd.begin(16, 2);
  lcd.print("Study Sergeant");
  lcd.setCursor(0, 1);
  lcd.print("Connecting...");
  
  delay(2000);
  mqtt.subscribe(&deviceStatus);
}

void loop() {
  MQTT_connect();

  // Check for incoming data (timeout 200ms)
  Adafruit_MQTT_Subscribe *subscription;
  while ((subscription = mqtt.readSubscription(200))) {
    if (subscription == &deviceStatus) {
      
      // 1. Get the new status
      String incomingStatus = (char *)deviceStatus.lastread;
      
      // 2. IMMEDIATE LED UPDATE (Always happens instantly)
      digitalWrite(ledGreen, LOW);
      digitalWrite(ledRed, LOW);
      digitalWrite(ledyellow, LOW);

      if (incomingStatus == "Studying") {
        digitalWrite(ledGreen, HIGH);
      } 
      else if (incomingStatus == "On Phone") {
        digitalWrite(ledRed, HIGH);
      }
      else {
        digitalWrite(ledyellow, HIGH); 
      }

      // 3. TIMER LOGIC FOR LCD
      // If status CHANGED from what we had before
      if (incomingStatus != lastStatus) {
         lastStatus = incomingStatus;
         lastStatusChangeTime = millis(); // Reset timer
         messageShown = false; // Ready to show new message later
         
         // Update LCD immediately to show current raw status
         lcd.clear();
         lcd.setCursor(0, 0);
         lcd.print("Status:");
         lcd.setCursor(0, 1);
         if(incomingStatus.length() > 16) incomingStatus = incomingStatus.substring(0, 16);
         lcd.print(incomingStatus);
      }
    }
  }

  // 4. CHECK 10-SECOND TIMER
  // If 10 seconds (10000ms) passed since last change AND we haven't updated LCD yet
  if (!messageShown && (millis() - lastStatusChangeTime > 10000)) {
      
      lcd.clear();
      lcd.setCursor(0, 0); // Top Row

      if (lastStatus == "Studying") {
          lcd.print("Great Job!");
          lcd.setCursor(0, 1);
          lcd.print("Keep it up!");
      } 
      else if (lastStatus == "On Phone") {
          lcd.print("GET OFF PHONE!");
          lcd.setCursor(0, 1);
          lcd.print("Focus now!");
      }
      else {
          lcd.print("Are you there?");
          lcd.setCursor(0, 1);
          lcd.print("Start working!");
      }
      
      messageShown = true; // Lock it so it doesn't flicker
  }
}

// Helper to keep connection alive
void MQTT_connect() {
  int8_t ret;
  if (mqtt.connected()) return;

  while ((ret = mqtt.connect()) != 0) {
       Serial.println(mqtt.connectErrorString(ret));
       mqtt.disconnect();
       delay(5000);
  }
}