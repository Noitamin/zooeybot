# zooeybot v1.0
Bot for discord shenanigans 

## Mention and reply conversations

Mention Zooey or reply to one of her messages to chat without `&chat`.
She receives up to ten preceding messages from the same channel or thread,
plus the message you replied to if it is older. Background is capped at
10,000 characters, with up to 1,000 characters per message. Attachment
contents are not read. Other bots do not trigger replies.

This background is temporary: only your request and Zooey's answer join
the existing per-server memory (per-user in DMs). Ordinary messages do not
trigger chat. Commands continue working normally. Enable **Read Message
History** for channel context; if history is unavailable, mentions still work.
Reply detection also requires access to the referenced message.

## Conversation summaries

Ask `@Zooey summarize the last 50 messages`, reply to her with `summarize
the conversation`, or use `&chat summarize the last 20 messages`.
Zooey fetches the requested messages from the current channel or thread and
summarizes them in character. The default is 40; supported counts are 1–200.
The request itself is excluded, and messages from other users and bots count
toward the total. Read Message History permission is required.

Large messages are shortened to keep the combined message text around
40,000 characters. Zooey is told when text was shortened or fewer messages
were available. Attachment contents are not read. Retrieved history is
temporary; only the request and final summary enter conversational memory.
This feature works without a Tavily key and uses the existing DeepSeek API.

## Web search

Create a [Tavily API key](https://app.tavily.com/) and add
`TAVILY_API_KEY=your-key` to `.env`. Rebuild/restart the bot after setup
(`docker compose up -d --build` for Docker).

Use `&chat <message>` as usual: DeepSeek can call the web search tool when
it needs current information or fact verification. It can make up to three
basic searches per reply, with up to five results each. Zooey blends the results
into her usual personality, without citation markers or source lists unless
you ask for links. Tool results are temporary; only the question and
final answer are stored in conversation memory.

Use `&search <question>` to explicitly request a single web search and answer.
Search questions and answers join the server's existing 20-message memory;
DM memory is separate per user. `&chat CLEAR` resets the relevant memory.

Search uses Tavily's basic mode (one credit per request). The explicit
`&search` command has a ten-second cooldown per user. Tavily currently
includes 1,000 free credits per month;
leave paid usage disabled in your Tavily account to stay on the free tier.
DeepSeek answer generation still uses your existing API billing. Without a
Tavily key, the bot runs normally and the search command explains how to enable it.

## Docker

Install Docker with Docker Compose. Copy the environment template:

```sh
cp .env.example .env
```

Edit `.env` to set `TOKEN` (Discord bot token), `PRIVATECHANNEL` (numeric
channel ID), `DEEPSEEK_KEY` (chat), and `KLIPY_API_KEY` (GIF searches).
`OPENAI_KEY` and `XAI_API_KEY` can remain empty unless you enable those providers.
Enable the privileged gateway intents for your bot in the Discord Developer
Portal, since the bot requests all intents.

```sh
docker compose up -d --build
docker compose logs -f bot
```

The image uses Python slim and only the active bot's runtime dependencies,
including FFmpeg for voice playback. It runs as an unprivileged user and
requires no published ports. Compose injects `.env` as environment variables.
The file is excluded from Git and the Docker image.

Databases and downloaded LINE stickers persist in the `bot-data` volume.
To migrate existing databases, stop the old bot and copy them before starting:

```sh
docker compose build
docker compose run --rm --no-deps --user root --volume "$PWD:/migration:ro" bot \
  sh -c 'cp /migration/*.db /data/ && chown 10001:10001 /data/*.db'
```

Use `docker compose down` to stop the bot while keeping its data. After code
changes, run `docker compose up -d --build` again. After editing `.env`,
run `docker compose up -d --force-recreate bot` to apply the new environment.

## Local setup

Use Python 3.11 and install FFmpeg and libopus using your system package
manager (`sudo apt install ffmpeg libopus0` on Debian/Ubuntu). Then:

```sh
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python zooey.py
```

Create `.env` as shown above before starting. Local startup loads it
automatically; existing environment variables take precedence. `config.py`
is no longer used. `python setup.py` also
installs the same requirements. The dependency list covers the enabled
extensions; the inactive `hololive` and `reddit_stuff` extensions need their
own additional dependencies and configuration if re-enabled.
