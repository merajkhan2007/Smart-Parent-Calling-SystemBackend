#include <SPI.h>
#include <MFRC522.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include "display.h"
#include "sim7670.h"
#include "students.h"

// ==========================================
// CONFIGURATION PARAMETERS
// ==========================================
#define WIFI_SSID       "SHADAAN"
#define WIFI_PASSWORD   "Makfreelance@759"
#define API_BASE_URL    "https://m9vtp9i2sl5xk7n28lktek4e.141.148.199.81.sslip.io/api"
#define DEVICE_ID       "ESP32_MAIN_GATE"
#define DEVICE_NAME     "Entrance Gate A Scanner"

// RFID RC522 Pins
#define SS_PIN    5
#define RST_PIN   4

// Hardware Button Pins
#define BUTTON_FATHER   25
#define BUTTON_MOTHER   26
#define BUTTON_END_CALL 27

// Global instances
MFRC522 mfrc522(SS_PIN, RST_PIN);
Display displayCtrl;
SIM7670 modem(Serial2);

// Active dialing/calling info (loaded dynamically or from local database)
String activeStudentName = "";
String activeFatherNumber = "";
String activeMotherNumber = "";
String activeFatherName = "";
String activeMotherName = "";
String activeUid = "";
String activeCallId = "";

// State Machine States
enum SystemState {
    STATE_BOOT,
    STATE_WAITING,
    STATE_VERIFYING,
    STATE_SELECT_PARENT,
    STATE_CALLING,
    STATE_COMPLETED,
    STATE_DENIED
};

SystemState currentState = STATE_BOOT;

// Non-blocking timer variables
uint32_t stateTimer = 0;
uint32_t lastStatusCheck = 0;
uint32_t lastCallCheck = 0;
uint32_t lastHeartbeatTime = 0;
uint32_t callStartTimer = 0;

// State transition duration constants
const uint32_t STATUS_CHECK_INTERVAL = 30000; // Check cellular status every 30 seconds
const uint32_t HEARTBEAT_INTERVAL    = 30000; // Send heartbeat to dashboard every 30 seconds
const uint32_t VERIFY_DELAY          = 2000;  // Show card verified screen for 2s
const uint32_t CALL_DURATION         = 20000; // Maintain parent call for 20s
const uint32_t COMPLETED_DELAY       = 3000;  // Show call completed screen for 3s
const uint32_t DENIED_DELAY          = 3000;  // Show access denied screen for 3s

// Cached status variables
int currentDbm = -115;
bool currentSimOk = false;
bool currentNetOk = false;
bool isOnline = false; // Set to true if WiFi connects and device registers with backend successfully

// Helper function declarations
String getUIDString(MFRC522& rfid);
const Student* findStudentLocal(const String& uidStr);
String getJsonValue(const String& json, const String& key);
void connectToWiFi();
void registerDeviceWithBackend();
void sendHeartbeat(const String& statusMessage);
bool queryRFIDScan(const String& uid);
void logCallStart(const String& parentType);
void logCallConnected();
void logCallEnd(const String& reason);

/**
 * @brief Arduino initialization routine.
 */
void setup() {
    // Initialize Hardware Button Pins
    pinMode(BUTTON_FATHER, INPUT_PULLUP);
    pinMode(BUTTON_MOTHER, INPUT_PULLUP);
    pinMode(BUTTON_END_CALL, INPUT_PULLUP);

    Serial.begin(115200);
    while (!Serial) {
        delay(10); // Wait for native USB serial monitor
    }
    Serial.println("\n=== STUDENT PARENT CALLING SYSTEM ===");
    Serial.println("[Init] Booting system...");

    // 1. Initialize SSD1306 OLED Display
    if (!displayCtrl.begin()) {
        Serial.println("[Error] OLED display failed to initialize! Check SCL (GPIO22) and SDA (GPIO21).");
        while (1) {
            delay(1000);
        }
    }
    Serial.println("[Init] OLED Display Ready.");

    // 2. Play boot splash screen logo and loading bar
    displayCtrl.bootScreen();

    // 3. Initialize Wi-Fi
    connectToWiFi();

    // 4. Initialize SIMCom A7670C 4G modem
    Serial.println("[Init] Connecting to SIM7670C Modem...");
    if (!modem.begin(115200)) {
        Serial.println("[Error] SIM7670C modem failed to respond! Check TX2 (GPIO17) and RX2 (GPIO16).");
        displayCtrl.errorScreen("SIM Init Fail");
        while (1) {
            delay(1000);
        }
    }
    Serial.println("[Init] SIM7670C Modem Online.");

    // 5. Initialize RFID Reader MFRC522
    SPI.begin(); // Uses default VSPI pins SCK (18), MISO (19), MOSI (23), SS (5)
    mfrc522.PCD_Init();
    
    byte rfidVer = mfrc522.PCD_ReadRegister(MFRC522::VersionReg);
    if (rfidVer == 0x00 || rfidVer == 0xFF) {
        Serial.println("[Error] MFRC522 RFID reader not found! Check SPI connections.");
        displayCtrl.errorScreen("RFID Init Fail");
        while (1) {
            delay(1000);
        }
    }
    Serial.print("[Init] RFID Reader MFRC522 initialized. Version: 0x");
    Serial.println(rfidVer, HEX);

    // Initial check of SIM & GSM registration
    currentSimOk = (modem.sendAT("AT+CPIN?").indexOf("READY") != -1);
    currentNetOk = modem.networkReady();
    currentDbm = modem.getSignal();
    
    // Register device with backend dashboard if WiFi connected
    if (isOnline) {
        registerDeviceWithBackend();
    }

    Serial.println("[Init] System ready. Entering idle state.");
    currentState = STATE_WAITING;
}

