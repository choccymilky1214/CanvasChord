from typing import List, Dict, Optional
import datetime
import mysql.connector

# This script will contain functions the bot will use for database calls.


async def getCanvasToken(discordID: int) -> int:
    # Get canvas token from discord id then return
    canvasToken = 123456789
    return canvasToken


async def changeNotificationSetting(
    settingName: str, settingValue: int, discordID: int
):
    # Change notification setting in database then return
    return


async def getNotificationSetting(settingName: str, discordID: int) -> bool:
    # Get named setting and return its value
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
