import psycopg2
import requests
import logging
import zlib
from psycopg2 import sql
from admin import PASSWORD
from datetime import datetime, timedelta


logging.basicConfig(filename='currency_app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    encoding='utf-8')


connection = psycopg2.connect(
    dbname='CurrencyMonitoring',
    host='localhost',
    port='5432',
    user='postgres',
    password=PASSWORD
)

cursor = connection.cursor()


table = (
    """
    CREATE TABLE IF NOT EXISTS currency
    (
        id SERIAL PRIMARY KEY,
        cur_id INTEGER NOT NULL,
        cur_abbreviation TEXT NOT NULL,
        official_rate FLOAT NOT NULL,
        cur_date TIMESTAMP NOT NULL
    );
    """
)

cursor.execute(table)
connection.commit()


def get_currency(date: str) -> requests.Response:
    """
    Sends a GET request to the NBRB API to retrieve exchange rate data for the given date.

    Args:
        date (str): The date in the format "YYYY-MM-DD".

    Returns:
        requests.Response: The response object from the API request.
    """
    url = f'https://api.nbrb.by/exrates/rates?ondate={date}&periodicity=0'
    logging.info(f"Отправлен запрос: {url}")
    response = requests.get(url, timeout=10)
    logging.info(f"Получен ответ со статусом: {response.status_code}")
    crc32 = zlib.crc32(response.content)
    response.headers['X-CRC32'] = str(crc32)
    return response


def integrity_check(response: requests.Response) -> None:
    """
    Checks the integrity of the response data by comparing the calculated CRC32 checksum with the
    one provided in the response headers.

    Args:
        response (requests.Response): The response object to be checked.

    Returns:
        None
    """
    crc32_header = response.headers.get('X-CRC32')
    crc32_calculated = zlib.crc32(response.content)
    if crc32_header and str(crc32_calculated) == crc32_header:
        print("(Контрольная сумма CRC32 верна. Данные не были изменены.)")
    else:
        print("Контрольная сумма CRC32 не совпадает. Данные могут быть повреждены или изменены.")


def previous_date(date: str) -> str:
    """
    Calculates the date one day earlier than the given date.

    Args:
        date (str): The date in the format "YYYY-MM-DD".

    Returns:
        str: The date one day earlier than the given date, in the format "YYYY-MM-DD".
    """
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    one_day_earlier = date_obj - timedelta(days=1)
    return one_day_earlier.strftime("%Y-%m-%d")


def get_currency_change(date: str, cur_id: int) -> str:
    """
    Calculates the change in the official exchange rate for the given currency ID between the current
    date and the previous day.

    Args:
        date (str): The date in the format "YYYY-MM-DD".
        cur_id (int): The ID of the currency.

    Returns:
        str: A string describing the change in the exchange rate.
    """
    data = get_currency(date).json()
    day_earlier = previous_date(date)
    prev_data = get_currency(day_earlier).json()

    for item in data:
        if item['Cur_ID'] == cur_id:
            for prev_item in prev_data:
                if prev_item['Cur_ID'] == item['Cur_ID']:
                    change_value = item['Cur_OfficialRate'] - prev_item['Cur_OfficialRate']
                    if change_value > 0:
                        change_text = f"Курс по сравнению с предыдущим днем увеличился на {change_value}"
                    elif change_value < 0:
                        change_text = f"Курс по сравнению с предыдущим днем уменьшился на {abs(change_value)}"
                    else:
                        change_text = "Курс по сравнению с предыдущим днем не изменился"
                    return change_text


class Currency:
    def __init__(self, dbname, user, password, host, port):
        self.connection = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        self.connection.set_session(autocommit=True)
        self.cursor = self.connection.cursor()

    def first_endpoint(self, date: str):
        response = get_currency(date)

        integrity_check(response)

        response.encoding = 'utf-8'
        response_data = response.json()

        for item in response_data:
            cur_id = item['Cur_ID']
            cur_abbreviation = item['Cur_Abbreviation']
            official_rate = item['Cur_OfficialRate']
            date = item['Date']
            query = sql.SQL(
                "INSERT INTO currency (cur_id, cur_abbreviation, official_rate, cur_date) VALUES (%s, %s, %s, %s)")
            self.cursor.execute(query, (cur_id, cur_abbreviation, official_rate, date))
            logging.info(f"Запрос на insert в базу данных: {query.as_string(self.connection)} с данными {(cur_id, cur_abbreviation, official_rate, date)}")
        return response.status_code

    def second_endpoint(self, cur_id: int, date: str):
        query = sql.SQL("""SELECT cur_id, cur_abbreviation,
                        official_rate, cur_date FROM currency WHERE cur_id = %s AND cur_date = %s""")
        self.cursor.execute(query, (cur_id, date))
        logging.info(f"Запрос на выборку из базы данных: {query.as_string(self.connection)} с параметрами {(cur_id, date)}")

        result = [item for row in self.cursor.fetchall() for item in row]

        if result:
            logging.info(f"Данные найдены в базе: {result}")
            column_names = [description[0] for description in self.cursor.description]
            currency = dict(zip(column_names, result))

            return currency
        else:
            response = get_currency(date)

            integrity_check(response)

            response.encoding = 'utf-8'
            response_data = response.json()

            for item in response_data:
                currency_code = item['Cur_ID']
                if currency_code == cur_id:
                    logging.info(f"Данные не найдены в базе, получены из API: {item}")
                    return {'cur_id ': item['Cur_ID'],
                            'cur_abbreviation': item['Cur_Abbreviation'],
                            'official_rate': item['Cur_OfficialRate'],
                            'cur_date': item['Date']}

    def close(self):
        self.cursor.close()
        self.connection.close()


db = Currency(
    dbname='CurrencyMonitoring',
    user='postgres',
    password=PASSWORD,
    host='localhost',
    port='5432'
)


def validate_date(date_str):
    try:
        year, month, day = map(int, date_str.split('-'))
        if len(str(year)) != 4 or month < 1 or month > 12 or day < 1 or day > 31:
            raise ValueError
        return True
    except (ValueError, IndexError):
        return False


while True:
    print('1. Первый endpoint')
    print('2. Второй endpoint')
    print('3. Выход')

    try:
        choice = int(input("Выберите действие (1-3): "))
    except ValueError:
        print('Введено некорректное действие. Попробуйте ещё раз!')
        continue

    match choice:
        case 1:
            date = input('Введите дату в формате ГГГГ-ММ-ДД: ')
            if validate_date(date):
                print(f"---Status code: {db.first_endpoint(date)}---")
            else:
                print('Введена некорректная дата. Попробуйте ещё раз.')
                continue
        case 2:
            try:
                code = int(input('Введите код валюты: '))
                if code < 0:
                    raise ValueError
            except ValueError:
                print('Введен некорректный код валюты. Попробуйте ещё раз.')
                continue

            date = input('Введите дату в формате ГГГГ-ММ-ДД: ')
            if validate_date(date):
                print('\n---Информация о валюте---')
                result = db.second_endpoint(code, date)
                for key, value in result.items():
                    print(f"{key}: {value}")
                print(get_currency_change(date, code), "\n")

            else:
                print('Введена некорректная дата. Попробуйте ещё раз.')
                continue
        case 3:
            db.close()
            break
        case _:
            print('Такой команды не существует. Попробуйте ещё раз!')