/**
 * @brief Main execution loop. Implements non-blocking state transitions.
 */
void loop() {
    // Keep WiFi connection alive in background (throttled to every 10 seconds to avoid flooding the CPU and freezing SPI)
    static uint32_t lastWifiReconnectAttempt = 0;
    if (WiFi.status() != WL_CONNECTED && isOnline) {
        if (millis() - lastWifiReconnectAttempt >= 10000) {
            lastWifiReconnectAttempt = millis();
            Serial.println("[WiFi] Disconnected! Attempting to reconnect...");
            WiFi.disconnect();
            WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
        }
    }

    // Background Non-blocking Heartbeat (updates dashboard every 30s)
    if (isOnline && (millis() - lastHeartbeatTime >= HEARTBEAT_INTERVAL || lastHeartbeatTime == 0)) {
        lastHeartbeatTime = millis();
        String statusMsg = (currentState == STATE_WAITING) ? "RFID Waiting" : "Busy";
        sendHeartbeat(statusMsg);
    }

    switch (currentState) {
        
        case STATE_WAITING: {
            // 1. Poll the RFID card reader FIRST (highest priority, non-blocking)
            if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
                String scannedUid = getUIDString(mfrc522);
                Serial.print("[RFID] Scanned Card UID: ");
                Serial.println(scannedUid);
                activeUid = scannedUid;

                // RFID Scan Logic (Backend validation with local fallback)
                bool scanOk = false;
                if (WiFi.status() == WL_CONNECTED) {
                    scanOk = queryRFIDScan(scannedUid);
                } else {
                    Serial.println("[RFID] WiFi offline. Falling back to local database search.");
                    const Student* student = findStudentLocal(scannedUid);
                    if (student != nullptr) {
                        activeStudentName = student->studentName;
                        activeFatherNumber = student->fatherNumber;
                        activeMotherNumber = student->motherNumber;
                        activeFatherName = "Father";
                        activeMotherName = "Mother";
                        scanOk = true;
                    }
                }

                if (scanOk) {
                    currentState = STATE_VERIFYING;
                    stateTimer = millis();
                    displayCtrl.verifiedScreen(activeStudentName.c_str());
                } else {
                    Serial.println("[RFID] Access Denied: Card unknown, student blocked, or server error.");
                    currentState = STATE_DENIED;
                    stateTimer = millis();
                    displayCtrl.deniedScreen();
                }

                // Instruct reader to put scanned card to sleep (prevents double readings)
                mfrc522.PICC_HaltA();
                mfrc522.PCD_StopCrypto1();
            }

            // 2. Periodically check modem signal and network status
            if (millis() - lastStatusCheck >= STATUS_CHECK_INTERVAL || lastStatusCheck == 0) {
                lastStatusCheck = millis();
                currentSimOk = (modem.sendAT("AT+CPIN?").indexOf("READY") != -1);
                currentNetOk = modem.networkReady();
                currentDbm = modem.getSignal();
                
                // Redraw idle screen with updated signal strength status
                displayCtrl.waitingScreen(currentDbm, currentSimOk, currentNetOk);
            }
            break;
        }

        case STATE_VERIFYING: {
            if (millis() - stateTimer >= VERIFY_DELAY) {
                if (activeStudentName.length() > 0) {
                    currentState = STATE_SELECT_PARENT;
                    stateTimer = millis();
                    displayCtrl.selectParentScreen(activeStudentName.c_str());
                } else {
                    currentState = STATE_WAITING;
                    lastStatusCheck = 0; // Force immediate display update
                }
            }
            break;
        }

        case STATE_SELECT_PARENT: {
            // 1. Check if Father button (Button 1) is pressed
            if (digitalRead(BUTTON_FATHER) == LOW) {
                Serial.print("[Call] Initiating voice call to Father: ");
                Serial.println(activeFatherNumber);
                
                displayCtrl.callingScreen(activeStudentName.c_str(), activeFatherName.c_str(), activeFatherNumber.c_str());
                
                // Log call start to backend
                if (WiFi.status() == WL_CONNECTED) {
                    logCallStart("father");
                }

                if (modem.dial(activeFatherNumber)) {
                    currentState = STATE_CALLING;
                    stateTimer = millis();
                    callStartTimer = millis();
                    lastCallCheck = millis(); // Reset check timer
                    
                    // Log call connected
                    if (WiFi.status() == WL_CONNECTED) {
                        logCallConnected();
                    }
                } else {
                    Serial.println("[Call Error] Voice call command (ATD) failed.");
                    if (WiFi.status() == WL_CONNECTED) {
                        logCallEnd("failed");
                    }
                    currentState = STATE_DENIED;
                    stateTimer = millis();
                    displayCtrl.errorScreen("Call Failed");
                }
                delay(200); // Debounce delay
            }
            // 2. Check if Mother button (Button 2) is pressed
            else if (digitalRead(BUTTON_MOTHER) == LOW) {
                Serial.print("[Call] Initiating voice call to Mother: ");
                Serial.println(activeMotherNumber);
                
                displayCtrl.callingScreen(activeStudentName.c_str(), activeMotherName.c_str(), activeMotherNumber.c_str());
                
                // Log call start to backend
                if (WiFi.status() == WL_CONNECTED) {
                    logCallStart("mother");
                }

                if (modem.dial(activeMotherNumber)) {
                    currentState = STATE_CALLING;
                    stateTimer = millis();
                    callStartTimer = millis();
                    lastCallCheck = millis(); // Reset check timer

                    // Log call connected
                    if (WiFi.status() == WL_CONNECTED) {
                        logCallConnected();
                    }
                } else {
                    Serial.println("[Call Error] Voice call command (ATD) failed.");
                    if (WiFi.status() == WL_CONNECTED) {
                        logCallEnd("failed");
                    }
                    currentState = STATE_DENIED;
                    stateTimer = millis();
                    displayCtrl.errorScreen("Call Failed");
                }
                delay(200); // Debounce delay
            }
            // 3. Check if Cancel/End Call button (Button 3) is pressed
            else if (digitalRead(BUTTON_END_CALL) == LOW) {
                Serial.println("[Select] Cancel button pressed. Returning to waiting state.");
                currentState = STATE_WAITING;
                lastStatusCheck = 0; // Force immediate update
                delay(200); // Debounce delay
            }
            // 4. Timeout if no selection is made in 10 seconds
            else if (millis() - stateTimer >= 10000) {
                Serial.println("[Select] Timeout. Returning to waiting state.");
                currentState = STATE_WAITING;
                lastStatusCheck = 0; // Force immediate update
            }
            break;
        }

        case STATE_CALLING: {
            // 1. Check if End Call button (Button 3) is pressed
            if (digitalRead(BUTTON_END_CALL) == LOW) {
                Serial.println("[Call] End Call button pressed. Hanging up...");
                modem.hangup();
                
                if (WiFi.status() == WL_CONNECTED) {
                    logCallEnd("hung_up");
                }

                currentState = STATE_COMPLETED;
                stateTimer = millis();
                displayCtrl.completedScreen();
                delay(200); // Debounce delay
                break;
            }

            // 2. Check if call is still active every 1000ms (after an 8-second dialing grace period)
            if (millis() - stateTimer >= 8000 && millis() - lastCallCheck >= 1000) {
                lastCallCheck = millis();
                if (!modem.isCallActive()) {
                    Serial.println("[Call] Call disconnected by parent/modem.");
                    
                    if (WiFi.status() == WL_CONNECTED) {
                        logCallEnd("hung_up");
                    }

                    currentState = STATE_COMPLETED;
                    stateTimer = millis();
                    displayCtrl.completedScreen();
                    break;
                }
            }

            // 3. Keep phone call open for 20 seconds, then disconnect
            if (millis() - stateTimer >= CALL_DURATION) {
                Serial.println("[Call] Duration limit reached. Hanging up...");
                modem.hangup();
                
                if (WiFi.status() == WL_CONNECTED) {
                    logCallEnd("timeout");
                }

                currentState = STATE_COMPLETED;
                stateTimer = millis();
                displayCtrl.completedScreen();
            }
            break;
        }

        case STATE_COMPLETED: {
            if (millis() - stateTimer >= COMPLETED_DELAY) {
                currentState = STATE_WAITING;
                lastStatusCheck = 0; // Force immediate status check
            }
            break;
        }

        case STATE_DENIED: {
            if (millis() - stateTimer >= DENIED_DELAY) {
                currentState = STATE_WAITING;
                lastStatusCheck = 0; // Force immediate status check
            }
            break;
        }

        default:
            currentState = STATE_WAITING;
            break;
    }
}

