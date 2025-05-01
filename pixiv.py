import asyncio
import sys
import re
import discord.ext
import requests
import time
from discord.ext import commands
import discord
import helpers
import random
from random import choice
import os
import uuid
import copy

from pixivpy3 import *

from secrets import PIXIV_REFRESH_TOKEN

assets_path = os.path.dirname(os.path.abspath(__file__))

class PixivCache():
    def __init__(self):
        self.cache = {}

    def new_cache(self, tag, illusts):
        print("adding new cache item")
        self.cache[tag] = {
            "illusts": illusts,
            "last_accessed": 0
        }

        #print(self.cache[tag])


    def _update_access(self):
        for item in self.cache:
            print(item)
            self.cache[item]['last_accessed'] += 1

    def get_cache(self, tag):
        self._update_access()

        print("updated access")

        if tag in self.cache:
            if self.cache[tag]['last_accessed'] > 0:
                self.cache[tag]['last_accessed'] = 0
            return self.cache[tag]['illusts']

        return None

    def clear_stale_cache(self):
        tags_to_remove = [
            tag for tag, entry in self.cache.items()
            if entry['last_acccessed'] > 3
        ]

        for tag in tags_to_remove:
            del self.cache[tag]

    def clear_cache(self):
        self.cache.clear()


class Pixiv(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = AppPixivAPI()
        self.start_time = time.time()
        #self.cache = PixivCache()

    def update_cache(self, tag):
        pass

    
    def get_pixiv(self, tag):
        self.api.auth(refresh_token=PIXIV_REFRESH_TOKEN)
        # search cache first to see if we already have an entry
        #print("checking cache")
        #cache_check = self.cache.get_cache(tag)

        #if cache_check is not None:
        #    print("cache found!")
        #    illusts = cache_check
        #else:
        #    print("no cache found")
        json_result = self.api.search_illust(tag, search_target="partial_match_for_tags", search_ai_type=0)
        illusts = json_result.illusts

        #self.cache.new_cache(tag, illusts)

        #if time.time() - self.start_time > 3600:
        #    self.cache.clear_cache()
        #    self.start_time = time.time()

        #print("cache done")

        rand_index = random.randint(0, len(illusts) - 1)

        url = illusts[rand_index]['image_urls']['large']

        file_id = str(uuid.uuid4()) + '.jpg'

        if self.api.download(url=url, name=file_id, path=os.path.join(assets_path, 'assets/pixiv/')):
            print("successful download")
            return file_id
        else:
            print("unsuccessful download")
            return None


    @commands.group(pass_context=True)
    async def pix(self, ctx, *args): 
        parsed_args = helpers.parse_options(args)
        override = None

        if len(parsed_args) < 1:
            await ctx.send("Please provide a tag to search")
            return
        
        for item in parsed_args: 
            if item.name == "input":
                tag = item.values[0]
            #elif item.name == "--hot":
            #    override = "hot"
            #elif item.name == "--new":
            #    override = "new"
            #elif item.name == "--top":
            #    override = "top"

        print("Tag is " + tag)

        file_id = self.get_pixiv(tag)
        mention_msg = "<@!{}>".format(ctx.message.author.id)

        if file_id is not None:
            file_path = os.path.join(assets_path, "assets/pixiv/" + file_id)

            await ctx.send(mention_msg)
            await ctx.send(file=discord.File(file_path))
            os.remove(file_path)

        else:
            await ctx.send(mention_msg)
            await ctx.send("woops something broke")


async def setup(bot):
    await bot.add_cog(Pixiv(bot))

