import asyncio
import sys
import re
import discord.ext
import requests
import time
from discord.ext import commands
import discord
import helpers
import random

from secrets import CLIENT_ID
from secrets import SECRET_TOKEN
from secrets import USERNAME
from secrets import PASSWORD

base_url = 'https://www.reddit.com/'
obase_url = 'https://oauth.reddit.com'
data = {'grant_type': 'password', 'username': USERNAME, 'password': PASSWORD}
auth = requests.auth.HTTPBasicAuth(CLIENT_ID, SECRET_TOKEN)
embed_links = ['imgur', '.jpg', '.png', 'i.redd.it']

class RedditStuff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    self.override = None

    @commands.group(pass_context=True)
    async def pls(self, ctx, *args):
        channel = ctx.message.channel
        parsed_args = helpers.parse_options(args)

        if len(parsed_args) < 1:
            await ctx.send("Please provide a subreddit name")
            return
        
        for item in parsed_args: 
            if item.name == "input":
                subreddit = item.values[0]
            elif item.name == "--hot":
                self.override = "hot"
            elif item.name == "--new":
                self.override = "new"
            elif item.name == "--top":
                self.override == "top"


        # obtain token for oauth requests
        r = requests.post(base_url + 'api/v1/access_token',
                          data=data, headers={'user-agent': 'zooeybot by decrypto'},
                          auth=auth)
        d = r.json()

        token = 'bearer ' + d['access_token']
        headers = {'Authorization': token, 'User-Agent': 'zooeybot by decrypto'}

        # search to make sure subreddit exists
        response = requests.get(obase_url + '/api/search_reddit_names?query=' + subreddit + '&exact=true', headers=headers)

        if 'error' in response.json():
            await ctx.send(subreddit + " does not exist, try again")
            return

        # make a post request to grab a random post from given 'subreddit'
        cap = 0
        need_request = True  # If a dict is returned from request, set to False and reuse the dict

        # only look for posts with url links and sfw
        # maximum of 10 tries before giving up
        while True:
            if need_request is True:
                if self.override == "hot" :
                    response = requests.get(obase_url + '/r/' + subreddit + '/hot', headers=headers)
                    need_request = False
                elif self.override == "new":
                    response = requests.get(obase_url + '/r/' + subreddit + '/new', headers=headers)
                    need_request = False
                elif self.override == "top":
                    response = requests.get(obase_url + '/r/' + subreddit + '/top', headers=headers)
                    need_request = False
                else:
                    response = requests.get(obase_url + '/r/' + subreddit + '/random', headers=headers)
                    if type(response.json()) is dict:
                        need_request = False

            if 'error' in response.json():
                await ctx.send("cannot access sub, " + response.json()['reason'])
                return

            # deal with certain subreddits that does not play nice with random
            # they return a dictionary rather than a list
            # additionally deals with the override flags as they will return a dict
            if type(response.json()) is dict:
                submission = random.choice(response.json()['data']['children'])
            else:
                submission = response.json()[0]['data']['children'][0]

            if 'url_overridden_by_dest' in submission['data'].keys() and submission['data']['over_18'] is False and 'gallery' not in submission['data']['url_overridden_by_dest']:
                break

            cap += 1
            print(cap)
            if cap > 10:
                await ctx.send("lol no luck, try again")
                return

        # get necessary information from response
        res_permalink = base_url + submission['data']['permalink']
        res_url = submission['data']['url_overridden_by_dest']
        res_title = submission['data']['title']
        res_ups = submission['data']['ups']
        user = ctx.message.author.name

        # format response into an embed message
        embed = discord.Embed(title=res_title, url=res_permalink)
        embed.set_footer(text=user + " | " + str(res_ups) + " upvotes")
        if any(link in res_url for link in embed_links):
            if 'imgur' in res_url and ('.jpg' not in res_url or '.png' not in res_url): 
                res_url = res_url + ".jpg"
            embed.set_image(url=res_url)
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=embed)
            await ctx.send(res_url)

    
def setup(bot):
    bot.add_cog(RedditStuff(bot))

