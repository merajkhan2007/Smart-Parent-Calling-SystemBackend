#ifndef STUDENTS_H
#define STUDENTS_H

#include <Arduino.h>

/**
 * @brief Structure representing a Student and their parent's contact info.
 */
struct Student {
    const char* uid;          // RFID UID string in hex (e.g. "D3 5B E7 00")
    const char* studentName;  // Full name of the student
    const char* fatherNumber; // Father's phone number for dialing
    const char* motherNumber; // Mother's phone number for dialing
};

/**
 * @brief Authorized student database.
 * To add a student, simply add a new row to this array.
 */
const Student STUDENT_DATABASE[] = {
    // Authorized RFID card details as requested
    { "D3 5B E7 00", "Alex Mercer", "7003055759", "9876543210" }
};

// Automatically calculate the number of records in the database
const size_t STUDENT_COUNT = sizeof(STUDENT_DATABASE) / sizeof(STUDENT_DATABASE[0]);

#endif // STUDENTS_H
