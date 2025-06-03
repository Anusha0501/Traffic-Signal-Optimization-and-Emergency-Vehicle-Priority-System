#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// WiFi & MQTT
const char* ssid = "Your_SSID";
const char* password = "Your_PASSWORD";
const char* mqttServer = "broker.hivemq.com";
WiFiClient espClient;
PubSubClient client(espClient);

// GPIO pin layout for each lane: [RED, YELLOW, GREEN]
int signals[4][3] = {
  {5, 18, 19},
  {21, 22, 23},
  {25, 26, 27},
  {32, 33, 4}
};

void setupWiFi() {
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) delay(500);
}

void callback(char* topic, byte* payload, unsigned int length) {
  StaticJsonDocument<200> doc;
  deserializeJson(doc, payload);

  JsonArray lanes = doc["lanes"];
  JsonArray emergency = doc["emergency"];

  for (int i = 0; i < 4; i++) {
    digitalWrite(signals[i][0], HIGH); // RED by default
    digitalWrite(signals[i][1], LOW);
    digitalWrite(signals[i][2], LOW);
  }

  int maxLane = 0;
  bool priority = false;
  for (int i = 0; i < 4; i++) {
    if (emergency[i]) {
      maxLane = i;
      priority = true;
      break;
    }
    if (lanes[i] > lanes[maxLane]) maxLane = i;
  }

  digitalWrite(signals[maxLane][0], LOW);
  digitalWrite(signals[maxLane][1], LOW);
  digitalWrite(signals[maxLane][2], HIGH);  // GREEN
}

void setup() {
  for (int i = 0; i < 4; i++)
    for (int j = 0; j < 3; j++)
      pinMode(signals[i][j], OUTPUT);

  setupWiFi();
  client.setServer(mqttServer, 1883);
  client.setCallback(callback);
  client.connect("ESP32_Traffic_Client");
  client.subscribe("iot/traffic/data");
}

void loop() {
  if (!client.connected()) client.connect("ESP32_Traffic_Client");
  client.loop();
}
