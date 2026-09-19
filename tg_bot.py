import os
import random
import asyncio
import traceback
import argparse
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
from quiz_parser import make_raw_answer


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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Здравствуйте',
        reply_markup=start_keyboard_markup,
    )

    return State.CHOOSING


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    traceback_lines = traceback.format_exception(None, context.error, context.error.__traceback__)
    error_report = ''.join(traceback_lines)

    await context.bot.send_message(
        chat_id=context.bot_data['admin_id'],
        text=f'Ошибка:\n{error_report}'
    )


async def handle_new_question_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    question = random.choice(list(context.bot_data['questions_with_answers'].keys()))

    await redis_db.set(str(user_id), question, ex=3600)

    await update.message.reply_text(
        question,
        reply_markup=ReplyKeyboardRemove()
    )

    return State.ANSWERING


async def handle_solution_attempt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    asked_question = await redis_db.get(str(user_id))

    if not asked_question:
        print(f"User's answer with id {user_id} not found")

    correct_answer = context.bot_data['questions_with_answers'].get(asked_question)

    user_answer_raw = make_raw_answer(user_text)
    correct_answer_raw = make_raw_answer(correct_answer)

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

    correct_answer =  context.bot_data['questions_with_answers'].get(asked_question)

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
    admin_id = os.environ['TG_ADMIN_ID']

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

    application = (
        Application.builder()
        .token(bot_token)
        .connect_timeout(15.0)
        .read_timeout(15.0)
        .write_timeout(15.0)
        .build()
    )

    application.bot_data['admin_id'] = admin_id
    application.bot_data['questions_with_answers'] = questions_with_answers

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

    application.add_error_handler(error_handler)

    application.post_shutdown = on_shutdown

    print('Бот запущен.')
    application.run_polling()


if __name__=='__main__':
    main()