from copy import copy
from typing import List

import oneai
from oneai.classes import Label, Labels, Output, Skill, TextContent
from oneai.parsing import parse_conversation


def build_output(
    skills: List[Skill], raw_output: dict, input_type: str,
) -> Output:
    if oneai.DEBUG_RAW_RESPONSES:
        return raw_output
    def get_text(index) -> TextContent:
        # get the input text for this Output object. use index=-1 to get the original input text
        # text can be returned as a simple str or parsed to match a given input type
        text = (
            raw_output["output"][index]["text"]
            if index >= 0
            else raw_output["input_text"]
        )
        if input_type == 'conversation':
            try:
                return parse_conversation(text)
            except:
                pass
        return text

    def split_pipeline(skills: List[Skill], i: int):
        # split pipeline at a generator Skill
        first, second = skills[: i + 1], skills[i + 1 :]
        if hasattr(skills[i], "output_attr1") and skills[i].output_attr1:
            # handle skills that create both text and labels
            clone = copy(skills[i])
            clone.is_generator = False
            clone.output_attr = skills[i].output_attr1
            second = (clone, *second)
        return first, second

    def build_internal(
        output_index: int, skills: List[Skill]
    ) -> "Output":
        text = get_text(output_index)
        # temporary fix- if 1st skill is not a generator, use input_text, not output[0].text,
        # since output[0].text is corrupted (not parsable) for conversation inputs
        output_index = max(output_index, 0)
        labels = [
            Label.from_dict(label)
            for label in raw_output["output"][output_index]["labels"]
        ]
        data = []
        for i, skill in enumerate(skills):
            if skill.is_generator:
                skills, next_skills = split_pipeline(skills, i)
                data.append(
                    build_internal(
                        output_index + 1, next_skills
                    )
                )
                break
            else:
                data.append(
                    Labels(filter(lambda label: label.type == skill.label_type, labels))
                )
        return Output(text=text, skills=list(skills), data=data)

    generator = raw_output["output"][0].get("text_generated_by_step_id", 0) - 1
    if generator < 0:
        return build_internal(-1, skills)
    else:
        # edge case- first Skill is a generator, or a generator preceded by Skills that didn't generate output
        # in this case the API will skip these Skills,
        # so we need to create filler objects to match the expected structure
        skills, next_skills = split_pipeline(skills, generator)
        return Output(
            text=get_text(-1),
            skills=list(skills),
            data=[Labels()] * generator + [build_internal(0, next_skills)],
        )
