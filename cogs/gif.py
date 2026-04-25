import asyncio
import aiohttp
import discord
from discord.ext import commands
from config import KLIPY_API_KEY

KLIPY_URL = f"https://api.klipy.com/api/v1/{KLIPY_API_KEY}/gifs/search"
PER_PAGE = 16
GROUP_SIZE = 4
MAX_PAGES = 4

NAV_PREV    = "⬅️"
NAV_NEXT    = "➡️"
NAV_MORE    = "🚫"
NAV_SELECT  = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
NAV_REACTIONS = [NAV_PREV] + NAV_SELECT + [NAV_NEXT, NAV_MORE]


class GifSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # user_id -> {channel, results, group, page, query, embed_msg, dm}
        self.sessions = {}

    async def search_klipy(self, query, page, customer_id):
        params = {
            "q": query,
            "page": page,
            "per_page": PER_PAGE,
            "customer_id": customer_id,
            "locale": "US",
            "content_filter": "off",
            "format_filter": "gif",
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(KLIPY_URL, params=params) as resp:
                return await resp.json()

    def extract_gifs(self, data):
        """Parse KLIPY response into a list of {url, preview_url, title} dicts."""
        results = []
        inner = data.get("data", {}) if isinstance(data, dict) else {}
        items = inner.get("data", []) if isinstance(inner, dict) else []
        for item in items:
            if not isinstance(item, dict):
                continue
            file = item.get("file", {})
            if not isinstance(file, dict):
                continue
            gif_url = (file.get("md") or file.get("hd") or file.get("sm") or {}).get("gif", {}).get("url")
            preview_url = (file.get("sm") or file.get("xs") or file.get("md") or {}).get("gif", {}).get("url")
            if gif_url:
                results.append({
                    "url": gif_url,
                    "preview_url": preview_url or gif_url,
                    "title": item.get("title", ""),
                })
        return results

    def build_embeds(self, results, group, page):
        start = group * GROUP_SIZE
        group_items = results[start:start + GROUP_SIZE]
        total_groups = (len(results) + GROUP_SIZE - 1) // GROUP_SIZE
        embeds = []
        for i, gif in enumerate(group_items):
            embed = discord.Embed(
                title=f"{i + 1}. {gif['title']}",
                color=discord.Color.purple()
            )
            embed.set_image(url=gif["preview_url"])
            embeds.append(embed)
        if embeds:
            embeds[-1].set_footer(
                text=f"Group {group + 1}/{total_groups}  ·  Page {page}/{MAX_PAGES}"
                     f"  |  ⬅️ ➡️ Browse  1️⃣2️⃣3️⃣4️⃣ Select  🚫 More"
            )
        return embeds

    @commands.command()
    async def gif(self, ctx):
        """Search for a GIF and post it to the channel."""
        user = ctx.author

        if user.id in self.sessions:
            del self.sessions[user.id]

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        try:
            dm = await user.create_dm()
            await dm.send("What GIF are you looking for? Reply with your search query.")
        except discord.Forbidden:
            await ctx.channel.send(
                f"{user.mention} I couldn't DM you. Enable DMs from server members and try again."
            )
            return

        def dm_check(m):
            return m.author.id == user.id and isinstance(m.channel, discord.DMChannel)

        try:
            query_msg = await self.bot.wait_for("message", timeout=60, check=dm_check)
        except asyncio.TimeoutError:
            await dm.send("Search timed out. Use `&gif` again to start over.")
            return

        query = query_msg.content.strip()
        if not query:
            await dm.send("No query provided. Use `&gif` again to start over.")
            return

        await dm.send(f'Searching for **"{query}"**...')

        page = 1
        try:
            data = await self.search_klipy(query, page, str(user.id))
        except Exception as e:
            await dm.send(f"Something went wrong contacting KLIPY: {e}")
            return

        results = self.extract_gifs(data)
        if not results:
            await dm.send("No results found. Try a different search term.")
            return

        group = 0
        embeds = self.build_embeds(results, group, page)
        embed_msg = await dm.send(embeds=embeds)
        for emoji in NAV_REACTIONS:
            await embed_msg.add_reaction(emoji)

        self.sessions[user.id] = {
            "channel": ctx.channel,
            "results": results,
            "group": group,
            "page": page,
            "query": query,
            "embed_msg": embed_msg,
            "dm": dm,
        }

        def reaction_check(r, u):
            return (
                u.id == user.id
                and r.message.id == embed_msg.id
                and str(r.emoji) in NAV_REACTIONS
            )

        while True:
            try:
                reaction, _ = await self.bot.wait_for(
                    "reaction_add", timeout=60, check=reaction_check
                )
            except asyncio.TimeoutError:
                await dm.send("Search timed out.")
                self.sessions.pop(user.id, None)
                return

            emoji = str(reaction.emoji)
            try:
                await embed_msg.remove_reaction(emoji, user)
            except discord.Forbidden:
                pass

            session = self.sessions[user.id]
            total_groups = (len(session["results"]) + GROUP_SIZE - 1) // GROUP_SIZE

            if emoji == NAV_PREV:
                session["group"] = (session["group"] - 1) % total_groups
                await embed_msg.edit(
                    embeds=self.build_embeds(session["results"], session["group"], session["page"])
                )

            elif emoji == NAV_NEXT:
                session["group"] = (session["group"] + 1) % total_groups
                await embed_msg.edit(
                    embeds=self.build_embeds(session["results"], session["group"], session["page"])
                )

            elif emoji in NAV_SELECT:
                pick = NAV_SELECT.index(emoji)
                idx = session["group"] * GROUP_SIZE + pick
                if idx >= len(session["results"]):
                    continue
                selected = session["results"][idx]
                await session["channel"].send(selected["url"])
                await dm.send("Posted!")
                self.sessions.pop(user.id, None)
                return

            elif emoji == NAV_MORE:
                if session["page"] >= MAX_PAGES:
                    await dm.send("No more pages available.")
                    continue
                session["page"] += 1
                await dm.send(f'Fetching page {session["page"]} for **"{session["query"]}"**...')
                try:
                    data = await self.search_klipy(session["query"], session["page"], str(user.id))
                except Exception as e:
                    await dm.send(f"Something went wrong: {e}")
                    session["page"] -= 1
                    continue

                new_results = self.extract_gifs(data)
                if not new_results:
                    await dm.send("No more results found.")
                    session["page"] -= 1
                    continue

                session["results"] = new_results
                session["group"] = 0
                await embed_msg.edit(
                    embeds=self.build_embeds(new_results, 0, session["page"])
                )


async def setup(bot):
    await bot.add_cog(GifSearch(bot))