// ==========================================
// WI-FI & NETWORK CLIENT HELPERS
// ==========================================

/**
 * @brief Initialize WiFi link and log progress to OLED/Serial.
 */
void connectToWiFi() {
    Serial.print("[WiFi] Connecting to ");
    Serial.println(WIFI_SSID);
    
    displayCtrl.loadingScreen("Connecting WiFi");
    
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    // Wait up to 10 seconds for Wi-Fi connection
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n[WiFi] Connected successfully!");
        Serial.print("[WiFi] IP Address: ");
        Serial.println(WiFi.localIP());
        isOnline = true;
    } else {
        Serial.println("\n[WiFi] Connection failed! Starting in OFFLINE mode.");
        isOnline = false;
    }
}

/**
 * @brief Registers this gate device with the Coolify backend.
 */
void registerDeviceWithBackend() {
    WiFiClientSecure client;
    client.setInsecure();
    HTTPClient http;
    String url = String(API_BASE_URL) + "/device/register";
    
    http.begin(client, url);
    http.addHeader("Content-Type", "application/json");
    
    String payload = "{\"device_id\":\"" + String(DEVICE_ID) + "\",\"name\":\"" + String(DEVICE_NAME) + "\",\"ip_address\":\"" + WiFi.localIP().toString() + "\",\"location\":\"School Main Entrance\",\"classroom\":\"Foyer\"}";
    
    Serial.print("[HTTP] Registering device: ");
    Serial.println(url);
    
    int httpResponseCode = http.POST(payload);
    if (httpResponseCode > 0) {
        Serial.print("[HTTP] Registration Response Code: ");
        Serial.println(httpResponseCode);
        Serial.println(http.getString());
    } else {
        Serial.print("[HTTP] Registration Error: ");
        Serial.println(http.errorToString(httpResponseCode).c_str());
    }
    http.end();
}

