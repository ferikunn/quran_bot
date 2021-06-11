#!./venv/bin/python3.8
import telebot
from telebot import types
import requests
import time
import json
import os

TOKEN = ""
BOT = telebot.TeleBot(TOKEN)

PAGES_URL = "http://mp3quran.net/api/quran_pages_arabic/"
with open('./messages.json', 'r') as j:
    messages = json.load(j)


def get_page(page_number, is_start):
    page_number = page_number if page_number > 1 and page_number < 604 else 604 if page_number < 1 else 1
    page_number = f"{'00' if page_number < 10 else '0' if page_number < 100 else ''}{page_number}"
    page_url = f"{PAGES_URL}{page_number}.png"
    binary_page = requests.get(page_url).content if not is_start else None
    file_name = f"{page_number}.jpg" if binary_page else "./img/start_img.jpg"
    if binary_page:
        with open(file_name, 'wb') as f:
            f.write(binary_page)
    return int(page_number), file_name

def send_page(call ,page_number:int, is_start=False):
    is_call = call.__class__ == types.CallbackQuery
    user_id = call.from_user.id
    first_name = call.from_user.first_name
    chat_id = call.message.chat.id if is_call else call.chat.id
    message_id = call.message.id if is_call else call.id
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton
    page_number, file_name= get_page(page_number, is_start)
    next_button = button(text="▶️الصفحة التالية", callback_data=f"{page_number + 1} {user_id} {first_name}")
    back_button = button(text="◀️الصفحة السابقة", callback_data=f"{page_number - 1} {user_id} {first_name}")
    start_button = button(text="فتح المصحف 🕋", callback_data=f"{1} {user_id} {first_name}")
    buttons_list = [start_button] if is_start else [back_button, next_button]
    markup.add(*buttons_list)
    with open(file_name, 'rb') as page:
        if is_start or not is_call:
            BOT.send_photo(chat_id, page,
                            reply_to_message_id=message_id,reply_markup=markup,
                                caption=messages.get('start') if  is_start else None)
        else:
            BOT.edit_message_media(types.InputMediaPhoto(page), chat_id, message_id, 
                                        reply_markup=markup)
    if not is_start:
        os.remove(file_name)


@BOT.message_handler(func=lambda msg: msg.text)
def command_handler(message):
    text = str(message.text)
    s_text = text.split()
    if text.startswith(('/start', 'فتح القران')):
        send_page(message, 1, is_start=text != "فتح القران")
    elif text.startswith('/help'):
        BOT.reply_to(message, messages.get('help'))
    elif text.startswith('فتح صفحة'):
            if len(s_text) > 2 and s_text[2].isnumeric():
                page_number = int(s_text[2])
                if page_number > 0 and page_number < 604:
                    send_page(message, page_number)
                else:
                    BOT.reply_to(message, "عدد صفحات القران 604")
            else:
                BOT.reply_to(message, "الرجاء ادخال رقم الصفحة مثال:\nفتح صفحة 10")
    elif text in ['سورس', 'السورس']:
        BOT.reply_to(message, "https://github.com/Awiteb/quran_bot")

@BOT.callback_query_handler(func=lambda call:True)
def query_handler(call):
    page_number, user_id, first_name = call.data.split(maxsplit=3)
    requester = call.from_user.id
    if int(user_id) == requester:
        send_page(call, int(page_number))
    else:
        BOT.answer_callback_query(call.id, f"هذا المصحف خاص بـ {first_name}")


while True:
    print(f"Start")
    try:
        BOT.polling(none_stop=True, interval=0, timeout=0)
    except Exception as e:
        print(e)
        time.sleep(10)
