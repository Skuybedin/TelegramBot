from datetime import datetime
from loguru import logger
from bot import cursor

logger.add('debug.log', format='{time:DD-MM-YYYY HH:mm:ss} | {level} | {message}', level='DEBUG', rotation='1 MB', compression='zip')

#Словари
months = {1: 'january', 2: 'february', 3: 'march', 4: 'april', 5: 'may', 6: 'june', 7: 'july', 8: 'august', 9: 'september', 10: 'october', 11: 'november', 12: 'december'}
months_print = {1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август', 9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'}
months_rus = {'январь': 'january', 'февраль': 'february', 'март': 'march', 'апрель': 'april', 'май': 'may', 'июнь': 'june', 'июль': 'july', 'август': 'august', 'сентябрь': 'september', 'октябрь': 'october', 'ноябрь': 'november', 'декабрь': 'december'}
types_dict = {'приход': 'salary', 'расход': 'costs'}
interval_month_dict = {'январь': 1, 'февраль': 2, 'март': 3, 'апрель': 4, 'май': 5, 'июнь': 6, 'июль': 7, 'август': 8, 'сентябрь': 9, 'октябрь': 10, 'ноябрь': 11, 'декабрь': 12}
group_dict = {'администрация': 'admin', 'пользователь': 'user'}

current_month = datetime.now().month

# cursor.execute("CREATE DATABASE IF NOT EXISTS calculate")
# cursor.execute("ALTER TABLE таблица ADD COLUMN test VARCHAR(255)")
# cursor.execute(CREATE TABLE IF NOT EXISTS calculate.users (id INT AUTO_INCREMENT PRIMARY KEY, date DATE, time TIME, telegram_id INT UNIQUE, name VARCHAR(255), status VARCHAR(255)))

#Дата
user_data, month_data, delete_data = {}, {}, {}
array_delete, id_delete, interval_data = {}, {}, {}
array_edit, id_edit, edit_data, users = {}, {}, {}, {}

#Классы
class User:
    def __init__(self, operation):
        self.operation = operation
        self.type = ''
        self.value = 0

class Month:
    def __init__(self, allow):
        self.allow = allow
        self.month = ''

class IntervalMonth:
    def __init__(self, start):
        self.start = start
        self.end = ''

class Delete:
    def __init__(self, table):
        self.type = table
        self.id = ''

class Edit:
    def __init__(self, table):
        self.type = table
        self.id = ''
        self.category = ''
        self.value = ''
        self.all = ''

#Функция очистки даты
def clear():
    delete_data.clear()
    user_data.clear()
    month_data.clear()
    array_delete.clear()
    edit_data.clear()
    id_delete.clear()
    array_edit.clear()
    id_edit.clear()
    interval_data.clear()

def person_clear(telegram):
    dict_array = [user_data, month_data, delete_data, array_delete, id_delete, interval_data, array_edit, id_edit, edit_data, users]
    for data in dict_array:
        if telegram in data:
            del data[telegram]

def check_rights(telegram):
    cursor.execute(f"SELECT telegram_id FROM users WHERE status='admin'")
    result = cursor.fetchall()
    for each in result:
        if telegram == each[0]:
            return True
    return False

def get_name(telegram):
    cursor.execute(f"SELECT name FROM users WHERE telegram_id={telegram}")
    result = cursor.fetchone()
    if result is None:
        return 'Если хотите, чтобы бот обращался к вам по имени, то пройдите регистрацию (/start)\nБез имени'
    else:
        return result[0]

def is_registred(telegram):
    cursor.execute(f"SELECT name FROM users WHERE telegram_id={telegram}")
    result = cursor.fetchone()
    if result is None:
        return False
    else:
        return True