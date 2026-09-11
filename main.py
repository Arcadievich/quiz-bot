import re


def main():
    with open('quiz_questions/1vs1200.txt', 'r', encoding='KOI8-R') as file:
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

    for question, answer in result.items():
        print(f'\nВопрос:\n{question}')
        print(f'\nОтвет:\n{answer}')


if __name__=='__main__':
    main()