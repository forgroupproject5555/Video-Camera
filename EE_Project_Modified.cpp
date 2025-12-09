/*
 * PROJECT: Study Sergeant Hardware (Photon P2)
 * AUTHOR: Brendon & Group
 * DATE: Dec 2025
 */

#include "Particle.h"
#include <LiquidCrystal.h>

// --- MQTT LIBRARIES ---
// Make sure you have added "Adafruit_MQTT" library in Particle IDE
#include "Adafruit_MQTT/Adafruit_MQTT.h"
#include "Adafruit_MQTT/Adafruit_MQTT_SPARK.h"

// --- CONFIGURATION ---
#define AIO_SERVER      "io.adafruit.com"
#define AIO_SERVERPORT  1883                   
#define AIO_USERNAME    "groupproject5555"
#define AIO_KEY         "aio_WBHy59QVm16gFRQDsqVNFTRkvbsL"

// Global Objects
TCPClient TheClient;
Adafruit_MQTT_SPARK mqtt(&TheClient, AIO_SERVER, AIO_SERVERPORT, AIO_USERNAME, AIO_KEY);
Adafruit_MQTT_Subscribe deviceStatus = Adafruit_MQTT_Subscribe(&mqtt, AIO_USERNAME "/feeds/devicestatus");

// Hardware Pins
const int ledGreen = D0; // Studying (Good)
const int ledRed   = D1; // Phone (Bad)
const int ledBlue  = D2; // Distracted / Idle (Attention)

// LCD Pins (RS, EN, D4, D5, D6, D7)
// Adjust these if your wiring is different!
const int rs = D3, en = D4, d4 = D5, d5 = D6, d6 = D7, d7 = A4;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

void MQTT_connect();

void setup() {
  Serial.begin(115200);
  
  pinMode(ledGreen, OUTPUT);
  pinMode(ledRed, OUTPUT);
  pinMode(ledBlue, OUTPUT);
  
  lcd.begin(16, 2);
  lcd.print("Study Sergeant");
  lcd.setCursor(0, 1);
  lcd.print("Online...");
  
  delay(2000);
  mqtt.subscribe(&deviceStatus);
}

void loop() {
  MQTT_connect();

  // Check for incoming data (timeout 200ms)
  Adafruit_MQTT_Subscribe *subscription;
  while ((subscription = mqtt.readSubscription(200))) {
    if (subscription == &deviceStatus) {
      
      // Get the status string
      String status = (char *)deviceStatus.lastread;
      
      // Update LCD
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Status:");
      lcd.setCursor(0, 1);
      // Truncate if too long
      if(status.length() > 16) status = status.substring(0, 16);
      lcd.print(status);

      // --- LED LOGIC ---
      // Reset all LEDs first
      digitalWrite(ledGreen, LOW);
      digitalWrite(ledRed, LOW);
      digitalWrite(ledBlue, LOW);

      if (status == "Studying") {
        digitalWrite(ledGreen, HIGH);
      } 
      else if (status == "On Phone") {
        digitalWrite(ledRed, HIGH);
      }
      else {
        // "Distracted", "Away", "Idle", "Slouching" -> Blue
        digitalWrite(ledBlue, HIGH); 
      }
    }
  }
}

// Helper to keep connection alive
void MQTT_connect() {
  int8_t ret;
  if (mqtt.connected()) return;

  // Serial.print("Connecting to MQTT... ");
  while ((ret = mqtt.connect()) != 0) {
       // Serial.println(mqtt.connectErrorString(ret));
       mqtt.disconnect();
       delay(5000);
  }
  // Serial.println("MQTT Connected!");
}
