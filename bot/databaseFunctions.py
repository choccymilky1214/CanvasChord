from typing import List, Dict, Optional
import datetime
import mysql.connector

# This script will contain functions the bot will use for database calls.


async def getCanvasToken(discordID: int) -> int:
    # Get canvas token from discord id then return
    pass


# Returns all notification settings for a user
async def getNotificationSettings(discordID: int) -> Dict[str, bool]:
    # Example return: {"enable_notifications": True, "grade_postings": False, ...}
    pass


# Updates multiple notification settings at once
async def changeNotificationSettings(discordID: int, settings: Dict[str, bool]):
    # settings will be a dict like {"grade_postings": True, "due_dates": False}
    pass


# Gets saved reminders for a user
async def getReminders(discordID: int) -> List[Dict]:
    # Example return format: [{"when": datetime.datetime, "recurring": "daily", "content": "Study!"}]
    pass


# Saves a reminder
async def addReminder(
    discordID: int, when: datetime.datetime, recurring: Optional[str], content: str
):
    pass


# Deletes a user's data (used for logout)
async def deleteUser(discordID: int):
    pass
