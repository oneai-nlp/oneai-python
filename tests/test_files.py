import oneai
import pytest

from tests.constants import *

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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mode, sync", [("r", False), ("rb", False), ("r", True), ("rb", True)]
)
async def test_csv(mode: str, sync: bool):
    if sync:
        pytest.skip("CSV upload is not supported in sync mode")
    pipeline = oneai.Pipeline([oneai.skills.Numbers()])
    with open(CSV_PATH, mode) as f:
        csv_params = oneai.CSVParams(
            columns=[
                "input",
                "timestamp",
                False,
                "input_translated",
                False,
                "metadata",
            ],
            skip_rows=1,
            max_rows=3,
        )
        output = (
            pipeline.run(f, csv_params=csv_params, multilingual=True)
            if sync
            else await pipeline.run_async(f, csv_params=csv_params, multilingual=True)
        )
        assert hasattr(output, "outputs")
        assert len(output.outputs) == 1
        assert hasattr(output.outputs[0], "numbers")
        assert len(output.outputs[0].numbers) == 1
        assert hasattr(output.outputs[0].numbers[0], "value")
        assert int(output.outputs[0].numbers[0].value) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("sync", [False, True])
async def test_txt(sync: bool):
    pipeline = oneai.Pipeline([oneai.skills.Numbers()])
    with open(TXT_PATH, "r") as f:
        output = pipeline.run(f) if sync else await pipeline.run_async(f)
        assert hasattr(output, "numbers")
        assert len(output.numbers) == 1
        assert hasattr(output.numbers[0], "value")
        assert int(output.numbers[0].value) == 1
