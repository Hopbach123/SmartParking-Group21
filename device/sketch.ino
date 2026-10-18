
#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h>

// SMART PARKING - DEVICE V4 / Group 21
// ESP32 + 4 Switches + Servo + MQTT
// Backend se gan received_at UTC.

// ========== 1. CONFIG ==========

const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASS = "";

const char* MQTT_HOST = "broker.hivemq.com";
const uint16_t MQTT_PORT = 1883;

const char* DEVICE_ID = "esp32-01";
const char* CLIENT_ID =
  "smartparking-group21-esp32-01-wokwi";

const char* TOPIC_DEVICE =
  "smartparking/group21/device/status";

const char* TOPIC_COMMAND =
  "smartparking/group21/gate/command";

const char* TOPIC_GATE_STATUS =
  "smartparking/group21/gate/status";

const char* SLOT_TOPICS[4] = {
  "smartparking/group21/slots/P01/state",
  "smartparking/group21/slots/P02/state",
  "smartparking/group21/slots/P03/state",
  "smartparking/group21/slots/P04/state"
};

const char* SLOT_IDS[4] = {
  "P01", "P02", "P03", "P04"
};

const uint8_t SENSOR_PINS[4] = {
  13, 14, 27, 26
};

const uint8_t SERVO_PIN = 18;

const unsigned long DEBOUNCE_MS = 400;
const unsigned long RETRY_MS = 5000;
const unsigned long HEARTBEAT_MS = 10000;
const unsigned long GATE_MOVE_MS = 700;

// ========== 2. OBJECTS ==========

WiFiClient network;
PubSubClient mqtt(network);
Servo servo;

// ========== 3. SENSOR STATE ==========

bool occupied[4] = {
  false, false, false, false
};

bool sampleState[4] = {
  false, false, false, false
};

bool slotDirty[4] = {
  true, true, true, true
};

unsigned long sampleChangedAt[4] = {
  0, 0, 0, 0
};

// ========== 4. CONNECTION STATE ==========

unsigned long lastWiFiAttempt = 0;
unsigned long lastMQTTAttempt = 0;
unsigned long lastHeartbeatAt = 0;

bool wifiWasConnected = false;

// ========== 5. GATE STATE ==========

bool gateMoving = false;
bool gateOpen = false;
bool targetOpen = false;

unsigned long gateStartedAt = 0;

char activeCommandId[81] = "";
char lastCommandId[81] = "";
char lastCommandStatus[16] = "";

char pendingAckId[81] = "";
char pendingAckStatus[16] = "";

bool ackPending = false;

// ========== 6. GATE STATUS ==========

bool publishGateStatus(
  const char* id,
  const char* status
) {
  if (!mqtt.connected()) {
    return false;
  }

  JsonDocument out;

  out["device_id"] = DEVICE_ID;
  out["command_id"] = id;
  out["status"] = status;

  char buf[256];

  size_t n = serializeJson(
    out, buf, sizeof(buf)
  );

  if (n == 0 || n >= sizeof(buf)) {
    return false;
  }

  bool ok = mqtt.publish(
    TOPIC_GATE_STATUS, buf
  );

  Serial.printf(
    "[GATE STATUS] %s (%s)\n",
    buf,
    ok ? "OK" : "FAILED"
  );

  return ok;
}

// ========== 7. QUEUE RESPONSE ==========

void queueGateStatus(
  const char* id,
  const char* status
) {
  snprintf(
    pendingAckId,
    sizeof(pendingAckId),
    "%s",
    id
  );

  snprintf(
    pendingAckStatus,
    sizeof(pendingAckStatus),
    "%s",
    status
  );

  ackPending = true;
}

// ========== 8. MQTT CALLBACK ==========

