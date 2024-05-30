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