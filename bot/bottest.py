import discord
from discord import app_commands
import apiKey

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # This allows all commands to be available in all context.
        self.tree = app_commands.CommandTree(self, allowed_contexts = app_commands.AppCommandContext(guild = True, dm_channel= True, private_channel= True))
        
    # This part runs when the bot first connects
    async def setup_hook(self):
        try:
            # Sync the commands to discord, this can take up to one hour.
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} commands.")
            # Copy all global commands then sync the commands to our test server, this takes at most a few minutes
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
    await interaction.response.send_message(f'Hi, {interaction.user.mention}')

# TODO example command, just adds 2 numbers
@client.tree.command()
@app_commands.describe(
    first_value='The first value you want to add something to',
    second_value='The value you want to add to the first value',
)
async def add(interaction: discord.Interaction, first_value: int, second_value: int):
    """Adds two numbers together."""
    await interaction.response.send_message(f'{first_value} + {second_value} = {first_value + second_value}')

# TODO example command, tests dm function
@client.tree.command(name="senddm", description="Send a DM to a user.")
@app_commands.describe(
    user="The user you want to DM",
    message="The message to send"
)
async def senddm(interaction: discord.Interaction, user: discord.User, message: str):
    """Sends a DM to a specified user."""
    try:
        await user.send(message)
        await interaction.response.send_message(f"Message sent to {user.mention}.", ephemeral=False)
    except discord.Forbidden:
        await interaction.response.send_message("Couldn't send the message. They may have DMs disabled.", ephemeral=False)
    except Exception as e:
        await interaction.response.send_message(f"Error sending DM: {e}", ephemeral=False)

# This runs when the bot is logged in and ready.
@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

client.run(apiKey.botToken)