import oneai
import pytest

from tests.constants import MP3_PATH, WAV_PATH, PDF_PATH

pipeline_audio = oneai.Pipeline(
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
async def test_audio(path: str, sync: bool):
    with open(path, "rb") as f:
        output = pipeline_audio.run(f) if sync else await pipeline_audio.run_async(f)
        assert hasattr(output, "transcription")
        assert hasattr(output.transcription, "sentences")
        assert hasattr(output.transcription, "segments")
        assert hasattr(output.transcription, "proofread")
        assert hasattr(output.transcription.proofread, "replacements")
        assert hasattr(output.transcription.proofread, "numbers")
        assert hasattr(output.transcription.proofread, "sentiments")


@pytest.mark.asyncio
@pytest.mark.parametrize("sync", [False, True])
async def test_pdf(sync: bool):
    if sync:
        pytest.skip("PDF extraction is not supported in sync mode")
    pipeline_pdf = oneai.Pipeline([oneai.skills.PDFExtractText()])
    with open(PDF_PATH, "rb") as f:
        output = pipeline_pdf.run(f) if sync else await pipeline_pdf.run_async(f)
        assert hasattr(output, "pdf_text")
        assert output.pdf_text.text