/**
 * @brief Transmit telemetry heartbeat pin.
 */
void sendHeartbeat(const String& statusMessage) {
    WiFiClientSecure client;
    client.setInsecure();
    HTTPClient http;
    String url = String(API_BASE_URL) + "/device/heartbeat";
    
    http.begin(client, url);
    http.addHeader("Content-Type", "application/json");
    
    // Fetch latest cellular signal strength (in dBm)
    currentDbm = modem.getSignal();
    
    String payload = "{\"device_id\":\"" + String(DEVICE_ID) + "\",\"battery_status\":95,\"wifi_signal\":" + String(WiFi.RSSI()) + ",\"sim_network\":\"SIM7670 (" + String(currentDbm) + " dBm)\",\"current_status_message\":\"" + statusMessage + "\"}";
    
    int httpResponseCode = http.POST(payload);
    http.end();
}

/**
 * @brief Query live RFID scan verification endpoint.
 */
bool queryRFIDScan(const String& uid) {
    WiFiClientSecure client;
    client.setInsecure();
    HTTPClient http;
    String url = String(API_BASE_URL) + "/rfid/scan";
    
    http.begin(client, url);
    http.addHeader("Content-Type", "application/json");
    
    String payload = "{\"uid\":\"" + uid + "\",\"device_id\":\"" + String(DEVICE_ID) + "\"}";
    
    Serial.print("[HTTP] Scanning RFID card at backend: ");
    Serial.println(url);
    
    int httpResponseCode = http.POST(payload);
    bool success = false;
    
    if (httpResponseCode == 200) {
        String response = http.getString();
        Serial.println("[HTTP] Scan response success!");
        
        // Parse simple json response fields
        activeStudentName = getJsonValue(response, "student_name");
        activeFatherNumber = getJsonValue(response, "father_mobile");
        activeMotherNumber = getJsonValue(response, "mother_mobile");
        activeFatherName = getJsonValue(response, "father_name");
        activeMotherName = getJsonValue(response, "mother_name");
        
        if (activeFatherName.length() == 0) activeFatherName = "Father";
        if (activeMotherName.length() == 0) activeMotherName = "Mother";
        
        success = true;
    } else {
        Serial.print("[HTTP] Scan Error Response: ");
        Serial.println(httpResponseCode);
        Serial.println(http.getString());
        success = false;
    }
    
    http.end();
    return success;
}

