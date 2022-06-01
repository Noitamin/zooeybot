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
from random import choice
from tweepy import Client, OAuth1UserHandler

# Reddit secrets
from secrets import CLIENT_ID
from secrets import SECRET_TOKEN
from secrets import USERNAME
from secrets import PASSWORD

# Twitter secrets
from secrets import CONSUMER_KEY
from secrets import CONSUMER_SECRET
from secrets import ACCESS_TOKEN
from secrets import ACCESS_TOKEN_SECRET
from secrets import BEARER_TOKEN

base_url = 'https://www.reddit.com/'
obase_url = 'https://oauth.reddit.com'
data = {'grant_type': 'password', 'username': USERNAME, 'password': PASSWORD}
embed_links = ['imgur', '.jpg', '.png', 'i.redd.it']


class RedditStuff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.twi_client = Client(bearer_token=BEARER_TOKEN,
                                 consumer_key=CONSUMER_KEY,
                                 consumer_secret=CONSUMER_SECRET,
                                 access_token=ACCESS_TOKEN,
                                 access_token_secret=ACCESS_TOKEN_SECRET)
        self.twi_auth = OAuth1UserHandler(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

        self.reddit_auth = requests.auth.HTTPBasicAuth(CLIENT_ID, SECRET_TOKEN)

    override = None

    def twitter_search(self, tag):

        max_res = 100
        if tag.startswith('@'):
            tweet_username = tag[1:]
            user_id = self.twi_client.get_user(username=tweet_username)
            tweets = self.twi_client.get_users_tweets(id=user_id.data.id, max_results=max_res, tweet_fields=['referenced_tweets'])

            if tweets.meta['result_count'] == 0:
                return "Could not find any results"
            choice_result = choice(range(0, tweets.meta['result_count']))

            # If tweet is a retweet (starts with "RT ")
            # then extract the user in the retweet
            tweet_data= tweets.data[choice_result]
            if tweet_data.text.startswith("RT "):
                match = re.search('@.*?[^:]+', tweet_data.text)
                if match is not None:
                    tweet_username = match.group(0)[1:]
                tweet_id = tweet_data['referenced_tweets'][0]['id']
            else:
                tweet_id = tweet_data['id']
        else:
            query = "{tag} -is:retweet has:images OR {tag} -is:retweet has:videos".format(tag=tag)
            tweets = self.twi_client.search_recent_tweets(query=query,
                                                 expansions='author_id',
                                                 max_results=max_res)
            if tweets.meta['result_count'] == 0:
                return "Could not find any results"
            choice_result = choice(range(0, tweets.meta['result_count']))
            tweet_username = self.twi_client.get_user(id=tweets.data[choice_result].author_id, user_auth=self.twi_auth).data.username
            tweet_id = tweets.data[choice_result].id


        tweet_url = "https://twitter.com/{tweet_username}/status/{tweet_id}/?e".format(tweet_username=tweet_username, tweet_id=tweet_id)
        return tweet_url


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
                self.override = "top"

        if subreddit.startswith('#'):
            await ctx.send(self.twitter_search(subreddit[1:]))
            return

        # obtain token for oauth requests
        r = requests.post(base_url + 'api/v1/access_token',
                          data=data, headers={'user-agent': 'zooeybot by decrypto'},
                          auth=self.reddit_auth)
        if r.status_code != 200:
            await ctx.send("Error: Status " + str(r.status_code))
            return
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
                    response = requests.get(obase_url + '/r/' + subreddit + '/top.json?t=all', headers=headers)
                    need_request = False
                else:
                    response = requests.get(obase_url + '/r/' + subreddit + '/random', headers=headers)
                    if type(response.json()) is dict:
                        need_request = False
                self.override = None

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

            if 'url_overridden_by_dest' in submission['data'].keys() \
                and submission['data']['over_18'] is False \
                and 'gallery' not in submission['data']['url_overridden_by_dest'] \
                and submission['data']['is_video'] is False \
                and 'crosspost_parent_list' not in submission['data'].keys():
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
        print(res_url)

        # format response into an embed message
        embed = discord.Embed(title=res_title, url=res_permalink)
        embed.set_footer(text=user + " | " + str(res_ups) + " upvotes")
        if any(link in res_url for link in embed_links):
            if 'imgur' in res_url and ('.jpg' not in res_url and '.png' not in res_url):
                res_url = res_url + ".jpg"
            embed.set_image(url=res_url)
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=embed)
            await ctx.send(res_url)

    
def setup(bot):
    bot.add_cog(RedditStuff(bot))

