import discord.ext
from discord.ext import commands
import re
from secrets import TOKEN
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

def lineno():
    return inspect.currentframe().f_back.f_lineno

assets_path = os.path.dirname(os.path.abspath(__file__))
print(assets_path)

#startup_extensions = ["helpmenu"]
startup_extensions = ["helpmenu", "sparkcalc", "hololive", "line", "reddit_stuff", "connect_four", "voice_player"]

description = '''Zooey bot for discord shenanigans'''
bot = commands.Bot(command_prefix='&', description=description)
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
async def on_message(message):
    scream_pattern = re.compile("^[aA]{4,}$")
    waaai_pattern = re.compile('(\\\o\\\)|(/o/)')
    rand_chance = numpy.random.choice(['no', 'birb', 'scream', ''], 1, p=[0.10, 0.15, 0.35, 0.40])

    if (waaai_pattern.match(message.content)):
        if re.match('(\\\o\\\)', message.content):
            await message.channel.send(file=discord.File(os.path.join(assets_path, "assets/waaai_left.jpg")))
        else:
            await message.channel.send(file=discord.File(os.path.join(assets_path, "assets/waaai.jpg")))
        await bot.process_commands(message)

    elif (scream_pattern.match(message.content)) and rand_chance != '':
        if rand_chance == 'no':
            if message.author.id != bot.user.id: 
                await message.channel.send("no.")
                await bot.process_commands(message)

        elif rand_chance == 'birb':
            await message.channel.send(file=discord.File(os.path.join(assets_path, "assets/birb_scream.jpg")))
            await bot.process_commands(message)

        elif rand_chance == 'scream':
            scream_msg = ''.join(random.choice("aA") for __ in range(1, random.randint(4, 25)))
            await message.channel.send(scream_msg) 
            await bot.process_commands(message)

    else:
        await bot.process_commands(message)
        return

@bot.command(pass_context=True)
async def rave(ctx):
    await ctx.send(file=discord.File(os.path.join(assets_path, "assets/sirin_smaller.gif")))

