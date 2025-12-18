/********************************************
   TTGO T-Call ESP32 SIM800L
   Soil Moisture + DHT22 + 16x4 LCD (hd44780_I2Cexp)
   With Django Backend Integration (SIM800L + GPRS)
*********************************************/

#include <Wire.h>
#include <hd44780.h>
#include <hd44780ioClass/hd44780_I2Cexp.h>
#include <DHT.h>
#include <ArduinoJson.h>

// ---------------------- SIM800L Configuration ----------------------
#define SIM800L_RX 26  // ESP32 RX pin connected to SIM800L TX
#define SIM800L_TX 27  // ESP32 TX pin connected to SIM800L RX
#define SIM800L_POWER_PIN 4  // Power control pin for SIM800L

HardwareSerial sim800(1);  // Use Serial1 for SIM800L

// ---------------------- APN Configuration ----------------------
const char* apn = "internet";  // Replace with your carrier's APN
const char* apnUser = "";      // APN username (if required)
const char* apnPass = "";      // APN password (if required)

// ---------------------- Server Configuration ----------------------
const char* serverHost = "192.168.0.152";         // Django server IP/domain
const int serverPort = 8008;
const char* submitPath = "/api/submit/";
const char* registerPath = "/api/register/";

String deviceId = "ESP32-001";                  // Unique device ID
String deviceName = "Soil Sensor 1";            // Device name
String deviceLocation = "Garden A";             // Device location
String apiKey = "";                             // Will be obtained after registration
String lastHttpResponse = "";                   // Store last HTTP response (headers+body)

// ---------------------- LCD Settings ----------------------
hd44780_I2Cexp lcd;  
const int LCD_COLS = 16;
const int LCD_ROWS = 4;

// ---------------------- Soil Moisture Sensor ----------------------
#define SOIL_PIN 34  // Analog input pin

// ---------------------- DHT22 Sensor ----------------------
#define DHTPIN 14
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// ---------------------- Timing ----------------------
unsigned long lastSendTime = 0;
const unsigned long sendInterval = 30000;  // Send data every 30 seconds

// -----------------------------------------------------------
// SIM800L Functions
// -----------------------------------------------------------
void powerOnSIM800L() {
  pinMode(SIM800L_POWER_PIN, OUTPUT);
  digitalWrite(SIM800L_POWER_PIN, HIGH);
  delay(1000);
  digitalWrite(SIM800L_POWER_PIN, LOW);
  delay(3000);
}

String sendATCommand(String command, unsigned long timeout = 1000) {
  sim800.println(command);
  String response = "";
  unsigned long startTime = millis();
  
  while (millis() - startTime < timeout) {
    while (sim800.available()) {
      char c = sim800.read();
      response += c;
    }
  }
  
  Serial.print("CMD: ");
  Serial.println(command);
  Serial.print("RSP: ");
  Serial.println(response);
  
  return response;
}

bool waitForResponse(String expected, unsigned long timeout = 10000) {
  String response = "";
  unsigned long startTime = millis();
  
  while (millis() - startTime < timeout) {
    while (sim800.available()) {
      char c = sim800.read();
      response += c;
      Serial.print(c);
      
      if (response.indexOf(expected) != -1) {
        return true;
      }
    }
  }
  return false;
}

// -----------------------------------------------------------
// Initialize SIM800L
// -----------------------------------------------------------
bool initSIM800L() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Init SIM800L...");
  
  sim800.begin(9600, SERIAL_8N1, SIM800L_RX, SIM800L_TX);
  delay(3000);
  
  // Test AT command
  sendATCommand("AT", 1000);
  delay(500);
  
  // Disable echo
  sendATCommand("ATE0", 1000);
  delay(500);
  
  // Check SIM card
  lcd.setCursor(0, 1);
  lcd.print("Checking SIM...");
  String simResponse = sendATCommand("AT+CPIN?", 2000);
  if (simResponse.indexOf("READY") == -1) {
    lcd.setCursor(0, 2);
    lcd.print("SIM Error!");
    return false;
  }
  
  // Wait for network
  lcd.setCursor(0, 1);
  lcd.print("Wait Network... ");
  int attempts = 0;
  while (attempts < 30) {
    String netResponse = sendATCommand("AT+CREG?", 2000);
    if (netResponse.indexOf(",1") != -1 || netResponse.indexOf(",5") != -1) {
      break;
    }
    delay(1000);
    attempts++;
    lcd.setCursor(14, 1);
    lcd.print(30 - attempts);
  }
  
  if (attempts >= 30) {
    lcd.setCursor(0, 2);
    lcd.print("Network Failed!");
    return false;
  }
  
  // Get signal strength
  String csqResponse = sendATCommand("AT+CSQ", 1000);
  lcd.setCursor(0, 2);
  lcd.print("Signal: ");
  lcd.print(csqResponse);
  delay(2000);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("SIM800L Ready!");
  delay(1000);
  
  return true;
}

