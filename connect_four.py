import asyncio
import sys
import re
import discord.ext
import processDB
from discord.ext import commands
import discord
import numpy
import os
from PIL import Image, ImageDraw
from secrets import PRIVATECHANNEL

board_width = 342
board_height = 294
bgcolor = (40, 40, 215)
p1color = (255, 0, 0)
p2color = (200, 200, 0)
hole_spc = 6
hole_d = 42
# board width is 7 cols * hole diameter + 8 * hole spacing
# board width 342
# spacing 6 -> 48 px of spacing
# 294/7 = 42 px hole diameter
# board height is 6d + 7s = 294
reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "🏳"]
reactdict = {
    "1️⃣" : 0,
    "2️⃣" : 1,
    "3️⃣" : 2,
    "4️⃣" : 3,
    "5️⃣" : 4,
    "6️⃣" : 5,
    "7️⃣" : 6,
    "🏳" : 7
}


def find_first_nonzero_in_col(board, col):
    for r in range(6):
        if board[r][col] == 0:
            return r
    return None

def check_for_victory(board,rmove,cmove):
    # Check to see if the played move won the game
    # Get diagonal; offset by (col - row)... for example (0,1) would want an offset of +1,
    d1 = numpy.diagonal(board,cmove-rmove)
    d2 = numpy.diagonal(numpy.fliplr(board), (6-cmove)-rmove)
    col = board[:,cmove]
    row = board[rmove,:]

    if d1.size >= 4:
        for s in range(d1.size-3):
            if d1[s] == d1[s+1] and d1[s] == d1[s+2] and d1[s] == d1[s+3] and d1[s] != 0:
                return d1[s]
    if d2.size >= 4:
        for s in range(d2.size-3):
            if d2[s] == d2[s+1] and d2[s] == d2[s+2] and d2[s] == d2[s+3] and d2[s] != 0:
                return d2[s]
    if col.size >= 4:
        for s in range(col.size-3):
            if col[s] == col[s+1] and col[s] == col[s+2] and col[s] == col[s+3] and col[s] != 0:
                return col[s]
    if row.size >= 4:
        for s in range(row.size-3):
            if row[s] == row[s+1] and row[s] == row[s+2] and row[s] == row[s+3] and row[s] != 0:
                return row[s]
    return 0

def generate_title(players,turn):
    title = None
    if players[1] is None:
        if turn == 0:
            title = "<@!{}> vs. nobody yet; <@!{}>'s move".format(players[0].id, players[0].id)
        else:
            title = "<@!{}> vs. nobody yet; make a move to join!".format(players[0].id)
    else:
        title = "<@!{}> vs. <@!{}>; <@!{}>'s move".format(players[0].id, players[1].id, players[turn].id)
    return title

class connect_four(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    gameinprogress = False

    async def draw_board(self, ctx, message, board):
        # Create an image of the board state
        # Create the backdrop
        channel = ctx.message.channel
        out = Image.new("RGB", (board_width, board_height), bgcolor)
        for r in range(6):
            for c in range(7):
                color = (0, 0, 0)
                if board[r][c] == 1:
                    color = p1color
                elif board[r][c] == 2:
                    color = p2color
                # bounding boxes for the ellipses
                # x1 = (s+d)*c - d, x2 = x1 + d
                x2 = (hole_spc + hole_d) * (c + 1)
                x1 = x2 - hole_d
                y2 = (hole_spc + hole_d) * ((5 - r) + 1)
                y1 = y2 - hole_d
                # draw circle
                outdraw = ImageDraw.Draw(out)
                outdraw.ellipse((x1, y1, x2, y2), fill=color)

        # generate image url by posting to private channel
        out.save("temp.png") # create temp image file
        pchan = self.bot.get_channel(PRIVATECHANNEL) # fetch private channel
        ppost = await pchan.send(file=discord.File("temp.png")) # send image to private channel
        purl = ppost.attachments[0].url # retrieve url
        await ppost.delete() #delete private server post
        os.remove("temp.png") # delete temp image

        # now we have url, just post the url
        print(purl)

        if message is None:
            message = await channel.send(purl)
            for reaction in reactions:
                await message.add_reaction(reaction)
        else:
            await message.edit(content=purl)
        return message

    @commands.group(pass_context=True)
    async def connect_four(self, ctx, *args):
        """Start a game of Connect Four"""
        mention_msg = "<@!{}>".format(ctx.message.author.id)
        channel = ctx.message.channel
        #parsed_args = helpers.parse_options(args)

        # Check if game is in progress
        if self.gameinprogress:
            await channel.send("A game is already in progress.")
            return

        self.gameinprogress = True

        # Initiate the message
        message = None

        # Initiate the players and turn order
        players = [ctx.author, None]
        turn = 0

        # Initiate the title
        title = generate_title(players,turn)
        tpost = await channel.send(title)

        # Initiate the board
        board = numpy.zeros((6, 7))
        bpost = await self.draw_board(ctx, message, board)

        await ctx.message.delete()

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=30)
                print(str(reaction.emoji))
                # Check whose turn it is.
                print(players[turn])
                print(user)
                print(players[turn] == user)

                if str(reaction.emoji) in reactions:
                    if user in players and reactdict[str(reaction.emoji)] == 7:
                        mention_msg = "<@!{}> surrendered.".format(user.id)
                        await channel.send(mention_msg)
                        self.gameinprogress = False
                        return
                    if players[turn] is None:
                        players[turn] = user
                    if players[turn] == user:
                        # process turn
                        c = reactdict[str(reaction.emoji)] # figure out what column to drop in
                        r = find_first_nonzero_in_col(board, c) # figure out what row to drop on, if possible
                        if r is not None:
                            board[r][c] = turn + 1 # 1 for p1, 2 for p2
                            turn = 1 - turn # vaild move; pass the turn
                            # update title and board messages
                            title = generate_title(players, turn)
                            await tpost.edit(content=title)
                            await self.draw_board(ctx, bpost, board)
                            # check for victory
                            v = check_for_victory(board,r,c)
                            if v != 0:
                                mention_msg = "<@!{}> won the game!".format(players[int(v)-1].id)
                                await channel.send(mention_msg)
                                self.gameinprogress = False
                                return

                await bpost.remove_reaction(reaction, user)

            except asyncio.TimeoutError:
                print("Timeout")
                await channel.send("Time's up, nerds.")
                self.gameinprogress = False
                return



def setup(bot):
    bot.add_cog(connect_four(bot))

