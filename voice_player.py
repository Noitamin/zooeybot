import asyncio
import sys
import discord.ext
from discord.ext import commands
import discord
import helpers

clips = {
    "pekoshit": "assets/pekora-horee-shiit.mp3",
    "pardun": "assets/usada-pekora-pardun.mp3",
    "yabe": "assets/shirakami-fubuki-yabe.mp3",
    "idc": "assets/i-don-t-care-i-m-pomu.mp3",
    "ray": "assets/gamma-ray.mp3",
    "ree": "assets/REEEEEE_Nijisanji_EN.mp3",
    "reee": "assets/watson_reeeeeee.mp3",
}

class voice_player(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

    async def join_play_leave(self, ctx, sourcefile):
        # Join the vc of the user, if any
        vc = await self.join_ctx(ctx)

        if vc is not None:
            # Initiate player and play clip
            player = discord.FFmpegPCMAudio(source=sourcefile)
            vc.play(player)
            # Wait until clip is done playing, then leave vc
            while vc.is_playing():
                await asyncio.sleep(0.5)
            await vc.disconnect(force=True)

    @commands.group(pass_context=True)
    async def vo(self, ctx, *args):
        parsed_args = helpers.parse_options(args)
        clip = None
        for item in parsed_args:
            if item.name == "input":
                try:
                    clip = clips[item.values[0]]
                except:
                    print("Invalid clip name")
                    return
        if clip is not None:
            await self.join_play_leave(ctx, clip)

def setup(bot):
    bot.add_cog(voice_player(bot))

