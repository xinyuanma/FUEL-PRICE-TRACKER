import schedule
import time
import logging
from threading import Thread
from scraper import scrape_fuel_prices
from database import Database
from api import app

def job():
    # 爬取油价
    prices = scrape_fuel_prices()

    # 存储油价
    db = Database()
    db.update_fuel_prices(prices)
    db.close()

def run_flask():
    app.run(host='0.0.0.0', port=5001)

def main():
    logging.info("Starting main program...")
    
    # 启动Flask API在一个单独的线程中
    api_thread = Thread(target=run_flask)
    api_thread.start()
    
    # 立即运行一次任务
    job()
    # 设置每小时运行一次任务
    schedule.every().hour.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    db = Database()  # 确保数据库连接被创建
    db.create_tables()  # 确保表被创建
    scrape_fuel_prices()  # 初始化时爬取一次数据
    app.run(host='0.0.0.0', port=5001, debug=True)
    