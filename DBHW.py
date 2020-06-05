"""Программа по учету товаров на складе."""

import sqlite3
import jsonschema
import json

import typing
from jsonschema import SchemaError

conn = sqlite3.connect('HomeworkDB.sqlite')
conn.execute("PRAGMA foreign_keys = ON")
cur = conn.cursor()  # посмотреть что делает

cur.executescript('''
CREATE TABLE IF NOT EXISTS goods(
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    name VARCHAR(25) NOT NULL,
    package_height FLOAT NOT NULL,
    package_width FLOAT NOT NULL
)''')

cur.execute('''
CREATE TABLE IF NOT EXISTS shops_goods(
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    id_good INTEGER NOT NULL,
    location VARCHAR(25) NOT NULL,
    amount INTEGER NOT NULL,
    FOREIGN KEY (id_good) references goods(id)
)''')

file_name = input('Enter file name: ')
if len(file_name) < 1:
    file_name = 'valid_json_example.json'

str_data = open(file_name, encoding='utf-8').read()
json_data = json.loads(str_data)

json_schema_name = 'schema.json'
json_schema_read = open(json_schema_name).read()
json_schema_data = json.loads(json_schema_read)
try:
    if jsonschema.validate(json_schema_data, json_data) is None:
        print('Valid json')
except SchemaError:
    print('Invalid json')
    quit()


def find(key: str, dictionary: dict) -> list:
    """В этой функции находим example."""

    for k, v in dictionary.items():
        if k == key:
            return v
        elif isinstance(v, dict):
            for result in find(key, v):
                return result
        elif isinstance(v, list):
            for d in v:
                for result in find(key, d):
                    return result
    return []


print(type(find('examples', json_data)))

res_data = list(find('examples', json_data))
print(res_data)

for n in res_data:
    name = n['name']
    width = n['package_params']['width']
    height = n['package_params']['height']
    cur.execute('''SELECT name FROM goods WHERE name = ?''', (name,))
    select_result = cur.fetchone()  # what is it? (sobaka, )
    try:
        if select_result[0] == name:
            cur.execute('''UPDATE goods SET package_height = ?,
                package_width = ? WHERE name = ?''', (height, width, name))
            cur.execute('''SELECT id FROM goods WHERE name = ?''', (name,))
            id_good = cur.fetchone()
            cur.execute('''SELECT location from shops_goods where
                 id_good = ?''', (id_good[0],))
            new_goods_location = cur.fetchall()
            for i in n['location_and_quantity']:
                for pur in new_goods_location:
                    if i['location'] == pur[0]:
                        amount = i['amount']
                        location = i['location']
                        cur.execute('''UPDATE shops_goods
                            SET amount = ? WHERE id_good = ?
                            AND location = ?''',
                                    (amount, id_good[0], location))
    except TypeError:

        cur.execute('''INSERT INTO goods
            (name,package_height,package_width)
            VALUES(?, ?, ?)''', (name, height, width))
        cur.execute('''SELECT id FROM goods WHERE name = ?
            and package_height = ? and package_width = ? limit 1''',
                    (name, height, width))
        id_good = cur.fetchone()
        for i in n['location_and_quantity']:
            location = i['location']
            amount = i['amount']
            cur.execute('''INSERT INTO shops_goods (id_good,location,amount)
                VALUES(?, ?, ?)''', (id_good[0], location, amount))

    conn.commit()
