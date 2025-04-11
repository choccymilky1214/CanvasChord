from typing import List, Dict
import datetime
import canvasapi

# This file will contain functions used by the bot code to make canvas api calls.


# Get list of canvas classes then return as names and id
async def getClassList(canvasToken: int) -> List[tuple[str, int]]:
    # Example: [("Intro to CS", 12345)]
    pass


# Return a list of recent announcements
async def getAnnouncements(canvasToken: int, classID: int) -> List[Dict[str, str]]:
    # Example: [{"title": "Exam Reminder", "url": "https://..."}]
    pass


# Return a list of assignments in class due in 3 months
async def getAssignments(canvasToken: int, classID: int) -> List[Dict[str, object]]:
    # Example:
    # [{"title": "HW1", "due_date": datetime, "class": "CSC 101"}]
    pass


# Returns announcements from a class from the past 7 days
async def getAnnouncements(canvasToken: int, classID: int) -> List[Dict]:
    # Example return format: [{"title": "Exam Reminder", "url": "https://canvas.com/class123/announcement456"}]
    pass


# Returns assignments due in the next 3 months from a given class
async def getAssignments(canvasToken: int, classID: int) -> List[Dict]:
    # Example return format:
    # [{"title": "Homework 1", "due_date": datetime.datetime(2025, 4, 20), "class": "CSC 101"}]
    pass
