import asyncio
from typing import Awaitable, List, Literal
import aiohttp

import oneai.skills as skills
from oneai.classes import *

URL = 'https://api.oneai.com/api/v0/pipeline'

api_key = ''
