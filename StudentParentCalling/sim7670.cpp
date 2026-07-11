#include "sim7670.h"

/**
 * @brief Construct a new SIM7670 object.
 * @param serialPort HardwareSerial reference to use (e.g. Serial2 on ESP32).
 */
SIM7670::SIM7670(HardwareSerial& serialPort) : modemSerial(serialPort), baud(115200) {}

/**
 * @brief Initialize communication link and detect SIMCom A7670C module.
 * @param baudRate Communication baud rate.
 * @return true if successful connection is verified, false if no response.
 */
bool SIM7670::begin(uint32_t baudRate) {
    baud = baudRate;
    
    // Initialize HardwareSerial for ESP32.
    // Spec Pinout: ESP32 RX2 GPIO16 <--- TX, ESP32 TX2 GPIO17 ---> RX.
    modemSerial.begin(baud, SERIAL_8N1, 16, 17);
    
    // Flush input buffer
    while (modemSerial.available()) {
        modemSerial.read();
    }
    
    // Attempt to wake up modem and check AT response.
    // Retry up to 5 times.
    for (int retry = 0; retry < 5; retry++) {
        String resp = sendAT("AT", 1000);
        if (resp.indexOf("OK") != -1) {
            // Disable echo (ATE0) so response strings do not contain echoing commands
            sendAT("ATE0", 1000);
            
            // Set SMS message format to text mode (optional but good practice)
            sendAT("AT+CMGF=1", 1000);
            
            return true;
        }
        delay(500);
    }
    return false;
}

/**
 * @brief Read characters from the serial buffer up to a timeout.
 * @param timeoutMs Max wait time.
 * @return String containing all response chars received.
 */
String SIM7670::waitResponse(uint32_t timeoutMs) {
    String response = "";
    uint32_t startTime = millis();
    
    while (millis() - startTime < timeoutMs) {
        while (modemSerial.available()) {
            char c = modemSerial.read();
            response += c;
        }
        
        // Small delay to allow buffer to fill
        delay(5);
        
        // Break early if we receive standard end-of-response sequences
        if (response.indexOf("OK\r\n") != -1 || 
            response.indexOf("ERROR\r\n") != -1 || 
            response.indexOf("NO CARRIER\r\n") != -1 ||
            response.indexOf("BUSY\r\n") != -1 ||
            response.indexOf("NO DIALTONE\r\n") != -1) {
            break;
        }
    }
    return response;
}

/**
 * @brief Send an AT command and return the modem response.
 * @param cmd Command string.
 * @param timeoutMs Maximum time to wait.
 * @return String Response from modem.
 */
String SIM7670::sendAT(const String& cmd, uint32_t timeoutMs) {
    // Flush any leftover buffer contents before sending
    while (modemSerial.available()) {
        modemSerial.read();
    }
    
    // Ensure command ends with a Carriage Return
    if (cmd.endsWith("\r") || cmd.endsWith("\n")) {
        modemSerial.print(cmd);
    } else {
        modemSerial.print(cmd + "\r");
    }
    
    return waitResponse(timeoutMs);
}

/**
 * @brief Command module to dial a voice number.
 * @param phoneNumber Number string to dial.
 * @return true if dial command successfully accepted.
 */
bool SIM7670::dial(const String& phoneNumber) {
    // ATD<number>; executes standard voice call dialing
    String cmd = "ATD" + phoneNumber + ";";
    String resp = sendAT(cmd, 3000);
    return (resp.indexOf("OK") != -1);
}

/**
 * @brief Send voice hang-up commands.
 * @return true if hanging up succeeded.
 */
bool SIM7670::hangup() {
    // AT+CHUP (Call Hang UP) terminates all connections
    String resp = sendAT("AT+CHUP", 3000);
    return (resp.indexOf("OK") != -1);
}

/**
 * @brief Query network signal strength from CSQ and map it to dBm.
 * @return Signal strength in dBm, or -115 if unknown or error.
 */
int SIM7670::getSignal() {
    String resp = sendAT("AT+CSQ", 1000);
    
    // CSQ response is formatted as: "+CSQ: <rssi>,<ber>"
    int csqIndex = resp.indexOf("+CSQ: ");
    if (csqIndex != -1) {
        int commaIndex = resp.indexOf(",", csqIndex);
        if (commaIndex != -1) {
            String csqStr = resp.substring(csqIndex + 6, commaIndex);
            csqStr.trim();
            int csqVal = csqStr.toInt();
            
            if (csqVal == 99) {
                return -115; // Unknown/No signal
            }
            
            // Map CSQ (0-31) to dBm
            // 0 is -113 dBm, 31 is -51 dBm
            // dBm = -113 + (csq * 2)
            return -113 + (csqVal * 2);
        }
    }
    return -115;
}

/**
 * @brief Checks if modem is registered to network.
 * @return true if registered on cellular network (home or roaming), false otherwise.
 */
bool SIM7670::networkReady() {
    // Query GPRS network registration status
    String resp = sendAT("AT+CGREG?", 1500);
    int idx = resp.indexOf("+CGREG: ");
    if (idx != -1) {
        int commaIdx = resp.indexOf(",", idx);
        if (commaIdx != -1) {
            String statStr = resp.substring(commaIdx + 1, commaIdx + 2);
            int stat = statStr.toInt();
            if (stat == 1 || stat == 5) {
                return true; // 1 = Home Network, 5 = Roaming
            }
        }
    }

    // Fallback: Query circuit switched network registration
    resp = sendAT("AT+CREG?", 1000);
    idx = resp.indexOf("+CREG: ");
    if (idx != -1) {
        int commaIdx = resp.indexOf(",", idx);
        if (commaIdx != -1) {
            String statStr = resp.substring(commaIdx + 1, commaIdx + 2);
            int stat = statStr.toInt();
            if (stat == 1 || stat == 5) {
                return true;
            }
        }
    }
    
    return false;
}

/**
 * @brief Checks if a call is currently active (dialing, alerting, or established).
 * @return true if call is active, false if idle/no active call.
 */
bool SIM7670::isCallActive() {
    String resp = sendAT("AT+CLCC", 1000);
    // If "+CLCC:" is found in the response, it means a call is active
    return (resp.indexOf("+CLCC:") != -1);
}
