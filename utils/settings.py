"""Load local .env settings; existing environment variables take precedence."""

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent.parent / ".env")

TOKEN = os.environ["TOKEN"]
PRIVATECHANNEL = int(os.environ["PRIVATECHANNEL"])
DEEPSEEK_KEY = os.environ["DEEPSEEK_KEY"]
KLIPY_API_KEY = os.environ["KLIPY_API_KEY"]
OPENAI_KEY = os.getenv("OPENAI_KEY") or "unused"
XAI_API_KEY = os.getenv("XAI_API_KEY") or "unused"
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "").strip()
