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
    settingValue = True
    return settingValue