// -----------------------------------------------------------
// Connect to GPRS
// -----------------------------------------------------------
bool connectGPRS() {
  lcd.setCursor(0, 1);
  lcd.print("Connect GPRS...");
  
  // Close any existing connection
  sendATCommand("AT+CIPSHUT", 2000);
  delay(1000);
  
  // Set connection type to GPRS
  sendATCommand("AT+CIPMODE=0", 1000);
  sendATCommand("AT+CIPMUX=0", 1000);
  
  // Set APN
  String apnCommand = "AT+CSTT=\"" + String(apn) + "\"";
  if (String(apnUser) != "") {
    apnCommand += ",\"" + String(apnUser) + "\",\"" + String(apnPass) + "\"";
  }
  sendATCommand(apnCommand, 2000);
  delay(1000);
  
  // Bring up wireless connection
  sendATCommand("AT+CIICR", 5000);
  delay(3000);
  
  // Get local IP address
  String ipResponse = sendATCommand("AT+CIFSR", 2000);
  
  if (ipResponse.indexOf("ERROR") != -1) {
    lcd.setCursor(0, 2);
    lcd.print("GPRS Failed!");
    return false;
  }
  
  lcd.setCursor(0, 2);
  lcd.print("GPRS Connected!");
  delay(1000);
  
  return true;
}

// -----------------------------------------------------------
// HTTP POST Request
// -----------------------------------------------------------
bool httpPost(String path, String jsonData) {
  // Close any existing connection
  sendATCommand("AT+CIPCLOSE", 1000);
  delay(500);
  
  // Start TCP connection
  String connectCmd = "AT+CIPSTART=\"TCP\",\"" + String(serverHost) + "\"," + String(serverPort);
  sendATCommand(connectCmd, 5000);
  
  if (!waitForResponse("CONNECT OK", 10000)) {
    Serial.println("Connection failed!");
    return false;
  }
  
  delay(1000);
  
  // Prepare HTTP request
  String httpRequest = "POST " + path + " HTTP/1.1\r\n";
  httpRequest += "Host: " + String(serverHost) + "\r\n";
  httpRequest += "Content-Type: application/json\r\n";
  httpRequest += "Content-Length: " + String(jsonData.length()) + "\r\n";
  httpRequest += "Connection: close\r\n\r\n";
  httpRequest += jsonData;
  
  // Send data length
  sendATCommand("AT+CIPSEND=" + String(httpRequest.length()), 2000);
  
  if (!waitForResponse(">", 5000)) {
    Serial.println("Send command failed!");
    return false;
  }
  
  // Send HTTP request
  sim800.print(httpRequest);
  delay(500);
  
  // Wait for response
  String response = "";
  unsigned long startTime = millis();
  while (millis() - startTime < 10000) {
    while (sim800.available()) {
      char c = sim800.read();
      response += c;
      Serial.print(c);
    }
    if (response.indexOf("CLOSED") != -1) {
      break;
    }
  }
  
  // Close connection
  sendATCommand("AT+CIPCLOSE", 1000);
  
  // Save full response for callers to parse (includes headers + body)
  lastHttpResponse = response;

  // Check if response contains HTTP 200 status
  if (response.indexOf("HTTP/1.1 200") != -1 || response.indexOf("200 OK") != -1) {
    return true;
  }

  return false;
}

// -----------------------------------------------------------
// Register Device with Server
// -----------------------------------------------------------
bool registerDevice() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Registering...");
  
  if (!connectGPRS()) {
    return false;
  }
  
  // Create JSON payload
  StaticJsonDocument<256> doc;
  doc["device_id"] = deviceId;
  doc["device_name"] = deviceName;
  doc["device_type"] = "multi";
  doc["location"] = deviceLocation;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  Serial.println("Registration JSON:");
  Serial.println(jsonString);
  
  if (httpPost(registerPath, jsonString)) {
    // Parse response body to extract api_key if present
    // lastHttpResponse contains headers followed by JSON body. Find first '{'
    int jsonStart = lastHttpResponse.indexOf('{');
    if (jsonStart != -1) {
      String body = lastHttpResponse.substring(jsonStart);
      Serial.println("Registration response body:");
      Serial.println(body);

      StaticJsonDocument<256> respDoc;
      DeserializationError err = deserializeJson(respDoc, body);
      if (!err && respDoc.containsKey("api_key")) {
        apiKey = String((const char*)respDoc["api_key"]);
      } else {
        // Fallback if server didn't include api_key
        apiKey = "temp_api_key_" + deviceId;
      }
    } else {
      // No JSON found - fallback to temp key
      apiKey = "temp_api_key_" + deviceId;
    }
    
    lcd.setCursor(0, 1);
    lcd.print("Registered OK!");
    delay(2000);
    return true;
  }
  
  lcd.setCursor(0, 1);
  lcd.print("Reg Failed!");
  delay(2000);
  return false;
}

