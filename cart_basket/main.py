#include <SPI.h>
#include <MFRC522.h>
#include <NimBLEDevice.h>

// =====================================================
// SPI 핀
// =====================================================
static const int PIN_SCK  = 18;
static const int PIN_MISO = 19;
static const int PIN_MOSI = 23;

// =====================================================
// RC522 4개 CS + RST 공용
// =====================================================
static const int PIN_SS[4] = { 5, 17, 16, 27 };
static const int PIN_RST   = 22;

// =====================================================
// MFRC522 객체 4개
// =====================================================
MFRC522 rfid[4] = {
  MFRC522(PIN_SS[0], PIN_RST),
  MFRC522(PIN_SS[1], PIN_RST),
  MFRC522(PIN_SS[2], PIN_RST),
  MFRC522(PIN_SS[3], PIN_RST),
};

// =====================================================
// BLE UUID
// =====================================================
static const char* SERVICE_UUID = "7b1c4b60-2c2d-4d7f-8f2d-9b0b2f2d0a01";
static const char* CHAR_UUID    = "7b1c4b60-2c2d-4d7f-8f2d-9b0b2f2d0a02";

// =====================================================
// BLE GATT Server
// =====================================================
static NimBLEServer* pServer = nullptr;
static NimBLECharacteristic* pChar = nullptr;
static volatile bool g_connected = false;

// =====================================================
// 반복 전송 주기(ms) - 같은 태그 계속 대면 이 주기로 계속 notify
// =====================================================
static const uint32_t REPEAT_MS = 200;

// 리더별 마지막 전송 시간/UID 저장
static uint32_t last_sent_ms[4] = {0,0,0,0};
static byte     last_uid_len[4] = {0,0,0,0};
static byte     last_uid[4][10];

// =====================================================
// 콜백
// =====================================================
class ServerCallbacks : public NimBLEServerCallbacks {
public:
  void onConnect(NimBLEServer* s) {
    (void)s;
    g_connected = true;
    Serial.println("[BLE] Central connected");
  }
  void onDisconnect(NimBLEServer* s) {
    (void)s;
    g_connected = false;
    Serial.println("[BLE] Central disconnected");
    NimBLEDevice::startAdvertising();
  }
  void onConnect(NimBLEServer* s, ble_gap_conn_desc* desc) {
    (void)s; (void)desc;
    g_connected = true;
    Serial.println("[BLE] Central connected");
  }
  void onDisconnect(NimBLEServer* s, ble_gap_conn_desc* desc) {
    (void)s; (void)desc;
    g_connected = false;
    Serial.println("[BLE] Central disconnected");
    NimBLEDevice::startAdvertising();
  }
};

// =====================================================
// 유틸
// =====================================================
static inline void select_reader(int i) {
  for (int k = 0; k < 4; k++) digitalWrite(PIN_SS[k], (k == i) ? LOW : HIGH);
}

static void deselect_all() {
  for (int k = 0; k < 4; k++) digitalWrite(PIN_SS[k], HIGH);
}

static void print_uid(const MFRC522 &dev, const char *tag) {
  Serial.print(tag);
  Serial.print(" UID = ");
  for (byte i = 0; i < dev.uid.size; i++) {
    if (dev.uid.uidByte[i] < 0x10) Serial.print("0");
    Serial.print(dev.uid.uidByte[i], HEX);
    if (i + 1 < dev.uid.size) Serial.print(":");
  }
  Serial.println();
}

static bool same_uid(int readerIdx, const MFRC522 &dev) {
  if (last_uid_len[readerIdx] != dev.uid.size) return false;
  for (byte i = 0; i < dev.uid.size; i++) {
    if (last_uid[readerIdx][i] != dev.uid.uidByte[i]) return false;
  }
  return true;
}

static void save_uid(int readerIdx, const MFRC522 &dev) {
  last_uid_len[readerIdx] = dev.uid.size;
  for (byte i = 0; i < dev.uid.size && i < 10; i++) {
    last_uid[readerIdx][i] = dev.uid.uidByte[i];
  }
}

// Notify payload: "R<id>,<len>,<HEX...>"
static void notify_uid(uint8_t readerId, const MFRC522 &dev) {
  if (!pChar) return;

  char buf[64];
  int idx = 0;

  idx += snprintf(buf + idx, sizeof(buf) - idx, "R%u,%u,", readerId, dev.uid.size);
  for (byte i = 0; i < dev.uid.size && idx < (int)sizeof(buf) - 3; i++) {
    idx += snprintf(buf + idx, sizeof(buf) - idx, "%02X", dev.uid.uidByte[i]);
  }
  buf[sizeof(buf) - 1] = '\0';

  pChar->setValue((uint8_t*)buf, strlen(buf));
  pChar->notify();
}

// =====================================================
// RC522 스캔 (계속 읽기)
// - HaltA 제거
// - 같은 UID라도 REPEAT_MS마다 계속 notify/출력
// =====================================================
static void scan_one(int i) {
  select_reader(i);

  byte atqa[2];
  byte atqaSize = sizeof(atqa);

  MFRC522::StatusCode s = rfid[i].PICC_RequestA(atqa, &atqaSize);
  if (s != MFRC522::STATUS_OK) { deselect_all(); return; }

  if (!rfid[i].PICC_ReadCardSerial()) { deselect_all(); return; }

  uint32_t now = millis();

  // 같은 UID이면 REPEAT_MS 주기 체크
  if (same_uid(i, rfid[i])) {
    if ((now - last_sent_ms[i]) < REPEAT_MS) {
      rfid[i].PCD_StopCrypto1();
      deselect_all();
      return;
    }
  } else {
    // UID가 바뀌면 즉시 반영
    save_uid(i, rfid[i]);
  }

  last_sent_ms[i] = now;

  char tag[8];
  snprintf(tag, sizeof(tag), "[R%d]", i + 1);
  print_uid(rfid[i], tag);

  notify_uid((uint8_t)(i + 1), rfid[i]);

  rfid[i].PCD_StopCrypto1();
  deselect_all();
}

// =====================================================
// BLE init
// =====================================================
static void ble_init() {
  NimBLEDevice::init("RC522-GATT");
  NimBLEDevice::setPower(ESP_PWR_LVL_P9);

  pServer = NimBLEDevice::createServer();
  pServer->setCallbacks(new ServerCallbacks());

  NimBLEService* svc = pServer->createService(SERVICE_UUID);

  pChar = svc->createCharacteristic(
    CHAR_UUID,
    NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY
  );

  pChar->setValue("READY");
  svc->start();

  NimBLEAdvertising* adv = NimBLEDevice::getAdvertising();
  adv->addServiceUUID(SERVICE_UUID);
  adv->start();

  Serial.println("[BLE] Advertising started (connect & subscribe notify)");
}

// =====================================================
// Setup / Loop
// =====================================================
void setup() {
  Serial.begin(115200);
  delay(1000);

  for (int i = 0; i < 4; i++) {
    pinMode(PIN_SS[i], OUTPUT);
    digitalWrite(PIN_SS[i], HIGH);
  }

  SPI.begin(PIN_SCK, PIN_MISO, PIN_MOSI);

  for (int i = 0; i < 4; i++) {
    select_reader(i);
    rfid[i].PCD_Init();
    delay(5);
  }
  deselect_all();

  ble_init();
  Serial.println("scan start (ESP32 + 4x RC522 + BLE GATT Notify / continuous)");
}

void loop() {
  for (int i = 0; i < 4; i++) scan_one(i);
  delay(20);
}
