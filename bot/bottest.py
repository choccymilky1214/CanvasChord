import discord
from discord.ext import commands
from apiKey import botToken

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='?', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

@bot.command()
async def hello(ctx):
    await ctx.send("hello!")

bot.run(testBotToken)