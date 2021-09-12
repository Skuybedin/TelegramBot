import telebot
import time
from data import *
from graphs import *
from connect import *
from datetime import datetime
from telebot import types
from telebot.types import InputMediaPhoto, InputMediaDocument

bot = telebot.TeleBot(token)

#Подключение к базе данных
db = connection

cursor = db.cursor()

#Команда очистки даты
@bot.message_handler(commands=['clear'])
def clear_dict(message):
    user_id = message.from_user.id
    if check_rights(user_id):
        clear()
        bot.send_message(message.chat.id, f"Мусор удален")
        logger.info(f"{user_id} - Мусор удален")
        send_welcome(message)
    else:
        bot.send_message(message.chat.id, f"У вас нет прав на использование этой команды")
        logger.error(f"{user_id} - пытался очистить мусор")
        send_welcome(message)

#Рассылка сообщений по базе
@bot.message_handler(commands=["send"])
def answer(message):
    user_id = message.from_user.id
    if (user_id == 413666238):
        newsletter = message.text.split(maxsplit=1)[1]
        cursor.execute("SELECT telegram_id FROM users")
        allusers = cursor.fetchall()
        for i in range(len(allusers)):
            try:
                if i % 20 == 0:
                    time.sleep(1)
                bot.send_message(allusers[i][0], newsletter)
                logger.success(f"{i+1}) Сообщение ('{newsletter}') успешно отправлено пользователю {allusers[i][0]}")
            except:
                continue
        send_welcome(message)
    else:
        bot.send_message(message.chat.id, f"У вас нет прав на использование этой команды")
        logger.error(f"{user_id} - пытался отправить рассылку от имени бота ('{message.text.split(maxsplit=1)}')")
        send_welcome(message)

#Выдача прав начало
@bot.message_handler(commands=['give'])
def give_rights(message):
    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    user_id = message.from_user.id
    cursor.execute(f"SELECT telegram_id,name FROM users")
    result = cursor.fetchall()
    if check_rights(user_id):
        for i, value in enumerate(result, 1):
            reply_markup.add(types.KeyboardButton(f'{str(value[0])}' + f' ({str(value[1][0].upper()) + str(value[1][1:])})'))
        msg = bot.send_message(message.chat.id, f"Выберите пользователя", reply_markup=reply_markup)
        bot.register_next_step_handler(msg, give_rights_final)
    else:
        bot.send_message(message.chat.id, f"У вас нет прав на использование этой команды")
        logger.error(f"{user_id} - пытался вызвать админ меню")
        send_welcome(message)

def give_rights_final(message):
    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    user_id = message.from_user.id
    splitted_text = message.text.lower().split(' ')
    user_data[user_id] = splitted_text[0]
    item_admin = types.KeyboardButton('Администрация')
    item_user = types.KeyboardButton('Пользователь')
    reply_markup.add(item_admin, item_user)
    msg = bot.send_message(message.chat.id, f"Выберите группу для пользователя {splitted_text[0]}", reply_markup=reply_markup)
    bot.register_next_step_handler(msg, give_rights_complete)

def give_rights_complete(message):
    user_id = message.from_user.id
    cursor.execute(f"UPDATE users SET status='{group_dict[message.text.lower()]}' WHERE telegram_id={user_data[user_id]}")
    db.commit()
    bot.send_message(message.chat.id, f"Пользователь {user_data[user_id]} добавлен в группу {group_dict[message.text.lower()]}")
    logger.success(f"{user_id} - изменил статус пользователя {user_data[user_id]} на {group_dict[message.text.lower()]}")
    send_welcome(message)
#Выдача прав конец

#Стартовое меню
@bot.message_handler(commands=['start', 'info'])
def reg_user(message):
    complete = True
    user_id = message.from_user.id
    cursor.execute(f"SELECT telegram_id FROM users")
    result = cursor.fetchall()
    for each in result:
        if user_id == each[0]:
            complete = False
    bot.send_message(message.chat.id, f"Здравствуйте!\nЧтобы начать пользоваться ботом - выберите нужный пункт в меню\n{'Чтобы зарегистрироваться введите /reg' if complete else 'Чтобы сменить имя введите /name'}")
    send_welcome(message)

#Начало регистрации
@bot.message_handler(commands=['reg'])
def start_registr(message):
    complete = True
    user_id = message.from_user.id
    cursor.execute(f"SELECT telegram_id FROM users")
    result = cursor.fetchall()
    for each in result:
        if user_id == each[0]:
            complete = False
    if complete:
        msg = bot.send_message(message.chat.id, f"Введите имя")
        bot.register_next_step_handler(msg, input_name)
    else:
        bot.send_message(message.chat.id, f"{get_name(user_id)}, вы уже зарегистрированы")
        logger.error(f"{user_id} - пытался повторно зарегистрироваться")

