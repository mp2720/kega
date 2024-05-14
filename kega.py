#!/usr/bin/python3

import argparse
import requests
import random
import sys
import os

KEGE_API_URI='https://kompege.ru/api/v1'

ap = argparse.ArgumentParser(prog="dokega")
ap.add_argument('kim', help='Номер КИМ')
ap.add_argument('-t', action='store', dest='token', help='Токен авторизации. Если не указан, то берётся из $KEGE_TOKEN, ~/.kege-token или stdin')
ap.add_argument('-s', action='store_true', dest='dont_send', help='Вывести ответы в stdout и не отправлять их на кегу')
ap.add_argument('-m', action='store', dest='mistakes', help='Список заданий, к которым будет отправлен ответ с ошибкой')
ap.add_argument('-e', action='store', dest='empty', help='Список заданий, к которым будет отправлен пустой ответ')
ap.add_argument('-y', action='store_true', dest='confirm_send', help='Отправить ответы без подтверждения')
ap.add_argument('-H', action='store', dest='hours', help='Часы "выполнения" работы (можно опустить, если указаны -M или -s)')
ap.add_argument('-M', action='store', dest='minutes', help='Минуты "выполнения" работы (можно опустить, если указаны -H или -s)')

args = ap.parse_args()

if args.hours is None and args.minutes is None and not args.dont_send:
    print('Нужно указать время выполнения работы в часах и/или минутах', file=sys.stderr)
    exit(1)

args.hours = int(args.hours) if args.hours is not None else 0
args.minutes = int(args.minutes) if args.minutes is not None else 0
duration = (int(args.hours) * 3600 + int(args.minutes) * 60) * 1000

if args.token is None:
    try:
        env = os.environ.get("KEGE_TOKEN")
        if env is not None:
            args.token = env
        else:
            token_file = open(os.path.expanduser('~/.kege-token'))
            args.token = token_file.read().strip(' \t\n\r')
    except:
        args.token = input('Введите токен авторизации: ').strip()

if args.mistakes is not None:
    args.mistakes = list(map(lambda x: int(x.strip()), args.mistakes.split(',')))
else:
    args.mistakes = []

if args.empty is not None:
    args.empty = list(map(lambda x: int(x.strip()), args.empty.split(',')))
else:
    args.empty = []

with requests.get(
    f'{KEGE_API_URI}/result/kim/{args.kim}/user_id',
    headers={
        'Authorization': f'Bearer {args.token}'
    }
) as r:
    assert 200 <= r.status_code < 300, f'HTTP код {r.status_code}'
    kim_data = r.json()

if kim_data is None:
    with requests.get(
        f'{KEGE_API_URI}/variant/kim/{args.kim}',
        headers={
            'Authorization': f'Bearer {args.token}'
        }
    ) as r:
        assert 200 <= r.status_code < 300, f'HTTP код {r.status_code}'
        kim_data = r.json()
        kim_id = None
        kim_tasks = kim_data['tasks']
else:
    kim_id = kim_data['id']
    kim_tasks = kim_data['result']


def convert_score(primary_score: int, max_primary_score: int):
    score_tab= {
        0: 0,
        1: 8,
        2: 15,
        3: 22,
        4: 29,
        5: 37,
        6: 43,
        7: 46,
        8: 48,
        9: 50,
        10: 53,
        11: 55,
        12: 57,
        13: 60,
        14: 62,
        15: 65,
        16: 67,
        17: 69,
        18: 71,
        19: 74,
        20: 76,
        21: 78,
        22: 81,
        23: 84,
        24: 85,
        25: 88,
        26: 90,
        27: 93,
        28: 95,
        29: 100
    }
    return score_tab[min(round(primary_score/max_primary_score * 29), 29)]


if args.dont_send:
    for task in kim_tasks:
        text = str(task['number'])
        if 'taskId' in task:
            text += f' ({task["taskId"]})'
        key = str(task['key']).replace('\\n', '\n')
        text += f': {key}'

        print(text)
    exit()

result = []

primary_score = 0
max_primary_score = 0
for task in kim_tasks:
    # print(task)
    task_result = {
        'key': task['key'],
        'number': task['number'],
        'taskId': task['taskId'] if 'taskId' in task else 0
    }
    if task['number'] in args.empty:
        task_result['score'] = 0
        task_result['answer'] = ''

        del args.empty[args.empty.index(task['number'])]
    elif task['number'] in args.mistakes:
        task_result['score'] = 0

        if task['number'] == 2:
            ans = list('wxyz')
            random.shuffle(ans)
            ans = ''.join(ans)
        elif task['number'] in (20, 21):
            ans = f'{random.randint(1, 30)} {random.randint(1, 30)}'
        elif task['number'] in (26, 27):
            ans = f'{random.randint(1000, 10000)} {random.randint(1_000_000, 100_000_000)}'
        elif task['number'] == 25:
            ans = '\n'.join([f'{random.randint(100000, 1000000)} {random.randint(1000, 10000)}' for _ in range(10)])
        else:
            ans = str(random.randint(0, 1000))

        task_result['answer'] = ans

        del args.mistakes[args.mistakes.index(task['number'])]
    else:
        task_result['score'] = 2 if task['number'] in (26, 27) else 1
        task_result['answer'] = task['key']

    result.append(task_result)
    primary_score += task_result['score']
    max_primary_score += 2 if task['number'] in (26, 27) else 1

secondary_score = convert_score(primary_score, max_primary_score)

print(f'Первичный балл: {primary_score}, тестовый балл: {secondary_score}')
print(f'Время выполнения: {duration} мс')

if kim_id is not None:
    print('Ответы на КИМ будет перезаписаны')

if not args.confirm_send:
    t = input('Продолжить (y/n)? ')
    if not t.lower().strip().startswith('y'):
        exit()

headers = {'Authorization': f'Bearer {args.token}'}
payload = {
    'duration': duration,
    'kim': args.kim,
    'primary_score': primary_score,
    'secondary_score': secondary_score,
    'result': result
}

if kim_id is not None:
    r = requests.put(f'{KEGE_API_URI}/result/{kim_data["id"]}', headers=headers, json=payload)
else:
    r = requests.post(f'{KEGE_API_URI}/result', headers=headers, json=payload)

assert 200 <= r.status_code < 300, f'HTTP код {r.status_code}'
