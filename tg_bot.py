import os
import random
import re
import asyncio
from enum import Enum, auto

import redis.asyncio as redis
from dotenv import load_dotenv
from telegram import Update
from telegram import ReplyKeyboardMarkup
from telegram import ReplyKeyboardRemove
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

from quiz_parser import extract_questions


start_keyboard = [['Новый вопрос', 'Мой счет']]

retry_keyboard = [
    ['Да', 'Нет'],
    ['Сдаться'],
]

start_keyboard_markup = ReplyKeyboardMarkup(start_keyboard, resize_keyboard=True)
retry_keyboard_markup = ReplyKeyboardMarkup(retry_keyboard, resize_keyboard=True)

redis_db = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True,
)


class State(Enum):
    CHOOSING = auto()
    ANSWERING = auto()
    RETRY = auto()


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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Здравствуйте',
        reply_markup=start_keyboard_markup,
    )

    return State.CHOOSING


async def handle_new_question_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    questions = extract_questions('1vs1200.txt')
    question = random.choice(list(questions.keys()))

    await redis_db.set(str(user_id), question, ex=3600)

    await update.message.reply_text(
        question,
        reply_markup=ReplyKeyboardRemove()
    )

    return State.ANSWERING


async def handle_solution_attempt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    all_questions = extract_questions('1vs1200.txt')

    asked_question = await redis_db.get(str(user_id))

    if not asked_question:
        print(f"User's answer with id {user_id} not found")

    correct_answer = all_questions.get(asked_question)
    print(correct_answer)

    user_answer_raw = make_raw_answer(user_text)
    correct_answer_raw = make_raw_answer(correct_answer)
    print(f'\nUser answer raw: {user_answer_raw}')
    print(f'Current answer raw: {correct_answer_raw}')

    if user_answer_raw == correct_answer_raw:
        await update.message.reply_text(
            'Правильный ответ!',
            reply_markup=start_keyboard_markup,
        )

        await redis_db.delete(str(user_id))

        return State.CHOOSING
    
    else:
        await update.message.reply_text('Ответ неверный...')

        await asyncio.sleep(3)

        await update.message.reply_text(
            'Пропробуете еще раз?',
            reply_markup=retry_keyboard_markup,
        )

        return State.RETRY


async def repeat_question_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    question = await redis_db.get(str(user_id))

    if not question:
        print(f"User's answer with id {user_id} not found")

    await update.message.reply_text(
        question,
        reply_markup=ReplyKeyboardRemove()
    )

    return State.ANSWERING


async def handle_give_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    asked_question = await redis_db.get(str(user_id))

    all_questions = extract_questions('1vs1200.txt')

    correct_answer =  all_questions.get(asked_question)

    await update.message.reply_text(
        f'Правильный ответ: {correct_answer}',
        reply_markup=ReplyKeyboardRemove()
    )

    await redis_db.delete(str(user_id))

    await asyncio.sleep(3)

    await handle_new_question_request(update, context)

    return State.ANSWERING


async def on_shutdown(application):

    await redis_db.aclose()


def main():
    load_dotenv()
    bot_token = os.environ['TG_BOT_TOKEN']

    application = (
        Application.builder()
        .token(bot_token)
        .connect_timeout(15.0)
        .read_timeout(15.0)
        .write_timeout(15.0)
        .build()
    )

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            State.CHOOSING: [
                MessageHandler(filters.Text(['Новый вопрос']), handle_new_question_request),
                MessageHandler(filters.Text(['Мой счет']), start),
            ],
            State.ANSWERING: [
                MessageHandler(filters.TEXT, handle_solution_attempt),
            ],
            State.RETRY: [
                MessageHandler(filters.Text(['Да']), repeat_question_request),
                MessageHandler(filters.Text(['Нет']), start),
                MessageHandler(filters.Text(['Сдаться']), handle_give_up),
            ]
        },

        fallbacks=[]
    )

    application.add_handler(conversation_handler)

    application.post_shutdown = on_shutdown

    print('Бот запущен.')
    application.run_polling()


if __name__=='__main__':
    main()