def input_name(message):
    complete = True
    user_id = message.from_user.id
    users[user_id] = message.text
    cursor.execute(f"SELECT telegram_id FROM users")
    result = cursor.fetchall()

    for each in result:
        if user_id == each[0]:
            complete = False
    if complete:
        if users[user_id].isdigit():
            bot.send_message(message.chat.id, f"Имя должно содержать только буквы")
            logger.error(f"({user_id}) - пытался ввести цифры в имя")
            send_welcome(message)
        elif users[user_id].isalpha():
            cursor.execute(f"INSERT INTO users (date, time, telegram_id, name, status) VALUES (CURDATE(), CURTIME(), {user_id}, '{users[user_id]}', 'user')")
            db.commit()
            bot.send_message(message.chat.id, f"{message.text}, регистрация прошла успешно")
            logger.success(f"{users[user_id]} ({user_id}) - добавлен в базу users")
            send_welcome(message)
        else:
            bot.send_message(message.chat.id, f"Имя должно содержать только буквы")
            logger.error(f"({user_id}) - пытался ввести символы в имя")
            send_welcome(message)
    else:
        bot.send_message(message.chat.id, f"{get_name(user_id)}, вы уже зарегистрированы")
        logger.error(f"{get_name(user_id)} ({user_id}) - пытался повторно зарегистрироваться")
        send_welcome(message)
#Конец регистрации

#Начало смены имени
@bot.message_handler(commands=['name'])
def change_name(message):
    user_id = message.from_user.id
    if is_registred(user_id):
        msg = bot.send_message(message.chat.id, f"Введите желаемое имя")
        bot.register_next_step_handler(msg, change_name_final)
    else:
        bot.send_message(message.chat.id, f"Сначала зарегистрируйтесь, чтобы изменить имя")
        logger.error(f"({user_id}) - пытался сменить имя будучи незарегистрированным")
        send_welcome(message)

def change_name_final(message):
    user_id = message.from_user.id
    cursor.execute(f"SELECT name FROM users WHERE telegram_id={user_id}")
    result = cursor.fetchone()
    person_clear(user_id)
    users[user_id] = message.text
    if users[user_id].isdigit():
        bot.send_message(message.chat.id, f"Имя должно содержать только буквы")
        logger.error(f"({user_id}) - пытался ввести цифры в имя")
        send_welcome(message)
    elif users[user_id] == result[0]:
        bot.send_message(message.chat.id, f"Новое имя не должно совпадать с текущим")
        logger.error(f"({user_id}) - изменить имя на текущее")
        send_welcome(message)
    elif users[user_id].isalpha():
        cursor.execute(f"UPDATE users SET name='{users[user_id]}' WHERE telegram_id={user_id}")
        db.commit()
        bot.send_message(message.chat.id, f"{result[0]}, имя успешно изменено на {message.text}")
        logger.success(f"{result[0]} ({user_id}) - изменил имя на {message.text}")
        send_welcome(message)
    else:
        bot.send_message(message.chat.id, f"Имя должно содержать только буквы")
        logger.error(f"({user_id}) - пытался ввести символы в имя")
        send_welcome(message)
#Конец смены имени

#Команда обновить
@bot.message_handler(commands=['update'])
def update_func(message):
    user_id = message.from_user.id
    if check_rights(user_id):
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {months[current_month]}_costs (id INT AUTO_INCREMENT PRIMARY KEY, date DATE, time TIME, telegram_id INT, type VARCHAR(255), value INT)")
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {months[current_month]}_salary (id INT AUTO_INCREMENT PRIMARY KEY, date DATE, time TIME, telegram_id INT, type VARCHAR(255), value INT)")
        bot.send_message(message.chat.id, f"Запрос на создание таблицы '{months[current_month]}_costs' и '{months[current_month]}_salary' отправлен")
        logger.info(f"({user_id}) отправил запрос на создание таблицы '{months[current_month]}_costs' и '{months[current_month]}_salary'")
        send_welcome(message)
    else:
        bot.send_message(message.chat.id, f"У вас нет прав на использование этой команды")
        logger.error(f"{user_id} - пытался обновить таблицы")
        send_welcome(message)

#Главное меню начало
@bot.message_handler(content_types=['text'])
def send_welcome(message):
        user_id = message.from_user.id
        markup_reply = types.InlineKeyboardMarkup()
        item_add = types.InlineKeyboardButton(text='Добавить', callback_data='add')
        item_edit = types.InlineKeyboardButton(text='Изменить', callback_data='edit')
        item_remove = types.InlineKeyboardButton(text='Удалить', callback_data='remove')
        item_total = types.InlineKeyboardButton(text='Выписка', callback_data='total')
        markup_reply.add(item_add, item_edit, item_remove, item_total)
        bot.send_message(message.chat.id, f"Выберите подходящее действие:", reply_markup=markup_reply)
        person_clear(user_id)
#Главное меню конец

