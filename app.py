import psycopg2
from admin import PASSWORD


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