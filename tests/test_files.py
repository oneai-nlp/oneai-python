import oneai
import pytest

from tests.constants import MP3_PATH, WAV_PATH

pipeline = oneai.Pipeline(
    [
        oneai.skills.Transcribe(timestamp_per_word=True),
        oneai.skills.SplitBySentence(),
        oneai.skills.SplitByTopic(),
        oneai.skills.Proofread(),
        oneai.skills.Numbers(),
        oneai.skills.Sentiments(),
    ]
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path, sync", [(MP3_PATH, False), (MP3_PATH, True), (WAV_PATH, True)]
)
async def test_file(path: str, sync: bool):
    with open(path, "rb") as f:
        output = pipeline.run(f) if sync else await pipeline.run_async(f)
        assert hasattr(output, "transcription")
        assert hasattr(output.transcription, "sentences")
        assert hasattr(output.transcription, "segments")
        assert hasattr(output.transcription, "proofread")
        assert hasattr(output.transcription.proofread, "replacements")
        assert hasattr(output.transcription.proofread, "numbers")
        assert hasattr(output.transcription.proofread, "sentiments")
