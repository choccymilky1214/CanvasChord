import mysql.connector

# This script will contain functions the bot will use for database calls.


async def changeNotificationSetting(
    settingName: str, settingValue: int, discordID: int
):
    # Change notification setting in database then return
    return


async def getNotificationSetting(settingName: str, discordID: int) -> bool:
    # Get named setting and return its value
    settingValue = True
    return settingValue
