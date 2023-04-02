import sys
import os
import dotenv

sys.path.insert(0, "src")
dotenv.load_dotenv()

import oneai

oneai.api_key = os.environ["API_KEY"]
