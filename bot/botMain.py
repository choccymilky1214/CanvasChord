import discord
from discord import app_commands
from typing import Optional
import apiKey
import canvasFunctions
import databaseFunctions
from datetime import datetime


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


# TODO example command, just says hello
@client.tree.command()
async def hello(interaction: discord.Interaction):
    """Says hello!"""
    await interaction.response.send_message(f"Hi, {interaction.user.mention}")


# TODO example command, just adds 2 numbers
@client.tree.command()
@app_commands.describe(
    first_value="The first value you want to add something to",
    second_value="The value you want to add to the first value",
)
async def add(interaction: discord.Interaction, first_value: int, second_value: int):
    """Adds two numbers together."""
    await interaction.response.send_message(
        f"{first_value} + {second_value} = {first_value + second_value}"
    )


# TODO example command, tests dm function
@client.tree.command(name="send_dm", description="Send a DM to a user.")
@app_commands.describe(user="The user you want to DM", message="The message to send")
async def send_dm(interaction: discord.Interaction, user: discord.User, message: str):
    """Sends a DM to a specified user."""
    try:
        await user.send(message)
        await interaction.response.send_message(
            f"Message sent to {user.mention}.", ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "Couldn't send the message. They may have DMs disabled.", ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"Error sending DM: {e}", ephemeral=True
        )


# /notification_settings command
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
    # Apply settings modifications
    try:
        if enable_notifications != None:
            await databaseFunctions.changeNotificationSetting(
                "enable_notifications", enable_notifications, interaction.user.id
            )
        if grade_postings != None:
            await databaseFunctions.changeNotificationSetting(
                "grade_postings", grade_postings, interaction.user.id
            )
        if due_dates != None:
            await databaseFunctions.changeNotificationSetting(
                "due_dates", due_dates, interaction.user.id
            )
        if announcement_postings != None:
            await databaseFunctions.changeNotificationSetting(
                "announcement_postings", announcement_postings, interaction.user.id
            )
    except Exception as e:
        await interaction.response.send_message(
            f"Something went wrong updating database settings\n {e}", ephemeral=True
        )
    # Return if notifications off
    try:
        if (
            await databaseFunctions.getNotificationSetting(
                "enable_notifications", interaction.user.id
            )
            != True
        ):
            await interaction.response.send_message(
                'You have disabled notifications, to enable use this command again and make "enable-notifications" True',
                ephemeral=True,
            )

        # Return current notification settings if on
        else:
            await interaction.response.send_message(
                "Notifications are enabled! Changed settings updated successfully!",
                ephemeral=True,
            )
    except Exception as e:
        await interaction.response.send_message(
            f"Something went wrong gathering your settings from the database\n {e}",
            ephemeral=True,
        )


@client.tree.command(name="announcements", description="Get recent class announcements")
@app_commands.describe(class_name="The name of the class to get announcements from")
async def announcements(interaction: discord.Interaction, class_name: str):
    """Returns recent announcements for a class."""
    await interaction.response.defer(ephemeral=True)

    try:
        canvas_token = await databaseFunctions.getCanvasToken(interaction.user.id)
        class_list = await canvasFunctions.getClassList(canvas_token)

        matched = [
            cid for name, cid in class_list if class_name.lower() in name.lower()
        ]
        if not matched:
            await interaction.followup.send(
                "No class found with that name.", ephemeral=True
            )
            return

        class_id = matched[0]
        announcements = await canvasFunctions.getAnnouncements(canvas_token, class_id)
        if not announcements:
            await interaction.followup.send(
                "No recent announcements found.", ephemeral=True
            )
            return

        content = "\n\n".join(
            f"**{a['title']}**\n<{a['url']}>" for a in announcements[:5]
        )
        await interaction.followup.send(content, ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"Error: {e}", ephemeral=True)


@client.tree.command(
    name="calendar",
    description="Get assignments between now and a future date (max 90 days)",
)
@app_commands.describe(
    end_date="The last date to look for assignments (YYYY-MM-DD)",
    class_name="Optional class name",
)
async def calendar(
    interaction: discord.Interaction, end_date: str, class_name: Optional[str] = None
):
    """Returns assignments due between now and given date (max 90 days)."""
    await interaction.response.defer(ephemeral=True)

    try:
        now = datetime.now()
        end = datetime.strptime(end_date, "%Y-%m-%d")

        if (end - now).days > 90 or (end - now).days < 0:
            await interaction.followup.send(
                "Please pick a date within the next 90 days.", ephemeral=True
            )
            return

        canvas_token = await databaseFunctions.getCanvasToken(interaction.user.id)
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

        # Filter and format
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


from discord import app_commands


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
    """Schedule a DM reminder."""
    await interaction.response.defer(ephemeral=True)

    try:
        remind_time = datetime.strptime(when, "%Y-%m-%d %H:%M")
        if remind_time <= datetime.now():
            await interaction.followup.send(
                "Please choose a future time.", ephemeral=True
            )
            return

        recurrence_value = recurring.value if recurring else None
        await databaseFunctions.addReminder(
            interaction.user.id, remind_time, recurrence_value, content
        )

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


@client.tree.command(name="classlist", description="List your current classes.")
async def classlist(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        token = await databaseFunctions.getCanvasToken(interaction.user.id)
        classes = await canvasFunctions.getClassList(token)
        if not classes:
            await interaction.followup.send("No classes found.")
            return
        msg = "\n".join([f"• {name}" for name, _ in classes])
        await interaction.followup.send(f"Here are your current classes:\n{msg}")
    except Exception as e:
        await interaction.followup.send(f"Error fetching class list: {e}")


@client.tree.command(name="login", description="Connect your Canvas account.")
async def login(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"[Click here to log in to Canvas](https://yourdomain.com/auth?user={interaction.user.id})",
        ephemeral=True,
    )


@client.tree.command(name="logout", description="Delete all your data from the bot.")
async def logout(interaction: discord.Interaction):
    try:
        await databaseFunctions.deleteUser(interaction.user.id)
        await interaction.response.send_message(
            "Your data has been deleted.", ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"Error during logout: {e}", ephemeral=True
        )


# This runs when the bot is logged in and ready.
# All commands should be above this
@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")


client.run(apiKey.botToken)