// -----------------------------------------------------------
// Send Sensor Data to Server
// -----------------------------------------------------------
bool sendSensorData(float temp, float hum, int soilPercent, int soilRaw) {
  if (apiKey == "") {
    return false;
  }
  
  lcd.setCursor(0, 3);
  lcd.print("Sending...      ");
  
  if (!connectGPRS()) {
    return false;
  }
  
  // Get signal strength
  String csqResponse = sendATCommand("AT+CSQ", 1000);
  int signalStrength = -99;
  int csqIndex = csqResponse.indexOf("+CSQ: ");
  if (csqIndex != -1) {
    String csqValue = csqResponse.substring(csqIndex + 6, csqResponse.indexOf(",", csqIndex));
    signalStrength = csqValue.toInt();
  }
  
  // Create JSON payload
  StaticJsonDocument<512> doc;
  doc["device_id"] = deviceId;
  doc["api_key"] = apiKey;
  doc["temperature"] = temp;
  doc["humidity"] = hum;
  doc["soil_moisture"] = soilPercent;
  doc["soil_raw"] = soilRaw;
  doc["battery_level"] = 100.0;
  doc["signal_strength"] = signalStrength;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  Serial.println("Sending JSON:");
  Serial.println(jsonString);
  
  if (httpPost(submitPath, jsonString)) {
    lcd.setCursor(0, 3);
    lcd.print("Sent OK!        ");
    return true;
  }
  
  lcd.setCursor(0, 3);
  lcd.print("Send Failed!    ");
  return false;
}

// -----------------------------------------------------------
// SETUP
// -----------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(500);

  // ----------- LCD INIT -----------
  int status = lcd.begin(LCD_COLS, LCD_ROWS);
  if (status) {  
    hd44780::fatalError(status);
  }

  lcd.clear();
  lcd.print("Soil IoT v2.0");
  lcd.setCursor(0, 1);
  lcd.print("SIM800L Mode");
  delay(1500);

  // ----------- Soil Sensor -----------
  pinMode(SOIL_PIN, INPUT);

  // ----------- DHT22 INIT -----------
  dht.begin();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("DHT22 Ready");
  delay(1000);

  // ----------- SIM800L Init -----------
  powerOnSIM800L();
  if (initSIM800L()) {
    registerDevice();
  }
  
  lcd.clear();
}

// -----------------------------------------------------------
// LOOP
// -----------------------------------------------------------
void loop() {
  // ----------- READ SOIL MOISTURE -----------
  int soilRaw = analogRead(SOIL_PIN);
  int soilPercent = map(soilRaw, 4095, 1500, 0, 100);
  soilPercent = constrain(soilPercent, 0, 100);

  // ----------- READ DHT22 -----------
  float temp = dht.readTemperature();
  float hum  = dht.readHumidity();

  // Handle potential DHT read errors
  if (isnan(temp) || isnan(hum)) {
    temp = 0;
    hum = 0;
    Serial.println("DHT22 ERROR: Check wiring");
  }

  // ----------- SERIAL DEBUG -----------
  Serial.println("------- SENSOR DATA -------");
  Serial.print("Soil Moisture: "); Serial.print(soilPercent); Serial.println("%");
  Serial.print("Raw Soil: "); Serial.println(soilRaw);
  Serial.print("Temp: "); Serial.print(temp); Serial.println(" C");
  Serial.print("Humidity: "); Serial.print(hum); Serial.println(" %");
  Serial.println("---------------------------");

  // ----------- LCD DISPLAY -----------
  // Line 0: Soil % and Temperature
  lcd.setCursor(0, 0);
  lcd.print("S:");
  lcd.print(soilPercent);
  lcd.print("% T:");
  lcd.print(temp, 1);
  lcd.print("C  ");

  // Line 1: Humidity and Raw Soil Value
  lcd.setCursor(0, 1);
  lcd.print("H:");
  lcd.print(hum, 0);
  lcd.print("% Raw:");
  lcd.print(soilRaw);
  lcd.print("    ");

  // ----------- SEND DATA TO SERVER -----------
  unsigned long currentTime = millis();
  if (currentTime - lastSendTime >= sendInterval) {
    if (sendSensorData(temp, hum, soilPercent, soilRaw)) {
      Serial.println("Data sent successfully!");
    } else {
      Serial.println("Failed to send data");
    }
    
    lastSendTime = currentTime;
  } else {
    // Show countdown
    int secondsUntilSend = (sendInterval - (currentTime - lastSendTime)) / 1000;
    lcd.setCursor(0, 2);
    lcd.print("Next: ");
    lcd.print(secondsUntilSend);
    lcd.print("s     ");
  }

  delay(1000);
}