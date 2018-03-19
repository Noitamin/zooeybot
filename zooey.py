import discord
from discord.ext import commands
import re

TOKEN = 'NDI1MzgzNDkzMjc5Njc4NDcy.DZGtyw.xG9Rx3PsL3SMia5LuFzpxIlKn9c'


description = '''Zooey bot for discord shenanigans'''
bot = commands.Bot(command_prefix='&', description=description)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command()
async def hello():
    """Says world"""
    await bot.say("world")


async def conjunction():
    """Secret to winning MVP races"""
    await bot.say("Enjoy your mvp!")

@bot.command()
async def add(left : int, right : int):
    """Adds two numbers together."""
    await bot.say(left + right)

@bot.command()
async def saber():
    """rekt."""
    await bot.say("git rekt")

@bot.command()
async def big(message):
    """Hugify a given emoji"""
    pattern = re.compile("\<\:.+\:\d+\>")
    if (pattern.match(message)):
        emoji_id = re.sub(r'\<\:\D+|\>', '', message)
        new_message = "https://cdn.discordapp.com/emojis/" + emoji_id + ".png" 
        await bot.say(new_message)
    else:
        await bot.say("That's not a custom emoji. Try again")
        

bot.run(TOKEN)