#Команды главного меню начало
@bot.callback_query_handler(func = lambda call: True)
def answer(call):
    if call.data == "total":
        markup_reply = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        item_single = types.KeyboardButton('За один месяц')
        item_all = types.KeyboardButton('За несколько месяцев')
        markup_reply.add(item_single, item_all)
        msg = bot.send_message(call.message.chat.id, f"Выберите период для выписки", reply_markup=markup_reply)
        bot.register_next_step_handler(msg, single_total)
    elif call.data == "add":
        markup_reply = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        item_minus = types.KeyboardButton(f'Расход ({months_print[current_month]})')
        item_plus = types.KeyboardButton(f'Приход ({months_print[current_month]})')
        markup_reply.add(item_minus, item_plus)
        msg = bot.send_message(call.message.chat.id, f"Выберите тип операции", reply_markup=markup_reply)
        bot.register_next_step_handler(msg, cost_types)
    elif call.data == "remove":
        markup_reply = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        item_minus = types.KeyboardButton('Расход (удаление)')
        item_plus = types.KeyboardButton('Приход (удаление)')
        markup_reply.add(item_minus, item_plus)
        msg = bot.send_message(call.message.chat.id, f"Выберите тип операции", reply_markup=markup_reply)
        bot.register_next_step_handler(msg, type_delete)
    elif call.data == "edit":
        markup_reply = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        item_minus = types.KeyboardButton('Расход (изменение)')
        item_plus = types.KeyboardButton('Приход (изменение)')
        markup_reply.add(item_minus, item_plus)
        msg = bot.send_message(call.message.chat.id, f"Выберите тип операции", reply_markup=markup_reply)
        bot.register_next_step_handler(msg, type_edit)
#Команды главного меню конец

#Блок редактирования начало
def type_edit(message):
    try:
        reply_markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        user_id = message.from_user.id
        person_clear(user_id)
        splitted_str = message.text.lower().split(' ')
        edit_data[user_id] = Edit(splitted_str[0])
        edit_val = edit_data[user_id]
        edit_val.table = splitted_str[0]

        def prepare_buttons(table):
            take_id = []
            cursor.execute(f"SELECT id,type,value FROM {months[current_month]}_{table} WHERE telegram_id={user_id}")
            result = cursor.fetchall()
            for i, value in enumerate(result, 1):
                take_id.append(str(value[0]))
                array_edit[user_id] = f'{str(value[0])}' + ') ' + f'{str(value[1][0].upper()) + str(value[1][1:])}' + ' ' + f'{str(value[2])}'
                reply_markup.add(types.KeyboardButton(array_edit[user_id]))

            id_edit[user_id] = take_id.copy()
            take_id.clear()

            msg = bot.send_message(message.chat.id, f"Выберите номер операции {splitted_str[0]}а, который вы хотите редактировать", reply_markup=reply_markup)
            bot.register_next_step_handler(msg, choose_category)

        if edit_val.table == 'расход':
            prepare_buttons('costs')
        elif edit_val.table == 'приход':
            prepare_buttons('salary')
        else:
            bot.send_message(message.chat.id, f"Ошибка! Проверьте тип операции")
            logger.error(f"Ошибка! Проверьте тип операции - {user_id} | {message.text}")
            send_welcome(message)
    except Exception as e:
        bot.send_message(message.chat.id, f'Что-то пошло не так: {e}')
        logger.error(f"Ошибка! {e} - {user_id} | {message.text}")
        send_welcome(message)

def choose_category(message):
    try:
        markup_reply = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        user_id = message.from_user.id
        edit_val = edit_data[user_id]
        edit_val.id = message.text.lower()
        cut_id = message.text.lower().split(' ')[0][:-1]
        item_type = types.KeyboardButton('Тип платежа')
        item_bill = types.KeyboardButton('Сумма платежа')
        item_all = types.KeyboardButton('Обе категории')
        markup_reply.add(item_type, item_bill, item_all)

        def check_id(take):
            check = False
            cursor.execute(f"SELECT id FROM {months[current_month]}_{types_dict[edit_val.table]} WHERE telegram_id={user_id}")
            result = cursor.fetchall()
            for operation in result:
                if int(take) == operation[0]:
                    check = True
                    break
            return check

        if check_id(cut_id):
            msg = bot.send_message(message.chat.id, f"Выберите категорию, которую хотите отредактировать", reply_markup=markup_reply)
            bot.register_next_step_handler(msg, edit_value)
        else:
            bot.send_message(message.chat.id, f"Ошибка! Проверьте корректность номера операции")
            logger.error(f"Ошибка! Проверьте корректность номера операции - {user_id} | {message.text}")
            send_welcome(message)
    except Exception as e:
        bot.send_message(message.chat.id, f'Что-то пошло не так: {e}')
        logger.error(f"Ошибка! {e} - {user_id} | {message.text}")
        send_welcome(message)

