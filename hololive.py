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
    "角巻わため": "Watame",
    "常闇トワ": "Towa",
    "ロボ子さん": "Roboco",
    "大神ミオ": "Mio",
}

url = 'https://schedule.hololive.tv/lives/all'


class Hololive():
    def __init__(self, bot):
        self.bot = bot

    def _check_dict(self, live_soup):
        live_dict = {}
        for t in live_soup:
            chan = str(t.text.replace(" ", "").replace("\n", "").replace("\r", "")).replace(":", "")
            chan = ''.join([i for i in chan if not i.isdigit()])
            if chan in holo_dict:
                live_dict[chan] = "<" + t['href'] + ">"
        return live_dict

    @commands.group(pass_context=True)
    async def hololive(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.bot.say("Invalid subcommand passed.")

    @hololive.command(pass_context=True)
    async def whomst(self, ctx):
        page = requests.get(url).content
        soup = BeautifulSoup(page, 'html.parser')
        live = soup.find_all('a', style=re.compile("border: 3px red solid"))
        live_chan = self._check_dict(live)

        if live is not None and len(live_chan) > 0:
            await self.bot.say("Streaming now:")
            for channel, stream_url in live_chan.items():
                await self.bot.say(holo_dict[channel] + " " + stream_url)
            return

        else:
            await self.bot.say("Nobody is live.")
            return

def setup(bot):
    bot.add_cog(Hololive(bot))

