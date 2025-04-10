import discord
from discord import app_commands
from typing import Optional
import apiKey
import canvasFunctions
import databaseFunctions


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


# This runs when the bot is logged in and ready.
# All commands should be above this
@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")


client.run(apiKey.botToken)