def edit_value(message):
    try:
        markup_reply = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        user_id = message.from_user.id
        edit_val = edit_data[user_id]
        edit_val.category = message.text.lower()

        if edit_val.category == 'тип платежа':
            if edit_val.type == 'расход':
                item_product = types.KeyboardButton('Продукты')
                item_kommunalka = types.KeyboardButton('Бытовые')
                item_connect = types.KeyboardButton('Связь')
                item_another = types.KeyboardButton('Другое')
                markup_reply.add(item_product, item_kommunalka, item_connect, item_another)
                msg = bot.send_message(message.chat.id, f"Выберите новый тип платежа", reply_markup=markup_reply)
                bot.register_next_step_handler(msg, edit_process)
            elif edit_val.type == 'приход':
                item_zp = types.KeyboardButton('Зарплата')
                item_drugoe = types.KeyboardButton('Другое')
                markup_reply.add(item_zp, item_drugoe)
                msg = bot.send_message(message.chat.id, f"Выберите новый тип платежа", reply_markup=markup_reply)
                bot.register_next_step_handler(msg, edit_process)
        elif edit_val.category == 'сумма платежа':
            msg = bot.send_message(message.chat.id, f"Введите новую сумму платежа")
            bot.register_next_step_handler(msg, edit_process)
        elif edit_val.category == 'обе категории':
            if edit_val.type == 'расход':
                item_product = types.KeyboardButton('Продукты')
                item_kommunalka = types.KeyboardButton('Бытовые')
                item_connect = types.KeyboardButton('Связь')
                item_another = types.KeyboardButton('Другое')
                markup_reply.add(item_product, item_kommunalka, item_connect, item_another)
                msg = bot.send_message(message.chat.id, f"Выберите новый тип платежа", reply_markup=markup_reply)
                bot.register_next_step_handler(msg, edit_all)
            elif edit_val.type == 'приход':
                item_zp = types.KeyboardButton('Зарплата')
                item_drugoe = types.KeyboardButton('Другое')
                markup_reply.add(item_zp, item_drugoe)
                msg = bot.send_message(message.chat.id, f"Выберите новый тип платежа", reply_markup=markup_reply)
                bot.register_next_step_handler(msg, edit_all)
        else:
            bot.send_message(message.chat.id, f"Ошибка! Проверьте корректность категории")
            logger.error(f"Ошибка! Проверьте корректность категории - {user_id} | {message.text}")
            send_welcome(message)
    except Exception as e:
        bot.send_message(message.chat.id, f'Что-то пошло не так: {e}')
        logger.error(f"Ошибка! {e} - {user_id} | {message.text}")
        send_welcome(message)

def edit_all(message):
    try:
        user_id = message.from_user.id
        edit_val = edit_data[user_id]
        edit_val.all = message.text.lower()

        def check_cat():
            check = False
            array_category = ['продукты','бытовые','связь','другое','все','зарплата']
            for cat in array_category:
                if edit_val.all == cat:
                    check = True
                    break
            return check

        if check_cat():    
            msg = bot.send_message(message.chat.id, f"Введите новую сумму платежа")
            bot.register_next_step_handler(msg, edit_process)
        else:
            bot.send_message(message.chat.id, f"Ошибка! Проверьте тип платежа")
            logger.error(f"Ошибка! Проверьте тип платежа - {user_id} | {message.text}")
            send_welcome(message)
    except Exception as e:
        bot.send_message(message.chat.id, f'Что-то пошло не так: {e}')
        logger.error(f"Ошибка! {e} - {user_id} | {message.text}")
        send_welcome(message)

def edit_process(message):
    try:
        user_id = message.from_user.id
        edit_val = edit_data[user_id]
        edit_val.value = message.text.lower()
        split_text = edit_val.id.split(' ')
        flag, allow = False, 0

        for i in range(len(id_edit[user_id])):
            if id_edit[user_id][i] == split_text[0][:-1]:
                flag = True
                break

        array_category = ['продукты','бытовые','связь','другое','все','зарплата']
        for i in range(len(array_category)):
            if edit_val.value == array_category[i]:
                allow = 1

        if edit_val.value.isdigit():
            allow = 2
        if edit_val.value.isdigit() and len(edit_val.all) > 0:
            allow = 3

        result = []
        cursor.execute(f"SELECT type FROM {months[current_month]}_{types_dict[edit_val.table]} WHERE telegram_id={user_id} AND id={split_text[0][:-1]}")
        type_value = cursor.fetchone()
        cursor.execute(f"SELECT value FROM {months[current_month]}_{types_dict[edit_val.table]} WHERE telegram_id={user_id} AND id={split_text[0][:-1]}")
        value_value = cursor.fetchone()
        result.append(type_value[0])
        result.append(value_value[0])


        def commit_sql(type):
            if type != 'all':
                cursor.execute(f"UPDATE {months[current_month]}_{types_dict[edit_val.table]} SET {type}='{edit_val.value}',date=CURDATE(),time=CURTIME() WHERE id={split_text[0][:-1]} AND telegram_id={user_id}")
                db.commit()
                logger.success(f"{user_id} успешно отредактировал запись #{split_text[0][:-1]} в таблице {months[current_month]}_{types_dict[edit_val.table]} [{result[0][0].upper() + result[0][1:] if type == 'type' else result[1]} -> {edit_val.value[0].upper() + edit_val.value[1:]}]")
            else:
                cursor.execute(f"UPDATE {months[current_month]}_{types_dict[edit_val.table]} SET type='{edit_val.all}',value='{edit_val.value}',date=CURDATE(),time=CURTIME() WHERE id={split_text[0][:-1]} AND telegram_id={user_id}")
                db.commit()
                logger.success(f"{user_id} успешно отредактировал запись #{split_text[0][:-1]} в таблице {months[current_month]}_{types_dict[edit_val.table]} [{result[0][0].upper() + result[0][1:]} -> {edit_val.all[0].upper() + edit_val.all[1:]}; {result[1]} -> {edit_val.value}]")
            bot.send_message(message.chat.id, f'Запись #{split_text[0][:-1]} успешно отредактирована')
            send_welcome(message)

        if flag:
            if allow == 1:
                commit_sql('type')
            elif allow == 2:
                commit_sql('value')
            elif allow == 3:
                commit_sql('all')
            else:
                bot.send_message(message.chat.id, f'Проверьте написание категории или корректность суммы платежа')
                logger.error(f"Проверьте написание категории или корректность суммы платежа - {user_id} | {message.text}")
                send_welcome(message)
        else:
            bot.send_message(message.chat.id, f'Вы не можете изменить чужую запись')
            logger.error(f"Вы не можете изменить чужую запись - {user_id} | {message.text}")
            send_welcome(message)
    except Exception as e:
        bot.send_message(message.chat.id, f'Что-то пошло не так: {e}')
        logger.error(f"Ошибка! {e} - {user_id} | {message.text}")
        send_welcome(message)
