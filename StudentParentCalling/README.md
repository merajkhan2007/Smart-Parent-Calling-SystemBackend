# Student Parent Calling System

A professional IoT embedded systems solution designed for schools and educational campuses using an **ESP32 DevKit V1**, an **RC522 RFID scanner**, a **0.96" SSD1306 OLED display**, and a **SIMCom A7670C 4G breakout module**. 

The system provides an automated, reliable way for students to call their parents directly by tapping their RFID identification card.

---

## Pin Connections

| Device | Component Pin | ESP32 GPIO Pin | Description |
| :--- | :--- | :--- | :--- |
| **RC522 RFID** | SDA | GPIO 5 | SPI Chip Select (SS) |
| | SCK | GPIO 18 | SPI Clock |
| | MOSI | GPIO 23 | SPI MOSI |
| | MISO | GPIO 19 | SPI MISO |
| | RST | GPIO 4 | Reset |
| **SSD1306 OLED** | SDA | GPIO 21 | I2C SDA |
| | SCL | GPIO 22 | I2C SCL |
| **SIMCom A7670C**| TXD | GPIO 16 (RX2) | ESP32 RX2 Pin |
| | RXD | GPIO 17 (TX2) | ESP32 TX2 Pin |
| | GND | GND | Common Ground Reference |
| **Push Buttons** | Button 1 (Father) | GPIO 25 | Active Low (Internal Pullup, connects to GND) |
| | Button 2 (Mother) | GPIO 26 | Active Low (Internal Pullup, connects to GND) |
| | Button 3 (End Call)| GPIO 27 | Active Low (Internal Pullup, connects to GND) |

> [!TIP]
> **4-Leg Tactile Button Wiring**: 
> A standard 4-leg push button has two pairs of internally connected pins. To ensure it functions correctly and does not short your connection:
> 1. Connect **one leg** (e.g., Top-Left) to the designated ESP32 GPIO pin.
> 2. Connect the **diagonally opposite leg** (e.g., Bottom-Right) to ESP32 Ground (`GND`).
> When the button is pressed, the circuit is completed (pulling the GPIO pin `LOW`). Using diagonal corners is the safest way to prevent permanent shorting.

> [!WARNING]
> Always ensure a common ground (GND) is shared between the ESP32 and the SIMCom A7670C module. The 4G module requires peak currents of up to 2A during network searches; power it using a dedicated 5V/2A external power supply, not from the ESP32's 3.3V pin.

---

## Required Libraries

Please install the following libraries via the Arduino Library Manager (`Ctrl+Shift+I` / `Cmd+Shift+I`):
1. **MFRC522** (by GitHub community) - For RFID card reading.
2. **Adafruit SSD1306** (by Adafruit) - For rendering graphics on the OLED.
3. **Adafruit GFX Library** (by Adafruit) - Core graphics drawing functions.
4. **Adafruit BusIO** (Dependency for SSD1306).

`SPI.h` and `Wire.h` are built directly into the ESP32 Core board support package and do not require manual installation.

---

## Installation Guide

1. **Board Configuration**: Add the ESP32 board URL to Arduino IDE (Preferences -> Additional Boards Manager URLs):
   `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
2. Open **Boards Manager** and install the `esp32` platform by Espressif.
3. Open the `StudentParentCalling.ino` file inside Arduino IDE 2.x.
4. Select the target board: **DOIT ESP32 DEVKIT V1** (or generic **ESP32 Dev Module**).
5. Ensure all project files (`display.h`, `display.cpp`, `sim7670.h`, `sim7670.cpp`, `students.h`, `icons.h`) are in the same directory as the main sketch.
6. Connect the ESP32 to your computer using a micro-USB cable.
7. Select the correct COM port, compile, and upload!

---

## Configuration Guide

### How to Add a Student
To register a new student, add a new row in the `STUDENT_DATABASE` array located in [students.h](file:///c:/Users/Meraj%20Khan/Desktop/parentcallingCode/StudentParentCalling/students.h):

```cpp
const Student STUDENT_DATABASE[] = {
    { "D3 5B E7 00", "Alex Mercer", "7003055759", "9876543210" },
    { "XX XX XX XX", "Student Name", "FatherNumber", "MotherNumber" } // <-- Add your new line here!
};
```
*Make sure to separate the hex bytes of the UID string with spaces (capitalized).*

### How to Change the Parent Number
To update the dial numbers for an existing student, locate the student's entry in [students.h](file:///c:/Users/Meraj%20Khan/Desktop/parentcallingCode/StudentParentCalling/students.h) and change the third (Father) or fourth (Mother) field values:

```cpp
{ "D3 5B E7 00", "Alex Mercer", "NEW_FATHER_NUMBER", "NEW_MOTHER_NUMBER" }
```

---

## Troubleshooting

- **OLED Init Fail**: Double-check I2C pins. SCL must be on GPIO22 and SDA on GPIO21. Ensure the OLED module address matches `0x3C`.
- **RFID Init Fail**: Verify SPI wiring. Ensure the MISO, MOSI, and SCK lines are connected to pins 19, 23, and 18 respectively. Check that SDA is on GPIO5 and RST is on GPIO4.
- **SIM Init Fail**:
  - The SIMCom A7670C requires a fast serial rate. Check TX2/RX2 wiring (cross TX to RX and RX to TX).
  - Ensure the modem is powered on. Many breakout modules require pulling a `PWRKEY` pin low/high for a brief period to boot up if they do not boot automatically.
- **No Signal / No SIM Icon**:
  - Verify that the Nano SIM is pushed firmly into the socket.
  - Test if the SIM is unlocked (does not require a PIN code).
  - Verify your antenna is attached properly to the A7670C module.
