import aiohttp
import trafilatura as tf, trafilatura.settings as tfsettings
import validators
import lxml.html, lxml.html.clean

from oneai.exceptions import InputError, ServerError


async def extract_base(input, session: aiohttp.ClientSession, extractor):
    text = input if isinstance(input, str) else input.raw
    if validators.url(text):
        try:
            async with session.get(text) as response:
                text = await response.text()
        except:
            raise ServerError(
                50001,
                "Retrieve URL failed",
                f"Failed to retrieve the input URL {text}.",
            )
    try:
        return extractor(text.encode("unicode-escape"))
    except:
        raise InputError(
            40008,
            "Input format was not recognized",
            f"Failed to extract HTML text from the input {text}.",
        )


cleaner = lxml.html.clean.Cleaner(
    style=True,
)


async def extract_text(input, session: aiohttp.ClientSession):
    return await extract_base(
        input,
        session,
        lambda text: cleaner.clean_html(lxml.html.fromstring(text)).xpath("string()"),
    )


async def extract_article(input, session: aiohttp.ClientSession):
    newconfig = tfsettings.use_config()
    newconfig.set("DEFAULT", "EXTRACTION_TIMEOUT", "0")
    return await extract_base(input, session, lambda text: tf.extract(text, config=newconfig))
