import asyncio
import sys
import re
import discord.ext
import processDB
import requests
import time
from discord.ext import commands
import discord
import zipfile
import helpers
import os
import json
from shutil import rmtree
from io import BytesIO
from random import randrange

api_url_start = "https://store.line.me/api/search/sticker?query="
api_url_end = "&offset=0&limit=36&type=ALL&includeFacets=true"
max_sticker_set = 5

class Line(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True)
    async def line(self, ctx, *args):
        """Post a given LINE sticker"""
        mention_msg = "<@!{}>".format(ctx.message.author.id)
        channel = ctx.message.channel
        parsed_args = helpers.parse_options(args)

        for item in parsed_args:
            if item.name == "input":
                try:
                    line_page_code = item.values[0]
                    if item.values[1].isdecimal():
                        line_sticker_number = int(item.values[1])
                    else:
                        line_sticker_number = item.values[1]
                except:
                    line_page_code = -1
                    line_sticker_number = -1

        if line_page_code != -1:

            # If sticker ID is a string of letters, send API search request and
            # grab the first item from the JSON response for now
            if not line_page_code.isdecimal():
                line_page_code.replace(" ", "+")
                api_url = api_url_start + line_page_code + api_url_end
                r = requests.get(api_url)
                if r.status_code != 200:
                    await ctx.send("{} LINE API call failed.".format(mention_msg))
                else:
                    r_content = json.loads(r.text)
                    if r_content["totalCount"] == 0:
                        await ctx.send("{} No sticker package found.".format(mention_msg))
                        return
                    line_page_code = r_content["items"][0]["id"]

            # Check if folder exists
            if os.path.isdir("./assets") == False:
                os.mkdir("./assets")

            if os.path.isdir("./assets/line") == False:
                os.mkdir("./assets/line")

            line_asset_path = "./assets/line/" + line_page_code

            flag_ok = 1

            if os.path.isdir(line_asset_path) == False:
                file_list = [f for f in os.listdir("./assets/line")]
                if len(file_list) >= max_sticker_set:
                    print("deleting " + line_page_code)
                    rmtree("./assets/line/" + file_list[0])

                os.mkdir(line_asset_path)
                # Check if this is a real LINE sticker set
                # Try stickerpack first
                line_zip = "http://dl.stickershop.line.naver.jp/products/0/0/1/"+line_page_code+"/iphone/stickerpack@2x.zip"
                r = requests.get(line_zip, stream=True)

                if r.ok:
                    # Download and extract to asset folder
                    # Check for animated versions first
                    z = zipfile.ZipFile(BytesIO(r.content))
                    img_pattern = re.compile("animation@2x/\d+@2x.png")
                    flag_found = 0
                    for zip_info in z.infolist():
                        if img_pattern.match(zip_info.filename):
                            zip_info.filename = os.path.basename(zip_info.filename)
                            z.extract(zip_info, line_asset_path)
                            flag_found = 1
                    if flag_found == 1:
                        # now convert all of these to gifs
                        apng_list = os.listdir(line_asset_path+"")
                        for apng in apng_list:
                            apng_path = line_asset_path + "/" + apng
                            helpers.APNGtoGIF(apng_path)
                            os.remove(apng_path)
                    else:
                        # not animated; get regular images
                        img_pattern = re.compile("\d+@2x.png")
                        for infile in z.namelist():
                            if img_pattern.match(infile):
                                z.extract(infile, line_asset_path)

                else:
                    # try stickers
                    line_zip = "http://dl.stickershop.line.naver.jp/products/0/0/1/"+line_page_code+"/iphone/stickers@2x.zip"
                    r = requests.get(line_zip, stream=True)

                    if r.ok:
                        # Download and extract to asset folder
                        # Skip downloading thumbnails and metadata files
                        img_pattern = re.compile("\d+@2x.png")
                        z = zipfile.ZipFile(BytesIO(r.content))

                        for infile in z.namelist():
                            if img_pattern.match(infile):
                                z.extract(infile, line_asset_path)
                    else:
                        flag_ok = 0

            if flag_ok == 1:
                # Post requested sticker
                # done through image number
                # get list of filenames
                file_list = sorted(os.listdir(line_asset_path))
                try:
                    if line_sticker_number == 'r':
                        num = randrange(len(file_list))
                    else:
                        num = line_sticker_number
                    line_sticker_path = line_asset_path+"/"+file_list[num]
                    await ctx.send(mention_msg)
                    await channel.send(file=discord.File(line_sticker_path))
                except:
                    await ctx.send("{} LINE sticker number not found.".format(mention_msg))
                await ctx.message.delete()

            else:
                await ctx.send("{} LINE sticker page not found.".format(mention_msg))

        else:
            await ctx.send("{} LINE sticker page not found.".format(mention_msg))
        #if ctx.invoked_subcommand is None:
        #    await ctx.send("Invalid subcommand passed.")

"""
    @holo.command(pass_context=True)
    async def live(self, ctx):
        page = requests.get(url).content
        soup = BeautifulSoup(page, 'html.parser')
        all_live = soup.find_all('a', style=re.compile("border: 3px red solid"))
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
"""
async def setup(bot):
    await bot.add_cog(Line(bot))

