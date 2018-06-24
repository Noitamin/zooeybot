import asyncio
import sys
import re
import discord.ext
from discord.ext import commands

'''
Help menu class for Zooey bot
Displays either a default help menu or more detailed menus for specific commands
'''

class HelpMenu():
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

        embed.add_field(name="big",
                        value="`\nHugifies a custom emoji.`",
                        inline=False)

        embed.add_field(name="intense",
                        value="`\nIntensifies a custom emoji or avatar of mentioned user.`",
                        inline=False)

        embed.add_field(name="jail",
                        value="`\nSends the mentioned user to jail!.`",
                        inline=False)

        embed.add_field(name="jail_stats",
                        value="`\nLearn what a deviant mentioned user is.`",
                        inline=False)

        await self.bot.send_message(channel, embed=embed)
        await self.bot.delete_message(ctx.message)

def setup(bot):
    bot.add_cog(HelpMenu(bot))
