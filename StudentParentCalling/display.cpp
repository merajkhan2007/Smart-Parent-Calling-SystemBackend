#include "display.h"
#include "icons.h"
#include <Wire.h>

/**
 * @brief Construct a new Display object.
 */
Display::Display() : oled(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET) {}

/**
 * @brief Initialize the SSD1306 OLED display.
 * @return true if initialization succeeded, false otherwise.
 */
bool Display::begin() {
    // SSD1306_SWITCHCAPVCC = generate display voltage from 3.3V internally
    if (!oled.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
        return false;
    }
    oled.clearDisplay();
    oled.setTextColor(SSD1306_WHITE);
    oled.display();
    return true;
}

/**
 * @brief Center and display a text string at a specific Y coordinate.
 * @param text The text string to display.
 * @param y The Y-coordinate for the baseline of the text.
 * @param textSize The font scale multiplier.
 * @param color The text color (defaults to White).
 */
void Display::drawCenteredText(const String& text, int y, int textSize, uint16_t color) {
    oled.setTextSize(textSize);
    oled.setTextColor(color);
    
    int16_t x1, y1;
    uint16_t w, h;
    
    // Calculate bounding box of text to center it perfectly
    oled.getTextBounds(text, 0, y, &x1, &y1, &w, &h);
    int x = (SCREEN_WIDTH - w) / 2;
    
    oled.setCursor(x, y);
    oled.print(text);
}

/**
 * @brief Draw the system status bar at the top of the OLED.
 * @param signalDbm Signal strength in dBm.
 * @param simOk true if SIM is present.
 * @param netOk true if registered to the cellular network.
 */
void Display::drawHeader(int signalDbm, bool simOk, bool netOk) {
    // Draw Title
    oled.setTextSize(1);
    oled.setTextColor(SSD1306_WHITE);
    oled.setCursor(2, 2);
    oled.print("RFID CALLER");

    // Draw bottom divider line for header
    oled.drawFastHLine(0, 11, SCREEN_WIDTH, SSD1306_WHITE);

    // Draw Signal Status
    drawSignal(112, 1, signalDbm, simOk, netOk);
}

/**
 * @brief Display the professional school boot logo and load progress bar.
 */
void Display::bootScreen() {
    oled.clearDisplay();
    
    // Draw school cap/graduation logo (48x48) centered at top
    // x = (128 - 48) / 2 = 40
    oled.drawBitmap(40, 2, logo_bmp, 48, 48, SSD1306_WHITE);
    
    // Draw loading animation below the logo (y = 54)
    loadingAnimation(54, 15);
}

/**
 * @brief Renders the idle waiting screen, prompting the user to tap their card.
 * @param signalDbm Current GSM network signal strength in dBm.
 * @param simOk true if GSM SIM card detected.
 * @param netOk true if GSM registered to home/roaming network.
 */
void Display::waitingScreen(int signalDbm, bool simOk, bool netOk) {
    oled.clearDisplay();
    
    // Draw header containing signal bars and title
    drawHeader(signalDbm, simOk, netOk);
    
    // Draw RFID bitmap centered (32x32)
    // x = (128 - 32) / 2 = 48, y = 14
    drawRFID(48, 14);
    
    // Prompt text
    drawCenteredText("TAP RFID CARD", 50, 1);
    
    oled.display();
}

/**
 * @brief Renders the success screen when an authorized RFID card is scanned.
 * @param studentName Name of the identified student.
 */
void Display::verifiedScreen(const char* studentName) {
    oled.clearDisplay();
    
    // Draw Check Tick Icon centered
    drawTick(48, 4);
    
    drawCenteredText("CARD VERIFIED", 42, 1);
    drawCenteredText(studentName, 52, 1);
    
    oled.display();
}

/**
 * @brief Renders the parent selection screen after verification.
 * @param studentName Name of the identified student.
 */
void Display::selectParentScreen(const char* studentName) {
    oled.clearDisplay();
    
    drawCenteredText("SELECT PARENT", 2, 1);
    oled.drawFastHLine(0, 11, SCREEN_WIDTH, SSD1306_WHITE);
    
    drawCenteredText(studentName, 16, 1);
    
    // Draw Father option
    oled.setCursor(4, 32);
    oled.setTextSize(1);
    oled.print("[Btn 1] FATHER");
    
    // Draw Mother option
    oled.setCursor(4, 44);
    oled.print("[Btn 2] MOTHER");
    
    // Draw Cancel/Exit option
    oled.setCursor(4, 56);
    oled.print("[Btn 3] CANCEL");
    
    oled.display();
}

/**
 * @brief Renders the dialing screen displaying student/parent details and dialing progress.
 * @param studentName Name of the student.
 * @param parentLabel Label for the parent ("Father" or "Mother").
 * @param phoneNumber Number being dialed.
 */
