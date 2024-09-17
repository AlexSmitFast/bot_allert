# -*- coding: utf8 -*-
from matplotlib.pyplot import table
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import pickle
import telebot

# необходимые зависимости
# pip install lxml



# описание парсинга таблицы
# https://idatica.com/blog/parsing-tablitsy-s-sayta-na-python-poshagovoye-rukovodstvo/
def parsMOEX(bot : telebot.TeleBot, ID_ch, parslist):
    lst_url = ['https://www.moex.com/ru/contract.aspx?code=MXI-3.24',
               'https://www.moex.com/ru/contract.aspx?code=MIX-3.24',
               'https://www.moex.com/ru/contract.aspx?code=Si-3.24',
               'https://www.moex.com/ru/contract.aspx?code=RTSM-3.24',
               'https://www.moex.com/ru/contract.aspx?code=RTS-3.24',
               'https://www.moex.com/ru/contract.aspx?code=SPYF-6.24',
               'https://www.moex.com/ru/contract.aspx?code=SBRF-3.24',
               'https://www.moex.com/ru/contract.aspx?code=GAZR-3.24',
               'https://www.moex.com/ru/contract.aspx?code=LKOH-3.24',
               'https://www.moex.com/ru/contract.aspx?code=GMKN-3.24',
               'https://www.moex.com/ru/contract.aspx?code=NLMK-3.24',
               'https://www.moex.com/ru/contract.aspx?code=MGNT-3.24',
               'https://www.moex.com/ru/contract.aspx?code=VTBR-3.24',
               "https://www.moex.com/ru/contract.aspx?code=NASD-3.24",
               'https://www.moex.com/ru/contract.aspx?code=NG-3.24',
               'https://www.moex.com/ru/contract.aspx?code=BR-4.24',
               'https://www.moex.com/ru/contract.aspx?code=GOLD-3.24',
               'https://www.moex.com/ru/contract.aspx?code=SILV-3.24',
               'https://www.moex.com/ru/contract.aspx?code=ED-3.24'
               ]
    if len(parslist) == 0:
        parslist = lst_url

    options = Options()
    options.binary_location = r'C:\\Program Files\\Mozilla Firefox\\firefox.exe'
    # options.add_argument('user-agent=Mozilla/5.0 (Windows Phone 10.0; Android 4.2.1; Microsoft; Lumia 640 XL LTE) '
    # 'AppleWebKit/537.36 (KHTML, like Gecko) '
    # 'Chrome/42.0.2311.135 Mobile Safari/537.36 Edge/12.10166')
    driver = webdriver.Edge()
    # driver = webdriver.Firefox(executable_path=r'C:\\drv\\geckodriver.exe', options=options)
    driver.maximize_window()
    driver.get('https://www.moex.com/ru/contract.aspx?code=MXI-3.24')
    time.sleep(2)
    share = driver.find_element(By.CLASS_NAME, 'btn2-primary')
    share.click()

    msg = '\n'
    msg += 'Дата:\n'
    msg += '#позиции_физиков_фьючерсы\n'
    quantity_refresh = 2
    count_refresh = 0
    refresh_flag = True
    for url1 in parslist:
        
        try:
            driver.get(url1)  # загружаем таблицу
            driver.execute_script("window.scrollTo(0,500)")  # прокручиваем вниз на один экран
            time.sleep(3)
            # поиск таблицы с открытыми позициями
            # share_tb = driver.find_element(By.CLASS_NAME, 'ContractTablesOptions_overflow_3zzJO')
            # pg_sourse = driver.page_source
            soup = BeautifulSoup(driver.page_source, 'lxml')
            name = soup.find('h1').text
            #Предусмотреть метку в которой будет информация о вызвашей ошибку функции.
            # Так же предусмотреть обработку этой ошибки
            trs = soup.find('div', class_="ContractTablesOptions_overflow_3zzJO").find('table').find_all('tr')

            # print (trs[2].find_all('td', class_='text_right'))
            znaki = trs[2].find_all('td', class_='text_right')
            out = []
            for i in znaki:
                m = i.get_text()
                t = m.replace(u'\xa0', '')
                out.append(int(t))

            delta_pos = trs[3].find_all('td', class_='text_right')
            pos_delta_out = []
            for i in delta_pos:
                m = i.get_text()
                t = m.replace(u'\xa0', '')
                pos_delta_out.append(int(t))

            # print (out)
            f_lng = out[0]
            f_shrt = out[1]
            delta_lng = pos_delta_out[0]
            delta_shrt = pos_delta_out[1]
            msg1 = ''  # сообщение для текущего одного фьючерса
            msg1 += f'{name}\n'
            msg1 += f'{url1}\n'
            if f_shrt > f_lng:
                f_xxx = f_shrt / f_lng
                f_xxx = round(f_xxx, 2)
                msg1 += f'Шортов больше в {f_xxx} раз\n'
            elif f_lng > f_shrt:
                f_xxx = f_lng / f_shrt
                f_xxx = round(f_xxx, 2)
                msg1 += f'Логов больше в {f_xxx} раз\n'
            else:
                f_xxx = f_lng / f_shrt
                f_xxx = round(f_xxx, 2)
                msg1 += f'Примерно одинаково [{f_xxx}]\n'
            msg += msg1 + '\n'  # одно большое сообщение по всем фьючерсам
            msg1 += f'\nВсего лонгов: {f_lng}\nВсего. шортов: {f_shrt}'
            msg1 += f'\n\nИзм. лонгов: {delta_lng}\nИзм. шортов: {delta_shrt}'
            print(msg1)
            bot.send_message(ID_ch, msg1, disable_web_page_preview=True, disable_notification=True)
        except Exception as ex:
            print(url1)
            print('ОШИБКА: ', ex)
            bot.send_message(ID_ch, f'ОШИБКА загрузки и чтения:\n{url1}', disable_web_page_preview=True, disable_notification=True)
            driver.refresh()

    print("ИТОГО:\n", msg)
    driver.close()
    driver.quit()
    msg += f'#позиции_физиков_фьючерсы'
    return msg

if __name__ == "__main__":
    from startunit import TG_TOKEN_ERR_BOT as TG_TOKEN3
    bot = telebot.TeleBot(TG_TOKEN3, num_threads=5)
    parsMOEX(bot,320887273,'')


# GetFuturesMargin
# Метод получения размера гарантийного обеспечения по фьючерсам.
#
# Тело запроса — GetFuturesMarginRequest
#
# Тело ответа — GetFuturesMarginResponse

# GetFuturesMarginResponse
# Данные по фьючерсу
#
# Field	Type	Description
# initial_margin_on_buy	MoneyValue	Гарантийное обеспечение при покупке.
# initial_margin_on_sell	MoneyValue	Гарантийное обеспечение при продаже.
# min_price_increment	Quotation	Шаг цены.
# min_price_increment_amount	Quotation	Стоимость шага цены.
