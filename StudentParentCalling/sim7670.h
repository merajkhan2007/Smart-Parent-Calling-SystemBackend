#ifndef SIM7670_H
#define SIM7670_H

#include <Arduino.h>

/**
 * @class SIM7670
 * @brief Class encapsulating AT command interface for the SIMCom A7670C 4G LTE module.
 */
class SIM7670 {
private:
    HardwareSerial& modemSerial; // Reference to HardwareSerial (e.g. Serial2)
    uint32_t baud;               // Baud rate of the serial link (typically 115200)

public:
    /**
     * @brief Constructor for SIM7670 interface.
     * @param serialPort HardwareSerial reference to communicate with the modem.
     */
    SIM7670(HardwareSerial& serialPort);

    /**
     * @brief Initialize Serial communication link.
     * @param baudRate Baud rate for communication (defaults to 115200).
     * @return true if communication is successfully established with the modem, false otherwise.
     */
    bool begin(uint32_t baudRate = 115200);

    /**
     * @brief Send an AT command and return the raw modem response.
     * @param cmd The AT command string (with or without ending \r\n).
     * @param timeoutMs Maximum time to wait for a response in milliseconds.
     * @return String containing the response text from the modem.
     */
    String sendAT(const String& cmd, uint32_t timeoutMs = 2000);

    /**
     * @brief Dial a phone number using voice call command ATD.
     * @param phoneNumber Destination phone number string (e.g. "7003055759").
     * @return true if the dialing command was accepted (OK response), false if error.
     */
    bool dial(const String& phoneNumber);

    /**
     * @brief Hang up/disconnect any active voice call using AT+CHUP or ATH.
     * @return true if call hung up successfully (OK response), false if error.
     */
    bool hangup();

    /**
     * @brief Query current RSSI (Received Signal Strength Indicator).
     * @return Signal strength in dBm (negative value, e.g. -85), or 0 on error/no signal.
     */
    int getSignal();

    /**
     * @brief Check network registration status (AT+CGREG? or AT+CREG?).
     * @return true if registered to the network (home or roaming), false otherwise.
     */
    bool networkReady();

    /**
     * @brief Check if a call is currently active (dialing, alerting, or established).
     * @return true if call is active, false if idle/no active call.
     */
    bool isCallActive();

    /**
     * @brief Wait and read modem serial buffer for incoming characters up to timeout.
     * @param timeoutMs Time to wait for serial response.
     * @return String response read from the modem.
     */
    String waitResponse(uint32_t timeoutMs = 2000);
};

#endif // SIM7670_H
