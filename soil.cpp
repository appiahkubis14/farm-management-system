/********************************************
   TTGO T-Call ESP32 SIM800L
   Soil Moisture + DHT22 + 16x4 LCD (hd44780_I2Cexp)
*********************************************/

#include <Wire.h>
#include <hd44780.h>
#include <hd44780ioClass/hd44780_I2Cexp.h>

#include <DHT.h>

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

// ---------------------- SIM800L Pins ----------------------
#define MODEM_RST            5
#define MODEM_POWER_ON       23
#define MODEM_TX             27
#define MODEM_RX             26
#define MODEM_DTR            32
#define MODEM_RI             33

#include <HardwareSerial.h>
HardwareSerial sim800l(1); 

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
  lcd.print("Soil IoT Device");
  lcd.setCursor(0, 1);
  lcd.print("Initializing...");
  delay(1500);
  lcd.clear();

  // ----------- Soil Sensor -----------
  pinMode(SOIL_PIN, INPUT);

  // ----------- DHT22 INIT -----------
  dht.begin();
  lcd.setCursor(0, 0);
  lcd.print("DHT22 Ready");
  delay(800);
  lcd.clear();

  // ----------- SIM800L INIT -----------
  pinMode(MODEM_POWER_ON, OUTPUT);
  digitalWrite(MODEM_POWER_ON, HIGH);

  sim800l.begin(115200, SERIAL_8N1, MODEM_RX, MODEM_TX);
  lcd.setCursor(0, 1);
  lcd.print("SIM800L Booting...");
  delay(3000);

  sim800l.println("AT");
  delay(500);
  sim800l.println("AT+CSQ");
  delay(500);
  sim800l.println("AT+CREG?");
  delay(500);

  lcd.setCursor(0, 2);
  lcd.print("Ready!");
  delay(1000);
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
  lcd.setCursor(0, 0);
  lcd.print("Soil:");
  lcd.print(soilPercent);
  lcd.print("%   ");

  lcd.setCursor(0, 1);
  lcd.print("Raw:");
  lcd.print(soilRaw);
  lcd.print("   ");

  lcd.setCursor(0, 2);
  lcd.print("Temp:");
  lcd.print(temp);
  lcd.print("C   ");

  lcd.setCursor(0, 3);
  lcd.print("Hum:");
  lcd.print(hum);
  lcd.print("%    ");

  delay(2000);
}
