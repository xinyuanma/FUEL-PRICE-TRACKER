import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import re

logging.basicConfig(level=logging.DEBUG)

def translate_time(finnish_time):
    # 简单的翻译字典
    translations = {
        'tuntia sitten': 'hours ago',
        'minuuttia sitten': 'minutes ago',
        'sekuntia sitten': 'seconds ago',
        'päivää sitten': 'days ago',
        'juuri nyt': 'just now',
        'tunti sitten': '1 hour ago',
    }
    
    for finnish, english in translations.items():
        if finnish in finnish_time:
            return finnish_time.replace(finnish, english)
    
    return finnish_time  # 如果没有匹配的翻译，返回原始字符串

def scrape_fuel_prices():
    try:
        url = "https://www.tankille.fi/oulu/"
        logging.info(f"Scraping fuel prices from {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        logging.debug(f"Response status code: {response.status_code}")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        all_data = {
            '95 E10': [],
            '98 E5': [],
            'Diesel': []
        }

        # 找到所有包含价格信息的表格
        tables = soup.find_all('table', class_='table')
        
        for i, table in enumerate(tables):
            if i == 0:
                fuel_type = '95 E10'
            elif i == 1:
                fuel_type = '98 E5'
            elif i == 2:
                fuel_type = 'Diesel'
            else:
                logging.warning(f"Unexpected table found. Skipping.")
                continue

            logging.info(f"Processing table for fuel type: {fuel_type}")
            
            rows = table.find_all('tr')[1:]  # 跳过表头
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 4:
                    station = cols[1].text.strip()
                    price_text = cols[2].text.strip()
                    updated = translate_time(cols[3].text.strip())  # 翻译时间
                    
                    # 使用更灵活的正则表达式来匹配价格
                    price_match = re.search(r'(\d+[.,]\d+)', price_text)
                    if price_match:
                        price = float(price_match.group(1).replace(',', '.'))
                        all_data[fuel_type].append({
                            'station': station,
                            'price': price,
                            'updated': updated,
                            'timestamp': datetime.now().isoformat()
                        })
                        logging.info(f"Extracted: {fuel_type} - {station}: €{price} (Updated: {updated})")
                    else:
                        logging.warning(f"Could not extract price for {station} ({fuel_type}): {price_text}")

        for fuel_type, prices in all_data.items():
            logging.info(f"Scraped {len(prices)} prices for {fuel_type}")
            
            # 删除以下循环
            # for price in prices:
            #     latitude, longitude = get_coordinates(price['station'])
            #     price['latitude'] = latitude
            #     price['longitude'] = longitude

        total_prices = sum(len(prices) for prices in all_data.values())
        logging.info(f"Scraped {total_prices} price entries in total")
        if total_prices == 0:
            logging.warning("No data scraped from the website")
        return all_data
    except Exception as e:
        logging.error(f"Error during scraping: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    prices = scrape_fuel_prices()
    for fuel_type, price_list in prices.items():
        print(f"\n{fuel_type}: {len(price_list)} prices")
        for price in price_list[:3]:  # 只打印前3个价格作为示例
            print(f"{price['station']}: €{price['price']} (Updated: {price['updated']})")