#Блок редактирования конец

#Блок добавления начало
def cost_types(message):
    try:
        user_id = message.from_user.id
        person_clear(user_id)
        split_text = message.text.lower().split(' ')
        user_data[user_id] = User(split_text[0])

        if split_text[0] == 'расход':
            markup_reply = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            item_product = types.KeyboardButton('Продукты')
            item_kommunalka = types.KeyboardButton('Бытовые')
            item_connect = types.KeyboardButton('Связь')
            item_another = types.KeyboardButton('Другое')
            markup_reply.add(item_product, item_kommunalka, item_connect, item_another)
            msg = bot.send_message(message.chat.id, f"Выберите категорию оплаты", reply_markup=markup_reply)
            bot.register_next_step_handler(msg, process_value_add)
        elif split_text[0] == 'приход':
            markup_reply = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            item_zp = types.KeyboardButton('Зарплата')
            item_drugoe = types.KeyboardButton('Другое')
            markup_reply.add(item_zp, item_drugoe)
            msg = bot.send_message(message.chat.id, f"Выберите категорию оплаты", reply_markup=markup_reply)
            bot.register_next_step_handler(msg, process_value_add)
        else:
            bot.send_message(message.chat.id, f"Ошибка! Проверьте тип операции")
            logger.error(f"Ошибка! Проверьте тип операции - {user_id} | {message.text}")
            send_welcome(message)
    except Exception as e:
        bot.send_message(message.chat.id, f'Что-то пошло не так: {e}')
        logger.error(f"Ошибка! {e} - {user_id} | {message.text}")
        send_welcome(message)

def process_value_add(message):
    try:
        user_id = message.from_user.id
        append_value = user_data[user_id]
        append_value.type = message.text.lower()
        if (append_value.type == 'продукты' or append_value.type == 'другое' or append_value.type == "бытовые" or append_value.type == "связь" or append_value.type == 'зарплата') and (append_value.operation == 'расход' or append_value.operation == 'приход'):
            msg = bot.send_message(message.chat.id, f"Введите сумму операции")
            bot.register_next_step_handler(msg, process_value_final)
        else:
            bot.send_message(message.chat.id, f"Ошибка! Проверьте тип категории")
            logger.error(f"Ошибка! Проверьте тип категории - {user_id} | {message.text}")
            send_welcome(message)
    except Exception as e:
        bot.send_message(message.chat.id, f'Что-то пошло не так: {e}')
        logger.error(f"Ошибка! {e} - {user_id} | {message.text}")
        send_welcome(message)

def process_value_final(message):
    try:
        array = []
        user_id = message.from_user.id
        append_value = user_data[user_id]
        append_value.value = message.text

        def add_func(table):
            sql = f"INSERT INTO {months[current_month]}_{table} (telegram_id, date, time, type, value) VALUES (%s, CURDATE(), CURTIME(), %s, %s)"
            val = (user_id, append_value.type, append_value.value)
            cursor.execute(sql, val)
            db.commit()

            cursor.execute(f"SELECT id FROM {months[current_month]}_{table} WHERE telegram_id={user_id}")
            result = cursor.fetchall()
            for i, value in enumerate(result, 1):
                array.append(str(value[0]))
            bot.send_message(message.chat.id, f'Операция #{array[-1]} успешно добавлена')
            logger.success(f"{user_id} успешно добавил запись #{array[-1]} в таблицу {months[current_month]}_{table} ['{append_value.type}', '{append_value.value}']")

        if append_value.value.isdigit():
            add_func('costs') if append_value.operation == 'расход' else add_func('salary')
            send_welcome(message)
        else:
            bot.send_message(message.chat.id, 'Ошибка! Пожалуйста, проверьте корректность суммы платежа')
            logger.error(f"Ошибка! Пожалуйста, проверьте корректность суммы платежа - {user_id} | {message.text}")
            send_welcome(message)
    except Exception as e:
        bot.send_message(message.chat.id, f'Что-то пошло не так: {e}')
        logger.error(f"Ошибка! {e} - {user_id} | {message.text}")
        send_welcome(message)