@bot.command(pass_context=True)
async def big(ctx, message):
    """Hugify a given emoji"""
    img_pattern = re.compile("\<\:.+\:\d+\>")
    gif_pattern = re.compile("\<a\:.+\:\d+\>")

    mention_msg = "<@!{}>".format(ctx.message.author.id)
    author_id = ctx.message.author.id
    channel = ctx.message.channel

    if (img_pattern.match(message)):
        emoji_id = re.sub(r'\<\:\D+|\>', '', message)
        emoji_url = "https://cdn.discordapp.com/emojis/" + emoji_id + ".png" 

        response = requests.get(emoji_url)
        img = Image.open(BytesIO(response.content)).convert("RGBA")
        img_name = str(author_id)+ "_temp.png"
        img.save(img_name) 

        await channel.send(mention_msg)
        await channel.send(file=discord.File(img_name))
        os.remove(img_name)
        await ctx.message.delete()

    elif (gif_pattern.match(message)):
        emoji_id = re.sub(r'\<a\:\D+|\>', '', message)
        emoji_url = "https://cdn.discordapp.com/emojis/" + emoji_id + ".gif" 
        gif_name = str(author_id) + "_temp.gif"

        #save each frame of the gif then reconstruct it in a list
        response = requests.get(emoji_url)
        frames = []
        nframes = 0 
        img = Image.open(BytesIO(response.content))
        bg = []
        transparent_color = 0
        pal = img.getpalette()
        dur = img.info['duration']
        disposal = []
        if not img.getpalette():
            img.putpalette(pal)

        #resize each frame and apply original palatte and save to frame list
        if 'transparency' in img.info:
            transparent_color = img.info['transparency']

        for frame in ImageSequence.Iterator(img):
            bg.append(frame.info['background'])
            disposal.append(frame.disposal_method)
            frame_pal = frame.getpalette()
            shiftme = len(frame_pal)//3 - frame.info['transparency']       
            frame = (numpy.array(frame) + shiftme) % (len(frame_pal)//3)  # shift data pointing into palette
            frame = Image.fromarray(frame).convert('P')
            frame.putpalette(pal[-3*shiftme:] + pal[:-3*shiftme])  # shift palette
            b = BytesIO()
            frame.save(b, format='GIF')
            frame = Image.open(b)
            frames.append(frame)

        #basically stolen from 'intense' command's method to save frames into gif   
        frames[0].save(fp=gif_name, format='gif', save_all=True,
                       append_images=frames[1:], duration=dur, loop=0,
                       background=bg,
                       transparency=0,
                       optimize=False, disposal=disposal)

        await channel.send(mention_msg)
        await channel.send(file=discord.File(gif_name))
        os.remove(gif_name)
        await ctx.message.delete()

    else:
        await channel.send("That's not a custom emoji. Try again")

@bot.command(pass_context=True)
async def intense(ctx, *args):
    """Intensify a given emoji"""
    # options:
    # -speed [val] -> sets duration according to speed array.
    #   note that 20 is the fastest possible duration
    # -duration [val] -> sets duration explicitly. not user-friendly.
    # -power [val] -> sets amplitude of displacement as a percentage of the default.
    # -red [val] -> tints red with alpha = val. default 123.
    #   note: alpha 0 is fully red and 255 is transparent, so not user-friendly; would expect
    #   higher val = more red. add array version like speeds array

    parsed_args = helpers.parse_options(args)

    image_in = args[0] # hardcoded; can add to pattern with if item.name == "input"
    # Default values
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

    img_pattern = re.compile("\<\:.+\:\d+\>")

    mention_msg = "<@!{}>".format(ctx.message.author.id)
    channel = ctx.message.channel

    if (img_pattern.match(image_in)):
        # print('matched img_pattern')
        emoji_id = re.sub(r'\<\:\D+|\>', '', image_in)
        image_url = "https://cdn.discordapp.com/emojis/" + emoji_id + ".png"
        image_present = True
    elif helpers.userInServer(ctx.message.server, image_in, 'mention'):
        # Get user id and grab avatar from corresponding object if mentioned user in server
        # Turn this into a helper later
        id_digits = re.search("^<@!{0,1}(\d+)>$", image_in)
        target_id = id_digits.group(1)
        target_obj = ctx.message.server.get_member(target_id)
        # Can't use target_obj.avatar_url since that's webp; instead, access the png version
        # Check if user has an avatar
        if target_obj.avatar == None:
            image_present = False
        else:
            image_url = "https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=1024".format(target_obj)
            image_present = True
    else:
        image_present = False

    if image_present == True:
        # fetch image from url without having to save it somewhere
        # print('waiting for response')
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        # Check for palette-based image
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # print('got response')

        # image dimensions
        dims = img.size
        width = dims[1]
        height = dims[0]

        # allow shifting up to 10% of the image dimensions
        w_bound = round(width/10)
        h_bound = round(height/10)

        crop_box = (w_bound, h_bound, width - w_bound, width - h_bound)

        # hardcoded shift amounts per frame; find a good way to randomize?
        coords_w = [0, -0.7, 0.3, 0.8, 0.4, -0.9]
        coords_h = [0, 0.1, -0.5, 0.7, -0.2, 0.2]

        num_frames = 6
        images = []

        # We have RGBA data but .gifs are a palette-based format
        # Extract alpha channel to use as a mask
        alpha = img.split()[3]

        # Apply red tint if flag provided
        if flag_red == 1:
            red_overlay = Image.new('RGB',img.size,(255,0,0))
            overlay_mask = Image.new('RGBA',img.size,(0,0,0,red_alpha))
            img = Image.composite(img,red_overlay,overlay_mask)

        # Convert base emoji to palette-based with 255 colors
        img = img.convert('P', palette=Image.ADAPTIVE, colors=255)

        # Paste color 256 (index 255) over all pixels with alpha < 128
        # Guaranteed not to be used because we only used 255 colors
        a_cutoff = 128
        transparent_color = 255
        mask = Image.eval(alpha, lambda a: 255 if a <= a_cutoff else 0)
        img.paste(transparent_color, mask)

        # generate frames
        for i in range(0, num_frames):
            coords = (round(w_bound*coords_w[i]), round(h_bound*coords_h[i]))
            box = (crop_box[0]+coords[0]*intensity, crop_box[1]+coords[1]*intensity,
                   crop_box[2]+coords[0]*intensity, crop_box[3]+coords[1]*intensity)
            images.append(img.crop(box))

        # save_all=True required for animation
        # loop=0 loops gif forever
        # set background color and transparency color to 255
        # Optimize=False prevents PIL from removing color 255
        # disposal=2 stops ghosting issue
        images[0].save(fp='temp.gif', format='gif', save_all=True,
                       append_images=images[1:], duration=dur, loop=0,
                       background=transparent_color,
                       transparency=transparent_color,
                       optimize=False, disposal=2)

        await ctx.send(mention_msg)
        await channel.send(file=discord.File('temp.gif'))
        os.remove('temp.gif')
        await ctx.message.delete()

    else:
        await ctx.send("That's not a custom emoji or user with an avatar. Try again")

@bot.command(pass_context=True)
async def jail_stats(ctx, message):
    """View mentioned user's jail history"""

    # Connect to db
    db_obj = processDB.db('{}.db'.format(ctx.message.server.id))

    # Check to make sure mentioned user even exists on this server
    if helpers.userInServer(ctx.message.server, message, 'mention'):

        # Get user id and generate mention for later
        id_digits = re.search("^<@!{0,1}(\d+)>$", message)
        userid = int(id_digits.group(1))
        mention_msg = "<@!{}>".format(userid)

        # Zooey is never in jail
        if userid == int(bot.user.id):
            await ctx.send("Why would anyone want to put {} in jail?".format(mention_msg))
            await ctx.message.delete()
        else:
            jail_count = db_obj.get(userid, 'jail_count')
            if jail_count == None:
                db_obj.set('jail_count', 0)
                jail_count = 0
            str = "{} has been sent to jail {} times.".format(mention_msg, jail_count)
            jail_last = db_obj.get(userid, 'jail_last')
            if jail_last is None:
                pass
            else:
                str += " {} was last sent to jail on {} UTC".format(
                    mention_msg, datetime.utcfromtimestamp(jail_last))
            await ctx.send(str)
            await ctx.message.delete()

@bot.command(pass_context=True)
async def jail(ctx, message):
    """Send mentioned user to jail"""

    author_mention_msg = "<@!{}>".format(ctx.message.author.id)

    # Connect to db
    db_obj = processDB.db('{}.db'.format(ctx.message.server.id))

    print("This is message:", message)
    # Check to make sure mentioned user even exists on this server
    if helpers.userInServer(ctx.message.server, message, 'mention'):

        # Get user id and generate mention for later
        id_digits = re.search("^<@!{0,1}(\d+)>$", message)
        userid = int(id_digits.group(1))
        mention_msg = "<@!{}>".format(userid)

        # Can't put Zooey in jail
        if userid == int(bot.user.id):
            await ctx.send("{} Nice try.".format(author_mention_msg))
            await ctx.message.delete()

        else:

            # Check last time user was in jail
            jail_last = db_obj.get(userid, 'jail_last')

            if jail_last is not None:
                rand_chance = numpy.random.choice(['shotty', ''], 1, p=[0.8, 0.2])
                elapsed = datetime.utcnow().timestamp() - jail_last

                if elapsed > 300:  # 5 minute timeout
                    db_obj.increment(userid, 'jail_count')
                    db_obj.set(userid, 'jail_last', datetime.utcnow().timestamp())
                    await ctx.send("{} sent {} to jail!".format(author_mention_msg, mention_msg))

                    if rand_chance == 'shotty':
                        print("im super shotty")
                        await channel.send(file=discord.File(os.path.join(assets_path, 'assets/jail_shotty.jpg')))
                        #await bot.process_commands(ctx.message)
                        await ctx.send("Moshi moshi, lolice desu.")
                    await ctx.message.delete()

                else:
                    await ctx.send("{} That user is already in jail.".format(author_mention_msg))
                    await ctx.message.delete()

            else:
                db_obj.set(userid, 'jail_count', 1)
                db_obj.set(userid, 'jail_last', datetime.utcnow().timestamp())
                await ctx.send("{} sent {} to jail!".format(author_mention_msg, mention_msg))
                await ctx.message.delete()

    else:
        await ctx.send("{} User not found.".format(author_mention_msg))
        await ctx.message.delete()

if __name__ == "__main__":
    for extension in startup_extensions:
        print('Loading cogs')
        try:
            bot.load_extension(extension)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))

    bot.run(TOKEN)
