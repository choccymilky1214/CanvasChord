from typing import List, Dict, Optional
import datetime
import mysql.connector
import apiKey

# Replace with your actual MySQL database credentials
DB_CONFIG = {
    "host": apiKey.databaseHost,
    "user": apiKey.databaseUser,
    "password": apiKey.databasePassword,
    "database": apiKey.databaseName,
}


# Helper function to create a new database connection
def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


# Retrieves the Canvas API token and domain for a given Discord user ID
async def getCanvasToken(discordID: int) -> Optional[tuple[str, str]]:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT ct.token, ct.domain
            FROM canvas_token ct
            JOIN users u ON ct.userID = u.userID
            WHERE u.discordID = %s
            """,
            (discordID,),
        )
        result = cursor.fetchone()
        return (result[0], result[1]) if result else None
    finally:
        cursor.close()
        conn.close()


# Retrieves all notification settings for a specific Discord user
async def getNotificationSettings(discordID: int) -> Dict[str, bool]:
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT c.enable_notifications, c.grade_postings, c.due_dates, c.announcement_postings
            FROM configurations c
            JOIN users u ON c.userID = u.userID
            WHERE u.discordID = %s
            """,
            (discordID,),
        )
        result = cursor.fetchone()
        return result if result else {}  # Return settings as a dictionary
    finally:
        cursor.close()
        conn.close()


# Updates or inserts multiple notification settings for a user
async def changeNotificationSettings(discordID: int, settings: Dict[str, bool]):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Get the internal userID
        cursor.execute("SELECT userID FROM users WHERE discordID = %s", (discordID,))
        result = cursor.fetchone()
        if not result:
            return  # User not found

        userID = result[0]

        # Prepare the SET clause dynamically for UPDATE
        set_clause = ", ".join(f"{k} = %s" for k in settings)
        values = list(settings.values()) + [userID]

        # Insert new record or update existing one using ON DUPLICATE KEY
        cursor.execute(
            f"""
            INSERT INTO configurations (userID, {', '.join(settings)})
            VALUES ({', '.join(['%s'] * (len(settings) + 1))})
            ON DUPLICATE KEY UPDATE {set_clause}
            """,
            values,
        )

        conn.commit()
    finally:
        cursor.close()
        conn.close()


# Fetches all saved reminders for a specific Discord user
async def getReminders(discordID: int) -> List[Dict]:
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT r.`when`, r.recurring, r.content
            FROM reminders r
            JOIN users u ON r.userID = u.userID
            WHERE u.discordID = %s
            """,
            (discordID,),
        )
        results = cursor.fetchall()
        return results  # Returns a list of reminder dictionaries
    finally:
        cursor.close()
        conn.close()


# Adds a new reminder for a user with optional recurrence and a custom message
async def addReminder(
    discordID: int, when: datetime.datetime, recurring: Optional[str], content: str
):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Get the internal userID
        cursor.execute("SELECT userID FROM users WHERE discordID = %s", (discordID,))
        result = cursor.fetchone()
        if not result:
            return  # User not found

        userID = result[0]

        cursor.execute(
            """
            INSERT INTO reminders (userID, `when`, recurring, content)
            VALUES (%s, %s, %s, %s)
            """,
            (userID, when, recurring, content),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


# Completely deletes a user and their associated data (for logout or account reset)
async def deleteUser(discordID: int):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Get the internal userID
        cursor.execute("SELECT userID FROM users WHERE discordID = %s", (discordID,))
        result = cursor.fetchone()
        if not result:
            return  # User not found

        userID = result[0]

        # Delete related records using userID
        cursor.execute("DELETE FROM reminders WHERE userID = %s", (userID,))
        cursor.execute("DELETE FROM configurations WHERE userID = %s", (userID,))
        cursor.execute("DELETE FROM canvas_token WHERE userID = %s", (userID,))

        # Delete from users table using discordID
        cursor.execute("DELETE FROM users WHERE discordID = %s", (discordID,))

        conn.commit()
    finally:
        cursor.close()
        conn.close()
