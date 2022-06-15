import aiohttp
import trafilatura as tf
import validators

async def extract_article(input, session: aiohttp.ClientSession):
    text = input if isinstance(input, str) else input.text
    if validators.url(text):
        async with session.get(text) as response:
            text = await response.text()
    return tf.extract(text)
