import discord
from discord.ext import commands
from apiKey import testBotToken

# Set bot permissions 
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Create bot object and set a prefix
bot = commands.Bot(command_prefix='?', intents=intents)

# Report login to terminal
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

# Command $hello 
@bot.command()
async def hello(ctx):

    # Reply hello
    await ctx.send("hello!")

# Start bot with token from ./bot/apiKey.py
bot.run(testBotToken)