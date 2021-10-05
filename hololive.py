import asyncio
import sys
import re
import discord.ext
import processDB
import requests
import time
from discord.ext import commands
import discord

from bs4 import BeautifulSoup

holo_dict = {
    "アキロゼ": "Aki",
    "湊あくあ": "Aqua",
    "癒月ちょこ": "Choco",
    "桐生ココ": "Coco",
    "不知火フレア": "Flare",
    "白上フブキ": "Fubuki",
    "赤井はあと": "Haato",
    "天音かなた": "Kanata",
    "戌神ころね": "Korone",
    "姫森ルーナ": "Luna",
    "宝鐘マリン": "Marine",
    "夏色まつり": "Matsuri",
    "夜空メル": "Mel",
    "さくらみこ": "Miko",
    "大神ミオ": "Mio",
    "白銀ノエル": "Noel",
    "猫又おかゆ": "Okayu",
    "兎田ぺこら": "Pekora",
    "ロボ子さん": "Roboco",
    "潤羽るしあ": "Rushia",
    "大空スバル": "Subaru",
    "常闇トワ": "Towa",
    "角巻わため": "Watame",
    "雪花ラミィ": "Lamy",
    "桃鈴ねね": "Nene",
    "獅白ぼたん": "Botan",
    "魔乃アロエ": "Aloe",
    "尾丸ポルカ": "Clownpiece",
    "Amelia": "Amelia",
    "Calli": "Calli",
    "Ina": "Ina",
    "Gura": "Gura",
    "Kiara": "Kiara",
    "Irys": "Irys",
    "Ollie": "Ollie",
    "Anya": "Anya",
    "Reine": "Reine",
    "Risu": "Risu",
    "Iofi": "Iofi",
    "Moona": "Moona",
    "Mumei": "Mumei",
    "Kronii": "Kronii",
    "Sana": "Sana",
    "Fauna": "Fauna",
    "Baelz": "Baelz",
}

url = 'https://schedule.hololive.tv/lives'


class Hololive(commands.Cog):
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
                    await ctx.send(holo_dict[channel] + " " + stream_url)
            return

        else:
            await ctx.send("Nobody is live, peko.")
            return

def setup(bot):
    bot.add_cog(Hololive(bot))

