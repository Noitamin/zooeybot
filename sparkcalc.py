import asyncio
import sys
import re
import discord.ext
import processDB
from discord.ext import commands

'''
Help menu class for Zooey bot
Displays either a default help menu or more detailed menus for specific commands
'''

resource_type = ["crystals", "singles", "tens"]

class SparkCalc():
    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True)
    async def spark(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.bot.say("Invalid subcommand passed.")

    @spark.command(pass_context=True)
    async def update(self, ctx, resource, amount):
        if resource not in resource_type:
            await self.bot.say("Resource type must be \"crystals\", \"singles\", or \"tens\".")
            return
        try:
            int(amount)
        except ValueError:
            await self.bot.say("Amount must be a positive integer.")
            return

        author_mention_msg = "<@!{}>".format(ctx.message.author.id)
        author_id = ctx.message.author.id

        # Connect to db
        db_obj = processDB.db('{}.db'.format(ctx.message.server.id))

        # Update respective resource with value
        db_obj.set(author_id, resource, int(amount))

        await self.bot.say("Updated, your {} are at {}.".format(resource, amount))

    @spark.command(pass_context=True)
    async def progress(self, ctx):

        author_mention_msg = "<@!{}>".format(ctx.message.author.id)
        author_id = ctx.message.author.id

        # Connect to db
        db_obj = processDB.db('{}.db'.format(ctx.message.server.id))

        # Get and show total progress of user
        crystals = db_obj.get(author_id, "crystals")
        singles = db_obj.get(author_id, "singles")
        tens = db_obj.get(author_id, "tens")

        total_spark = (crystals // 300) + singles + tens * 10
        spark_amount = total_spark // 300
        to_next_spark = 300 - (total_spark % 300)
        progress_msg = "\nCrystals: {}\nSingles: {}\nTens: {}\nCeruleans: {}\nSparks: {}\n".format(crystals, singles, tens, total_spark,  spark_amount)
        next_spark_msg = "Ceruleans to next spark: {}\n".format(to_next_spark)

        await self.bot.say("{}, Your spark progress:{}{}".format(author_mention_msg, progress_msg, next_spark_msg))


def setup(bot):
    bot.add_cog(SparkCalc(bot))