#Блок добавления конец

#Блок удаления начало
def type_delete(message):
    try:
        reply_markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        user_id = message.from_user.id
        person_clear(user_id)
        splitted_str = message.text.lower().split(' ')
        delete_data[user_id] = Delete(splitted_str[0])
        delete_val = delete_data[user_id]
        delete_val.table = splitted_str[0]

        def prepare_buttons(table):
            take_id = []
            cursor.execute(f"SELECT id,type,value FROM {months[current_month]}_{table} WHERE telegram_id={user_id}")
            result = cursor.fetchall()
            for i, value in enumerate(result, 1):
                take_id.append(str(value[0]))
                array_delete[user_id] = f'{str(value[0])}' + ') ' + f'{str(value[1][0].upper()) + str(value[1][1:])}' + ' ' + f'{str(value[2])}'
                reply_markup.add(types.KeyboardButton(array_delete[user_id]))

            id_delete[user_id] = take_id.copy()
            take_id.clear()
            msg = bot.send_message(message.chat.id, f"Выберите номер операции {splitted_str[0]}а, который вы хотите удалить", reply_markup=reply_markup)
            bot.register_next_step_handler(msg, remove_process)

        if delete_val.table == 'расход':
            prepare_buttons('costs')
        elif delete_val.table == 'приход':
            prepare_buttons('salary')
        else:
            bot.send_message(message.chat.id, f"Ошибка! Проверьте тип операции")
            logger.error(f"Ошибка! Проверьте тип операции - {user_id} | {message.text}")
            send_welcome(message)
    except Exception as e:
        bot.send_message(message.chat.id, f'Что-то пошло не так: {e}')
        logger.error(f"Ошибка! {e} - {user_id} | {message.text}")
        send_welcome(message)

def remove_process(message):
    try:
        user_id = message.from_user.id
        delete_val = delete_data[user_id]
        delete_val.id = message.text.lower()
        split_text = delete_val.id.split(' ')
        flag = False

        for i in range(len(id_delete[user_id])):
            if id_delete[user_id][i] == split_text[0][:-1]:
                flag = True
                break

        if flag:
            cursor.execute(f"DELETE FROM {months[current_month]}_{types_dict[delete_val.table]} WHERE id={split_text[0][:-1]} AND telegram_id={user_id}")
            db.commit()
            bot.send_message(message.chat.id, f'Запись #{split_text[0][:-1]} успешно удалена')
            logger.success(f"{user_id} успешно удалил запись #{split_text[0][:-1]} из таблицы {months[current_month]}_{types_dict[delete_val.table]}")
            send_welcome(message)
        else:
            bot.send_message(message.chat.id, f'Вы не можете удалить чужую запись')
            logger.error(f"Попытка удаления чужой записи - {user_id} | {message.text}")
            send_welcome(message)
    except Exception as e:
        bot.send_message(message.chat.id, f'Что-то пошло не так: {e}')
        logger.error(f"Ошибка! {e} - {user_id} | {message.text}")
        send_welcome(message)
#Блок удаления конец

#Блок выписки начало
def single_total(message):
    try:
        user_id = message.from_user.id
        person_clear(user_id)
        split_message = message.text.lower().split(' ')
        month_data[user_id] = Month(split_message[1])
        total_month = month_data[user_id]
        total_month.allow = split_message[1]
        item_jan = types.KeyboardButton('Январь')
        item_feb = types.KeyboardButton('Февраль')
        item_mar = types.KeyboardButton('Март')
        item_apr = types.KeyboardButton('Апрель')
        item_may = types.KeyboardButton('Май')
        item_june = types.KeyboardButton('Июнь')
        item_july = types.KeyboardButton('Июль')
        item_aug = types.KeyboardButton('Август')
        item_sep = types.KeyboardButton('Сентябрь')
        item_oct = types.KeyboardButton('Октябрь')
        item_nov = types.KeyboardButton('Ноябрь')
        item_dec = types.KeyboardButton('Декабрь')
        if total_month.allow == 'несколько':
            markup_reply = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup_reply.add(item_jan, item_feb, item_mar, item_apr, item_may, item_june, item_july, item_aug, item_sep, item_oct, item_nov, item_dec)
            msg = bot.send_message(message.chat.id, f"Выберите начальный месяц", reply_markup=markup_reply)
            bot.register_next_step_handler(msg, first_month_interval)
        elif total_month.allow == 'один':
            markup_reply = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup_reply.add(item_jan, item_feb, item_mar, item_apr, item_may, item_june, item_july, item_aug, item_sep, item_oct, item_nov, item_dec)
            msg = bot.send_message(message.chat.id, f"Выберите месяц, по которому вы хотите получить выписку\n\nТекущий месяц: {months_print[current_month]}", reply_markup=markup_reply)
            bot.register_next_step_handler(msg, total_month_print)
        else:
            bot.send_message(message.chat.id, f"Ошибка! Выберите корректный период для выписки")
            logger.error(f"Ошибка! Выберите корректный период для выписки - {user_id} | {message.text}")
            send_welcome(message)
    except Exception as e:
        bot.send_message(message.chat.id, f'Что-то пошло не так: {e}')
        logger.error(f"Ошибка! {e} - {user_id} | {message.text}")
        send_welcome(message)

