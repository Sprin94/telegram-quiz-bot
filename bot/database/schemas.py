from pydantic import BaseModel, validator


class QuestionSchema(BaseModel):
    text: str
    chat_id: int

    @validator('text')
    def check_text_length(cls, v):
        if 300 < len(v):
            raise ValueError('Длинна вопроса должна быть от 1 до 300')
        return v


class AnswerSchema(BaseModel):
    question_id: int | None
    text: str
    is_right: bool

    @validator('text')
    def check_text_length(cls, v):
        if 100 < len(v):
            raise ValueError('Длинна ответа должна быть от 1 до 100')
        return v
