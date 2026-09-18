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

    result = {}

    for pair in text:
        for match in pattern.finditer(pair):
            question = " ".join(match['q'].split())
            answer   = " ".join(match['a'].split())
            result[question] = answer

    return result


def main():
    questions_with_answers = {}

    files_names = os.listdir('./quiz_questions')

    for file_name in files_names:
        records = extract_questions(file_name)
        questions_with_answers.update(records)

    with open('questions_with_answers.json', 'w', encoding='utf-8') as file:
        json.dump(questions_with_answers, file, ensure_ascii=False, indent=4)


if __name__=='__main__':
    main()