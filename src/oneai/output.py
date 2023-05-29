from oneai.classes import Input, Skill, TextContent, Labels
from typing import (
    Awaitable,
    Hashable,
    Iterable,
    List,
    Tuple,
    Union,
    TYPE_CHECKING,
    Dict,
)

if TYPE_CHECKING:
    from oneai.skills import OutputAttrs


class Output(Input[TextContent], OutputAttrs if TYPE_CHECKING else object):
    """
    Represents the output of a pipeline. The structure of the output is dynamic, and corresponds to the Skills used and their order in the pipeline.
    Skill outputs can be accessed as attributes, either with the `api_name` of the corresponding Skill or the `output_attr` field.

    ## Attributes

    `text: TextContent`
        The input text from which this `Output` instance was produced.
    `skills: List[Skill]`
        The Skills used to process `text` and produce this `Output` instance.
    See `OutputAttrs` for the attributes generated by different Skills.
    """

    def __init__(
        self,
        text: TextContent,
        skills: List[Skill] = [],
        data: List[Union[Labels, "Output"]] = [],
        outputs: List["Output"] = None,
        task_id: str = None,
    ):
        super().__init__(
            text,
            type="article" if isinstance(text, str) else "conversation",
            content_type="text/plain" if isinstance(text, str) else "application/json",
        )

        self.task_id = task_id
        self.skills = skills
        for skill, value in zip(skills, data):
            setattr(self, skill.text_attr or skill.labels_attr or skill.api_name, value)

        if outputs:
            setattr(self, "outputs", outputs)

    def __dir__(self) -> Iterable[str]:
        return super().__dir__() + [
            skill.text_attr or skill.labels_attr or skill.api_name
            for skill in self.skills
        ]

    def __repr__(self) -> str:
        if self.text is None and self.task_id is not None:
            return f"oneai.Output(task_id={self.task_id})"
        result = f"oneai.Output(text={repr(self.text)}"
        for skill in self.skills:
            attr = skill.text_attr or skill.labels_attr or skill.api_name
            result += f", {attr}={repr(getattr(self, attr))}"
        return result + ")"

    async def get_status(self, api_key: str = None) -> Awaitable[str]:
        if self.task_id is None:
            raise ValueError("No task_id found")
        if self.text is not None:
            return "COMPLETED"

        if api_key is None:
            from oneai import api_key

        from oneai.process_scheduler import process_task_status

        return (await process_task_status(self.task_id, None, api_key, self.skills))[0]

    async def await_completion(
        self, api_key: str = None, *, interval: int = 1
    ) -> Awaitable["Output[TextContent]"]:
        if self.task_id is None:
            raise ValueError("No task_id found")
        if self.text is not None:
            return self

        if api_key is None:
            from oneai import api_key
        from oneai.process_scheduler import task_polling

        return await task_polling(
            self.task_id,
            None,
            api_key,
            self.skills,
            interval,
        )


class BatchResponse:
    def __init__(self):
        self._data: Dict[Input, Output] = {}

    def __setitem__(self, key: Input, value: Output):
        self._data[key] = value

    def __getitem__(self, key: Input) -> Output:
        return (
            self._data[key]
            if isinstance(key, Hashable) and key in self._data
            else next(v for k, v in self._data.items() if k.text == key)
        )

    def items(self) -> Iterable[Tuple[Input, Output]]:
        return self._data.items()

    def __contains__(self, key: Input) -> bool:
        return (
            isinstance(key, Hashable)
            and key in self._data
            or any(k.text == key for k in self._data)
        )
