import os
import random
import traceback
import argparse
from time import sleep

import redis
from dotenv import load_dotenv
import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from quiz_parser import extract_questions
from quiz_parser import make_raw_answer


redis_db = redis.Redis(
    host='localhost',
    port=6379,
    db=1,
    decode_responses=True,
)


def get_start_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Мой счет', color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


def get_retry_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Да', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Нет', color=VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()


def handle_message_start(user_id, vk_api):
    vk_api.messages.send(
        user_id=user_id,
        message='Здравствуйте',
        random_id=random.randint(1,1000),
        keyboard=get_start_keyboard(),
    )


def handle_new_question_request(user_id, vk_api, questions_with_answers):
    question = random.choice(list(questions_with_answers.keys()))

    redis_db.set(str(user_id), question, ex=3600)

    vk_api.messages.send(
        user_id=user_id,
        message=question,
        random_id=random.randint(1,1000)
    )


def handle_solution_attempt(user_id, message_text, vk_api, questions_with_answers):
    asked_question = redis_db.get(str(user_id))

    if not asked_question:
        print(f"User's answer with id {user_id} not found")

    correct_answer = questions_with_answers.get(asked_question)

    user_answer_raw = make_raw_answer(message_text)
    correct_answer_raw = make_raw_answer(correct_answer)

    if user_answer_raw == correct_answer_raw:
        vk_api.messages.send(
            user_id=user_id,
            message='Правильный ответ!',
            random_id=random.randint(1,1000),
            keyboard=get_start_keyboard()
        )

        redis_db.delete(str(user_id))

    else:
        vk_api.messages.send(
            user_id=user_id,
            message='Ответ неверный...',
            random_id=random.randint(1,1000)
        )

        sleep(3)

        vk_api.messages.send(
            user_id=user_id,
            message='Попробуете еще раз?',
            random_id=random.randint(1,1000),
            keyboard=get_retry_keyboard()
        )


def repeat_question_request(user_id, vk_api):
    question = redis_db.get(str(user_id))

    if not question:
        print(f"User's answer with id {user_id} not found")

    vk_api.messages.send(
        user_id=user_id,
        message=question,
        random_id=random.randint(1,1000)
    )


def handle_give_up(user_id, vk_api, questions_with_answers):
    asked_question = redis_db.get(str(user_id))

    correct_answer = questions_with_answers.get(asked_question)

    vk_api.messages.send(
        user_id=user_id,
        message=f'Правильный ответ: {correct_answer}',
        random_id=random.randint(1,1000)
    )

    redis_db.delete(str(user_id))

    sleep(3)

    handle_new_question_request(user_id, vk_api, questions_with_answers)


def main():
    load_dotenv()
    vk_bot_token = os.environ['VK_BOT_TOKEN']
    admin_id = os.environ['VK_ADMIN_ID']

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'path',
        type=str,
        nargs='?',
        default='1vs1200.txt',
        help='Path to the txt file with questions',
    )
    args = parser.parse_args()

    questions_with_answers = extract_questions(args.path)

    vk_session = vk.VkApi(token=vk_bot_token)
    vk_api = vk_session.get_api()

    print('Бот запущен')

    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        try:
            if event.type != VkEventType.MESSAGE_NEW or not event.to_me:
                continue

            user_id = event.user_id
            message_text = event.text.lower()

            if message_text == '/start' or message_text == 'start':
                handle_message_start(user_id, vk_api)

            elif message_text == 'новый вопрос':
                handle_new_question_request(user_id, vk_api, questions_with_answers)

            elif message_text == 'да':
                repeat_question_request(user_id, vk_api)

            elif message_text == 'нет':
                handle_give_up(user_id, vk_api, questions_with_answers)

            elif message_text:
                handle_solution_attempt(user_id, message_text, vk_api, questions_with_answers)

        except Exception as e:
            traceback_lines = traceback.format_exception(None, e, e.__traceback__)
            error_report = ''.join(traceback_lines)
            vk_api.messages.send(
                user_id=admin_id,
                message=f'Ошибка:\n{error_report}',
                random_id=random.randint(1,1000)
            )
                

if __name__ == "__main__":
    main()
    