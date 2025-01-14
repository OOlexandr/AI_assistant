import pprint

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import Answer, Question, User
from ..schemas.chat import Response
from ..services.llmchain import Chain

chain = Chain()


async def respond(current_user: User, session: AsyncSession, instruction: str) -> str:
    question = Question(
        user_id=current_user.id,
        question_text=instruction,
    )

    session.add(question)
    await session.commit()

    response = chain(instruction, current_user.id)
    answer = Answer(
        question_id=question.id,
        answer_text=response,
    )

    session.add(answer)
    await session.commit()

    history = await extract_history(current_user, session)
    pprint.pprint(history)

    return Response(string=response)


async def extract_history(current_user: User, session: AsyncSession) -> list:
    user_history = []

    async with session.begin():
        result = await session.execute(
            select(Question, Answer)
            .join(Answer)
            .filter(Question.user_id == current_user.id)
        )

        for question, answer in result.all():
            user_history.append((question.question_text, answer.answer_text))

    return user_history
