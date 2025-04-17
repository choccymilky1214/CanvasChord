import mysql.connector
from mysql.connector import Error

# Database connection settings (update with your actual credentials)
DB_CONFIG = {
    "host": "localhost",
    "user": "your_username",
    "password": "your_password",
    "database": "your_database_name"
}

# Helper function to get a connection to the MySQL database
def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Get the latest Canvas token for a user using their Discord ID
async def getCanvasToken(discordID: int) -> str:
    """
    Retrieves the most recent Canvas token for the user linked to the provided Discord ID.
    Uses a JOIN to find the matching UserID, then gets the latest token based on ExpirationDate.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ct.Token 
            FROM Canvas_Token ct
            JOIN Users u ON ct.UserID = u.UserID
            WHERE u.DiscordID = %s
            ORDER BY ct.ExpirationDate DESC
            LIMIT 1;
        """, (discordID,))
        
        result = cursor.fetchone()
        return result[0] if result else None

    except Error as e:
        print(f"[DB ERROR] getCanvasToken: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

# Update a user's notification setting (e.g., enable/disable grade posts)
async def changeNotificationSetting(settingName: str, settingValue: bool, discordID: int):
    """
    Changes one of the user's notification settings in the Configurations table.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        valid_settings = {"enable_notifications", "grade_postings", "due_dates", "announcement_postings"}
        if settingName not in valid_settings:
            raise ValueError(f"Invalid setting name: {settingName}")

        query = f"""
            UPDATE Configurations c
            JOIN Users u ON c.UserID = u.UserID
            SET c.{settingName} = %s
            WHERE u.DiscordID = %s;
        """
        cursor.execute(query, (int(settingValue), discordID))
        conn.commit()

    except Error as e:
        print(f"[DB ERROR] changeNotificationSetting: {e}")
    finally:
        cursor.close()
        conn.close()

# Fetch a specific setting (like enable_notifications) for a given user
async def getNotificationSetting(settingName: str, discordID: int) -> bool:
    """
    Retrieves the value of a notification setting for a user using their Discord ID.
    Returns False if the setting is not found or an error occurs.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        valid_settings = {"enable_notifications", "grade_postings", "due_dates", "announcement_postings"}
        if settingName not in valid_settings:
            raise ValueError(f"Invalid setting name: {settingName}")

        query = f"""
            SELECT c.{settingName}
            FROM Configurations c
            JOIN Users u ON c.UserID = u.UserID
            WHERE u.DiscordID = %s;
        """
        cursor.execute(query, (discordID,))
        result = cursor.fetchone()
        return bool(result[0]) if result else False

    except Error as e:
        print(f"[DB ERROR] getNotificationSetting: {e}")
        return False
    finally:
        cursor.close()
        conn.close()
