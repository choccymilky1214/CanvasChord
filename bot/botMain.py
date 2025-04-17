from datetime import datetime
from typing import Optional, List
import discord
from discord import app_commands
import apiKey
import canvasFunctions
import databaseFunctions


async def ensure_logged_in(interaction: discord.Interaction) -> Optional[str]:
    try:
        token = await databaseFunctions.getCanvasToken(interaction.user.id)
        if not token:
            raise ValueError("No token")
        return token
    except Exception:
        await interaction.response.send_message(
            f"You are not logged in. Please use the /login command or visit: https://{apiKey.domainURL}/auth?user={interaction.user.id}",
            ephemeral=True,
        )
        return None


async def class_name_autocomplete(
    interaction: discord.Interaction, current: str
) -> List[app_commands.Choice[str]]:
    try:
        token = await databaseFunctions.getCanvasToken(interaction.user.id)
        classes = await canvasFunctions.getClassList(token)

        # Filter classes based on what user is typing (`current`)
        matches = [
            app_commands.Choice(name=name, value=name)
            for name, _ in classes
            if current.lower() in name.lower()
        ][
            :25
        ]  # Max 25 results
        return matches

    except Exception:
        return []  # Return empty if anything fails


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # This allows all commands to be available in all context.
        self.tree = app_commands.CommandTree(
            self,
            allowed_contexts=app_commands.AppCommandContext(
                guild=True, dm_channel=True, private_channel=True
            ),
        )

    # This part runs when the bot first connects
    async def setup_hook(self):
        try:
            # Sync the commands to discord, this can take up to one hour.
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} commands.")
            # Copy all global commands then sync the commands to our test server, this takes at most a few minutes.
            self.tree.copy_global_to(guild=discord.Object(apiKey.ownerGuild))
            syncedGuild = await self.tree.sync(guild=discord.Object(apiKey.ownerGuild))
            print(f"Synced {len(syncedGuild)} commands to guild.")
        except Exception as e:
            print(f"Error syncing commands in setup_hook: {e}")


intents = discord.Intents.default()
client = MyClient(intents=intents)


# /notification_settings command - sets new notification settings in the database
# TODO Rewrite this to use lists instead of if statement for nicer database queries
@client.tree.command(
    name="notification_settings", description="Edit notification settings"
)
@app_commands.describe(
    enable_notifications="Enable notifications",
    grade_postings="If you would like to notified when grades are posted.",
    due_dates="If you would like to be notified about upcoming due dates.",
    announcement_postings="If you would like to be notified about new announcements.",
)
async def notification_settings(
    interaction: discord.Interaction,
    enable_notifications: Optional[bool] = None,
    grade_postings: Optional[bool] = None,
    due_dates: Optional[bool] = None,
    announcement_postings: Optional[bool] = None,
):
    # Defer response to prevent timeout
    await interaction.response.defer(ephemeral=True)
    canvas_token = await ensure_logged_in(interaction)
    if not canvas_token:
        return

    # Collect only the provided settings
    new_settings = {
        k: v
        for k, v in {
            "enable_notifications": enable_notifications,
            "grade_postings": grade_postings,
            "due_dates": due_dates,
            "announcement_postings": announcement_postings,
        }.items()
        if v is not None
    }

    try:
        # Update only if there are any settings provided
        if new_settings:
            await databaseFunctions.changeNotificationSettings(
                interaction.user.id, new_settings
            )

        # Fetch updated settings to determine response
        current_settings = await databaseFunctions.getNotificationSettings(
            interaction.user.id
        )

        if not current_settings.get("enable_notifications", False):
            await interaction.followup.send(
                'You have disabled notifications. To enable them, use this command again and set "enable-notifications" to True.',
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                "Notifications are enabled! Your settings were updated successfully!",
                ephemeral=True,
            )

    except Exception as e:
        await interaction.followup.send(
            f"Something went wrong updating your settings:\n{e}", ephemeral=True
        )


# /announcements - get recent announcements
# TODO rewrite so it can autofill class's from user class list
@client.tree.command(name="announcements", description="Get recent class announcements")
@app_commands.describe(class_name="The name of the class to get announcements from")
@app_commands.autocomplete(class_name=class_name_autocomplete)
async def announcements(interaction: discord.Interaction, class_name: str):
    # We use defer command to tell discord to wait up to 15 minutes for a response form the bot, otherwise the command will fail if this takes time.
    await interaction.response.defer(ephemeral=True)

    try:
        # Gather canvas token and list of classes
        canvas_token = await ensure_logged_in(interaction)
        if not canvas_token:
            return

        class_list = await canvasFunctions.getClassList(canvas_token)

        matched = [
            cid for name, cid in class_list if class_name.lower() in name.lower()
        ]
        # Return if no classes found
        if not matched:
            await interaction.followup.send(
                "No class found with that name.", ephemeral=True
            )
            return

        # Return if no announcements found for class
        class_id = matched[0]
        announcements = await canvasFunctions.getAnnouncements(canvas_token, class_id)
        if not announcements:
            await interaction.followup.send(
                "No recent announcements found.", ephemeral=True
            )
            return

        # Gather all the announcements and then send them in the message
        content = "\n\n".join(
            f"**{a['title']}**\n<{a['url']}>" for a in announcements[:5]
        )
        await interaction.followup.send(content, ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"Error: {e}", ephemeral=True)


