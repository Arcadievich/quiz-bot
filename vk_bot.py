import os
import random

from dotenv import load_dotenv
import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType


def echo(event, vk_api):
    vk_api.messages.send(
        user_id=event.user_id,
        message=event.text,
        random_id=random.randint(1,1000)
    )


def main():
    load_dotenv()
    vk_bot_token = os.environ['VK_BOT_TOKEN']

    vk_session = vk.VkApi(token=vk_bot_token)
    vk_api = vk_session.get_api()

    print('Бот запущен')

    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            echo(event, vk_api)


if __name__ == "__main__":
    main()