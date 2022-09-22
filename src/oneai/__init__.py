__version__ = "0.6.3"
__package__ = "oneai"

from typing_extensions import Final
import oneai.logger
import oneai.skills as skills
from oneai.classes import *
from oneai.pipeline import Pipeline
import oneai.clustering as clustering

URL: Final[str] = "https://api.oneai.com"
"""
Base URL for the pipeline API. Only change if you know what you're doing.
"""

api_key = None
"""
Default api key to use. You can use different keys for different pipelines by setting the `Pipeline.api_key` attribute or passing an `api_key` parameter to `Pipeline.run` calls.
"""

MAX_CONCURRENT_REQUESTS: Final[int] = 2
"""
Max number of allowed concurrent requests to be made by the SDK.
Currently only enforced on `pipeline.run_batch`, other calls may be limited by the API
"""
PRINT_PROGRESS = True
"""
Does nothing. Set `logging.get('oneai').propagate = False` to disable logging
"""
DEBUG_RAW_RESPONSES = False
"""
Debug flag, return raw API responses instead of structured `Output` object. Only enable if you know what you're doing
"""
