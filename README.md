Currency Exchange Microservice  
This is a Python-based microservice that retrieves and displays currency exchange rates from the National Bank of the Republic of Belarus (NBRB) API.

# FEATURES

1.  First endpoint: Retrieves exchange rate data for a specific date and adds it to the database.  
    Endpoint: /first_endpoint  
    Input: date (in the format "YYYY-MM-DD")  
    Output: A response indicating the success of the data retrieval process.  
2.  Second endpoint: Retrieves exchange rate data for a specific date and currency.  
    Endpoint: /second_endpoint  
    Input: date (in the format "YYYY-MM-DD") and currency_code  
    Output: Information about the exchange rate for the specified date and currency, including the change compared to the previous business day.

# ADDITIONAL FEATURES:

-Logging of requests and responses  
-CRC32 checksum of the response body in the response header  
-Documentation of the developed interaction protocol  

# PIP INSTALL  
• pip install -r requirements.txt  

# INSTALLATION
Clone the repo with

• git clone https://github.com/klypol/CurrencyMonitoring.git  
• Create the admin file, which will contain the password variable.

# CURRENCY CODE
431: USD  
451: EUR  
456: RUB
