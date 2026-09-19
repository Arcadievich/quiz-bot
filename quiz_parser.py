import re
import os
import json


def extract_questions(path):
    with open(f'quiz_questions/{path}', 'r', encoding='KOI8-R') as file:
        questions_file = file.read()

    text = questions_file.split('\n\n\n')

    pattern = re.compile(
        r'Вопрос\s+\d+\s*:\s*\n'
        r'(?P<q>.*?)\n'
        r'\s*Ответ\s*:\s*\n'
        r'(?P<a>.*?)'
        r'(?=\n\s*\n\s*Автор\s*:|\n\s*\n\s*Источник\s*:|\nВопрос\s+\d+\s*:|\Z)',
        re.DOTALL
    )

    questions_and_answers = {}

    for pair in text:
        for match in pattern.finditer(pair):
            question = " ".join(match['q'].split())
            answer   = " ".join(match['a'].split())
            questions_and_answers[question] = answer

    return questions_and_answers


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