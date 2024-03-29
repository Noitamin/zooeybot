import asyncio
import sys
import discord.ext
from discord.ext import commands
import discord
import helpers
import os
import json
import random

assets_path = os.path.dirname(os.path.abspath(__file__))
json_path = "jsons/clips.json"

class voice_player(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        f = open(os.path.join(assets_path, json_path),)
        self.clips = json.load(f)
        f.close()

    async def join_ctx(self, ctx):
        v = ctx.message.author.voice
        vc = None
        if v:
            await v.channel.connect()
            if ctx.voice_client:
                vc = ctx.guild.voice_client
        return vc

    async def leave_ctx(self, ctx):
        if ctx.voice_client:
            await ctx.guild.voice_client.disconnect()

    def play_n_times(self, vc, sourcepath, n):
        if n > 0:
            vc.play(discord.FFmpegPCMAudio(source=sourcepath), after=lambda e: self.play_n_times(vc, sourcepath, n-1))

    async def join_play_leave(self, ctx, sourcefile):
        # Join the vc of the user, if any
        vc = await self.join_ctx(ctx)

        if vc is not None:
            # Initiate player and play clip
            source_abs_path = os.path.join(assets_path, sourcefile)
            player = discord.FFmpegPCMAudio(source=source_abs_path)
            vc.play(player)
            # Wait until clip is done playing, then leave vc
            while vc.is_playing():
                await asyncio.sleep(0.5)
            await vc.disconnect(force=True)

    async def join_repeat_leave(self, ctx, sourcefile, n):
        # Join the vc of the user, if any
        vc = await self.join_ctx(ctx)

        if vc is not None:
            source_abs_path = os.path.join(assets_path, sourcefile)
            self.play_n_times(vc, source_abs_path, n)
            while vc.is_playing():
                await asyncio.sleep(0.5)
            # Leave vc when done repeating
            await vc.disconnect(force=True)

    @commands.group(pass_context=True)
    async def vo(self, ctx, *args):
        parsed_args = helpers.parse_options(args)
        clip = None
        is_nut = False
        for item in parsed_args:
            if item.name == "input":
                try:
                    clip = random.choice(self.clips[item.values[0]])
                    if item.values[0] == "nut":
                        is_nut = True
                except:
                    print("Invalid clip name")
                    return
        if clip is not None:
            if is_nut is True:
                n = random.randint(1, 5)
                print(n)
                await self.join_repeat_leave(ctx, clip, n)
            else:
                await self.join_play_leave(ctx, clip)

async def setup(bot):
    await bot.add_cog(voice_player(bot))

