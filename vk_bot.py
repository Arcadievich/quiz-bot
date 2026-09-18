import os
import re
import random
from time import sleep

import redis
from dotenv import load_dotenv
import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from quiz_parser import extract_questions


redis_db = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True,
)


def make_raw_answer(text):
    if not text:
        return ""

    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"\[[^\]]*\]", " ", text)
    text = re.sub(r"\{[^}]*\}", " ", text)

    text = text.split(".")[0]

    text = text.lower()

    text = text.replace("ё", "е")

    text = re.sub(r"[^\w\s\-]", " ", text, flags=re.UNICODE)

    text = re.sub(r"\s+", " ", text).strip()

    return text


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


def handle_new_question_request(user_id, vk_api):
    questions = extract_questions('1vs1200.txt')
    question = random.choice(list(questions.keys()))

    redis_db.set(str(user_id), question, ex=3600)

    vk_api.messages.send(
        user_id=user_id,
        message=question,
        random_id=random.randint(1,1000)
    )


def handle_solution_attempt(user_id, message_text, vk_api):
    all_questions = extract_questions('1vs1200.txt')
    asked_question = redis_db.get(str(user_id))

    if not asked_question:
        print(f"User's answer with id {user_id} not found")

    correct_answer = all_questions.get(asked_question)
    print(correct_answer)

    user_answer_raw = make_raw_answer(message_text)
    correct_answer_raw = make_raw_answer(correct_answer)

    print(f'\nUser answer raw: {user_answer_raw}')
    print(f'Current answer raw: {correct_answer_raw}')

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


def handle_give_up(user_id, vk_api):
    asked_question = redis_db.get(str(user_id))

    all_questions = extract_questions('1vs1200.txt')

    correct_answer = all_questions.get(asked_question)

    vk_api.messages.send(
        user_id=user_id,
        message=f'Правильный ответ: {correct_answer}',
        random_id=random.randint(1,1000)
    )

    redis_db.delete(str(user_id))

    sleep(3)

    handle_new_question_request(user_id, vk_api)


def main():
    load_dotenv()
    vk_bot_token = os.environ['VK_BOT_TOKEN']

    vk_session = vk.VkApi(token=vk_bot_token)
    vk_api = vk_session.get_api()

    print('Бот запущен')

    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = event.user_id
            message_text = event.text.lower()

            if message_text == '/start' or message_text == 'start':
                handle_message_start(user_id, vk_api)

            elif message_text == 'новый вопрос':
                handle_new_question_request(user_id, vk_api)

            elif message_text == 'да':
                repeat_question_request(user_id, vk_api)

            elif message_text == 'нет':
                handle_give_up(user_id, vk_api)

            elif message_text:
                handle_solution_attempt(user_id, message_text, vk_api)
                

if __name__ == "__main__":
    main()