void mqttCallback(
  char* topic,
  byte* payload,
  unsigned int length
) {
  if (strcmp(topic, TOPIC_COMMAND) != 0) {
    return;
  }

  if (length == 0 || length > 256) {
    Serial.println(
      "[ERROR] Command length invalid"
    );
    return;
  }

  JsonDocument doc;

  if (
    deserializeJson(doc, payload, length)
    != DeserializationError::Ok
  ) {
    Serial.println(
      "[ERROR] Malformed JSON"
    );
    return;
  }

  if (
    !doc["command_id"].is<const char*>() ||
    !doc["action"].is<const char*>() ||
    !doc["direction"].is<const char*>()
  ) {
    Serial.println(
      "[ERROR] Missing/wrong field type"
    );
    return;
  }

  const char* id = doc["command_id"];
  const char* action = doc["action"];
  const char* direction = doc["direction"];

  if (!id[0] || strlen(id) > 80) {
    Serial.println(
      "[ERROR] Invalid command_id"
    );
    return;
  }

  bool validDirection =
    strcmp(direction, "ENTRY") == 0 ||
    strcmp(direction, "EXIT") == 0;

  bool validAction =
    strcmp(action, "OPEN") == 0 ||
    strcmp(action, "CLOSE") == 0;

  if (!validDirection || !validAction) {
    Serial.println(
      "[ERROR] Invalid action/direction"
    );

    queueGateStatus(id, "ERROR");
    return;
  }

  // Kiem tra lenh trung
  if (strcmp(id, lastCommandId) == 0) {
    Serial.println(
      "[GATE] Duplicate command: re-ack"
    );

    queueGateStatus(
      id, lastCommandStatus
    );
    return;
  }

  // Neu Servo dang quay
  if (gateMoving) {
    Serial.println(
      "[GATE] Busy: command rejected"
    );

    queueGateStatus(id, "ERROR");
    return;
  }

  snprintf(
    activeCommandId,
    sizeof(activeCommandId),
    "%s",
    id
  );

  targetOpen =
    strcmp(action, "OPEN") == 0;

  servo.write(
    targetOpen ? 90 : 0
  );

  gateMoving = true;
  gateStartedAt = millis();

  Serial.printf(
    "[GATE] %s direction=%s id=%s\n",
    action, direction, id
  );
}

// ========== 9. SERVO PROCESS ==========

void processServo() {
  if (!gateMoving) {
    return;
  }

  if (
    millis() - gateStartedAt
    < GATE_MOVE_MS
  ) {
    return;
  }

  gateMoving = false;
  gateOpen = targetOpen;

  const char* result =
    gateOpen ? "OPENED" : "CLOSED";

  snprintf(
    lastCommandId,
    sizeof(lastCommandId),
    "%s",
    activeCommandId
  );

  snprintf(
    lastCommandStatus,
    sizeof(lastCommandStatus),
    "%s",
    result
  );

  queueGateStatus(
    activeCommandId, result
  );

  Serial.printf(
    "[GATE] %s\n", result
  );
}

// ========== 10. PUBLISH SLOT ==========

bool publishSlot(int i) {
  if (!mqtt.connected()) {
    return false;
  }

  JsonDocument doc;

  doc["device_id"] = DEVICE_ID;
  doc["slot_id"] = SLOT_IDS[i];
  doc["occupied"] = occupied[i];

  char buf[192];

  size_t n = serializeJson(
    doc, buf, sizeof(buf)
  );

  if (n == 0 || n >= sizeof(buf)) {
    return false;
  }

  bool ok = mqtt.publish(
    SLOT_TOPICS[i],
    buf,
    false
  );

  Serial.printf(
    "[SLOT %s] %s (%s)\n",
    SLOT_IDS[i],
    buf,
    ok ? "OK" : "FAILED"
  );

  return ok;
}

// ========== 11. HEARTBEAT ==========

void publishHeartbeat() {
  if (!mqtt.connected()) {
    return;
  }

  JsonDocument doc;

  doc["device_id"] = DEVICE_ID;
  doc["status"] = "online";
  doc["uptime_ms"] = millis();

  char buf[192];

  size_t n = serializeJson(
    doc, buf, sizeof(buf)
  );

  if (n > 0 && n < sizeof(buf)) {
    bool ok = mqtt.publish(
      TOPIC_DEVICE,
      buf,
      false
    );

    Serial.printf(
      "[HEARTBEAT] %s (%s)\n",
      buf,
      ok ? "OK" : "FAILED"
    );
  }
}

// ========== 12. READ SENSORS ==========

void pollSensors() {
  unsigned long now = millis();

  for (int i = 0; i < 4; i++) {
    bool sample =
      digitalRead(SENSOR_PINS[i]) == LOW;

    if (sample != sampleState[i]) {
      sampleState[i] = sample;
      sampleChangedAt[i] = now;
    }

    // Chong nhieu 400ms
    if (
      now - sampleChangedAt[i] >= DEBOUNCE_MS &&
      sample != occupied[i]
    ) {
      occupied[i] = sample;
      slotDirty[i] = true;

      Serial.printf(
        "[SENSOR] %s -> %s\n",
        SLOT_IDS[i],
        sample ? "CO XE" : "TRONG"
      );

      int busy = 0;

      for (bool state : occupied) {
        if (state) {
          busy++;
        }
      }

      Serial.printf(
        "[PARKING] Busy=%d Free=%d%s\n",
        busy,
        4 - busy,
        busy == 4 ? " FULL" : ""
      );
    }
  }
}