void Display::callingScreen(const char* studentName, const char* parentLabel, const char* phoneNumber) {
    oled.clearDisplay();
    
    // Draw calling phone icon slightly higher to leave space
    drawPhone(48, 2);
    
    String callingLabel = "Calling " + String(parentLabel) + "...";
    drawCenteredText(callingLabel, 36, 1);
    
    drawCenteredText(studentName, 46, 1);
    
    // Hint that button 3 ends the call
    drawCenteredText("[Btn 3] END CALL", 56, 1);
    
    oled.display();
}

/**
 * @brief Renders the screen indicating a successful call termination.
 */
void Display::completedScreen() {
    oled.clearDisplay();
    
    drawTick(48, 6);
    drawCenteredText("CALL COMPLETED", 44, 1);
    drawCenteredText("Have a nice day!", 54, 1);
    
    oled.display();
}

/**
 * @brief Renders the access denied screen when an unauthorized card is tapped.
 */
void Display::deniedScreen() {
    oled.clearDisplay();
    
    drawCross(48, 6);
    drawCenteredText("ACCESS DENIED", 44, 1);
    drawCenteredText("Unknown Card", 54, 1);
    
    oled.display();
}

/**
 * @brief Displays hardware or runtime system error notices.
 * @param errorMsg Reason for system failure.
 */
void Display::errorScreen(const char* errorMsg) {
    oled.clearDisplay();
    
    drawCross(48, 6);
    drawCenteredText("SYSTEM ERROR", 44, 1);
    drawCenteredText(errorMsg, 54, 1);
    
    oled.display();
}

// =========================================================================
// Drawing Helpers
// =========================================================================

void Display::drawPhone(int x, int y) {
    oled.drawBitmap(x, y, phone_bmp, 32, 32, SSD1306_WHITE);
}

void Display::drawRFID(int x, int y) {
    oled.drawBitmap(x, y, rfid_bmp, 32, 32, SSD1306_WHITE);
}

void Display::drawTick(int x, int y) {
    oled.drawBitmap(x, y, check_bmp, 32, 32, SSD1306_WHITE);
}

void Display::drawCross(int x, int y) {
    oled.drawBitmap(x, y, cross_bmp, 32, 32, SSD1306_WHITE);
}

/**
 * @brief Draw cell network signal bars dynamically based on dBm value.
 */
void Display::drawSignal(int x, int y, int dbm, bool simOk, bool netOk) {
    // If SIM missing, draw a stylized 'no sim' indicator
    if (!simOk) {
        // Draw standard SIM shape outline
        oled.drawRect(x, y, 12, 9, SSD1306_WHITE);
        oled.drawLine(x + 2, y + 2, x + 10, y + 7, SSD1306_WHITE);
        oled.drawLine(x + 10, y + 2, x + 2, y + 7, SSD1306_WHITE);
        return;
    }

    // Determine how many bars to fill based on dBm signal strength
    int bars = 0;
    if (netOk && dbm != 0) {
        if (dbm > -70) {
            bars = 4; // Excellent
        } else if (dbm > -85) {
            bars = 3; // Good
        } else if (dbm > -100) {
            bars = 2; // Fair
        } else if (dbm > -110) {
            bars = 1; // Weak
        } else {
            bars = 0; // Extremely weak
        }
    }

    // Draw the 4 signal bars outlines
    // Bar heights: 2, 4, 6, 8 at offset x
    for (int i = 0; i < 4; i++) {
        int barHeight = (i + 1) * 2;
        int barX = x + (i * 3);
        int barY = y + 8 - barHeight;
        
        if (netOk && i < bars) {
            // Draw filled bars for active signal
            oled.fillRect(barX, barY, 2, barHeight, SSD1306_WHITE);
        } else {
            // Draw empty outlines or nothing
            oled.drawFastVLine(barX, barY, barHeight, SSD1306_WHITE);
        }
    }

    // Draw an 'x' next to signal bars if network registration failed
    if (!netOk) {
        oled.drawLine(x - 4, y, x - 1, y + 8, SSD1306_WHITE);
        oled.drawLine(x - 1, y, x - 4, y + 8, SSD1306_WHITE);
    }
}

/**
 * @brief Smoothly animate a rounded progress bar.
 */
void Display::loadingAnimation(int y, int delayMs) {
    int w = 80;
    int h = 6;
    int x = (SCREEN_WIDTH - w) / 2;
    
    // Draw loading frame outline
    oled.drawRoundRect(x, y, w, h, 2, SSD1306_WHITE);
    oled.display();
    
    // Smoothly fill the loading bar
    for (int i = 0; i <= (w - 4); i += 2) {
        oled.fillRect(x + 2, y + 2, i, h - 4, SSD1306_WHITE);
        oled.display();
        delay(delayMs);
    }
}
