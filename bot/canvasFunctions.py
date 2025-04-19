from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple, Any
import os


# Get list of canvas classes then return as names and ids
async def getClassList(CANVAS_TOKEN: str, CANVAS_BASE_URL) -> list[tuple[str, int]]:
    """
    Get a list of active courses for the user in the current term.
    Returns a list of tuples with (course_name, course_id)
    """
    headers = {"Authorization": f"Bearer {CANVAS_TOKEN}"}

    try:
        response = requests.get(
            f"{CANVAS_BASE_URL}/api/v1/courses",
            headers=headers,
            params={
                "enrollment_state": "active",
                "state[]": "available",
                "current_only": True,
            },
        )

        if response.status_code == 200:
            courses = response.json()
            # Filter out courses without a name (access restricted)
            course_list = [
                (course["name"], course["id"]) for course in courses if "name" in course
            ]
            return course_list
        else:
            print(f"Error fetching courses: {response.status_code}")
            return []
    except Exception as e:
        print(f"Exception in getClassList: {e}")
        return []


async def getRecentAnnouncementsAllClasses(
    CANVAS_TOKEN: str, CANVAS_BASE_URL
) -> List[Dict[str, str]]:
    now = datetime.now(tz=timezone.utc)
    start_date = (now - timedelta(days=14)).isoformat()
    headers = {"Authorization": f"Bearer {CANVAS_TOKEN}"}

    announcements_all = []

    # Get the list of active classes
    class_list = await getClassList(CANVAS_TOKEN)

    for class_name, class_id in class_list:
        try:
            response = requests.get(
                f"{CANVAS_BASE_URL}/api/v1/courses/{class_id}/discussion_topics",
                headers=headers,
                params={"only_announcements": True, "start_date": start_date},
            )

            if response.status_code == 200:
                announcements = response.json()
                for ann in announcements:
                    posted_at = ann.get("posted_at", "")
                    if posted_at:
                        posted_date = datetime.fromisoformat(
                            posted_at.replace("Z", "+00:00")
                        )
                        if posted_date >= now - timedelta(days=14):
                            soup = BeautifulSoup(ann.get("message", ""), "html.parser")
                            announcements_all.append(
                                {
                                    "class": class_name,
                                    "title": ann.get("title", "No Title"),
                                    "url": ann.get("html_url", ""),
                                    "message": soup.get_text(strip=True),
                                    "posted_at": posted_date.strftime(
                                        "%Y-%m-%d %H:%M:%S"
                                    ),
                                }
                            )
            else:
                print(
                    f"Error fetching announcements for {class_name}: {response.status_code}"
                )
        except Exception as e:
            print(f"Exception for class {class_name}: {e}")

    return announcements_all


# Return a list of announcements from a class from the past 7 days
async def getAnnouncements(
    canvasToken: str, classID: int, CANVAS_BASE_URL
) -> List[Dict]:
    """
    Get announcements for a specific class from the past 7 days.
    Returns a list of dictionaries with title and url.
    Example: [{"title": "Exam Reminder", "url": "https://canvas.com/class123/announcement456"}]
    """
    headers = {"Authorization": f"Bearer {canvasToken}"}

    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)

    try:
        response = requests.get(
            f"{CANVAS_BASE_URL}/api/v1/courses/{classID}/discussion_topics",
            headers=headers,
            params={"only_announcements": True},
        )

        if response.status_code == 200:
            announcements = response.json()
            result = []

            for ann in announcements:
                posted_at = ann.get("posted_at")
                title = ann.get("title", "No Title")
                url = ann.get("html_url", "")

                if posted_at:
                    try:
                        posted_time = datetime.fromisoformat(
                            posted_at.replace("Z", "+00:00")
                        )
                        if posted_time >= seven_days_ago:
                            result.append({"title": title, "url": url})
                    except ValueError:
                        continue

            return result
        else:
            print(f"Error fetching announcements: {response.status_code}")
            return []
    except Exception as e:
        print(f"Exception in getAnnouncements: {e}")
        return []


# Returns assignments due in the next 3 months from a given class
async def getAssignments(
    CANVAS_TOKEN: str, classID: int, className: str, CANVAS_BASE_URL
) -> List[Dict]:
    """
    Get assignments for a specific class due in the next 3 months.
    Returns a list of dictionaries with assignment details.
    """
    headers = {"Authorization": f"Bearer {CANVAS_TOKEN}"}

    # Get current UTC time and future cutoff
    now = datetime.now(timezone.utc)
    three_months_later = now + timedelta(days=90)

    try:
        # Get class name from API if not provided
        if not className:
            class_response = requests.get(
                f"{CANVAS_BASE_URL}/api/v1/courses/{classID}", headers=headers
            )
            if class_response.status_code == 200:
                class_info = class_response.json()
                className = class_info.get("name", f"Class {classID}")
            else:
                className = f"Class {classID}"

        # Get all assignments
        response = requests.get(
            f"{CANVAS_BASE_URL}/api/v1/courses/{classID}/assignments", headers=headers
        )
        if response.status_code != 200:
            print(f"Error fetching assignments: {response.status_code}")
            return []

        assignments = response.json()
        result = []

        for assignment in assignments:
            due_str = assignment.get("due_at")
            if not due_str:
                continue

            # Convert to timezone-aware datetime
            try:
                due_date = datetime.fromisoformat(due_str.replace("Z", "+00:00"))
            except Exception as e:
                print(f"Skipping assignment due to date parsing error: {e}")
                continue

            # Check if it's within the next 3 months
            if now <= due_date <= three_months_later:
                result.append(
                    {
                        "title": assignment.get("name", "Unnamed Assignment"),
                        "due_date": due_date,
                        "class_name": className,
                        "class_id": classID,
                    }
                )

        result.sort(key=lambda x: x["due_date"])
        return result

    except Exception as e:
        print(f"Exception in getAssignments: {e}")
        return []
