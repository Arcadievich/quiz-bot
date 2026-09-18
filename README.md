# Бот для викторины в Telegram и VK

Данный проект создан для проведения викторин посредством взаимодействия с ботами в Telegram и ВКонтакте.


## Установка

Установите пакетный менеджер `uv`:

Команда для Linux:
```bash
sudo snap install astral-uv --classic
```
или
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Команда для Windows:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Скачайте данный [репозиторий](https://github.com/Arcadievich/chat-bot-3/archive/refs/heads/main.zip)

Чтобы скачать зависимости и создать виртуальную среду используйте следующую команду внутри папки с репозиторием:

```bash
uv sync
```

Установите [Docker](https://www.docker.com) в вашу операционную систему

Запустите базу данных на Redis командой:

```bash
docker run -d \
  --name redis-rdb \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:latest \
  redis-server --save 60 1
```

Или в одну строку:

```powershell
docker run -d --name redis-rdb -p 6379:6379 -v redis-data:/data redis:latest redis-server --save 60 1
```

В папке репозитория создайте `.env` файл и укажите в нем следующие переменные:
- `TG_BOT_TOKEN` - токен вашего Telegram-бота, который можно получить, создав бота через [BotFather](https://web.telegram.org/k/#@BotFather)
- `VK_BOT_TOKEN` - API токен вашего бота во ВКонтакте. Бот создается вместе с [Сообществом](https://vk.ru/groups), затем нужно открыть вкладку `Управление` -> `Дополнительно` -> `Работа с API` в правом меню на главной странице сообщества
- `TG_ADMIN_ID` - ID пользователя в Telegram, которому должны приходить сообщения об ошибках
- `VK_ADMIN_ID` - ID пользователя ВКонтакте, которому должны приходить сообщения об ошибках


## Ссылки на ботов

Telegram Bot

[![Telegram Bot](https://img.shields.io/badge/Telegram-@training_second_bot-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/training_second_bot)

Бот в ВКонтакте

[![VK Community](https://img.shields.io/badge/VK-Сообщество_бота-0077FF?style=for-the-badge&logo=vk&logoColor=white)](https://vk.ru/club240711385)


### Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org).