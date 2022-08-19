import oneai
import csv
import os

"""
in this example, we take a csv file,
 add summary + topics of the first column to each row,
 and create a new csv file with the added data
"""

# retrieve API key from environment variable
api_key = os.environ["ONEAI_APIKEY"]
# create a pipeline to extract topics & summarize the input
pipeline = oneai.Pipeline(
    steps=[
        oneai.skills.Topics(),
        oneai.skills.Summarize(),
    ],
    api_key=api_key,
)

# custom input class to hold csv row data
class RowInput(oneai.Document):
    # override oneai.Document for a simple str input
    def __init__(self, row_data: str):
        # set the first column as input
        super().__init__(row_data[0])
        # keep the row data to create the output file
        self.row_data = row_data


with open("input_file.csv", "r", newline="", encoding="utf-8") as inputf, open(
    "output_file.csv", "w", newline="", encoding="utf-8"
) as outputf:
    reader, writer = csv.reader(inputf), csv.writer(outputf)

    # create the header for the output file
    header = next(reader) + ["topics", "summary"]
    writer.writerow(header)

    # run our pipeline over csv rows
    pipeline.run_batch(
        # convert csv rows to our RowInput class
        map(RowInput, reader),
        # on successful output, write the row in the output file with the topics and the summary text
        on_output=lambda input, output: writer.writerow(
            input.row_data + [";".join(output.topics.values), output.summary.text]
        ),
    )
