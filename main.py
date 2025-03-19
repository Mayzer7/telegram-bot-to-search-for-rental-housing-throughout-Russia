import telebot
from telebot import types

API_TOKEN = 'API_TOKEN_KEY' 
bot = telebot.TeleBot(API_TOKEN)

# Словарь для хранения параметров пользователей
user_data = {}

# Список городов и их идентификаторов для Cian
CITIES = {
    'Нижний Новгород': 4885,
    'Москва': 1,
    'Санкт-Петербург': 2,
    'Казань': 3,
    'Екатеринбург': 4,
    'Новосибирск': 5,
    'Краснодар': 6,
    'Самара': 7,
    'Ростов-на-Дону': 8,
    'Уфа': 9,
    'Челябинск': 10,
    'Воронеж': 11,
    'Томск': 12,
    'Пермь': 13,
}

# Начало общения с ботом
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Я помогу подобрать аренду квартиры. Укажи город.")
    bot.send_message(message.chat.id, "Вот доступные города: " + ", ".join(CITIES.keys()))
    bot.register_next_step_handler(message, ask_city)

# Функция для запроса города
def ask_city(message):
    city = message.text.strip()
    if city not in CITIES:
        bot.send_message(message.chat.id, "Извините, я не знаю такой город. Попробуйте выбрать один из доступных.")
        bot.register_next_step_handler(message, ask_city)  # Повторяем запрос
        return
    user_data['city'] = city
    bot.send_message(message.chat.id, f"Вы выбрали город: {city}. Теперь укажите параметры для поиска.")
    ask_rooms(message)

# Функция для запроса количества комнат
def ask_rooms(message):
    markup = types.InlineKeyboardMarkup()
    for i in range(1, 11):  # Кнопки от 1 до 10 комнат
        markup.add(types.InlineKeyboardButton(text=str(i), callback_data=f'rooms_{i}'))
    
    bot.send_message(message.chat.id, "Выберите количество комнат:", reply_markup=markup)

# Обработка выбора количества комнат
@bot.callback_query_handler(func=lambda call: call.data.startswith('rooms_'))
def handle_rooms(call):
    rooms = int(call.data.split('_')[1])
    user_data['rooms'] = rooms
    bot.send_message(call.message.chat.id, f"Вы выбрали {rooms} комнат.")
    ask_property_type(call.message)

# Функция для запроса типа жилья
def ask_property_type(message):
    markup = types.InlineKeyboardMarkup()
    property_types = [
        ('Квартира', 'flat'),
        ('Комната', 'room'),
        ('Койко-место', 'place'),
        ('Дом/дача', 'house'),
        ('Часть дома', 'part_house'),
        ('Таунхаус', 'townhouse'),
        ('Гараж', 'garage')
    ]
    for name, value in property_types:
        markup.add(types.InlineKeyboardButton(text=name, callback_data=f'type_{value}'))
    
    bot.send_message(message.chat.id, "Выберите тип жилья:", reply_markup=markup)

# Обработка выбора типа жилья
@bot.callback_query_handler(func=lambda call: call.data.startswith('type_'))
def handle_property_type(call):
    property_type = call.data.split('_')[1]
    user_data['property_type'] = property_type
    ask_price_range(call.message)

# Функция для запроса минимальной цены
def ask_price_range(message):
    bot.send_message(message.chat.id, "Введите минимальную цену:")
    bot.register_next_step_handler(message, handle_min_price_input)

# Обработка минимальной цены
def handle_min_price_input(message):
    try:
        min_price = int(message.text.strip())
        if min_price < 0:
            raise ValueError("Цена не может быть отрицательной.")
        user_data['min_price'] = min_price
        bot.send_message(message.chat.id, "Введите максимальную цену:")
        bot.register_next_step_handler(message, handle_max_price_input)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректную минимальную цену (целое положительное число).")
        bot.register_next_step_handler(message, handle_min_price_input)

# Обработка максимальной цены
def handle_max_price_input(message):
    try:
        max_price = int(message.text.strip())
        if max_price < 0:
            raise ValueError("Цена не может быть отрицательной.")
        user_data['max_price'] = max_price
        bot.send_message(message.chat.id, "Спасибо за информацию! Я найду квартиру, подходящую под эти параметры.")
        find_apartment(message)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректную максимальную цену (целое положительное число).")
        bot.register_next_step_handler(message, handle_max_price_input)

# Функция для генерации ссылки на Cian для аренды
def generate_cian_url():
    city = user_data.get('city', '')
    region_id = CITIES.get(city, '4885')  # Нижний Новгород по умолчанию
    min_price = user_data.get('min_price', '0')
    max_price = user_data.get('max_price', '1000000')
    rooms_count = user_data.get('rooms', 1)
    property_type = user_data.get('property_type', 'flat')  # Тип жилья по умолчанию - квартира

    # Формируем URL с параметрами для аренды
    room_params = ""
    for i in range(1, rooms_count + 1):
        room_params += f"room{i}=1&"
    
    url = (f"https://{city.lower()}.cian.ru/cat.php?currency=2&deal_type=rent&engine_version=2"
           f"&maxprice={max_price}&minprice={min_price}&offer_type=flat&region={region_id}"
           f"&{room_params}type={property_type}")
    
    return url

# Функция для поиска квартиры и отправки ссылки
def find_apartment(message):
    # Генерируем ссылку
    cian_url = generate_cian_url()
    
    # Отправляем ссылку пользователю
    bot.send_message(message.chat.id, f"Вот ссылка на аренду квартир, подходящих под ваш запрос: {cian_url}")
    
    # Спрашиваем, хочет ли пользователь продолжить поиск
    ask_repeat(message)

# Функция для повторного поиска квартиры
def ask_repeat(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("Да, найти еще", "Нет, я закончил")
    bot.send_message(message.chat.id, "Хотите найти еще квартиру?", reply_markup=markup)
    bot.register_next_step_handler(message, handle_repeat)

# Обработка ответа на повторный запрос
def handle_repeat(message):
    if message.text == "Да, найти еще":
        # Сбросим данные пользователя и начнем новый поиск
        user_data.clear()
        bot.send_message(message.chat.id, "Давайте начнем заново. Укажите город.")
        bot.register_next_step_handler(message, ask_city)
    elif message.text == "Нет, я закончил":
        bot.send_message(message.chat.id, "Спасибо за использование бота! Если понадобится помощь, всегда рад помочь.")
    else:
        bot.send_message(message.chat.id, "Пожалуйста, выберите 'Да, найти еще' или 'Нет, я закончил'.")
        bot.register_next_step_handler(message, handle_repeat)

# Запуск бота
bot.polling(none_stop=True)