/**
 * @brief Log call initialized.
 */
void logCallStart(const String& parentType) {
    WiFiClientSecure client;
    client.setInsecure();
    HTTPClient http;
    String url = String(API_BASE_URL) + "/call/start";
    
    http.begin(client, url);
    http.addHeader("Content-Type", "application/json");
    
    String payload = "{\"rfid_uid\":\"" + activeUid + "\",\"device_id\":\"" + String(DEVICE_ID) + "\",\"parent_type\":\"" + parentType + "\"}";
    
    int httpResponseCode = http.POST(payload);
    if (httpResponseCode == 200) {
        String response = http.getString();
        activeCallId = getJsonValue(response, "call_id");
        Serial.print("[HTTP] Call started logged. ID: ");
        Serial.println(activeCallId);
    }
    http.end();
}

/**
 * @brief Log call answered.
 */
void logCallConnected() {
    if (activeCallId.length() == 0) return;
    
    WiFiClientSecure client;
    client.setInsecure();
    HTTPClient http;
    String url = String(API_BASE_URL) + "/call/connected";
    
    http.begin(client, url);
    http.addHeader("Content-Type", "application/json");
    
    String payload = "{\"call_id\":" + activeCallId + "}";
    
    http.POST(payload);
    http.end();
}

/**
 * @brief Log call disconnected/completed.
 */
void logCallEnd(const String& reason) {
    if (activeCallId.length() == 0) return;
    
    WiFiClientSecure client;
    client.setInsecure();
    HTTPClient http;
    String url = String(API_BASE_URL) + "/call/end";
    
    http.begin(client, url);
    http.addHeader("Content-Type", "application/json");
    
    uint32_t duration = (millis() - callStartTimer) / 1000;
    String payload = "{\"call_id\":" + activeCallId + ",\"duration\":" + String(duration) + ",\"status\":\"completed\",\"reason\":\"" + reason + "\"}";
    
    http.POST(payload);
    http.end();
    
    activeCallId = ""; // Reset call ID
}

/**
 * @brief Extract a simple string parameter value from raw json input.
 */
String getJsonValue(const String& json, const String& key) {
    int keyIndex = json.indexOf("\"" + key + "\"");
    if (keyIndex == -1) return "";
    int colonIndex = json.indexOf(":", keyIndex);
    if (colonIndex == -1) return "";
    
    int firstQuote = json.indexOf("\"", colonIndex);
    if (firstQuote != -1 && firstQuote < json.indexOf(",", colonIndex) && firstQuote < json.indexOf("}", colonIndex)) {
        int secondQuote = json.indexOf("\"", firstQuote + 1);
        if (secondQuote != -1) {
            return json.substring(firstQuote + 1, secondQuote);
        }
    } else {
        int endPos = json.indexOf(",", colonIndex);
        if (endPos == -1) {
            endPos = json.indexOf("}", colonIndex);
        }
        if (endPos != -1) {
            String val = json.substring(colonIndex + 1, endPos);
            val.trim();
            return val;
        }
    }
    return "";
}

/**
 * @brief Extract and format hex bytes of RFID UID into a formatted space-separated string.
 */
String getUIDString(MFRC522& rfid) {
    String uidStr = "";
    for (byte i = 0; i < rfid.uid.size; i++) {
        if (rfid.uid.uidByte[i] < 0x10) {
            uidStr += "0";
        }
        uidStr += String(rfid.uid.uidByte[i], HEX);
        if (i < rfid.uid.size - 1) {
            uidStr += " ";
        }
    }
    uidStr.toUpperCase();
    return uidStr;
}

/**
 * @brief Search fallback offline student database.
 */
const Student* findStudentLocal(const String& uidStr) {
    for (size_t i = 0; i < STUDENT_COUNT; i++) {
        if (uidStr.equalsIgnoreCase(STUDENT_DATABASE[i].uid)) {
            return &STUDENT_DATABASE[i];
        }
    }
    return nullptr;
}
