import pandas as pd
import seaborn as sns
import os
import matplotlib.pyplot as plt
from connect import connection

months_num_dict = {1: 'january', 2: 'february', 3: 'march', 4: 'april', 5: 'may', 6: 'june', 7: 'july', 8: 'august', 9: 'september', 10: 'october', 11: 'november', 12: 'december'}
label_month = {1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август', 9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'}

def create_file(v1, v2, v3, v4, name, user_id, month):
    df = pd.DataFrame({'Продукты': v1,
                   'Бытовые': v2,
                   'Связь': v3,
                   'Другое': v4}, index=[1], )
    if not os.path.isdir(f"data/{user_id}"):
        os.mkdir(f"data/{user_id}")
    if not os.path.isdir(f"data/{user_id}/{label_month[month]}"):
        os.mkdir(f"data/{user_id}/{label_month[month]}")
    explode = (0.1, 0, 0, 0)
    fig, ax = plt.subplots()
    ax.pie(df.values[0], labels=df.columns, autopct='%1.1f%%', explode=explode, wedgeprops={'lw':1, 'ls':'-','edgecolor':"k"})
    ax.axis("equal");
    plt.savefig(f"data/{user_id}/{label_month[month]}/{name}.png")

def multi_create_file(start, end, user_id, name, cursor):
    category, labels = ['продукты', 'бытовые', 'связь', 'другое'], []
    data_array, result_array, data = [], [], {}
    df = pd.DataFrame()
    for i in range(start, end+1):
        labels.append(label_month[i])
        if len(data_array) > 0:
            result_array.append(data_array.copy())
            data_array.clear()
        for cat in range(len(category)):
            cursor.execute(f"SELECT sum(value) FROM {months_num_dict[i]}_costs WHERE telegram_id={user_id} AND type='{category[cat]}'")
            result = cursor.fetchall()
            for j, value in enumerate(result, 1):
                if value[0] is None:
                    data_array.append(0)
                else:
                    data_array.append(value[0])
    if len(data_array) > 0:
        result_array.append(data_array.copy())
        data_array.clear()
    for pack in range(len(result_array)):
        data = {'Месяц': labels[pack], 'Продукты': int(result_array[pack][0]), 'Бытовые': int(result_array[pack][1]), 'Связь': int(result_array[pack][2]), 'Другое': int(result_array[pack][3])}
        df = df.append(data, ignore_index=True)
        data.clear()
    if not os.path.isdir(f"data/{user_id}"):
        os.mkdir(f"data/{user_id}")
    if not os.path.isdir(f"data/{user_id}/{label_month[start]}-{label_month[end]}({name})"):
        os.mkdir(f"data/{user_id}/{label_month[start]}-{label_month[end]}({name})")
    explode = (0.1, 0, 0, 0)
    fig, ax = plt.subplots()
    ax.pie(sum(df.iloc[:,1:].values), labels=df.iloc[:,1:].columns, autopct='%1.1f%%', explode=explode, wedgeprops={'lw':1, 'ls':'-','edgecolor':"k"})
    ax.axis("equal");
    plt.savefig(f"data/{user_id}/{label_month[start]}-{label_month[end]}({name})/Сводная.png")
    category_img = ['Продукты', 'Бытовые', 'Связь', 'Другое']
    for img in category_img:
        sns_plot = sns.catplot(x='Месяц', y=img, data=df, kind='bar', palette='magma', height=5, aspect=.7);
        sns_plot.savefig(f"data/{user_id}/{label_month[start]}-{label_month[end]}({name})/{img}.png")

def make_excel(cursor, user_id, name, current_month):
    cursor.execute(f"SELECT date,date_format(time, '%H:%i:%s'),type,value FROM {months_num_dict[current_month]}_costs WHERE telegram_id={user_id}")
    result = cursor.fetchall()
    data, result_array = [], []
    labels = ["Дата",'Время','Категория','Сумма']
    for i in range(len(labels)):
        if len(data) > 0:
            result_array.append(data.copy())
            data.clear()
        for j, value in enumerate(result, 1):
            data.append(value[i])
    if len(data) > 0:
        result_array.append(data.copy())
        data.clear()
    data_dict = {labels[0]: result_array[0], labels[1]: result_array[1], labels[2]: result_array[2], labels[3]: result_array[3]}
    df = pd.DataFrame.from_dict(data_dict)
    writer = pd.ExcelWriter(f'data/{user_id}/{label_month[current_month]}/{label_month[current_month]}_{name}.xlsx', datetime_format='HH:MM:SS')
    df.to_excel(writer, f'{label_month[current_month]}')
    writer.save()

def make_excel_interval(start, end, user_id, name):
    df = pd.read_sql(f"SELECT date AS 'Дата',date_format(time, '%H:%i:%s') AS 'Время',type AS 'Категория',value AS 'Сумма' FROM {months_num_dict[start]}_costs WHERE telegram_id={user_id}", con=connection)
    df = df.rename(index = lambda x: label_month[start])
    for month in range(start+1, end+1):
        df_month = pd.read_sql(f"SELECT date AS 'Дата',date_format(time, '%H:%i:%s') AS 'Время',type AS 'Категория',value AS 'Сумма' FROM {months_num_dict[month]}_costs WHERE telegram_id={user_id}", con=connection)
        df_month = df_month.rename(index = lambda x: label_month[month])
        df = pd.concat([df, df_month.copy()])
    writer = pd.ExcelWriter(f'data/{user_id}/{label_month[start]}-{label_month[end]}({name})/Выгрузка.xlsx', datetime_format='HH:MM:SS')
    df.to_excel(writer, f'{label_month[start]}-{label_month[end]}')
    writer.save()