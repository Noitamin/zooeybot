import asyncio
from discord.ext import commands
from utils.chatcompletion import completion, completion_ds, completion_xai
from utils import instruction as inst

MAX_HISTORY = 20
DISCORD_CHAR_LIMIT = 2000

class ChatBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.messages = []   

    @commands.command()
    async def chat(self, ctx, *, message):
        user_name = ctx.author.display_name
        async with ctx.channel.typing():
            try:
                if message == "CLEAR":
                    self.messages = []
                    await ctx.send("BEEP BOOP, RESETTING MEMORY...")
                    return

                if len(self.messages) == 0:
                    self.messages.append({"role": "system", "content": inst.sys_prompt})
                    self.messages.append({"role": "user", "content": f"{user_name}: {message}"})
                else:
                    self.messages.append({"role": "user", "content": f"{user_name}: {message}"})

                response = await asyncio.to_thread(completion_ds, self.messages)

                if len(response) > DISCORD_CHAR_LIMIT:
                    await ctx.send("wooops response was over 2000 characters limit tehe pero.")
                else:
                    self.messages.append({"role": "assistant", "content": response})
                    await ctx.send(response)
                    if len(self.messages) > MAX_HISTORY + 1:
                        self.messages = [self.messages[0]] + self.messages[-MAX_HISTORY:]

            except Exception as e:
                print(f"Exception: {e}")
                await ctx.send(f"Exception occurred: {e}")


async def setup(bot):
    await bot.add_cog(ChatBot(bot))
