#ifndef DISPLAY_H
#define DISPLAY_H

#include <Arduino.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define SCREEN_ADDRESS 0x3C

/**
 * @class Display
 * @brief Class managing SSD1306 OLED interface and modern UI screens.
 */
class Display {
private:
    Adafruit_SSD1306 oled;
    
    // Internal helper to print centered text
    void drawCenteredText(const String& text, int y, int textSize, uint16_t color = SSD1306_WHITE);
    
    // Draw the top bar with signal strength and status
    void drawHeader(int signalDbm, bool simOk, bool netOk);

public:
    Display();

    // Initialize the OLED screen
    bool begin();

    // Screens
    void bootScreen();
    void waitingScreen(int signalDbm, bool simOk, bool netOk);
    void verifiedScreen(const char* studentName);
    void selectParentScreen(const char* studentName);
    void callingScreen(const char* studentName, const char* parentLabel, const char* phoneNumber);
    void completedScreen();
    void deniedScreen();
    void errorScreen(const char* errorMsg);

    // Core Drawing Helpers
    void drawPhone(int x, int y);
    void drawRFID(int x, int y);
    void drawTick(int x, int y);
    void drawCross(int x, int y);
    void drawSignal(int x, int y, int dbm, bool simOk, bool netOk);
    void loadingAnimation(int y, int delayMs);
};

#endif // DISPLAY_H