def first_month_interval(message):
    try:
        user_id = message.from_user.id
        interval_data[user_id] = IntervalMonth(message.text.lower())
        interval_month = interval_data[user_id]
        interval_month.start = message.text.lower()
        markup_reply = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        item_jan = types.KeyboardButton('Январь')
        item_feb = types.KeyboardButton('Февраль')
        item_mar = types.KeyboardButton('Март')
        item_apr = types.KeyboardButton('Апрель')
        item_may = types.KeyboardButton('Май')
        item_june = types.KeyboardButton('Июнь')
        item_july = types.KeyboardButton('Июль')
        item_aug = types.KeyboardButton('Август')
        item_sep = types.KeyboardButton('Сентябрь')
        item_oct = types.KeyboardButton('Октябрь')
        item_nov = types.KeyboardButton('Ноябрь')
        item_dec = types.KeyboardButton('Декабрь')
        markup_reply.add(item_jan, item_feb, item_mar, item_apr, item_may, item_june, item_july, item_aug, item_sep, item_oct, item_nov, item_dec)
        month_array, flag = ['январь','февраль','март','апрель','май','июнь','июль','август','сентябрь','октябрь','ноябрь','декабрь'], False
        for month in month_array:
            if interval_month.start == month:
                flag = True
                break
        if flag:
            msg = bot.send_message(message.chat.id, f"Выберите конечный месяц", reply_markup=markup_reply)
            bot.register_next_step_handler(msg, calculate_interval)
        else:
            bot.send_message(message.chat.id, f"Ошибка! Проверьте написание месяца")
            logger.error(f"Ошибка! Проверьте написание месяца - {user_id} | {message.text}")
            send_welcome(message)
    except Exception as e:
        bot.send_message(message.chat.id, f'Что-то пошло не так: {e}')
        logger.error(f"Ошибка! {e} - {user_id} | {message.text}")
        send_welcome(message)

def calculate_interval(message):
    try:
        user_id = message.from_user.id
        interval_month = interval_data[user_id]
        interval_month.end = message.text.lower()
        result = [0,0,0,0,0,0,0,0]
        count = interval_month_dict[interval_month.end] - interval_month_dict[interval_month.start] + 1

        def calculate(table, result_array, val):
            for i in range(interval_month_dict[interval_month.start], interval_month_dict[interval_month.end]+1):
                cursor.execute(f"SELECT SUM(value) FROM {months[i]}_{table} WHERE telegram_id={user_id}")
                result = cursor.fetchone()
                if result[0] is None:
                    result_array[val] += 0
                else:
                    result_array[val] += result[0]

        def calculate_types(table, product, result_array, val):
            for i in range(interval_month_dict[interval_month.start], interval_month_dict[interval_month.end]+1):
                cursor.execute(f"SELECT SUM(value) FROM {months[i]}_{table} WHERE telegram_id={user_id} AND type='{product}'")
                result = cursor.fetchone()
                if result[0] is None:
                    result_array[val] += 0
                else:
                    result_array[val] += result[0]

        b_month_start = interval_month.start[0].upper() + interval_month.start[1:]
        b_month_end = interval_month.end[0].upper() + interval_month.end[1:]

        if (interval_month_dict[interval_month.start] < interval_month_dict[interval_month.end]) and interval_month_dict[interval_month.start] < current_month or interval_month_dict[interval_month.end] < current_month:
            calculate('salary', result, 7)
            calculate('costs', result, 4)
            array_costs = ['продукты','бытовые','связь','другое']
            for x in range(len(array_costs)):
                calculate_types('costs',array_costs[x],result,x)
            calculate_types('salary','зарплата',result,5)
            calculate_types('salary','другое',result,6)
            current_date = datetime.now().strftime('%d.%m.%y_%H.%M.%S')
            multi_create_file(interval_month_dict[interval_month.start], interval_month_dict[interval_month.end], user_id, current_date, cursor)
            make_excel_interval(interval_month_dict[interval_month.start], interval_month_dict[interval_month.end], user_id, current_date)
            with open(f"data/{user_id}/{b_month_start}-{b_month_end}({current_date})/Сводная.png", 'rb') as f1, open(f"data/{user_id}/{b_month_start}-{b_month_end}({current_date})/Продукты.png", 'rb') as f2, open(f"data/{user_id}/{b_month_start}-{b_month_end}({current_date})/Бытовые.png", 'rb') as f3, open(f"data/{user_id}/{b_month_start}-{b_month_end}({current_date})/Связь.png", 'rb') as f4, open(f"data/{user_id}/{b_month_start}-{b_month_end}({current_date})/Другое.png", 'rb') as f5:
                bot.send_media_group(message.chat.id, [InputMediaPhoto(f1), InputMediaPhoto(f2), InputMediaPhoto(f3), InputMediaPhoto(f4), InputMediaPhoto(f5)])
            bot.send_message(message.chat.id, f"{get_name(user_id)}, ваша сводная информация за {b_month_start}-{b_month_end}:\n\n---------Расходы---------\nПродукты - {result[0]} рублей\nБытовые - {result[1]} рублей\nСвязь - {result[2]} рублей\nДругое - {result[3]} рублей\nИтого - {result[4]} рублей\n\n-------Поступления-------\nЗарплата - {result[5]} рублей\nДругое - {result[6]} рублей\nИтого - {result[7]} рублей\n\nСредняя трата в месяц: {int(result[4] / count)} рублей\nСредний доход в месяц: {int(result[7] / count)} рублей\nОстаток за все месяцы: {result[7] - result[4]} рублей")
            bot.send_media_group(message.chat.id, [InputMediaDocument(open(f"data/{user_id}/{b_month_start}-{b_month_end}({current_date})/Выгрузка.xlsx", 'rb'))])
            logger.success(f"{user_id} успешно получил выписку за {b_month_start}-{b_month_end}")
            send_welcome(message)
        else:
            bot.send_message(message.chat.id, f"Ошибка, проверьте следующие пункты:\n1) Первый месяц не может быть больше второго\n2) Первый или второй месяц не может быть больше текущего")
            logger.error(f"Ошибка, проверьте следующие пункты:\n1) Первый месяц не может быть больше второго\n2) Первый или второй месяц не может быть больше текущего - {user_id} | {message.text}")
            send_welcome(message)
    except Exception as e:
        bot.send_message(message.chat.id, f'Что-то пошло не так: {e}')
        logger.error(f"Ошибка! {e} - {user_id} | {message.text}")
        send_welcome(message)

