import sqlite3
from datetime import datetime
import logging
import os

logging.basicConfig(level=logging.DEBUG)

class Database:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.conn = None
            cls._instance.cursor = None
        return cls._instance

    def __init__(self, database_url):
        self.database_url = database_url
        if self.conn is None:
            logging.debug(f"Initializing database connection with URL: {self.database_url}")
            self.conn = sqlite3.connect(self.database_url, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self.create_tables()

    def create_tables(self):
        logging.debug("Creating tables if they don't exist")
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS users
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             email TEXT UNIQUE,
             threshold REAL,
             fuel_type TEXT)
        ''')
        
        # 检查是否需要添加新列
        cursor = self.conn.execute('PRAGMA table_info(users)')
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'latitude' not in columns:
            self.conn.execute('ALTER TABLE users ADD COLUMN latitude REAL')
        if 'longitude' not in columns:
            self.conn.execute('ALTER TABLE users ADD COLUMN longitude REAL')
        if 'address' not in columns:
            self.conn.execute('ALTER TABLE users ADD COLUMN address TEXT')
        
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS fuel_prices
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             fuel_type TEXT,
             station TEXT,
             price REAL,
             updated TEXT,
             timestamp DATETIME,
             UNIQUE(fuel_type, station))
        ''')
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS user_vehicles
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             user_email TEXT,
             latitude REAL,
             longitude REAL,
             FOREIGN KEY (user_email) REFERENCES users(email))
        ''')
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS stations
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             name TEXT UNIQUE,
             latitude REAL,
             longitude REAL)
        ''')
        self.conn.commit()
        logging.info("Tables created and updated successfully")

    def add_user(self, email, threshold, fuel_type, latitude=None, longitude=None, address=None):
        self.conn.execute('''
            INSERT OR REPLACE INTO users 
            (email, threshold, fuel_type, latitude, longitude, address) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (email, threshold, fuel_type, latitude, longitude, address))
        self.conn.commit()

    def remove_user(self, email):
        self.conn.execute('DELETE FROM users WHERE email = ?', (email,))
        self.conn.commit()

    def get_all_subscriptions(self):
        cursor = self.conn.execute('PRAGMA table_info(users)')
        columns = [row[1] for row in cursor.fetchall()]
        
        select_columns = ['email', 'threshold', 'fuel_type']
        if 'latitude' in columns:
            select_columns.append('latitude')
        if 'longitude' in columns:
            select_columns.append('longitude')
        if 'address' in columns:
            select_columns.append('address')
        
        query = f"SELECT {', '.join(select_columns)} FROM users"
        cursor = self.conn.execute(query)
        return cursor.fetchall()

    def update_fuel_prices(self, prices):
        logging.info("Updating fuel prices in database")
        for fuel_type, price_list in prices.items():
            for price in price_list:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO fuel_prices 
                    (fuel_type, station, price, updated, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (fuel_type, price['station'], price['price'], price['updated'], price['timestamp']))

        self.conn.commit()
        logging.info("Fuel prices updated successfully")

    def get_latest_fuel_prices(self):
        cursor = self.conn.execute('''
            SELECT fuel_type, station, price, updated
            FROM fuel_prices
            WHERE (fuel_type, station, timestamp) IN (
                SELECT fuel_type, station, MAX(timestamp)
                FROM fuel_prices
                GROUP BY fuel_type, station
            )
        ''')
        return cursor.fetchall()

    def get_latest_top10_fuel_prices(self, fuel_type):
        query = '''
        WITH latest_prices AS (
            SELECT *,
                   ROW_NUMBER() OVER (PARTITION BY station ORDER BY timestamp DESC) as rn
            FROM fuel_prices
            WHERE fuel_type = ?
        ),
        top_10_latest AS (
            SELECT *
            FROM latest_prices
            WHERE rn = 1
            ORDER BY timestamp DESC
            LIMIT 10
        )
        SELECT fuel_type, station, price, updated, timestamp
        FROM top_10_latest
        ORDER BY price ASC
        LIMIT 10
        '''
        self.cursor.execute(query, (fuel_type,))
        return self.cursor.fetchall()

    def close(self):
        if hasattr(self, 'conn'):
            self.conn.close()

    def update_fuel_price_timestamps(self, updates):
        query = """
        UPDATE fuel_prices
        SET timestamp = ?
        WHERE fuel_type = ? AND station = ?
        """
        self.cursor.executemany(query, updates)
        self.conn.commit()

    def insert_new_fuel_prices(self, new_prices):
        query = """
        INSERT INTO fuel_prices (fuel_type, station, price, timestamp)
        VALUES (?, ?, ?, ?)
        """
        self.cursor.executemany(query, new_prices)
        self.conn.commit()

    def add_user_vehicle(self, email, latitude, longitude):
        self.conn.execute('''
            INSERT OR REPLACE INTO user_vehicles (user_email, latitude, longitude)
            VALUES (?, ?, ?)
        ''', (email, latitude, longitude))
        self.conn.commit()

    def get_user_vehicle(self, email):
        cursor = self.conn.execute('''
            SELECT latitude, longitude FROM user_vehicles WHERE user_email = ?
        ''', (email,))
        return cursor.fetchone()

    def add_or_update_station(self, name, latitude, longitude):
        self.conn.execute('''
            INSERT OR REPLACE INTO stations (name, latitude, longitude)
            VALUES (?, ?, ?)
        ''', (name, latitude, longitude))
        self.conn.commit()

    def get_station_location(self, name):
        cursor = self.conn.execute('''
            SELECT latitude, longitude FROM stations WHERE name = ?
        ''', (name,))
        result = cursor.fetchone()
        if result:
            return result
        else:
            logging.warning(f"No location found for station: {name}")
            return None

    def get_all_stations(self):
        cursor = self.conn.execute('SELECT name, latitude, longitude FROM stations')
        return cursor.fetchall()

    def update_user_location(self, email, latitude, longitude, address):
        self.conn.execute('''
            UPDATE users 
            SET latitude = ?, longitude = ?, address = ?
            WHERE email = ?
        ''', (latitude, longitude, address, email))
        self.conn.commit()

    def get_user_location(self, email):
        cursor = self.conn.execute('''
            SELECT latitude, longitude, address FROM users WHERE email = ?
        ''', (email,))
        return cursor.fetchone()