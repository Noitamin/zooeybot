import asyncio
import sys
import re
import discord.ext
import processDB
import requests
import time
from discord.ext import commands
import discord
import os
import json

from bs4 import BeautifulSoup

url = 'https://schedule.hololive.tv/lives'
assets_path = os.path.dirname(os.path.abspath(__file__))
json_path = "jsons/holomem.json"

class Hololive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        f = open(os.path.join(assets_path, json_path),)
        self.holo_dict = json.load(f)
        f.close()

    def _check_dict(self, live_soup):
        live_dict = {}
        for t in live_soup:
            chan = str(t.text.replace(" ", "").replace("\n", "").replace("\r", "")).replace(":", "")
            chan = ''.join([i for i in chan if not i.isdigit()])
            if chan in self.holo_dict:
                live_dict[chan] = "<" + t['href'] + ">"
        return live_dict

    @commands.group(pass_context=True)
    async def holo(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommand passed.")

    @holo.command(pass_context=True)
    async def live(self, ctx):
        page = requests.get(url).content
        soup = BeautifulSoup(page, 'html.parser')
        all_live = soup.find_all('a', style=re.compile("border: 3px red"))
        live_chan = self._check_dict(all_live)

        if all_live is not None and len(live_chan) > 0:
            await ctx.send("Streaming now:")
            for channel, stream_url in live_chan.items():
                if channel == "Gura":
                    emoji = discord.utils.get(self.bot.emojis, name='a_')
                    await ctx.send(str(emoji) + " " + stream_url)
                elif channel == "Amelia":
                    emoji = discord.utils.get(self.bot.emojis, name='amewat')
                    await ctx.send(str(emoji) + " " + stream_url)
                else:
                    await ctx.send(self.holo_dict[channel] + " " + stream_url)
            return

        else:
            await ctx.send("Nobody is live, peko.")
            return

def setup(bot):
    bot.add_cog(Hololive(bot))

