from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, render_template_string
from database import Database
from scraper import scrape_fuel_prices
from apscheduler.schedulers.background import BackgroundScheduler
from email_sender import send_email
import logging
import sqlite3
from datetime import datetime, timedelta
from distance_calculator import calculate_distance_and_time, get_address
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import os
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件中的环境变量

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

scheduler = BackgroundScheduler()
scheduler.start()

def get_db():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    logging.info(f"Connecting to database: {database_url}")
    return Database(database_url)

# 所有路由定义
@app.route('/')
def home():
    logging.debug("Entering home route")
    try:
        db = get_db()
        logging.debug("Getting subscriptions from database")
        subscriptions = db.get_all_subscriptions()
        logging.debug(f"Retrieved {len(subscriptions)} subscriptions")
        
        logging.debug("Getting latest top 10 fuel prices from database")
        grouped_prices = {
            '95 E10': db.get_latest_top10_fuel_prices('95 E10'),
            '98 E5': db.get_latest_top10_fuel_prices('98 E5'),
            'Diesel': db.get_latest_top10_fuel_prices('Diesel')
        }
        logging.debug(f"Retrieved fuel prices for {len(grouped_prices)} fuel types")
    
        user_email = request.args.get('email')
        user_location = None
        if user_email:
            user_location = db.get_user_location(user_email)
        
        if user_location and len(user_location) >= 2:
            for fuel_type in grouped_prices:
                for i, price in enumerate(grouped_prices[fuel_type]):
                    station_location = db.get_station_location(price[1])
                    logging.debug(f"Station location for {price[1]}: {station_location}")
                    if station_location:
                        station_lat, station_lon = station_location
                        calc_result = calculate_distance_and_time(user_location[0], user_location[1], station_lat, station_lon)
                        grouped_prices[fuel_type][i] = price + (calc_result['distance'], calc_result['time_minutes'])
                        logging.debug(f"Calculated distance and time for {price[1]}: {calc_result}")
                    else:
                        grouped_prices[fuel_type][i] = price + (None, None)
                        logging.warning(f"No location found for station: {price[1]}")
    
        logging.debug("Rendering index.html template")
        return render_template('index.html', subscriptions=subscriptions, grouped_prices=grouped_prices, user_email=user_email, user_location=user_location)
    except Exception as e:
        logging.error(f"Error in home route: {str(e)}", exc_info=True)
        return "An error occurred", 500

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    threshold = request.form.get('threshold')
    fuel_type = request.form.get('fuel_type')
    
    if not email or not threshold or not fuel_type:
        flash("Email, threshold and fuel type are required", "error")
        return redirect(url_for('home'))
    
    db = get_db()
    db.add_user(email, float(threshold), fuel_type)
    
    flash("Subscription successful", "success")
    return redirect(url_for('home'))

@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    email = request.form.get('email')
    
    if not email:
        flash("Email is required", "error")
        return redirect(url_for('home'))
    
    with get_db() as db:
        db.remove_user(email)
    
    flash("Unsubscription successful", "success")
    return redirect(url_for('home'))

