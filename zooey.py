import discord
from discord.ext import commands

TOKEN = 'MzYyODc4NzMyMjc0MzY4NTIy.DK9vWg.Mi5Sw_roiyTxE1gJHq33nJcQX0o'

description = '''Zooey bot for discord shenanigans'''
bot = commands.Bot(command_prefix='!', description=description)

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

@bot.command()
async def conjunction():
    """Secret to winning MVP races"""
    await bot.say("Enjoy your mvp!")

@bot.command()
async def add(left : int, right : int):
    """Adds two numbers together."""
    await bot.say(left + right)

bot.run(TOKEN)