# /calendar command - retrieves upcoming assignments from Canvas
# Accepts a future end date (max 90 days ahead) and an optional class name
# Gathers assignments from all classes or a specific class
# Filters by due date and formats results by class
@client.tree.command(
    name="calendar",
    description="Get assignments between now and a future date (max 90 days)",
)
@app_commands.describe(
    end_date="The last date to look for assignments (YYYY-MM-DD)",
    class_name="Optional class name",
)
@app_commands.autocomplete(class_name=class_name_autocomplete)
async def calendar(
    interaction: discord.Interaction, end_date: str, class_name: Optional[str] = None
):
    await interaction.response.defer(ephemeral=True)

    try:
        # Validate the date format and range
        now = datetime.now()
        end = datetime.strptime(end_date, "%Y-%m-%d")

        if (end - now).days > 90 or (end - now).days < 0:
            await interaction.followup.send(
                "Please pick a date within the next 90 days.", ephemeral=True
            )
            return

        # Retrieve user's Canvas token and optionally filter by class name
        canvas_token = await ensure_logged_in(interaction)
        if not canvas_token:
            return
        assignments = []

        if class_name:
            classes = await canvasFunctions.getClassList(canvas_token)
            matched = [
                cid for name, cid in classes if class_name.lower() in name.lower()
            ]
            if not matched:
                await interaction.followup.send("Class not found.", ephemeral=True)
                return
            assignments = await canvasFunctions.getAssignments(canvas_token, matched[0])
        else:
            classes = await canvasFunctions.getClassList(canvas_token)
            for _, cid in classes:
                assignments += await canvasFunctions.getAssignments(canvas_token, cid)

        # Aggregate and filter assignments by due date
        filtered = [a for a in assignments if now <= a["due_date"] <= end]
        grouped = {}
        for a in filtered:
            grouped.setdefault(a["class"], []).append(
                f"- {a['title']} (due {a['due_date'].strftime('%b %d')})"
            )

        if not grouped:
            await interaction.followup.send(
                "No assignments found in that time range.", ephemeral=True
            )
            return

        # Group results and format message per class
        msg = ""
        for cls, items in grouped.items():
            msg += f"\n**{cls}**\n" + "\n".join(items) + "\n"

        await interaction.followup.send(msg.strip(), ephemeral=True)

    except ValueError:
        await interaction.followup.send(
            "Invalid date format. Please use YYYY-MM-DD.", ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(f"Error: {e}", ephemeral=True)


# /reminder command - creates a new reminder with optional recurrence
# Accepts a future datetime, a message, and optional daily/weekly repeat
# Saves reminder to the database and confirms setup
@client.tree.command(name="reminder", description="Set a reminder")
@app_commands.describe(
    when="Time in 'YYYY-MM-DD HH:MM' format",
    recurring="Repeat daily or weekly",
    content="Reminder message",
)
@app_commands.choices(
    recurring=[
        app_commands.Choice(name="Daily", value="daily"),
        app_commands.Choice(name="Weekly", value="weekly"),
    ]
)
async def reminder(
    interaction: discord.Interaction,
    when: str,
    recurring: Optional[app_commands.Choice[str]],
    content: str,
):
    await interaction.response.defer(ephemeral=True)

    try:
        # Parse and validate the datetime input
        remind_time = datetime.strptime(when, "%Y-%m-%d %H:%M")
        if remind_time <= datetime.now():
            await interaction.followup.send(
                "Please choose a future time.", ephemeral=True
            )
            return

        # Check if user is logged in
        token_check = await ensure_logged_in(interaction)
        if not token_check:
            return

        # Save reminder details in the database
        recurrence_value = recurring.value if recurring else None
        await databaseFunctions.addReminder(
            interaction.user.id, remind_time, recurrence_value, content
        )

        # Format and send confirmation message
        note = f" and will repeat {recurrence_value}" if recurrence_value else ""
        await interaction.followup.send(
            f"Reminder set for {remind_time}{note}!", ephemeral=True
        )

    except ValueError:
        await interaction.followup.send(
            "Time must be in format YYYY-MM-DD HH:MM", ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(f"Error setting reminder: {e}", ephemeral=True)


# /classlist command - lists the user's current enrolled Canvas classes
# Uses Canvas API token to retrieve class list
# Returns formatted bullet list or error
@client.tree.command(name="classlist", description="List your current classes.")
async def classlist(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        token = await ensure_logged_in(interaction)
        if not token:
            return
        classes = await canvasFunctions.getClassList(token)
        if not classes:
            await interaction.followup.send("No classes found.")
            return
        msg = "\n".join([f"• {name}" for name, _ in classes])
        await interaction.followup.send(f"Here are your current classes:\n{msg}")
    except Exception as e:
        await interaction.followup.send(f"Error fetching class list: {e}")


# /login command - provides a link for the user to connect their Canvas account
# Includes user ID in query string for identification
@client.tree.command(name="login", description="Connect your Canvas account.")
async def login(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await interaction.response.send_message(
        f"[Click here to log in to Canvas](https://{apiKey.domainURL}/auth?user={interaction.user.id})",
        ephemeral=True,
    )


# /logout command - deletes all user data from the bot
# Calls database cleanup and confirms with user
@client.tree.command(name="logout", description="Delete all your data from the bot.")
async def logout(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        await databaseFunctions.deleteUser(interaction.user.id)
        await interaction.response.send_message(
            "Your data has been deleted.", ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"Error during logout: {e}", ephemeral=True
        )


# Event - triggered when the bot finishes connecting to Discord
# Logs bot identity and startup confirmation
@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")


# Starts the Discord bot using the provided bot token
client.run(apiKey.botToken)