@app.route('/update_prices', methods=['POST'])
def update_prices():
    try:
        update_fuel_prices_and_notify()
        flash("Fuel prices updated successfully", "success")
    except Exception as e:
        flash(f"Error updating prices: {str(e)}", "error")
    return redirect(url_for('home'))

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/view_data')
def view_data():
    conn = sqlite3.connect('/data/fuel_prices.db')  # 修改这里
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    data = {}
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT * FROM {table_name}")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        data[table_name] = {
            'columns': columns,
            'rows': rows
        }
    
    conn.close()

    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Database Data</title>
        <style>
            table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h1>Database Data</h1>
        {% for table_name, table_data in data.items() %}
            <h2>{{ table_name }}</h2>
            <table>
                <tr>
                    {% for column in table_data['columns'] %}
                        <th>{{ column }}</th>
                    {% endfor %}
                </tr>
                {% for row in table_data['rows'] %}
                    <tr>
                        {% for cell in row %}
                            <td>{{ cell }}</td>
                        {% endfor %}
                    </tr>
                {% endfor %}
            </table>
        {% endfor %}
    </body>
    </html>
    """
    
    return render_template_string(html_template, data=data)

# 错误处理器
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500

@app.errorhandler(Exception)
def handle_exception(e):
    print(f"Unhandled exception: {str(e)}")
    return "An error occurred", 500

# 辅助函数
def update_fuel_prices_and_notify():
    try:
        prices = scrape_fuel_prices()
        logging.info(f"Scraped prices: {prices}")
        db = get_db()
        db.update_fuel_prices(prices)
        
        # 获取最新的前10个最低价格
        latest_prices = {}
        for fuel_type in ['95 E10', '98 E5', 'Diesel']:
            latest_prices[fuel_type] = db.get_latest_top10_fuel_prices(fuel_type)
        
        # 通知逻辑
        subscriptions = db.get_all_subscriptions()
        logging.info(f"Found {len(subscriptions)} subscriptions")
        
        # 用于存储每个用户的通知信息
        notifications = {}
        
        for sub in subscriptions:
            email, threshold, fuel_type = sub
            logging.info(f"Checking subscription: {email}, {threshold}, {fuel_type}")
            if fuel_type in latest_prices:
                for price in latest_prices[fuel_type]:
                    logging.info(f"Comparing price {price[2]} with threshold {threshold}")
                    if price[2] <= threshold:
                        if email not in notifications:
                            notifications[email] = []
                        notifications[email].append({
                            'fuel_type': fuel_type,
                            'station': price[1],
                            'price': price[2],
                            'threshold': threshold,
                            'updated': price[3]
                        })
        
        # 发送合并后的通知
        for email, alerts in notifications.items():
            subject = "Fuel Price Alert"
            message = "The following fuel prices have dropped below your thresholds:\n\n"
            for alert in alerts:
                message += f"- {alert['fuel_type']} at {alert['station']}: €{alert['price']} (Threshold: €{alert['threshold']}, Updated: {alert['updated']})\n"
            
            logging.info(f"Sending email to {email}: {subject}")
            if send_email(email, subject, message):
                logging.info(f"Successfully sent price alert to {email}")
            else:
                logging.error(f"Failed to send price alert to {email}")
        
        logging.info("Fuel prices updated and notifications sent successfully")
    except Exception as e:
        logging.error(f"Error updating fuel prices and sending notifications: {str(e)}", exc_info=True)

# 设置定时任务，每小时更新一次燃料价格并发送通知
scheduler.add_job(update_fuel_prices_and_notify, 'interval', hours=1)

# 辅助函数
def clean_database():
    try:
        db = get_db()
        conn = sqlite3.connect('/data/fuel_prices.db')
        cursor = conn.cursor()

        # 检查 fuel_prices 表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fuel_prices'")
        if cursor.fetchone() is None:
            logging.warning("fuel_prices table does not exist, skipping database cleaning")
            return

        # 获取数据库中的记录数
        cursor.execute("SELECT COUNT(*) FROM fuel_prices")
        record_count = cursor.fetchone()[0]

        logging.info(f"Current number of records in database: {record_count}")

        conn.close()

        logging.info("Database check completed successfully")
    except Exception as e:
        logging.error(f"Error checking database: {str(e)}", exc_info=True)

def initialize_data():
    logging.info("Initializing data...")
    try:
        db = get_db()
        # 确保表已创建
        db.create_tables()
        
        prices = scrape_fuel_prices()
        logging.info(f"Scraped prices during initialization: {prices}")
        if prices:
            db.update_fuel_prices(prices)
            logging.info(f"Initialized {sum(len(price_list) for price_list in prices.values())} fuel prices in database")
        else:
            logging.warning("No fuel prices scraped during initialization")
        
        check_prices = db.get_latest_fuel_prices()
        logging.info(f"After initialization, retrieved {len(check_prices)} prices from database")
    except Exception as e:
        logging.error(f"Error initializing data: {str(e)}", exc_info=True)



@app.route('/add_vehicle', methods=['POST'])
def add_vehicle():
    email = request.form.get('email')
    address = request.form.get('address')
    
    if not email or not address:
        flash("Email and address are required", "error")
        return redirect(url_for('home'))
    
    try:
        geolocator = Nominatim(user_agent="fuel_price_tracker")
        location = geolocator.geocode(address)
        if location:
            db = get_db()
            db.update_user_location(email, location.latitude, location.longitude, address)
            flash("Vehicle location added successfully", "success")
        else:
            flash("Could not find the location. Please try a more specific address.", "error")
    except (GeocoderTimedOut, GeocoderServiceError):
        flash("Geocoding service is currently unavailable. Please try again later.", "error")
    
    return redirect(url_for('home'))

@app.route('/manage_stations', methods=['GET', 'POST'])
def manage_stations():
    db = get_db()
    if request.method == 'POST':
        name = request.form.get('name')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        if name and latitude and longitude:
            db.add_or_update_station(name, float(latitude), float(longitude))
            flash("Station location added/updated successfully", "success")
        else:
            flash("All fields are required", "error")
    
    stations = db.get_all_stations()
    return render_template('manage_stations.html', stations=stations)


# 确保在应用启动时调用这个函数
if __name__ == '__main__':
    logging.info("Starting the application")
    initialize_data()
    clean_database()
    
    print("Registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.methods} {rule.rule}")
    
    app.run(host='0.0.0.0', port=5001, debug=True)