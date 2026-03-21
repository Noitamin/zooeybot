import discord.ext
from discord.ext import commands
import re
from config import TOKEN
from PIL import Image
from PIL import ImageSequence
import requests
from io import BytesIO
import imageio
import os
import numpy
import helpers
import sqlite3
import processDB
from datetime import datetime
import random
import string
import zipfile
import inspect
import asyncio

print(discord.__version__)

def lineno():
    return inspect.currentframe().f_back.f_lineno

assets_path = os.path.dirname(os.path.abspath(__file__))
print(assets_path)

startup_extensions = ["helpmenu", "line", "connect_four", "voice_player", "chatbot"]
message_id_cache = {}

description = '''Zooey bot for discord shenanigans'''
intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix='&', description=description, intents=intents)
bot.remove_command('help')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    print('------')
    print('Performing database checks...')
    for guild in bot.guilds:
        db_obj = processDB.db('{}.db'.format(guild.id))
        db_obj.update_users(guild)

    game = discord.Game("with your gacha")
    await bot.change_presence(status=None, activity=game)

@bot.event
async def on_command_error(ctx, error):
    print(f"Command fucked up: {error}")
    await ctx.send(f"shit broke: {error}")

@bot.event
async def on_message(message):
    print("Message got")

    if message.author.id == bot.user.id:
        if message.channel not in message_id_cache:
            message_id_cache[message.channel] = []
        message_id_cache[message.channel].insert(0, message.id)
        if len(message_id_cache[message.channel]) > 10:
            message_id_cache[message.channel].pop()

    if message.author.bot:
        await bot.process_commands(message)
        return

    print("going down the list...")

    scream_pattern = re.compile(r"^[aA]{4,}$")
    waaai_pattern = re.compile(r'(\\o\\)|(/o/)')
    rand_chance = random.choices(['no', 'birb', 'scream', ''], weights=[0.10, 0.15, 0.35, 0.40], k=1)[0]

    print("processing triggers")

    if waaai_pattern.search(message.content):
        if r'\o\\' in message.content:
            await message.channel.send(file=discord.File(os.path.join(assets_path, "assets/waaai_left.jpg")))
        else:
            await message.channel.send(file=discord.File(os.path.join(assets_path, "assets/waaai.jpg")))

    elif scream_pattern.match(message.content) and rand_chance != '':
        if rand_chance == 'no':
            await message.channel.send("no.")
        elif rand_chance == 'birb':
            await message.channel.send(file=discord.File(os.path.join(assets_path, "assets/birb_scream.jpg")))
        elif rand_chance == 'scream':
            scream_msg = ''.join(random.choice("aA") for _ in range(random.randint(4, 25)))
            await message.channel.send(scream_msg)

    elif 'same' in message.content.lower():
        if random.randint(0, 3) == 2:
            await message.channel.send("same")

    elif message.content.lower() == "wow":
        if random.randint(0, 4) == 1:
            await message.channel.send("wowie zowie!")

    print("about to process commands")
    await bot.process_commands(message)
    print("commands processed")


# --- Commands ---
# pass_context=True is removed everywhere; ctx is automatically injected in 2.x.
# ctx.message.server  →  ctx.guild
# ctx.message.author  →  ctx.author
# ctx.message.channel →  ctx.channel

@bot.command()
async def bonk(ctx):
    this_channel = ctx.channel
    if (this_channel not in message_id_cache) or (len(message_id_cache[this_channel]) < 1):
        await ctx.send("Nothing to bonk in this channel.")
        return
    message_id = message_id_cache[this_channel].pop(0)
    message_to_delete = await this_channel.fetch_message(message_id)
    await message_to_delete.delete()

@bot.command()
async def rave(ctx):
    await ctx.send(file=discord.File(os.path.join(assets_path, "assets/sirin_smaller.gif")))

