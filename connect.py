import mysql.connector
from mysql.connector import Error
from data import logger

token = "1869294186:AAFTKrzNeuAn4AU2nrYRGB7gItbdAx2ROyM"

connection = None
try:
    connection = mysql.connector.connect(
        host = "localhost",
        user = "root",
        password = "password",
        port = "3306",
        database = "calculate"
    )
    logger.success("Вы успешно подключились к базе данных")
except Error as e:
    logger.error(f"Ошибка: '{e}'")