// ========== 13. WIFI RECONNECT ==========

void reconnectWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  if (
    lastWiFiAttempt != 0 &&
    millis() - lastWiFiAttempt < RETRY_MS
  ) {
    return;
  }

  lastWiFiAttempt = millis();

  Serial.println("[WIFI] Connecting...");

  WiFi.begin(
    WIFI_SSID,
    WIFI_PASS,
    6
  );
}

// ========== 14. MQTT RECONNECT ==========

void reconnectMQTT() {
  if (
    WiFi.status() != WL_CONNECTED ||
    mqtt.connected()
  ) {
    return;
  }

  if (
    lastMQTTAttempt != 0 &&
    millis() - lastMQTTAttempt < RETRY_MS
  ) {
    return;
  }

  lastMQTTAttempt = millis();

  Serial.println("[MQTT] Connecting...");

  bool ok = mqtt.connect(
    CLIENT_ID,
    TOPIC_DEVICE,
    0,
    false,
    "{\"device_id\":\"esp32-01\","
    "\"status\":\"offline\"}"
  );

  if (!ok) {
    Serial.printf(
      "[MQTT] FAILED state=%d\n",
      mqtt.state()
    );
    return;
  }

  Serial.println("[MQTT] CONNECTED");

  bool subscribed = mqtt.subscribe(
    TOPIC_COMMAND,
    1
  );

  Serial.printf(
    "[MQTT] SUBSCRIBE %s\n",
    subscribed ? "OK" : "FAILED"
  );

  // Gui lai trang thai 4 o
  for (int i = 0; i < 4; i++) {
    slotDirty[i] = true;
  }

  publishHeartbeat();
  lastHeartbeatAt = millis();
}

// ========== 15. SETUP ==========

void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println(
    "SMART PARKING - DEVICE V4"
  );

  // Khoi tao 4 cam bien
  for (int i = 0; i < 4; i++) {
    pinMode(
      SENSOR_PINS[i],
      INPUT_PULLUP
    );

    occupied[i] =
      digitalRead(SENSOR_PINS[i]) == LOW;

    sampleState[i] = occupied[i];
    sampleChangedAt[i] = millis();
  }

  // Khoi tao Servo
  servo.attach(
    SERVO_PIN,
    500,
    2400
  );

  servo.write(0);

  Serial.println(
    "[SERVO] CLOSED 0 deg"
  );

  // Khoi tao WiFi
  WiFi.mode(WIFI_STA);

  // Cau hinh MQTT
  mqtt.setServer(
    MQTT_HOST,
    MQTT_PORT
  );

  mqtt.setCallback(mqttCallback);
  mqtt.setBufferSize(512);
  mqtt.setKeepAlive(15);
  mqtt.setSocketTimeout(3);

  reconnectWiFi();
}

// ========== 16. MAIN LOOP ==========

void loop() {

  // Doc 4 cam bien
  pollSensors();

  // Xu ly Servo khong block
  processServo();

  bool wifiNow =
    WiFi.status() == WL_CONNECTED;

  if (!wifiNow) {

    if (wifiWasConnected) {
      Serial.println(
        "[WIFI] DISCONNECTED"
      );
    }

    wifiWasConnected = false;
    reconnectWiFi();

  } else {

    if (!wifiWasConnected) {
      Serial.print(
        "[WIFI] CONNECTED IP="
      );

      Serial.println(
        WiFi.localIP()
      );
    }

    wifiWasConnected = true;

    // Ket noi lai MQTT
    if (!mqtt.connected()) {
      reconnectMQTT();
    }

    if (mqtt.connected()) {

      mqtt.loop();

      // Gui phan hoi Gate con cho
      if (
        ackPending &&
        publishGateStatus(
          pendingAckId,
          pendingAckStatus
        )
      ) {
        ackPending = false;
      }

      // Gui cac o thay doi
      for (int i = 0; i < 4; i++) {
        if (
          slotDirty[i] &&
          publishSlot(i)
        ) {
          slotDirty[i] = false;
        }
      }

      // Heartbeat moi 10 giay
      if (
        millis() - lastHeartbeatAt
        >= HEARTBEAT_MS
      ) {
        publishHeartbeat();
        lastHeartbeatAt = millis();
      }
    }
  }

  delay(20);
}
