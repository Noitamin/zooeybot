import asyncio
import sys
import re
import discord.ext
from discord.ext import commands

'''
Help menu class for Zooey bot
Displays either a default help menu or more detailed menus for specific commands
'''

class HelpMenu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def help(self, ctx):
        """Prints the default help menu"""
        channel = ctx.message.channel

        embed = discord.Embed(
            title = "Zooey, at your service!",
            description = "These are the commands that I can execute for you.",
            color = discord.Color.blue()
        )

        embed.add_field(name="&big",
                        value="`Hugifies a custom emoji.`",
                        inline=False)

        embed.add_field(name="&intense",
                        value="`Intensifies a custom emoji or avatar of mentioned user.`",
                        inline=False)

        embed.add_field(name="&jail",
                        value="`Sends the mentioned user to jail!.`",
                        inline=False)

        embed.add_field(name="&jail_stats",
                        value="`Learn what a deviant mentioned user is.`",
                        inline=False)

        embed.add_field(name="&line PACK_NAME INDEX",
                        value="`Post a line sticker given a sticker pack name (e.g. hololive, honkai) or a raw ID string. Index is the sticker number from the pack. Can also use 'r' for a random sticker`",
                        inline=False)

        embed.add_field(name="&holo live",
                        value="`Show hololive members who are currently streaming. May not be accurate in timing as it relies on hololive's schedule website which has a delay.`",
                        inline=False)
        await ctx.send(embed=embed)
        await ctx.message.delete()

def setup(bot):
    bot.add_cog(HelpMenu(bot))