@bot.command()
async def big(ctx, message):
    """Hugify a given emoji"""
    img_pattern = re.compile(r"\<\:.+\:\d+\>")
    gif_pattern = re.compile(r"\<a\:.+\:\d+\>")

    mention_msg = "<@!{}>".format(ctx.author.id)   # ctx.message.author → ctx.author
    author_id = ctx.author.id

    if img_pattern.match(message):
        emoji_id = re.sub(r'\<\:\D+|\>', '', message)
        emoji_url = "https://cdn.discordapp.com/emojis/" + emoji_id + ".png"

        response = requests.get(emoji_url)
        img = Image.open(BytesIO(response.content)).convert("RGBA")
        img_name = str(author_id) + "_temp.png"
        img.save(img_name)

        await ctx.send(mention_msg)
        await ctx.send(file=discord.File(img_name))
        os.remove(img_name)

    elif gif_pattern.match(message):
        emoji_id = re.sub(r'\<a\:\D+|\>', '', message)
        emoji_url = "https://cdn.discordapp.com/emojis/" + emoji_id + ".gif"
        gif_name = str(author_id) + "_temp.gif"

        response = requests.get(emoji_url)
        frames = []
        img = Image.open(BytesIO(response.content))
        bg = []
        pal = img.getpalette()
        dur = img.info['duration']
        disposal = []
        if not img.getpalette():
            img.putpalette(pal)

        transparent_color = 0
        if 'transparency' in img.info:
            transparent_color = img.info['transparency']

        for frame in ImageSequence.Iterator(img):
            bg.append(frame.info['background'])
            disposal.append(frame.disposal_method)
            frame_pal = frame.getpalette()
            shiftme = len(frame_pal) // 3 - frame.info['transparency']
            frame = (numpy.array(frame) + shiftme) % (len(frame_pal) // 3)
            frame = Image.fromarray(frame).convert('P')
            frame.putpalette(pal[-3 * shiftme:] + pal[:-3 * shiftme])
            b = BytesIO()
            frame.save(b, format='GIF')
            frame = Image.open(b)
            frames.append(frame)

        frames[0].save(fp=gif_name, format='gif', save_all=True,
                       append_images=frames[1:], duration=dur, loop=0,
                       background=transparent_color,
                       transparency=0,
                       optimize=False, disposal=disposal)

        await ctx.send(mention_msg)
        await ctx.send(file=discord.File(gif_name))
        os.remove(gif_name)

    else:
        await ctx.send("That's not a custom emoji. Try again")

@bot.command()
async def intense(ctx, *args):
    """Intensify a given emoji"""
    parsed_args = helpers.parse_options(args)

    image_in = args[0]
    dur = 30
    speeds = [90, 80, 70, 60, 50, 40, 30, 20]
    intensity = 1
    flag_red = 0
    red_alpha = 123

    for item in parsed_args:
        if item.name == "--duration":
            try:
                dur = int(item.values[0])
            except:
                dur = 30
        elif item.name == "--speed":
            try:
                speed_in = min(max(int(item.values[0]), 0), len(speeds) - 1)
                dur = speeds[speed_in]
            except:
                dur = 30
        elif item.name == "--power":
            try:
                intensity = int(item.values[0]) / 100
            except:
                intensity = 1
        elif item.name == "--red":
            flag_red = 1
            try:
                red_alpha = min(max(int(item.values[0]), 0), 255)
            except:
                red_alpha = 123

    img_pattern = re.compile(r"\<\:.+\:\d+\>")

    mention_msg = "<@!{}>".format(ctx.author.id)    # ctx.message.author → ctx.author

    if img_pattern.match(image_in):
        emoji_id = re.sub(r'\<\:\D+|\>', '', image_in)
        image_url = "https://cdn.discordapp.com/emojis/" + emoji_id + ".png"
        image_present = True
    elif helpers.userInServer(ctx.guild, image_in, 'mention'):   # ctx.message.server → ctx.guild
        id_digits = re.search(r"^<@!{0,1}(\d+)>$", image_in)
        target_id = int(id_digits.group(1))                      # cast to int; get_member requires int in 2.x
        target_obj = ctx.guild.get_member(target_id)
        if target_obj.avatar is None:
            image_present = False
        else:
            image_url = "https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(target_obj)
            image_present = True
    else:
        image_present = False

    if image_present:
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        dims = img.size
        width = dims[1]
        height = dims[0]

        w_bound = round(width / 10)
        h_bound = round(height / 10)

        crop_box = (w_bound, h_bound, width - w_bound, width - h_bound)

        coords_w = [0, -0.7, 0.3, 0.8, 0.4, -0.9]
        coords_h = [0, 0.1, -0.5, 0.7, -0.2, 0.2]

        num_frames = 6
        images = []

        alpha = img.split()[3]

        if flag_red == 1:
            red_overlay = Image.new('RGB', img.size, (255, 0, 0))
            overlay_mask = Image.new('RGBA', img.size, (0, 0, 0, red_alpha))
            img = Image.composite(img, red_overlay, overlay_mask)

        img = img.convert('P', palette=Image.ADAPTIVE, colors=255)

        a_cutoff = 128
        transparent_color = 255
        mask = Image.eval(alpha, lambda a: 255 if a <= a_cutoff else 0)
        img.paste(transparent_color, mask)

        for i in range(num_frames):
            coords = (round(w_bound * coords_w[i]), round(h_bound * coords_h[i]))
            box = (crop_box[0] + coords[0] * intensity, crop_box[1] + coords[1] * intensity,
                   crop_box[2] + coords[0] * intensity, crop_box[3] + coords[1] * intensity)
            images.append(img.crop(box))

        images[0].save(fp='temp.gif', format='gif', save_all=True,
                       append_images=images[1:], duration=dur, loop=0,
                       background=transparent_color,
                       transparency=transparent_color,
                       optimize=False, disposal=2)

        await ctx.send(mention_msg)
        await ctx.send(file=discord.File('temp.gif'))
        os.remove('temp.gif')

    else:
        await ctx.send("That's not a custom emoji or user with an avatar. Try again")

@bot.command()
async def jail_stats(ctx, message):
    """View mentioned user's jail history"""
    db_obj = processDB.db('{}.db'.format(ctx.guild.id))    # ctx.message.server → ctx.guild

    if helpers.userInServer(ctx.guild, message, 'mention'):
        id_digits = re.search(r"^<@!{0,1}(\d+)>$", message)
        userid = int(id_digits.group(1))
        mention_msg = "<@!{}>".format(userid)

        if userid == int(bot.user.id):
            await ctx.send("Why would anyone want to put {} in jail?".format(mention_msg))
        else:
            jail_count = db_obj.get(userid, 'jail_count')
            if jail_count is None:
                db_obj.set(userid, 'jail_count', 0)
                jail_count = 0
            out = "{} has been sent to jail {} times.".format(mention_msg, jail_count)
            jail_last = db_obj.get(userid, 'jail_last')
            if jail_last is not None:
                out += " {} was last sent to jail on {} UTC".format(
                    mention_msg, datetime.utcfromtimestamp(jail_last))
            await ctx.send(out)

@bot.command()
async def jail(ctx, message):
    """Send mentioned user to jail"""
    author_mention_msg = "<@!{}>".format(ctx.author.id)    # ctx.message.author → ctx.author
    db_obj = processDB.db('{}.db'.format(ctx.guild.id))    # ctx.message.server → ctx.guild

    print("This is message:", message)
    if helpers.userInServer(ctx.guild, message, 'mention'):
        id_digits = re.search(r"^<@!{0,1}(\d+)>$", message)
        userid = int(id_digits.group(1))
        mention_msg = "<@!{}>".format(userid)

        if userid == int(bot.user.id):
            await ctx.send("{} Nice try.".format(author_mention_msg))
        else:
            jail_last = db_obj.get(userid, 'jail_last')

            if jail_last is not None:
                rand_chance = random.choices(['shotty', ''], weights=[0.8, 0.2], k=1)[0]
                elapsed = datetime.utcnow().timestamp() - jail_last

                if elapsed > 300:
                    db_obj.increment(userid, 'jail_count')
                    db_obj.set(userid, 'jail_last', datetime.utcnow().timestamp())
                    await ctx.send("{} sent {} to jail!".format(author_mention_msg, mention_msg))

                    if rand_chance == 'shotty':
                        await ctx.send(file=discord.File(os.path.join(assets_path, 'assets/jail_shotty.jpg')))
                        await ctx.send("Moshi moshi, lolice desu.")
                else:
                    await ctx.send("{} That user is already in jail.".format(author_mention_msg))
            else:
                db_obj.set(userid, 'jail_count', 1)
                db_obj.set(userid, 'jail_last', datetime.utcnow().timestamp())
                await ctx.send("{} sent {} to jail!".format(author_mention_msg, mention_msg))
    else:
        await ctx.send("{} User not found.".format(author_mention_msg))

@bot.command()
async def reload_cogs(ctx):
    for extension in startup_extensions:
        await bot.reload_extension(extension)
    await ctx.send("Cogs reloaded.")


async def main():
    for extension in startup_extensions:
        print(f'Loading {extension}')
        try:
            await bot.load_extension(extension)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
