import asyncio
import sys
import re
import discord.ext
import processDB
import requests
import time
from discord.ext import commands

from bs4 import BeautifulSoup

holo_dict = {
    "湊あくあ": "Aqua",
    "兎田ぺこら": "Pekora",
    "さくらみこ": "Miko",
    "桐生ココ": "Coco",
    "天音かなた": "Kanata",
    "赤井はあと": "Haato",
    "宝鐘マリン": "Marine",
    "戌神ころね": "Korone",
    "潤羽るしあ": "Rushia",
    "夏色まつり": "Matsuri",
    "角巻わため": "Watame"
}

url = 'https://schedule.hololive.tv/lives/all'

page = requests.get(url).content
soup = BeautifulSoup(page, 'html.parser')
live = soup.findAll('a', style=re.compile("border: 3px red solid"))

class Hololive():
    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True)
    async def hololive(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.bot.say("Invalid subcommand passed.")

    @hololive.command(pass_context=True)
    async def whomst(self, ctx):
        if live is not None:
            await self.bot.say("The following Vtubers are live:")
            for tuber in live:
                stream_url = "<" + tuber['href'] + ">"
                channel = str(tuber.text.replace(" ", "").replace("\n", "").replace("\r", "")).replace(":", "")
                channel = ''.join([i for i in channel if not i.isdigit()])
                if channel in holo_dict:
                    await self.bot.say(holo_dict[channel] + " " + stream_url)
            return

        else:
            await self.bot.say("Nobody is live.")
            return

def setup(bot):
    bot.add_cog(Hololive(bot))

