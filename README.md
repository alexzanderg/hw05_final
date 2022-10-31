# Yatube

![](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green)

Yatube - веб-приложение для публикации и просмотра постов пользователей, поддерживающий следующий функционал:
- регистрация и авторизация пользователей
- публикация и комментирование постов
- подписка на других авторов

## Установка

Клонировать репозиторий и перейти в него в командной строке:
```
git clone git@github.com:alexzanderg/hw05_final.git
```
```
cd hw05_final
```
Cоздать и активировать виртуальное окружение:
```
python3 -m venv env
source env/bin/activate
```

Установить зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```

Выполнить миграции:
```
python3 manage.py migrate
```
Запустить проект:
```
python3 manage.py runserver
```
