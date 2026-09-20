"""Bounded, channel-local history for conversation summaries."""

import discord

DEFAULT_SUMMARY_MESSAGES = 40
MAX_SUMMARY_MESSAGES = 200
SUMMARY_TEXT_BUDGET = 40000


async def summary_history(message, count=DEFAULT_SUMMARY_MESSAGES):
    if type(count) is not int or not 1 <= count <= MAX_SUMMARY_MESSAGES:
        return {"error": f"Choose between 1 and {MAX_SUMMARY_MESSAGES} messages."}
    records = []
    truncated = False
    # Every selected message gets space; large requests shorten each excerpt.
    per_message = min(2000, SUMMARY_TEXT_BUDGET // count)
    try:
        async for previous in message.channel.history(limit=count, before=message):
            text = previous.clean_content or "[No text content]"
            if len(text) > per_message:
                text = text[:per_message] + " [truncated]"
                truncated = True
            records.append({
                "author": previous.author.display_name[:80],
                "text": text,
                "attachments": len(previous.attachments),
            })
    except discord.Forbidden:
        return {"error": "I need View Channel and Read Message History permissions to summarize this channel."}
    except discord.HTTPException:
        return {"error": "Discord message history is unavailable right now. Please try again."}
    records.reverse()
    return {
        "requested_count": count,
        "returned_count": len(records),
        "text_truncated": truncated,
        "messages": records,
        "note": "Oldest first, from the current channel only, excluding the request. Attachment contents are not available.",
    }
