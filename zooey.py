import discord
from discord.ext import commands
import re
from secrets import TOKEN
from PIL import Image
import requests
from io import BytesIO
import imageio
import os
import numpy
import helpers

description = '''Zooey bot for discord shenanigans'''
bot = commands.Bot(command_prefix='&', description=description)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command()
async def hello():
    """Says world"""
    await bot.say("world")


async def conjunction():
    """Secret to winning MVP races"""
    await bot.say("Enjoy your mvp!")

@bot.command()
async def add(left : int, right : int):
    """Adds two numbers together."""
    await bot.say(left + right)

@bot.command()
async def saber():
    """rekt."""
    await bot.say("git rekt")

@bot.command(pass_context=True)
async def big(ctx, message):
    """Hugify a given emoji"""
    img_pattern = re.compile("\<\:.+\:\d+\>")
    gif_pattern = re.compile("\<a\:.+\:\d+\>")

    mention_msg = "<@!{}>".format(ctx.message.author.id)
    channel = ctx.message.channel

    if (img_pattern.match(message)):
        emoji_id = re.sub(r'\<\:\D+|\>', '', message)
        emoji_url = "https://cdn.discordapp.com/emojis/" + emoji_id + ".png" 

        response = requests.get(emoji_url)
        img = Image.open(BytesIO(response.content)).convert("RGBA")
        img.save('temp.png') 

        await bot.say(mention_msg)
        await bot.send_file(channel, 'temp.png')
        os.remove('temp.png')
        await bot.delete_message(ctx.message)

    elif (gif_pattern.match(message)):
        emoji_id = re.sub(r'\<a\:\D+|\>', '', message)
        emoji_url = "https://cdn.discordapp.com/emojis/" + emoji_id + ".gif?v=1" 

        response = requests.get(emoji_url)
        img = imageio.mimread(BytesIO(response.content))
        reader = imageio.get_reader(BytesIO(response.content))
        fps = reader.get_meta_data()['duration']
        imageio.mimwrite('temp.gif', img, 'GIF', fps=fps)

        await bot.say(mention_msg)
        await bot.send_file(channel, 'temp.gif')
        os.remove('temp.gif')
        await bot.delete_message(ctx.message)

    else:
        await bot.say("That's not a custom emoji. Try again")

@bot.command()
async def goat():
    await bot.say("https://cdn.modernfarmer.com/wp-content/uploads/2013/09/saanen.jpg")

@bot.command(pass_context=True)
async def intense(ctx, message):
    """Intensify a given emoji"""
    #print('ok')
    img_pattern = re.compile("\<\:.+\:\d+\>")

    mention_msg = "<@!{}>".format(ctx.message.author.id)
    channel = ctx.message.channel

    if (img_pattern.match(message)):
        # print('matched img_pattern')
        emoji_id = re.sub(r'\<\:\D+|\>', '', message)
        emoji_url = "https://cdn.discordapp.com/emojis/" + emoji_id + ".png"

        # fetch image from url without having to save it somewhere
        # print('waiting for response')
        response = requests.get(emoji_url)
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
            box = (crop_box[0]+coords[0], crop_box[1]+coords[1],
                   crop_box[2]+coords[0], crop_box[3]+coords[1])
            images.append(img.crop(box))

        # save_all=True required for animation
        # loop=0 loops gif forever
        # set background color and transparency color to 255
        # optimize=False prevents PIL from removing color 255
        # disposal=2 stops ghosting issue
        images[0].save(fp='temp.gif', format='gif', save_all=True,
                       append_images=images[1:], duration=30, loop=0,
                       background=transparent_color,
                       transparency=transparent_color,
                       optimize=False, disposal=2)

        await bot.say(mention_msg)
        await bot.send_file(channel, 'temp.gif')
        os.remove('temp.gif')
        await bot.delete_message(ctx.message)

    else:
        await bot.say("That's not a custom emoji. Try again")


bot.run(TOKEN)