def total_month_print(message):
    try:
        print_costs, print_salary = [], []
        user_id = message.from_user.id
        total_month = month_data[user_id]
        total_month.month = message.text.lower()

        input_month = total_month.month[0].upper() + total_month.month[1:]

        array_costs, array_salary = ['продукты','бытовые','связь','другое','все'], ['зарплата', 'другое', 'все']
        def calculate_total(table, array, result_array):
            for i in range(len(array)):
                cursor.execute(f"SELECT SUM(value) FROM {months_rus[total_month.month]}_{table} WHERE telegram_id={user_id} AND type='{array[i]}'") if array[i] != 'все' else cursor.execute(f"SELECT SUM(value) FROM {months_rus[total_month.month]}_{table} WHERE telegram_id={user_id}")
                result = cursor.fetchone()
                if result[0] is None:
                    result_array.append(0)
                else:
                    result_array.append(result[0])

        calculate_total('costs',array_costs,print_costs)
        calculate_total('salary',array_salary,print_salary)

        if total_month.month in months_rus:
            current_date = datetime.now().strftime('%d.%m.%y_%H.%M.%S')
            create_file(print_costs[0],print_costs[1],print_costs[2], print_costs[3], current_date, user_id, current_month)
            bot.send_photo(message.chat.id, open(f"data/{user_id}/{months_print[current_month]}/{current_date}.png", 'rb'), caption=f"{get_name(user_id)}, ваша сводная информация за {input_month}:\n\n---------Расходы---------\nПродукты - {print_costs[0]} рублей\nБытовые - {print_costs[1]} рублей\nСвязь - {print_costs[2]} рублей\nДругое - {print_costs[3]} рублей\nИтого - {print_costs[4]} рублей\n\n-------Поступления-------\nЗарплата - {print_salary[0]} рублей\nДругое - {print_salary[1]} рублей\nИтого - {print_salary[2]} рублей\n\nОстаток за месяц: {print_salary[2] - print_costs[4]} рублей");
            make_excel(cursor, user_id, current_date, current_month)
            with open(f"data/{user_id}/{months_print[current_month]}/{label_month[current_month]}_{current_date}.xlsx", 'rb') as f1:
                bot.send_media_group(message.chat.id, [InputMediaDocument(f1)])
            send_welcome(message)
            logger.success(f"{user_id} успешно получил выписку за {input_month}")
        else:
            bot.send_message(message.chat.id, 'Ошибка! Проверьте написание месяца')
            logger.error(f"Ошибка! Проверьте написание месяца - {user_id} | {message.text}")
            send_welcome(message)
    except Exception as e:
        bot.send_message(message.chat.id, f'Что-то пошло не так: {e}')
        logger.error(f"Ошибка! {e} - {user_id} | {message.text}")
        send_welcome(message)
#Блок выписки конец

bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()

if __name__ == '__main__':
    bot.polling(none_stop=True)