# -*- coding: utf8 -*-
# pip install openpyxl
import os
os.system('cls' if os.name == 'nt' else 'clear')  # очистка консоли
print('Поиск роста или снижения 3 периода подряд')
print ('Директории для поиска сторонних библиотек и расширений')
import site
print(site.getsitepackages())
print()
print("Импорт модулей")
from bot_aller_btn import *
from bot_allert_globals import *
import parsMOIEX2 as pM
import mplfinance as mpf
import myutils
import numpy as np
import tinvest as ti # старый API Дрянькофф
from startunit import TOKEN
from startunit import TG_PA1_TOKEN as TG_TOKEN1
from startunit import TG_PA2_TOKEN as TG_TOKEN2
from startunit import TG_TOKEN_ERR_BOT
from startunit import TG_GRAFIK_POST_BOT as TG_GRAF_BOT
G_VALID_BOT = TG_TOKEN1

from tinkoff.invest import Client, AsyncClient, InstrumentStatus, InstrumentIdType, ShareResponse, RequestError, OrderType, CandleInterval, \
    HistoricCandle, OperationType, PortfolioPosition, OrderDirection, Future, Quotation,Share, services, SecurityTradingStatus, \
    GetOperationsByCursorRequest, OperationState, OperationItem
from tinkoff.invest.utils import quotation_to_decimal, decimal_to_quotation
from datetime import datetime, timedelta, timezone
import time
from progress.bar import IncrementalBar, Bar
import pandas as pd
import telebot
from telebot import types, util  # для указания типов и переноса текста
import subprocess
from threading import Thread
from mplfinance.original_flavor import candlestick_ohlc
# from mpl_finance import candlestick_ohlc
import matplotlib.dates as mpl_dates
import matplotlib
import matplotlib.pyplot as plt
import logging
# Настройка журналирования
# logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
bot = telebot.TeleBot(G_VALID_BOT)
print('Создаем экземпляр  бота для ошибок')
err_bot = telebot.TeleBot(TG_TOKEN_ERR_BOT)
print('Создаем экземпляр бота для для графиков')
graf_bot = telebot.TeleBot(TG_GRAF_BOT)

# глобальные переменные и значения по умолчанию
g_reg_msg = {
    'msg_count': 0, # счетчик сообщений
    'msg_t_30': [],
    'msg_t_x': [],
    'mg_time': [],
    'msg_dt': []
}
glodal_inp_interval =  CandleInterval.CANDLE_INTERVAL_DAY # значение интервала обработки сервиса акций
global_interval_load = CandleInterval.CANDLE_INTERVAL_DAY
global_interval_load_s = '1 день'
global_max_range = round(24 * 60 / 30, 0)
global_inp_var = 1  # значение по умолчанию: RUB
global_val_nom = "RUB"
global_in_progress_state = False
global_bag_of_stocks = []  # весь список объектов акций для фильтрации загруженный через openAPIv1. Загружается при запуске бота в main
global_finaly_bag_of_stocks = []  # отфильтрованный список акций для обработки и загрузки
global_all_list = []  # список со всеми загруженными свечами по отфильтрованному списку акций
all_list = []
g_full_list_sh2 = []
global_list_sel2 = []  # глобальный список акций для выборки 2
global_list_sel3 = []  # глобальный список акций для выборки 3
global_set_from_orders = {
    'user_id': '320887273',
    'user_name': 'Kos_ST',
    'user_first_name': 'Konstantin',
    'oper_block_bt': True,  # Блокировать возможность совершать сделаки кнопками из стакана котировок
    'oper_confirm': False,  # Требовать подтверждения операций при совершени сделок черезе кнопки
    'oper_ac_ID': global_options['ac_id']  # счет для совершения операций
}
ADIMIN_ID_TG = '320887273'
# Глобальный датафрейм с совершенными операциями
g_df = pd.DataFrame(columns=["figi", "direction", "price", "quantity", "comis", "time"])
# Глобальный датафрейм для хранения портфеля виртуальных сделок
g_df_p = pd.DataFrame(columns=["figi", "avg_price", "quantity"])
# Глобальный фрейм хранения позиций из портфеля bag of stocks
g_df_bs = pd.DataFrame(columns=['time','figi','price','quantity'])
matplotlib.use('agg')  # чтобы не было ошибки :
# plotting.py:475: UserWarning: Starting a Matplotlib GUI outside the main thread will likely fail.
g_long_count = 0 # счетчик пауз циклов создаваемых telegramm


# Главная функция при запуске бота
def main() -> None:
    global global_f_opt, glodal_inp_interval, global_interval_load, global_interval_load_s, g_df, g_df_p, g_df_bs
    global global_max_range, global_inp_var, global_val_nom, global_bag_of_stocks, global_finaly_bag_of_stocks
    global global_options, global_all_list, all_list, g_full_list_sh2, global_list_sel3, global_list_sel2, bot
    print(global_options['last_interval_calc'])
    try:
        reg_msg()
        bot.send_message(ADIMIN_ID_TG,f'АЛЯ УЛЮ')
    except Exception as e:
        telega_error (e)
    if os.name == 'nt':
        subprocess.call("TASKKILL /f  /IM  CHROME.EXE")
        subprocess.call("TASKKILL /f  /IM  CHROMEDRIVER.EXE")

    if os.path.isfile('df_oper.csv'):
        g_df = pd.read_csv ('df_oper.csv')
    else:
        g_df.to_csv('df_oper.csv', index = False)
    
    if os.path.isfile('df_portf.csv'):
        g_df_p = pd.read_csv ('df_portf.csv')
    else:
        g_df_p.to_csv('df_portf.csv', index = False) 

    if os.path.isfile('g_df_bs.csv'):
        g_df_bs = pd.read_csv ('g_df_bs.csv')
    else:
        g_df_bs.to_csv('g_df_bs.csv', index = False) 
    
    # Подключение через OpenAPI, выделить в отдельную функцию с обработкой исключений
    print('\nПодключаемся через OpenAPI')
    client = ti.SyncClient(TOKEN)
    print('Подключение: Выполнено')

    # получаем текущую дату и время
    curr_time = datetime.now(timezone.utc).astimezone()
    # переводим в текстовый вид
    d1 = datetime.strftime(curr_time, '%d.%m.%Y')
    ht1 = datetime.strftime(curr_time, '%H:%M:%S')
    print(f'Текущая дата: {d1} \nВремя: {ht1}')

    # Получаем список всех акций OpenAPI
    print('\nТИНьКОФФ СЛОМАЛ APIv1\n')
    # totalstocks = ti.schemas.MarketInstrumentListResponse

    try:
        with Client(TOKEN) as client_g:
            # Метод получения списка акций.
            dict_stoks = client_g.instruments.shares(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)
            global_bag_of_stocks = dict_stoks.instruments
            print(len(global_bag_of_stocks), " акций загружено через APIv2\n")

    except Exception as e:
        print()
        print('ВОЗНИКЛА ОШИБКА загрузки списка акций')
        print(datetime.now(timezone.utc).astimezone())
        print("Текст ошибки:")
        print(e)


    # Задаем настройки по умолчанию

    # задаем интервал загрузки и максимальную глубину

    # По результатам выбора фильтруем для загрузки баров список акций global_inp_var и
    # global_val_nom, по умолчанию установлены в RUB
    if global_inp_var == 0:
        print('Добавление записей номинированных в: USD')
        global_val_nom = "usd"
        for i in global_bag_of_stocks:
            if i.currency == ti.Currency.usd:
                global_finaly_bag_of_stocks.append(i)
    elif global_inp_var == 1:
        print('Добавление акций с номиналом: RUB')
        global_val_nom = "RUB"
        for i in global_bag_of_stocks:
            if i.currency == 'rub':
                global_finaly_bag_of_stocks.append(i)
    elif global_inp_var == 2:
        print('Добавление записей с номиналом: EUR')
        global_val_nom = "EUR"
        for i in global_bag_of_stocks:
            if i.currency == ti.Currency.eur:
                global_finaly_bag_of_stocks.append(i)
    else:
        print('Будут загружены и обработаны все акции из списка БЕЗ фильтрации')
        global_inp_var = 3
        global_val_nom = "USD, RUB, EUR"
        global_finaly_bag_of_stocks = global_bag_of_stocks
    print(f'Количество акций для загрузки и обработки после фильтрации: {len(global_finaly_bag_of_stocks)} ')

    # Устанавливаем интервал (interval_load) и максимальную глубину загрузки информации (max_range)
    print(glodal_inp_interval)
    if glodal_inp_interval == 0:
        interval_load = CandleInterval.CANDLE_INTERVAL_1_MIN
        max_range = 24 * 60
    elif glodal_inp_interval == 1:
        interval_load = CandleInterval.CANDLE_INTERVAL_2_MIN
        max_range = round(24 * 60 / 2, 0)
    elif glodal_inp_interval == 2:
        interval_load = CandleInterval.CANDLE_INTERVAL_3_MIN
        max_range = round(24 * 60 / 2, 0)
    elif glodal_inp_interval == 3:
        interval_load = CandleInterval.CANDLE_INTERVAL_5_MIN
        max_range = round(24 * 60 / 5, 0)
    elif glodal_inp_interval == 4:
        interval_load = CandleInterval.CANDLE_INTERVAL_10_MIN
        max_range = round(24 * 60 / 10, 0)
    elif glodal_inp_interval == 5:
        interval_load = CandleInterval.CANDLE_INTERVAL_15_MIN
        max_range = round(24 * 60 / 15, 0)
    elif glodal_inp_interval == 6:
        global_interval_load = CandleInterval.CANDLE_INTERVAL_30_MIN
        global_interval_load_s = '30 минут'
        global_max_range = round(24 * 60 / 30, 0)
        print('Выбран интервал: 30 минут','\nмаксимальная глубина интервалов:',global_max_range)
    elif glodal_inp_interval == 7:
        global_interval_load = CandleInterval.CANDLE_INTERVAL_HOUR
        global_max_range = round(24 * 7, 0)
        global_interval_load_s = '1 ЧАС'
        print('Выбран интервал: 1 ЧАС')
    elif glodal_inp_interval == 8:
        global_interval_load = CandleInterval.CANDLE_INTERVAL_DAY
        global_max_range = 365
        global_interval_load_s = 'ДЕНЬ'
        print('Выбран интервал: ДЕНЬ')
    elif glodal_inp_interval == 9:
        global_interval_load = CandleInterval.CANDLE_INTERVAL_WEEK
        global_max_range = 52 * 2
        global_interval_load_s = 'НЕДЕЛЯ'
        print('Выбран интервал: НЕДЕЛЯ')
    elif glodal_inp_interval == 10:
        global_interval_load = CandleInterval.CANDLE_INTERVAL_MONTH
        global_max_range = 12 * 10
        global_interval_load_s = 'МЕСЯЦ'
        print('Выбран интервал: МЕСЯЦ')
    else:
        global_interval_load = CandleInterval.CANDLE_INTERVAL_MONTH
        global_max_range = 12 * 10
        global_interval_load_s = 'МЕСЯЦ'
        print('Выбран интервал: МЕСЯЦ')

    # На основании интервала и максимальной глубины расчитываем даты начала и окончания загрузки баров
    # дату и время от которой вести загрузку и расчет устанавливаем текущую.

    # Руками устанавливаем нужную дату.
    # end_time: дата и время окончания загрузки баров
    # end_time=datetime(2022,5,14,6,45,00)
    # или берем текущую дату и время
    end_time = curr_time

    print("\nДата и время от которых в глубину будет обработка:")
    end_time_d1_s = datetime.strftime(end_time, '%d.%m.%Y')
    end_time_ht1_s = datetime.strftime(end_time, '%H:%M:%S')
    print("Дата:", end_time_d1_s)
    print('Время:', end_time_ht1_s)

    # time_frame_s: выбранный временной интервал для поиска по условию
    it1 = 0  # ставим в ноль счетчик загруженных записей в текущей партии запросов


  # ЗАПУСКАЕМ БОТА
    while True:
        try:
            bot_tok = bot.token
            bot_name_s = bot.get_my_name()
            bot_des_s = bot.get_my_description()
            print(f'Начинам запуск БОТА.......... \n {bot_tok}\n {bot_name_s}\n {bot_des_s}')
            create_bot()  # создаем бота и назначаем на него все нужные функции и реакции на события
            err_count = global_f_opt['bot_err_count']
            global_f_opt['In_process'] = False
            global_f_opt['repeat_flag'] = False

            # ЗАПУСК функции graf_3 через ПОТОК
            global_f_opt['repeat_flag'] = True
            print('Запуск функции graf_3 через поток')
            gr_th = Thread(target=graf_3, args=(bot, ADIMIN_ID_TG), name = "graf_3_Thread", daemon=True)
            gr_th.start()
            show_run_repit_btn(bot, ADIMIN_ID_TG, 'Цикл_gr')

            if err_count == 0:
                print('БОТ ГОТОВ и ЖДЕТ КОМАНДУ!!!!! \nСтарт работы')
                try:
                    reg_msg()
                    bot.send_message(ADIMIN_ID_TG,f'БОТ ГОТОВ и ЖДЕТ КОМАНДУ!!!!! \nСтарт работы')
                    dt = datetime.now(timezone.utc).astimezone()
                    err_bot.send_message(ADIMIN_ID_TG,f'{dt}\nБОТ ALLER ГОТОВ и ЖДЕТ КОМАНДУ!!!!! \nСтарт работы\n#bot_first_start')
                except Exception as e:
                    telega_error (e)
            else:
                print(f'БОТ ГОТОВ и ЖДЕТ КОМАНДУ!!!!! \nперзагрузка №{err_count}')
                try:
                    reg_msg()
                    bot.send_message(ADIMIN_ID_TG,f'БОТ ГОТОВ и ЖДЕТ КОМАНДУ!!!!! \nперзагрузка №{err_count}')
                    err_bot.send_message(ADIMIN_ID_TG,f'БОТ ALLER ГОТОВ и ЖДЕТ КОМАНДУ!!!!! \nперзагрузка №{err_count}\n#bot_reload')
                except Exception as e:
                    telega_error (e)
            
            # ПАРАМЕТРЫ bot.polling
            # skip_pending: пропускать старые обновления
            # non_stop: Не останавливайте опрос при возникновении исключения ApiException.
            # interval: Задержка между двумя запросами обновления
            # timeout:  Тайм-аут запроса соединения
            print ("Старт bot.polling")
            bot.polling(non_stop=True, skip_pending=True, interval=0, timeout=60)

        except Exception as e:
            global_f_opt['bot_err_count'] +=1
            print()
            print('ВОЗНИКЛА ОШИБКА, по непонятной причине, в bot.polling блоке' )
            print(now_dtime())
            print(e)
            print()
            try:
                err_bot.send_message(ADIMIN_ID_TG,f'ВОЗНИКЛА ОШИБКА, по непонятной причине, в bot.polling блоке')
            except Exception as e:
                telega_error (e)
            # ЕСЛИ работал цикл, то останавливаем его
            if global_f_opt['repeat_flag'] :
                what_is_repeat = global_f_opt['repeat_flag']
                print ('ЦИКЛ был запущен, когда произошла ошибка')
                print (f'Значение переменной global_f_opt[repeat_flag] = {what_is_repeat}')
                print ("ЦИКЛ будет остановлен")
                global_f_opt['In_process'] = False
                global_f_opt['repeat_flag'] = False
            else:
                what_is_repeat = global_f_opt['repeat_flag']
                print ("ЦИКЛ не выполнялся, когда произошла ошибка")
                print (f'Значение переменной global_f_opt[repeat_flag] = {what_is_repeat}')
                print ('На всякий случай пометим переменную ЦИКЛа на остановку ')
                global_f_opt['In_process'] = False
                global_f_opt['repeat_flag'] = False
            err_count = global_f_opt['bot_err_count']
            print (f"Счетчик количества возникновения исключений:  {err_count}\n  при работе бота от начала запуска программы:")
            print('Погнали еще раз.. ПЕРЕЗАПУСК БОТА')
            bot.stop_polling()
            print("пауза 15 сек...")
            time.sleep(15)
            print("Пауза 15 сек закончилась\nТекущее дата и время:\n",now_dtime())
            print()


def now_dtime():
    return datetime.now(timezone.utc).astimezone()

def datetime_now():
    return datetime.now(timezone.utc).astimezone()

def now_dt():
    return datetime.now(timezone.utc).astimezone()

def now_date_txt_file():
    return datetime.strftime(now_dtime(), '%d-%m-%Y')

def d_t_to_txt (dt1):
    """"    Перевод заданной даты и времени в текст    """
    return datetime.strftime(dt1, '%d.%m.%Y %H:%M:%S')

def datetime_txt ():
    """"    Перевод текущей даты и времени в текст    """
    dt1 = now_dtime()
    return datetime.strftime(dt1, '%d.%m.%Y %H:%M:%S')
    

# простой вывод в консоль текущей даты и времени
def print_date_time_now():
    # получаем текущую дату и время
    curr_time = datetime.now(timezone.utc).astimezone()
    # переводим в текстовый вид
    d1 = datetime.strftime(curr_time, '%d.%m.%Y')
    ht1 = datetime.strftime(curr_time, '%H:%M:%S')
    print(f'Текущая дата: {d1} '
          f'\nВремя: {ht1}')


# проверка на доступность торгов по инструменту
def is_activ(ti_g_client, FIGI, type_figi):
    if type_figi == 'futures':
        pass
    pass


def now_time_txt_file():
    return datetime.strftime(now_dtime(), '%H-%M-%S')

def gen_msg_actual_sets():
    '''генерация сообщения с актуальными текущими настройками'''
    actual_name = global_f_opt['full_future_name'] # какое актуальное наименование
    actual_figi = global_f_opt['future_FIGI']
    actual_interv = what_interval() # какой актуальный интервал
    actual_depth =  global_f_opt['depth_load_bars']
    actual_in_process = global_f_opt['In_process']
    actual_tiker = ''
    if actual_in_process ==True:
        actual_in_process_s = 'РАБОТАЕТ'
    else:
        actual_in_process_s = 'НЕ РАБОТАЕТ'
    msg = ''
    msg += 'Текущие настройки:\n'
    msg += f'    имя:  {actual_name}\n'
    msg += f'    тикер:  {actual_tiker}\n'
    msg += f'    figi:  {actual_figi}\n'
    msg += f'    интервал:  {actual_interv}\n'
    msg += f'    количество бар:  {actual_depth}\n'
    msg += f'    состояние цикла:  {actual_in_process_s}'
    return msg

# вкл/откл кнопки операций с фуючерсной позицией
def oper_selector (t_bot: telebot.TeleBot, ID_ch, name_btn):
    if global_set_from_orders['oper_block_bt']:
        global_set_from_orders['oper_block_bt'] = False
        t_bot.send_message(ID_ch, text="✅Кнопки раблокированы", disable_notification=True)
    else :
        global_set_from_orders['oper_block_bt'] = True
        try:
            reg_msg()
            t_bot.send_message(ID_ch, text="⛔️Кнопки заблокированы", disable_notification=True)
        except Exception as e:
            telega_error (e)

# вкл/откл отображения результата по отдельным операциям позиции
def show_pos_selector (t_bot: telebot.TeleBot, ID_ch, name_btn):
    if global_f_opt['show_oper_in_chat']:
        global_f_opt['show_oper_in_chat'] = False
        try:
            reg_msg()
            t_bot.send_message(ID_ch, text="ОТКЛЮЧЕНО отображение label_oper", disable_notification=True)
        except Exception as e:
            telega_error (e)
    else :
        global_f_opt['show_oper_in_chat'] =  True
        try:
            reg_msg()
            t_bot.send_message(ID_ch, text="ВКЛЮЧЕНО отображение label_oper", disable_notification=True)
        except Exception as e:
            telega_error (e)

# вывод в чат информации о годовой комиссии и зачислении марж, а также по отдельным дням
def comiss_report (t_bot: telebot.TeleBot, ID_ch, msg_txt, show_dds = False):
    """
    вывод в чат информации о годовой комиссии и зачислении марж, а также по отдельным дням
    msg_txt должно иметь одно из значений: f11, f1, f1-, f1--, f1---
    show_dds доп. отображение зачисления и вывода средств
    """
    
    # номер аккаунта по которому запрашиваем информацию
    account_id = global_options['ac_id']        
    with Client(TOKEN) as client:
        # информация с начала года
        if msg_txt == "f11": 
            c_d = datetime.now(timezone.utc).astimezone() - timedelta(days=0)
            # c_d = datetime(2022, 12, 31, 23, 59, 59)
            # задаем первый день года
            f_d = datetime(c_d.year, 1, 1, 0, 0, 0)
            t_d = datetime(c_d.year, c_d.month, c_d.day, 23, 59, 59)

        # информация за день
        if msg_txt == "f1" or msg_txt == "F1" or msg_txt == "Ф1"  or msg_txt == "ф1":  
                c_d = datetime.now(timezone.utc).astimezone() - timedelta(days=0)
                f_d = datetime(c_d.year, c_d.month, c_d.day, 0, 0, 0)
                t_d = datetime(c_d.year, c_d.month, c_d.day, 23, 59, 59)

         # информация за предыдущий день
        if msg_txt == "f1-" or msg_txt == "F1-" or msg_txt == "Ф1-"  or msg_txt == "ф1-": 
            c_d = datetime.now(timezone.utc).astimezone() - timedelta(days=1)
            f_d = datetime(c_d.year, c_d.month, c_d.day, 0, 0, 0)
            t_d = datetime(c_d.year, c_d.month, c_d.day, 23, 59, 59)
        
        # информация два дня назад
        if msg_txt == "f1--" or msg_txt == "F1--" or msg_txt == "Ф1--"  or msg_txt == "ф1--":  
            c_d = datetime.now(timezone.utc).astimezone() - timedelta(days=2)
            f_d = datetime(c_d.year, c_d.month, c_d.day, 0, 0, 0)
            t_d = datetime(c_d.year, c_d.month, c_d.day, 23, 59, 59)

        # информация три дня назад
        if msg_txt == "f1---" or msg_txt == "F1---" or msg_txt == "А1---"  or msg_txt == "а1---":  
            c_d = datetime.now(timezone.utc).astimezone() - timedelta(days=3)
            f_d = datetime(c_d.year, c_d.month, c_d.day, 0, 0, 0)
            t_d = datetime(c_d.year, c_d.month, c_d.day, 23, 59, 59)
        
        # запрос всех операций из указанного диапазона дат
        # ВНИМАНИЕ ТЫНЬКОФФ НЕ ВСЕ ОПЕРАЦИИ ВЫДАЕТ!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        operations = client.operations.get_operations(account_id=account_id, from_=f_d, to=t_d)
        operations = operations.operations
        if len(operations) > 0:
            fack_date = operations[-1].date.astimezone()
            print ("Требовалось:")
            print ("Окончание:", d_t_to_txt (t_d))
            print ('Начало: ', d_t_to_txt (f_d))
            print ('Фактически:')
            print ('Начало: ', d_t_to_txt(operations[0].date.astimezone()))
            print ("Окончание:", d_t_to_txt(fack_date))
            print ()
            circle_1 = range (10)
            t_d2 = fack_date - timedelta(seconds=1)
            for m in circle_1:
                operations2 = client.operations.get_operations(account_id=account_id, from_=f_d, to=t_d2)
                operations2 = operations2.operations
                if len(operations2) > 0:
                    fack_date = operations2[-1].date.astimezone()
                    print (f"[{m}] Требовалось:")
                    print ("Окончание:", d_t_to_txt (t_d2))
                    print ('Начало: ', d_t_to_txt (f_d))
                    print ('Фактически:')
                    print ('Начало: ', d_t_to_txt(operations2[0].date.astimezone()))
                    print ("Окончание:", d_t_to_txt(fack_date))
                    print (f'Глубина: {len(operations2)}')
                    operations= operations + operations2
                    if len(operations2) <1000:
                        break
                    t_d2 = fack_date - timedelta(seconds=1)
                    print()
                else:
                    break
        # ВНИМАНИЕ ТЫНЬКОФФ сломал функцию
        repit_read = True # Повторять пока в списке операций не появится нужная дата

        summ = 0
        summ2 = 0
        summ3 = 0
        summ4 = 0
        summ5 = 0
        summ6 = 0
        summ7 = 0
        cunter_oper = 0
        cunter_oper2 = 0
        cunter_oper3 = 0
        cunter_oper4 = 0
        cunter_oper5 = 0
        cunter_oper6 = 0
        cunter_oper7 = 0
        msg_input_many = 'Операции зачисления и вывода средств:\n\n'
        for oper in operations:
            # считаем комиссию за сделки с активами в рублях
            if oper.operation_type == OperationType.OPERATION_TYPE_BROKER_FEE and oper.currency == 'rub':
                k1 = cast_money(oper.payment)
                d1 = oper.date + timedelta(hours=3)
                summ += k1
                cunter_oper += 1
                # print(f'[1.{cunter_oper}]: {k1}      {d1}')

            # считаем стоимость обслуживания
            if oper.operation_type == OperationType.OPERATION_TYPE_SERVICE_FEE and oper.currency == 'rub':
                k2 = cast_money(oper.payment)
                d2 = oper.date + timedelta(hours=3)
                summ2 += k2
                cunter_oper2 += 1
                # print(f'[2.{cunter_oper2}]: {k2}      {d2}')

            # считаем удержания за маржинальные позиции
            if oper.operation_type == OperationType.OPERATION_TYPE_MARGIN_FEE and oper.currency == 'rub':
                k3 = cast_money(oper.payment)
                d3 = oper.date + timedelta(hours=3)
                summ3 += k3
                cunter_oper3 += 1
                # print(f'[3.{cunter_oper3}]: {k3}      {d3}')

            # OPERATION_TYPE_ACCRUING_VARMARGIN	26	Зачисление вариационной маржи.
            if oper.operation_type == OperationType.OPERATION_TYPE_ACCRUING_VARMARGIN and \
                    oper.currency == 'rub':
                k4 = cast_money(oper.payment)
                d4 = oper.date + timedelta(hours=3)
                summ4 += k4
                cunter_oper4 += 1
                # print(f'[4.{cunter_oper4}]: {k4}      {d4}')

            # OPERATION_TYPE_WRITING_OFF_VARMARGIN	27	Списание вариационной маржи.
            if oper.operation_type == OperationType.OPERATION_TYPE_WRITING_OFF_VARMARGIN and \
                    oper.currency == 'rub':
                k5 = cast_money(oper.payment)
                d5 = oper.date + timedelta(hours=3)
                summ5 += k5
                cunter_oper5 += 1
            
            # Доп. информация о зачислении и выводе средств        
            #Пополнение брокерского счета 
            if oper.operation_type == OperationType.OPERATION_TYPE_INPUT and \
                    oper.currency == 'rub' :
                k6 = cast_money(oper.payment)
                d6 = oper.date + timedelta(hours=3)
                d6_txt = datetime.strftime(d6, '%d.%m.%Y %H:%M:%S')
                summ6 += k6
                cunter_oper6 += 1
                msg_input_many += f'Засчислено:\n{d6_txt}   {k6} руб.\n\n'
            #вывод средств
            if oper.operation_type == OperationType.OPERATION_TYPE_OUTPUT and \
                    oper.currency == 'rub' :
                k7 = cast_money(oper.payment)
                d7 = oper.date + timedelta(hours=3)
                d7_txt = datetime.strftime(d7, '%d.%m.%Y %H:%M:%S')
                summ7 += k7
                cunter_oper7 += 1
                msg_input_many += f'ВЫВОД средств:\n{d7_txt}   {k7} руб.\n\n' 
            
        # вывод дневного результата
        if msg_txt == "f1" or msg_txt == "F1" or msg_txt == "Ф1"  or msg_txt == "ф1" \
            or msg_txt == "f1-" or msg_txt == "F1-" or msg_txt == "Ф1-"  or msg_txt == "ф1-" or msg_txt == "f1--" \
            or msg_txt == "f1--" or msg_txt == "F1--" or msg_txt == "Ф1--"  or msg_txt == "ф1--" \
            or msg_txt == "f1---" or msg_txt == "F1---" or msg_txt == "А1---"  or msg_txt == "а1---":
            msg = ''
            msg = f'{c_d.day}-{c_d.month}\n'
            msg += f'ком:  {round(summ, 2)}\n'
            msg += f'зач:  {round(summ4, 2)}\n'
            msg += f'спи:  {round(summ5, 2)}\n'
            msg += f'итг:  {round((summ + summ4 + summ5), 2)}'
            t_bot.send_message(ID_ch, msg)

        # вывод годового результата
        if msg_txt == "f11" and not (show_dds):
            msg = ''
            msg += f"Информация по КОМИССИЯМ за {c_d.year} год:\n"
            msg += f'от {c_d.day}-{c_d.month}-{c_d.year}'
            msg += f'По счету {account_id}:\n\n'
            msg += f'КОМИСИИ:\n'
            msg += f'Сумма за сделки:   {round(summ, 2)} руб.\n'
            msg += f'Сумма за обслугу счета:   {round(summ2, 2)} руб.\n'
            msg += f'Сумма за перенос позиций:   {round(summ3, 2)} руб.\n'
            msg += f'ИТОГО комисии:   {round(summ + summ2 + summ3, 2)} руб.\n\n'
            msg += f'Сумма зачислений вар. маржи:   {round(summ4, 2)} руб.\n'
            msg += f'Сумма списаний вар. маржи:   {round(summ5, 2)} руб.\n'
            msg += f'ИТОГО по вар. марже:   {round((summ4 + summ5), 2)} руб.\n\n'
            msg += f'ИТОГ по комиссиям и вар. марже:   {round((summ + summ2 + summ3 + summ4 + summ5), 2)} руб.\n'
            msg += f'#комиссии_итог'
            t_bot.send_message(ID_ch, msg)
        # Вывод только зачислений и списаний
        if show_dds and msg_txt == "f11":
            # вывод результата по зачислениям и списаниям средств
            msg_input_many += f'\n#ЗАЧИСЛЕНИЯ\nВсего зачилено за период:\n {summ6}\n\n'
            msg_input_many += f'#ВЫВОД_СРЕДСТВ\nВсего выведено за период:\n {summ7}'
            for message1 in util.smart_split(msg_input_many, 4000):
                t_bot.send_message(ID_ch, message1, disable_web_page_preview=True)

            print()
            print(f'Сумма комиссий за сделки:   {round(summ, 2)} руб.')
            print(f'Сумма за обслугу счета:   {round(summ2, 2)} руб.')
            print(f'Сумма за маржинальные позиции:   {round(summ3, 2)} руб.')
            print(f'Сумма зачислений вар. марже:   {round(summ4, 2)} руб.')
            print(f'Сумма списаний вар. марже:   {round(summ5, 2)} руб.')
            print(f'Итог по вар. марже:   {round((summ4 + summ5), 2)} руб.')
            print(f'Итог по комиссиям и вар. марже:  {round((summ + summ2 + summ3 + summ4 + summ5), 2)} руб.\n')   
    

def porfolio_report (t_bot: telebot.TeleBot, ID_ch):
    t_bot.send_message(ID_ch, '💼')
    # ПРОВЕРЯТЬ, что за учетка запустила эту команду
    with Client(TOKEN) as client_gs:
        portfel = client_gs.operations.get_portfolio(account_id=global_options['ac_id'])
        pos_prt = portfel.positions
        df = cr_df_pos(pos_prt)
        msg = ''
        for m in range(df.shape[0]):
            msg += f'[{m}] {df.iloc[m, 0]}\n   {df.iloc[m, 2]} шт.\n' \
            f'   {df.iloc[m, 8]} >> {df.iloc[m, 7]}\n   [{df.iloc[m, 5]}]\n\n'
            
            print(f'[{m}] {df.iloc[m, 0]}  {df.iloc[m, 1]}   {df.iloc[m, 2]}  {df.iloc[m, 3]} >> {df.iloc[m, 7]}'
                f'   [{df.iloc[m, 5]}]  {df.iloc[m, 6]}   {df.iloc[m, 8]}   {df.iloc[m, 9]}')
            
        msg += f'#портфель'
        t_bot.send_message(ID_ch, text=msg)


def show_good_day_report (t_bot: telebot.TeleBot, msg_obj: telebot.types.Message, name_btn):
    ID_ch = msg_obj.chat.id
    # состав портфеля f3
    porfolio_report (t_bot, ID_ch)

    # показать итог за год по комиссиям и зачилением маржи (без пополнений) f11
    comiss_report (t_bot,ID_ch,'f11', show_dds = False)

    # показать итог за день f1
    comiss_report (t_bot,ID_ch, 'f1', show_dds = False)

    # показать аналитику бара
    figi = global_f_opt['future_FIGI']
    msg = graf_analitiks(figi=figi)
    if len(msg) > 0:
        try:
            reg_msg()
            t_bot.send_message(ID_ch, text=msg, disable_notification=True)
        except Exception as e:
            telega_error (e)

    # показать дневные графики фьючерсов
    try:
        reg_msg()
        t_bot.send_message(ID_ch,'👀',disable_notification=True)
    except Exception as e:
        telega_error (e)
    load_period = 20
    load_inter = "DAY"
    show_futur_graf (t_bot, ID_ch, '⭐️Показать фьючерсы', load_period, load_inter, 'graf')
    load_period = 15
    load_inter = "WEEK"
    show_futur_graf (t_bot, ID_ch, '⭐️Показать фьючерсы', load_period, load_inter, 'graf')
    
    # показать парсинг pMoex
    klst = []
    msg = ''
    msg = pM.parsMOEX(t_bot, ID_ch, klst)
    for message1 in util.smart_split(msg, 4000):
        try:
            reg_msg()
            t_bot.send_message(ID_ch, message1, disable_web_page_preview=True)
        except Exception as e:
            telega_error (e)

    # показать отклонения фьючерсов
    show_delta_futures (t_bot, ID_ch)

    # показать годовое отклонение всех активов (желательно только RU)
    show_stoks_year_fun(t_bot, ID_ch, 2022, 2023)
    
    # показать аналитику бара за день
    figi = global_f_opt['future_FIGI']
    msg = graf_analitiks(figi = figi)
    if len(msg) > 0:
        try:
            reg_msg()
            t_bot.send_message(ID_ch, text=msg, disable_notification=True)
        except Exception as e:
            telega_error (e)
  
    # показать все фьючерсы

# ручное выставление заявки
def manual_orders (t_bot: telebot.TeleBot, ID_ch, name_btn):
    # PostOrderRequest 
    # https://tinkoff.github.io/investAPI/orders/#postorderrequest
    account_id = global_options['ac_id']
    with Client(TOKEN) as client:
        # akt_orders = client.orders.post_order (account_id = account_id).orders
        pass
        

# отображение информации о марже
def show_aktiv_orders (t_bot: telebot.TeleBot, ID_ch, name_btn):
    # GetOrdersRequest
    account_id = global_options['ac_id']
    with Client(TOKEN) as client:
        akt_orders = client.orders.get_orders (account_id = account_id).orders
        if len(akt_orders) > 0:
            ord_list_info = []
            
            for order in akt_orders:
             msg = ''
             msg += f'order_id:  {order.order_id}\n'
             msg += f'order_date:  {order.order_date}\n'
             msg += f'{order.figi}\n'
             msg += f'Текущий статус заявки: {order.execution_report_status}\n'
             msg += f'Направление заявки: {order.direction}\n'
             msg += f'Тип заявки: {order.order_type}\n' 
             msg += f'Запрошено лотов: {order.lots_requested}\n'
             msg += f'Начальная цена заявки: {cast_money(order.initial_order_price)}\n'  
             msg += f'Исполнено лотов: {order.lots_executed}\n'
             t_bot.send_message(ID_ch, text=msg, disable_notification=True)  
           
            # order_id	string	Биржевой идентификатор заявки.
            # execution_report_status	OrderExecutionReportStatus	Текущий статус заявки.
            # lots_requested	int64	Запрошено лотов.
            # lots_executed	int64	Исполнено лотов.
            # initial_order_price	MoneyValue	Начальная цена заявки. Произведение количества запрошенных лотов на цену.
            # executed_order_price	MoneyValue	Исполненная цена заявки. Произведение средней цены покупки на количество лотов.
            # total_order_amount	MoneyValue	Итоговая стоимость заявки, включающая все комиссии.
            # average_position_price	MoneyValue	Средняя цена позиции по сделке.
            # initial_commission	MoneyValue	Начальная комиссия. Комиссия, рассчитанная на момент подачи заявки.
            # executed_commission	MoneyValue	Фактическая комиссия по итогам исполнения заявки.
            # figi	string	Figi-идентификатор инструмента.
            # direction	OrderDirection	Направление заявки.
            # initial_security_price	MoneyValue	Начальная цена за 1 инструмент. Для получения стоимости лота требуется умножить на лотность инструмента.
            # stages	Массив объектов OrderStage	Стадии выполнения заявки.
            # service_commission	MoneyValue	Сервисная комиссия.
            # currency	string	Валюта заявки.
            # order_type	OrderType	Тип заявки.
            # order_date	google.protobuf.Timestamp	Дата и время выставления заявки в часовом поясе UTC.
            # instrument_uid	string	UID идентификатор инструмента.
            # order_request_id	string	Идентификатор ключа идемпотентности, переданный клиентом, в формате UID. Максимальная длина 36 символов.
        else:
            print (f"Активных заявок по счету {account_id}  НЕТ !!!")
            t_bot.send_message(ID_ch, text=f"Активных заявок по счету {account_id}  НЕТ !!!", disable_notification=True)


# отображение списка последних операций за 20 дней
def show_last_operation (t_bot: telebot.TeleBot, ID_ch, opt_fun, name_btn):
    '''opt_fun:\n
    show_month_yeld_now доходность за текущий месяц\n
    full перечень всех операций за последние 5 дней'''
    # номер аккаунта по кторому запрашиваем информацию
    account_id = global_options['ac_id']
    with Client(TOKEN) as client:
        # текущая дата
        c_d = datetime.now(timezone.utc).astimezone() - timedelta(days=0)
        # дата и время начала чтения операций
        f_d = datetime.now(timezone.utc).astimezone() - timedelta(days=5)
        f_d = datetime(f_d.year, f_d.month, f_d.day, 0, 0, 0)
        # дата и время окончания чтения операций
        t_d = datetime(c_d.year, c_d.month, c_d.day, 23, 59, 59)
        if opt_fun == 'show_month_yeld_now':
            cur_month = c_d.month
            cur_year = c_d.year
            f_d = datetime(cur_year, cur_month, 1, 0, 0, 0)
            t_d = datetime(c_d.year, c_d.month, c_d.day, 23, 59, 59)
            # f_d = datetime(cur_year, 7, 1, 0, 0, 0)
            # t_d = datetime(c_d.year, 7, 31, 23, 59, 59)
            print ("Результаты за месяц")
            print (f'Дата начала загрузки (дата от): {f_d}')
            print (f'Дата окончание загрузки (дата до): {t_d}')
        # запрос всех операций из указанного диапазона дат
        # https://tinkoff.github.io/investAPI/operations/#operation
        operations = client.operations.get_operations(account_id=account_id, from_=f_d, to=t_d).operations
        # https://tinkoff.github.io/investAPI/operations/#getoperationsbycursorrequest
        # operationsby = client.operations.get_operations_by_cursor (account_id=account_id, from_=f_d, to=t_d, limit = 100)
        # GetOperationsByCursor
        msg = ''
        msg = f'Список операций по счету: {account_id}\n'
        msg += f'#СПИСОК_ОПЕРАЦИЙ\n'
        msg += f'c    {d_t_to_txt(f_d)}\n'
        msg += f'по  {d_t_to_txt(t_d)}\n\n\n'

        figi_list_oper =[]
        t_bot.send_chat_action(ID_ch, action ='typing')
        for oper in operations:
            # начинаем разбор операций
            # figi	string	Figi-идентификатор инструмента, связанного с операцией.
            oper_figi = oper.figi
            if not (oper_figi in figi_list_oper) and not(oper_figi ==''):
                figi_list_oper.append(oper_figi)
            # quantity	int64	Количество единиц инструмента.
            oper_quant = oper.quantity
            # oper.payment	MoneyValue	Сумма операции.
            oper_money = cast_money(oper.payment)
            # price	MoneyValue	Цена операции за 1 инструмент. 
            #                   Для получения стоимости лота требуется умножить на лотность инструмента.
            oper_price = cast_money(oper.price)
            # instrument_type	string	Тип инструмента. Возможные значения:
                                        # bond — облигация;
                                        # share — акция;
                                        # currency — валюта;
                                        # etf — фонд;
                                        # futures — фьючерс.   
            oper_type_instr = oper.instrument_type
            # date	google.protobuf.Timestamp	Дата и время операции в формате часовом поясе UTC.
            oper_date = d_t_to_txt (oper.date + timedelta(hours=3))
            # type	string	Текстовое описание типа операции.
            oper_type_txt = oper.type
            # operation_type	OperationType	Тип операции.
            #                   https://tinkoff.github.io/investAPI/operations/#operationtype
            oper_type = oper.operation_type
            oper_id = oper.id
            oper_cur = oper.currency
            # state	OperationState	Статус операции.
            #                       https://tinkoff.github.io/investAPI/operations/#operationstate
            oper_stat = oper.state
            # quantity_rest	int64	Неисполненный остаток по сделке.
            # 15 - продажа, 22 - покупка; 1 - операция исполнена
            if (oper_type == 15 or oper_type == 22) and oper_type_instr == 'futures' and oper_stat == 1: 
                #формирование сообщения
                msg += f'{oper_date}   {oper_type_txt}\n'
                # msg += f'Тип инструмента: {oper_type_instr}    Тип операции: {oper_type}\n'
                msg += f'{oper_figi}   {oper_price}   {oper_quant}   {oper_money} {oper_cur}\n\n'
        print (figi_list_oper)
        #ЕЩЕ один СПОСОБ ВЫВОДА ОПЕРАЦИЙ
        FIGI = 'FUTMXI092300'
        r1 = GetOperationsByCursorRequest()
        r1.account_id = account_id
        r1.instrument_id = FIGI
        r1.from_ = f_d
        r1.to = t_d
        r1.limit = 1000 #Лимит количества операций. Сделать в виде цикла вдруг в списке будут не все операции которые сформировали позицию
        # 15	Покупка ЦБ.
        # 16	Покупка ЦБ с карты.
        # 18	Продажа в результате Margin-call.
        # 20	Покупка в результате Margin-call.
        # 22	Продажа ЦБ.
        # OPERATION_TYPE_ACCRUING_VARMARGIN	26	Зачисление вариационной маржи.
        # OPERATION_TYPE_WRITING_OFF_VARMARGIN	27	Списание вариационной маржи.

        # комисии
        # OPERATION_TYPE_SERVICE_FEE	12	Удержание комиссии за обслуживание брокерского счёта.
        # OPERATION_TYPE_MARGIN_FEE	14	Удержание комиссии за непокрытую позицию.
        # OPERATION_TYPE_BROKER_FEE	19	Удержание комиссии за операцию.
        oper_type_l = [OperationType.OPERATION_TYPE_BUY, OperationType.OPERATION_TYPE_SELL, 
                       OperationType.OPERATION_TYPE_SERVICE_FEE, OperationType.OPERATION_TYPE_MARGIN_FEE, 
                       OperationType.OPERATION_TYPE_BROKER_FEE
                       ]
        oper_type_comiss = [OperationType.OPERATION_TYPE_SERVICE_FEE, 
                            OperationType.OPERATION_TYPE_MARGIN_FEE,
                            OperationType.OPERATION_TYPE_BROKER_FEE]
        r1.operation_types = oper_type_l
        r1.state = OperationState.OPERATION_STATE_EXECUTED # 	1	Исполнена.
        r1.without_commissions = False
        r1.without_trades = True # Флаг получения ответа без массива сделок
        r1.without_overnights = True
        s_oper = client.operations.get_operations_by_cursor(r1)

        s1_oper = s_oper.items
        msg1 = ''
        msg1 = f"\n\n\nОперации по инструменту #{FIGI}\n"
        plus_yeld = 0
        minus_yeld = 0
        totel_yeld = 0
        fig_yeld = ''
        total_comiss = 0
        msg2 = ''
        msg2 = f"\n\n\n#Доходность_операций {FIGI}\n"
        msg3 = '' # результаты текущий за месяц
        for oper in s1_oper:
            msg1 += "   \n"
            msg1 += str(d_t_to_txt(oper.date + timedelta(hours=3)))
            msg1 += "   \n"
            # msg1 += oper.figi
            # msg1 += "   "
            # msg1 += oper.name
            # msg1 += "   \n"
            msg1 += oper.description
            msg1 += "   \n"
            # msg1 += str(oper.quantity_done)
            # msg1 += "   "
            # msg1 += str(oper.type)
            oper_type = oper.type
            if oper_type in oper_type_comiss:
                oper_comiss = cast_money (oper.payment)
                total_comiss += oper_comiss
            msg1 += "   "
            msg1 += str(cast_money (oper.price))
            msg1 += " пт.   "
            msg1 += str(cast_money (oper.payment))
            msg1 += " руб.   "
            msg1 += str(cast_money (oper.yield_))
            msg1 += " пт.   "
            msg1 += str(round(cast_money (oper.yield_relative), 2))
            msg1 += ' %\n'
            yeld_ooo = oper.yield_
            if not (cast_money (yeld_ooo) == 0):
                msg2 += "   \n"
                msg2 += str(d_t_to_txt(oper.date + timedelta(hours=3)))
                msg2 += "   \n"
                msg2 += oper.description
                msg2 += "   \n"
                msg2 += "   "
                msg2 += str(cast_money (oper.price))
                msg2 += " пт.   "
                # msg2 += str(cast_money (oper.payment))
                # msg2 += " руб.   "
                msg2 += str(cast_money (yeld_ooo))
                msg2 += " пт.   "
                msg2 += str(round(cast_money (oper.yield_relative), 2))
                msg2 += ' %\n'
                yeee = cast_money (yeld_ooo)
                if yeee > 0:
                    plus_yeld += yeee
                else:
                    minus_yeld += yeee
                totel_yeld += yeee
                fig_yeld = oper.figi
        msg3 = ''
        msg3 += f"Результаты за месяц {f_d.month}."
        msg3 += f'\nдата НАЧАЛА загрузки (дата от):\n {f_d}\n'
        msg3 += f'\nДата ОКОНЧАНИЯ загрузки (дата до):\n {t_d}\n'
        msg3 += f'\nАктив: {fig_yeld}\n'
        msg3 += f'\nПоложительный результат: {round (plus_yeld, 2)} пт.'
        msg3 += f'\nОтрицательный результат: {round (minus_yeld, 2)} пт.'
        msg3 += f'\nИтоговый результат: {round(totel_yeld, 2)} пт.'
        msg3 += f'\nБрокер отхерачил себе комисий: {round(total_comiss, 2)} руб.'

        if opt_fun == "full":
            # выдача сообщений о результатах обработки не более 4000 символов за раз
            for message1 in util.smart_split(msg, 4000):
                t_bot.send_message(ID_ch, message1, disable_web_page_preview=True, disable_notification=True)

        elif opt_fun == "full":
            # выдача сообщений о результатах обработки не более 4000 символов за раз
            for message1 in util.smart_split(msg1, 4000):
                t_bot.send_message(ID_ch, message1, disable_web_page_preview=True, disable_notification=True)
        
        
        elif opt_fun == "show_oper_yeld":
            for message1 in util.smart_split(msg2, 4000):
                t_bot.send_message(ID_ch, message1, disable_web_page_preview=True, disable_notification=True)
        
        elif opt_fun == "show_month_yeld_now":
            for message1 in util.smart_split(msg3, 4000):
                t_bot.send_message(ID_ch, message1, disable_web_page_preview=True, disable_notification=True)

        else:
            for message1 in util.smart_split(msg, 4000):
                t_bot.send_message(ID_ch, message1, disable_web_page_preview=True, disable_notification=True)
            for message1 in util.smart_split(msg1, 4000):
                t_bot.send_message(ID_ch, message1, disable_web_page_preview=True, disable_notification=True)
            for message1 in util.smart_split(msg2, 4000):
                t_bot.send_message(ID_ch, message1, disable_web_page_preview=True, disable_notification=True)

# отображение информации о марже
def show_margin_status (t_bot: telebot.TeleBot, ID_ch, name_btn):
 # https://tinkoff.github.io/investAPI/head-users/#_4
 # номер аккаунта по кoторому запрашиваем информацию
 account_id = global_options['ac_id']
 with Client(TOKEN) as client:
    marg_att = client.users.get_margin_attributes (account_id = account_id)
    # liquid_portfolio - Стоимость плановых позиций активов, которые признаны ликвидными (для которых определены ставки риска).
    print ('Стоимость плановых позиций активов, которые признаны ликвидными (для которых определены ставки риска):')
    print ("liquid_portfolio: ликвидный портфель")
    print (cast_money(marg_att.liquid_portfolio), 'руб')
    print()
    # starting_margin - Сумма модулей стоимостей плановых позиций активов, которые признаны ликвидными, умноженных на начальные ставки риск
    print ('Сумма модулей стоимостей плановых позиций активов, которые признаны ликвидными, умноженных на начальные ставки риск')
    print ('starting_margin: начальная (стартовая) маржа')
    print (cast_money(marg_att.starting_margin), 'руб')
    print()
    # minimal_margin - Сумма модулей стоимостей плановых позиций активов, которые признаны ликвидными, умноженных на минимальные ставки риска
    print ('Сумма модулей стоимостей плановых позиций активов, которые признаны ликвидными, умноженных на минимальные ставки риск')
    print ('minimal_margin: минимальная маржа')
    print (cast_money(marg_att.minimal_margin), 'руб')
    print()
    print ('funds_sufficiency_level')
    print (cast_money(marg_att.funds_sufficiency_level), 'руб')
    print()
    print ('amount_of_missing_funds')
    print (cast_money(marg_att.amount_of_missing_funds), 'руб')
    print()
    print ('corrected_Margin ')
    print (cast_money(marg_att.corrected_margin), 'руб')

    msg = ''
    msg += "Ликвидный портфель (liquid_portfolio):\n"
    msg += f"   {cast_money(marg_att.liquid_portfolio)} руб.\n\n"
    msg += 'Начальная маржа (starting_margin):\n'
    msg += f"   {cast_money(marg_att.starting_margin)} руб.\n\n"
    msg += 'Минимально допустимая маржа (minimal_margin):\n'
    msg += f"   {cast_money(marg_att.minimal_margin)} руб.\n\n"
    msg += 'Уровень достаточности средств:\n'
    msg += f"   {cast_money(marg_att.funds_sufficiency_level)}\n\n"
    msg += 'Объем недостающих средств:\n'
    msg += f"   {cast_money(marg_att.amount_of_missing_funds)} руб.\n\n"
    msg += 'Начальная маржа с учетом выставленных заявок (при их наличии):\n' 
    msg += f"   {cast_money(marg_att.corrected_margin)} руб.\n"
    msg += '#состояние_маржи'

 t_bot.send_message(ID_ch, text=msg, disable_notification=True)


#  Показать в чате серию графиков для избранных фьючерсов
def show_futur_graf (t_bot: telebot.TeleBot, ID_ch, parm_txt, load_period, load_inter, name_btn):
    '''Показать в чате графики избранных фьючерсов
    load_period: количество баров для загрузки и отображения на графике
    load_inter = 15min, 30min, 1h, 4h, DAY, WEEK, MONTH
    parm_txt = 'f2': показать только график фьчерса на Сбер
    parm_txt = "⭐️Показать фьючерсы": показать только избранные фьючерсы
    '''
    # 'f2' показать только график фьчерса на Сбер
    # MX	MIX	Индекс МосБиржи
    # MM	MXI	Индекс МосБиржи (мини)
    # RI	RTS	Индекс РТС
    # RM	RTSM	Индекс РТС (мини)
    # VI	RVI	Волатильность российского рынка
    # HO	HOME	Индекс московской недвижимости ДомКлик
    # RB	RGBI	Индекс RGBI

    # Январь	F
    # Февраль	G
    # Март	    H
    # Апрель	J
    # Май	    K
    # Июнь	    M
    # Июль	    N
    # Август	Q
    # Сентябрь	U
    # Октябрь	        V
    # Ноябрь	        X
    # Декабрь	Z
    
    
    #Код периода отображения
    # -9.24
    year_f = '4'
    month_f = 'U'
    # ИЗБРАННОЕ для отображения дневных графиков
    fav_lst= ['MM', 'MX','RM','RI','SR','GZ','LK', 
              'Si','Eu','ED','SF','RL','YN', 'GD','SV', 'BR', 'NG', 'SF','NA', 'GK', 'NM','MN', 'VB']
    fav_lst_f=[]
    # преобразование в актуальные полные наименования
    for ft in fav_lst:
        fav_lst_f.append(f'{ft}{month_f}{year_f}')

    with Client(TOKEN) as client:
        loop_circle = 0
        loop_end = 1
        while loop_circle < loop_end:
            # ФЬюЧЕРСЫ
            futures_instr = []
            futures = client.instruments.futures(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)
            futures_instr = futures.instruments
            future_list = []
            future_filter_instr = []
            if parm_txt == "⭐️Показать фьючерсы":
                #  только избранное
                for i in futures_instr:
                    if  i.ticker in fav_lst_f:
                        future_list.append(f'{i.figi} \t {i.ticker} \t {i.name}')
                        future_filter_instr.append(i)
                future_list.sort()

            elif parm_txt == "f2":
                # только сбер в списке для загрузки
                for i in futures_instr:
                    if 'SRZ2' == i.ticker:
                        future_list.append(f'{i.figi} \t {i.ticker} \t {i.name}')
                        future_filter_instr.append(i)

            # загружаем бары по списку выбранных активов
            if parm_txt != "f2":
                print(f'Начинаем загрузку баров для избранных: {len(future_filter_instr)} фьючерсов.\nИнтервал: {load_inter} ')
                try:
                    reg_msg()
                    t_bot.send_message(ID_ch,
                                    f'Начинаем загрузку баров для избранных: {len(future_filter_instr)} фьючерсов.\nИнтервал: {load_inter}',
                                    disable_notification=True)
                except Exception as e:
                    telega_error (e)
                stoks_status_bar = IncrementalBar(' ЗАГРУЗКА', max=len(future_filter_instr))
            start_count_sec = time.time()  # счетчик секунд для определения общего вермени загрузки
            count_res = 0
            # получаем текущую дату и время
            curr_time = datetime.now(timezone.utc).astimezone()
            # переводим в текстовый вид
            d1 = datetime.strftime(curr_time, '%d.%m.%Y')
            ht1 = datetime.strftime(curr_time, '%H:%M:%S')
            print(f'Текущая дата: {d1} \nВремя: {ht1}')

            if len(future_filter_instr) > 280:
                count_end_minute = (60 - curr_time.second)  # количество секунд до конца текущей минуты
                print(f'До начала следующей минуты: {count_end_minute} сек')
                print(f'Засыпаем на {count_end_minute} сек ')
                try:
                    reg_msg()
                    t_bot.send_message(ID_ch, f'Засыпаем на {count_end_minute} сек ',
                                    disable_web_page_preview=True, disable_notification=True)
                    reg_msg()
                    t_bot.send_chat_action(ID_ch, action='typing')
                except Exception as e:
                    telega_error (e)
                time.sleep(count_end_minute)  # ждем конца минутыq

            if not (parm_txt == "f2"):
                print(f'Всего фьючерсов для чтения: {len(future_filter_instr)}')
                try:
                    reg_msg()
                    t_bot.send_message(ID_ch, f'Всего фьючерсов для чтения: {len(future_filter_instr)}',
                                    disable_web_page_preview=True, disable_notification=True)
                except Exception as e:
                    telega_error (e)

            # CANDLE_INTERVAL_UNSPECIFIED	0	Интервал не определён.
            # CANDLE_INTERVAL_1_MIN	1	1 минута.
            # CANDLE_INTERVAL_5_MIN	2	5 минут.
            # CANDLE_INTERVAL_15_MIN	3	15 минут.
            # CANDLE_INTERVAL_HOUR	4	1 час.
            # CANDLE_INTERVAL_DAY	5	1 день.

            # вычисление дат начала и окончания нагрузки
            # до какой даты загрузить
            load_to = datetime.now(timezone.utc).astimezone()
            #  при пустом периоде
            if load_period == 0:
                load_period = 10

            # интервал День
            if load_inter == 'DAY':
                load_from = load_to - timedelta(days=load_period)
            
            # интервал Неделя
            elif load_inter == 'WEEK':
                load_from = load_to - timedelta(weeks=load_period)
            
            else:
                load_from = load_to - timedelta(days=load_period)

            bars_list = []
            bar_items = []
            # Основной цикл загрузки
            for k in future_filter_instr:
                bar_items = []
                if count_res == 300:
                    stop_count_sec = time.time()
                    delta = stop_count_sec - start_count_sec
                    print(f'\nC момента запуска прошло {int(delta)} сек')
                    print("Достигнут предел: 300 запросов в минуту")
                    try:
                        reg_msg()
                        t_bot.send_message(ID_ch, "Достигнут предел: 300 запросов в минуту")
                    except Exception as e:
                        telega_error (e)

                    wait_end_minute = (60 - datetime.now(
                        timezone.utc).astimezone().second + 5)  # количество секунд до конца текущей минуты
                    # плюс небольшой запас
                    print(f'Засыпаем на {wait_end_minute} сек\n')
                    time.sleep(wait_end_minute)  # ждем конца минуты
                    count_res = 0  # обнуляем счетчик запросов в минуту
                # if count_end_minute count_sec
                try:

                    bars = client.market_data.get_candles(
                        figi=k.figi,
                        from_=load_from,
                        to=load_to,
                        interval=CandleInterval.CANDLE_INTERVAL_DAY
                    )
                except Exception as ebx:
                    print(ebx)
                    try:
                        reg_msg()
                        t_bot.send_message(ID_ch,
                                        '⚡️ОШИБКА⚡️ '
                                        '\nЧто-то пошло не так при загрузке данных из платформы Тинькофф.'
                                        '\nПопробуйте вернуть настройки на первоначальные⚡️'
                                        f'\n{ebx}')
                    except Exception as e:
                        telega_error (e)
                    return 0

                canl_shop = bars.candles
                # преобразование объекта canl_shop  в dataframe
                df333 = create_df_bars_set(canl_shop)

                # преобразование данных, если интервал неделя
                if load_inter == 'WEEK':
                    ohlc = {
                            'Open': 'first',
                            'High': 'max',
                            'Low': 'min',
                            'Close': 'last',
                            'Volume': 'sum'
                        }
                    b_df333 = df333.copy
                    df333 = df333.resample('1W').agg(ohlc)

                # вычисление изменениея за интервал
                f111111 = df333.iloc[-1]['Close']
                f333333 = df333.iloc[-2]['Close']
                f222222 = k.name
                f4444 = round((f111111 - f333333) / f333333 * 100, 2)
                f5555 = round((f111111 - f333333), 2)
                name_file_img = f'images/img{k.ticker}.png'
                try:
                    mpf.plot(df333, style='mike', figsize=(7.2, 12.80),
                                title=f"{f222222} [{load_inter}]\n{f333333} ➡️ {f111111} пт.    {f4444}%   {f5555} пт.", volume=True,
                                savefig=name_file_img)
                except Exception as e:
                    print()
                    print('ВОЗНИКЛА ОШИБКА mpf.plot')
                    print(datetime.now(timezone.utc).astimezone())
                    print("Текст ошибки:")
                    print(e)
                    print()

                try:
                    reg_msg()
                    t_bot.send_photo(ID_ch, photo=open(name_file_img, 'rb'),
                                caption=f'{f222222} [{load_inter}]\n{f333333} ➡️ {f111111} пт.   {f4444}%   {f5555} пт.',
                                disable_notification=True)
                except Exception as e:
                    telega_error (e)
                bar_items.append(bars.candles)
                bar_items[0].insert(0, k)
                bars_list.append(bar_items)
                count_res += 1  # счетчик обращений
                if not (parm_txt == "f2"):
                    stoks_status_bar.next()
                    print(' ', k.name, k.ticker)

            # загрузка тек поз портфеля
            portfel = client.operations.get_portfolio(account_id=global_options['ac_id'])
            pos_prt = portfel.positions
            df = cr_df_pos(pos_prt)

            # вывод сообщения с итогом обработки
            msg = ''
            msg += f'\n[{load_inter}]\n'
            for m in bars_list:
                if len(m[0]) > 3:
                    izm = round((cast_money(m[0][-1].close) - cast_money(m[0][-2].close)) / cast_money(
                        m[0][-2].close) * 100, 2)
                    izm_abs = round((cast_money(m[0][-1].close) - cast_money(m[0][-2].close)), 2)
                    print(m[0][0].ticker, '\t', cast_money(m[0][-2].close), '\t', cast_money(m[0][-1].close),
                            '\t', izm, '% \t', m[0][0].name)
                    if not (parm_txt == "f2"):
                        msg += f'{m[0][0].name}\n{m[0][0].ticker}   {cast_money(m[0][-2].close)} -> ' \
                                f'{cast_money(m[0][-1].close)} пт.  {izm} %   {izm_abs} пт.\n'
                        # msg+= f'https://www.tinkoff.ru/invest/futures/{m[0][0].ticker}\n'
                        msg +='\n'
                    elif parm_txt == "f2": # по фьючу на сбер
                        sbrf_pos = 0  # признак наличия позиции по фьючу на сбер
                        close_dd = cast_money(m[0][-1].close)

                        for dc in range(df.shape[0]):
                            if m[0][0].figi == df.iloc[dc, 0]:
                                # расчет относительно средней позиции
                                if df.iloc[dc, 9] < 0:  # расчет для позиции шорт
                                    izm_pos = round((df.iloc[dc, 3] - close_dd) / df.iloc[dc, 3] * 100,
                                                    2)  # в процентах
                                    izm_pos_abs = round(df.iloc[dc, 3] - close_dd, 2)
                                elif df.iloc[dc, 9] > 0:  # расчет для позиции лонг
                                    izm_pos = round((close_dd - df.iloc[dc, 3]) / df.iloc[dc, 3] * 100,
                                                    2)  # в процентах
                                    izm_pos_abs = round(close_dd - df.iloc[dc, 3], 2)

                                msg += f'{m[0][0].ticker}: {df.iloc[dc, 3]}  {close_dd}  {izm_pos}%  ' \
                                        f'{izm_pos_abs * abs(df.iloc[dc, 9])}   ({df.iloc[dc, 9]}) \n'
                                sbrf_pos = 1

                        if sbrf_pos != 1:  # если не нашли позицию выводим просто тек цену
                            msg += f'{m[0][0].ticker}   {close_dd}   {izm} %   {izm_abs}\n'
            msg += f'[{load_inter}]'

            # print (bars_list)
            if parm_txt != "f2":
                stop_count_sec = time.time()
                delta = stop_count_sec - start_count_sec
                delta_min = delta / 60
                print(f'\n\nВсего прошло с момента запуска: {int(delta)} сек')
                print(f'в минутах с момента запуска: {int(delta_min)} мин')
            # выдача сообщений о результатах обработки не более 4000 символов за раз
            for message1 in util.smart_split(msg, 4000):
                try:
                    reg_msg()
                    t_bot.send_message(ID_ch, message1, disable_web_page_preview=True)
                except Exception as e:
                    telega_error (e)
            loop_circle += 1
            if loop_circle != loop_end:
                print('все приехали!')
                time.sleep(60)

# отображение информации о текущем фьючерсе
def show_info_of_G_O (t_bot: telebot.TeleBot, ID_ch, name_btn):
 '''
 # отображение информации о текущем фьючерсе, в том числе и о ГО
 '''
 # имя тек фьючерса с которым идет работа
 full_name_load = global_f_opt['full_future_name']
 with Client(TOKEN) as client:
    print('Подключились к Tinkoff')
    # имя тек фьючерса с которым идет работа
    full_name_load = global_f_opt['full_future_name']
    flag_r = True  # повторять попытки загрузки списка пока не получиться загрузить
    print('Загрузка списка фьючерсов')
    while flag_r:
        try:
            futures = client.instruments.futures(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)
            flag_r = False  # получилось загрузить и поэтому повтора не требуется
            # требуемый список фьючерсов
            full_futures_instr = futures.instruments
            print(f'Всего фьючерсов в списке: {len(full_futures_instr)}')
        except Exception as ebx:
            print(datetime.now(timezone.utc).astimezone())
            print('\nВОЗНИКЛА ОШИБКА загрузки списка фьючерсов от платформы Tinkoff при обработке команды /show_go. Цикл будет бесконечен пока не получится подключиться.')
            print(ebx)
            print()
            try:
                reg_msg()
                t_bot.send_message(ID_ch, text=f"ВОЗНИКЛА ОШИБКА загрузки списка фьючерсов с платформы Tinkoff"
                                            f"\n{ebx}"
                                            f"\nНЕ Попробуем ещё раз загрузить")
            except Exception as e:
                telega_error (e)
            flag_r = False
    full_name_len = len(full_name_load)
    # поиск требуемого фьючерса
    for i in full_futures_instr:
        # находим тот у которого совпадает полное имя совпадает с требуемым
        i_name_len = len(i.name)
        if full_name_len <= i_name_len:
            i_name = i.name[:full_name_len]
        if full_name_load in i_name:
            # получаем описание о ГО фьючерса
            # описание функции по ссылке
            # https://tinkoff.github.io/investAPI/instruments/#getfuturesmarginrequest
            f_inf = client.instruments.get_futures_margin(figi=i.figi) # информация о маржинальных параметрах
            f_name = i.name  # 0
            f_ticker_f = i.ticker,  # 1
            f_figi = i.figi  # 2
            f_margin_buy = cast_money(f_inf.initial_margin_on_buy)  # 3 Размер ГО Лонг
            f_margin_sell = cast_money(f_inf.initial_margin_on_sell)  # 4 ГО шорт
            f_margin_cur = f_inf.initial_margin_on_buy.currency  # 5 валюта
            f_step_price_pt = q_to_var(f_inf.min_price_increment)  # 6 шаг цены
            f_step_price = q_to_var(f_inf.min_price_increment_amount) # 7 стоимость шага
            #8 стоимость пункта цены. На это значение надо упножать значение в пунктах
            f_step_cost_curr = f_step_price/f_step_price_pt
            f_asset_type = i.asset_type  # 9 Тип базового актива
            f_link = f'https://www.tinkoff.ru/invest/futures/{i.ticker}'  # 10 ссылка на график
            # работа с последней ценой
            lps = client.market_data.get_last_prices(figi=[f_figi]).last_prices  # последняя цена
            f_lps = q_to_var(lps[0].price)
            # расчет тек стоимости в руб, т.е. перевод из пт. в руб.
            f_lps_rub = f_lps * f_step_cost_curr
            # расчет плеча buy, т.е. во всколько раз ГО меньще цены (плечо)
            f_kx_buy = round (f_lps_rub /  f_margin_buy, 2)
            # расчет плеча sell, т.е. во всколько раз ГО меньще цены (плечо)
            f_kx_sell = round (f_lps_rub /  f_margin_sell, 2)

            # FutureBy
            # Метод получения фьючерса по его идентификатору.
            # Тело запроса — InstrumentRequest
            # Тело ответа — FutureResponse
            # min_price_increment	Quotation	Шаг цены.
            # https://tinkoff.github.io/investAPI/instruments/#futureby
            # https://tinkoff.github.io/investAPI/instruments/#future
            f_obg = client.instruments.future_by (id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, id=f_figi).instrument
            f_exp_data = datetime.strftime(f_obg.expiration_date, '%d.%m.%Y')

            # Выдача сообщения в чат
            msg = ''
            msg +=  f'\n{f_name}' \
                    f'\n{f_figi}\n' \
                    f'\nРазмер ГО buy:  {f_margin_buy} {f_margin_cur}' \
                    f'\nРазмер ГО sell:  {f_margin_sell} {f_margin_cur}\n' \
                    f'\nГО buy меньше цены, раз:   {f_kx_buy}' \
                    f'\nГО sell меньше цены, раз:   {f_kx_sell}\n' \
                    f'\n{f_ticker_f}    {f_figi}' \
                    f'\nПослед знач.:   {f_lps} пт.' \
                    f'\nПосл.цена:       {f_lps_rub}   {f_margin_cur}' \
                    f'\nСтоимость пункта:   {f_step_cost_curr} {f_margin_cur}' \
                    f'\n\nДата экспирации:   {f_exp_data}' \
                    f'\n{f_link}'
            # выдача сообщений о результатах обработки не более 4000 символов за раз
            for message1 in util.smart_split(msg, 4000):
                try:
                    reg_msg()
                    t_bot.send_message(ID_ch, message1, disable_web_page_preview=True, disable_notification=True)
                except Exception as e:
                    telega_error (e)
            break
    
def show_type_instr_btn(t_bot: telebot.TeleBot, ID_ch, name_btn):
    # https://habr.com/ru/post/522720
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    fonds_b = types.KeyboardButton("Фонды_gr")
    stocks_b = types.KeyboardButton("Акции_gr")
    future_b = types.KeyboardButton("Фьючерсы_gr")
    markup.add(fonds_b, stocks_b, future_b)
    menu_b = types.KeyboardButton("Меню")
    if global_f_opt['repeat_flag']:
        stop_b = types.KeyboardButton("❌Стоп_цикл_gr")
        markup.add(menu_b, stop_b)
    else:
        markup.add(menu_b)
    try:
        reg_msg()
        t_bot.send_message(ID_ch, text="Выберите настройку", reply_markup=markup)
    except Exception as e:
        telega_error (e)

def what_param_is_now (t_bot: telebot.TeleBot, ID_ch, show_param):
    msg =''
    if show_param == 'Интервал_gr':
        interv = what_interval()
        msg = f'Текущий интервал: {interv}'
    else:
        msg = "Не удалось определить, что сейчас задано в настройках"
    try:
        reg_msg()
        t_bot.send_message(ID_ch, msg,disable_notification=True)
    except Exception as e:
        telega_error (e)

def mOrd_price_val(msg: telebot.types.Message, t_bot: telebot.TeleBot):
    ID_ch = msg.chat.id
    m_price = msg.text # необходимо проверять, что в итоге введено !!!! Число или что-то другое, команда отмены например
    if m_price == '🙅Отмена_mOrd':
        show_run_repit_btn(t_bot, ID_ch, 'graf')
        return 'exit'
    global_bids_data['manual_order_price'] = m_price
    print ("Введено значение: ", m_price)
    try:
        reg_msg()
        t_bot.send_message (msg.chat.id, text=f'Введено значение цены: {m_price}')
        msg = t_bot.send_message (msg.chat.id, text=f'Введите необходимое колличество:')
        reg_msg()
        t_bot.register_next_step_handler(msg, mOrd_quant_val, t_bot)
    except Exception as e:
        telega_error (e)

def mOrd_quant_val (msg: telebot.types.Message, t_bot: telebot.TeleBot):
    m_quant = msg.text
    global_bids_data['manual_order_quant'] = m_quant
    print ('Запрошено колличество: ', m_quant)
    try:
        reg_msg()
        t_bot.send_message (msg.chat.id, text=f'Введено значение количества: {m_quant}')
    except Exception as e:
        telega_error (e)

# изменение за год для выбранных акций
def show_stoks_year_fun(T_bot: telebot.TeleBot, ID_ch, year_1, year_2 ):
    """
    # изменение за год для всех акций
    """
    # получаем список всех акций через APIv2
    try:
        full_stock_obj = gRPC_Load_List()
        msg = f'Сравнение изменений акций за год,'
        msg += f'\nзакрытие {year_1} к закрытию {year_2}'
        msg += f'\nДоступно акций: {len(full_stock_obj)} шт.'
        try:
            reg_msg()
            T_bot.send_message(ID_ch, msg ,disable_notification=True)
        except Exception as e:
            telega_error (e)
        df_list = create_df_stoks_list(full_stock_obj)
        df_list.to_csv('full_list_stoks.csv', encoding = 'cp1251')
    except Exception as ebx:
        print(datetime.now(timezone.utc).astimezone())
        print('\nВОЗНИКЛА ОШИБКА  gRPC_Load_List()')
        print(ebx)
        print()
        try:
            T_bot.send_message(ID_ch, f'ВОЗНИКЛА ОШИБКА  gRPC_Load_List()',disable_notification=True)
        except Exception as e:
            telega_error (ebx)
        return 0
    f_d = datetime(year_1, 12, 31, 12, 0, 0)
    t_d = datetime(year_2, 12, 31, 23, 0, 0)
    i_s = CandleInterval.CANDLE_INTERVAL_DAY
    list_cdl=[]
    list_obj_cdl=[]
    print('Подключаемся к Tinkoff для чтения акций')
    with Client(TOKEN) as g_client:
        print('Подключились к Tinkoff')
        cont = 1
        curr_time = datetime.now(timezone.utc).astimezone()
        # переводим в текстовый вид
        d1 = datetime.strftime(curr_time, '%d.%m.%Y')
        ht1 = datetime.strftime(curr_time, '%H:%M:%S')
        try:
            reg_msg()
            T_bot.send_message(ID_ch, f'Запуск:\n{d1}\n{ht1}\n\nЖДИТЕ: от 6 до 10 минут....\n\nзагружаются годовые данные по акциям: \n{len(full_stock_obj)} шт.',disable_notification=True)
        except Exception as e:
            telega_error (e)
        print_date_time_now()
        start_time= time.time()
        use_platform = 1  # тип платформы для загрузки: 1 - g_client; 2 - tiAPIv1
        time_reset_limit_1 = 0  # время ожидания когда снимут ограничение для платформы 1
        time_reset_limit_2 = 0  # время ожидания когда снимут ограническе для платформы 2
        for st_1 in full_stock_obj:
            repit = True # повтор загрузки после  ошибки
            while repit:
                try:
                    if use_platform == 1:
                        cndl_list_1 = g_client.market_data.get_candles(figi=st_1.figi, from_=f_d, to=t_d, interval=i_s).candles
                        repit = False
                    else: #сервич стал не доступен после 01 06 2023
                        # сломал ТЫНКОФФ теперь не работает
                        print ('сломал ТЫНКОФФ теперь не работает')
                        # cndl_list_2 = tiAPIv1.get_market_candles(st_1.figi, f_d, t_d,  ti.CandleResolution.day).payload.candles
                        cndl_list_2 = []
                        repit = False
                        # Ресурс	Количество запросов для пользователя	Количество запросов на IP	Интервал ограничения
                        # /market	240	                                    500	                        1 минута
                except Exception as ebx:
                    try:
                        reg_msg()
                        T_bot.send_chat_action(ID_ch, action ='typing')
                    except Exception as e:
                        telega_error (e)
                    if use_platform == 1:
                        if ebx.code.name == 'RESOURCE_EXHAUSTED':
                            repit = True # повтор загрузки после  ошибки
                            stop_time = ebx.metadata.ratelimit_reset + 1
                            if time_reset_limit_1 == 0:
                                use_platform = 1
                                time_reset_limit_1 = stop_time
                                print()
                                print_date_time_now()
                                print("Прерывание при чтении актива:", cont, st_1.ticker, st_1.name)
                                print(ebx)
                                print("Переключение на tiAPIv1 не произодет ТЫНКОВ сломал сервис")
                                print (f'Доступность ресурса g_client через: {stop_time} сек...')
                                print()
                            else:
                                print()
                                print_date_time_now()
                                print("Прерывание при чтении актива:", cont, st_1.ticker, st_1.name)
                                print(ebx)
                                print (f'Ожидание доступности ресурса ТЫНКОВФ g_client.\nПауза: {stop_time} сек...')
                                time.sleep(stop_time)
                                print_date_time_now()
                                print()
                                time_reset_limit_1 = 0
                                use_platform = 1
                    else:
                        use_platform = 1
                        repit = True
                        print()
                        print_date_time_now()
                        print("Прерывание при чтении актива:", cont, st_1.ticker, st_1.name)
                        print (type(ebx))
                        print("Переключение на g_client")
                        time_reset_limit_2 = 30
                        # print ('сон 30 сек...')
                        # time.sleep(30)
                        print_date_time_now()
                        print()
            # обработка и внесение результатов очередной FIG после чтения баров через платформу g_client 
            try:
                if use_platform == 1:
                    if len(cndl_list_1) > 0 :
                        list_obj_cdl.append({'ticker': st_1.ticker,
                                            'name': st_1.name,
                                            'figi': st_1.figi,
                                            'cndls_all': cndl_list_1})
                        cap = st_1.issue_size * q_to_var(cndl_list_1[-1].close)
                        y1_c = q_to_var(cndl_list_1[0].close)
                        y2_c = q_to_var(cndl_list_1[-1].close)
                        rez = round(y2_c - y1_c, 2)
                        rez_pr = round(rez/y1_c*100, 2)
                        list_cdl.append({'ticker': st_1.ticker,
                                            'name': st_1.name,
                                            'rez_%': rez_pr,
                                            'rez': rez,
                                            'y1_c1': y1_c,
                                            'y2_c1': y2_c,
                                            'link': f'https://www.tinkoff.ru/invest/stocks/{st_1.ticker}',
                                            'link_2': f'https://www.moex.com/ru/issue.aspx?board=TQBR&code={st_1.ticker}',
                                            'ticker': st_1.ticker,
                                            'figi': st_1.figi,
                                            'isin': st_1.isin,
                                            'currency': st_1.currency,  # Валюта расчётов
                                            'issue_size': st_1.issue_size,  # Размер выпуска
                                            'capitaliz': cap,
                                            'sector': st_1.sector,  # Сектор экономики
                                            'otc_flag': st_1.otc_flag,  # Признак внебиржевой ценной бумаги
                                            'for_qual_investor_flag': st_1.for_qual_investor_flag,  # только для квалифицированных
                                            'y1_dt': cndl_list_1[0].time,
                                            'y1_o': q_to_var(cndl_list_1[0].open),
                                            'y1_h': q_to_var(cndl_list_1[0].high),
                                            'y1_l': q_to_var(cndl_list_1[0].low),
                                            'y1_c': y1_c,
                                            'y2_dt': cndl_list_1[-1].time,
                                            'y2_o': q_to_var(cndl_list_1[-1].open),
                                            'y2_h': q_to_var(cndl_list_1[-1].high),
                                            'y2_l': q_to_var(cndl_list_1[-1].low),
                                            'y2_c': y2_c
                                            })
                else:
                    # обработка списка от старого API
                    if len(cndl_list_2) > 0 :
                            list_obj_cdl.append({'ticker': st_1.ticker,
                                                'name': st_1.name,
                                                'figi': st_1.figi,
                                                'cndls_all': cndl_list_2})

                            y1_c = cndl_list_2[0].c
                            y2_c =cndl_list_2[-1].c
                            cap = st_1.issue_size * y2_c
                            rez = round(y2_c - y1_c, 2)
                            rez_pr = round(rez/y1_c*100, 2)
                            list_cdl.append({'ticker': st_1.ticker,
                                                'name': st_1.name,
                                                'rez': rez,
                                                'rez_%': rez_pr,
                                                'link': f'https://www.tinkoff.ru/invest/stocks/{st_1.ticker}',
                                                'figi': st_1.figi,
                                                'isin': st_1.isin,
                                                'currency': st_1.currency,  # Валюта расчётов
                                                'issue_size': st_1.issue_size,  # Размер выпуска
                                                'capitaliz': cap,
                                                'sector': st_1.sector,  # Сектор экономики
                                                'otc_flag': st_1.otc_flag,  # Признак внебиржевой ценной бумаги
                                                'for_qual_investor_flag': st_1.for_qual_investor_flag,  # только для квалифицированных
                                                'y1_dt': cndl_list_2[0].time,
                                                'y1_o': cndl_list_2[0].o,
                                                'y1_h': cndl_list_2[0].h,
                                                'y1_l': cndl_list_2[0].l,
                                                'y1_c': y1_c,
                                                'y2_dt': cndl_list_2[-1].time,
                                                'y2_o': cndl_list_2[-1].o,
                                                'y2_h': cndl_list_2[-1].h,
                                                'y2_l': cndl_list_2[-1].l,
                                                'y2_c': y2_c
                                                })
                print(cont, st_1.ticker, st_1.name)
                cont += 1
            except Exception as ebx:
                    print()
                    print_date_time_now()
                    print(ebx)
                    print(st_1.ticker, st_1.name)
                    print()
                    
        end_time= time.time()
        delta_time = end_time - start_time
        delta_time_min = round (delta_time/60, 2)
        curr_time = datetime.now(timezone.utc).astimezone()
        # переводим в текстовый вид
        d1 = datetime.strftime(curr_time, '%d.%m.%Y')
        ht1 = datetime.strftime(curr_time, '%H:%M:%S')
        print(round(delta_time, 0), "или")
        print(delta_time_min, 'мин')
        try:
            msg = f'Окончание:\n{d1}\n{ht1}'
            msg += f'\n\nВсего времени прошло:\n{round(delta_time, 0)} сек. или\n{delta_time_min} мин.'
            reg_msg()        
            T_bot.send_message(ID_ch, msg ,disable_notification=True)
        except Exception as e:
            telega_error (e)
        df_cndl_y = pd.DataFrame(list_cdl)
        df_cndl_y = df_cndl_y.sort_values(by='rez_%', ascending=False)
        # только российские акции
        rub_df_stoks = df_cndl_y[df_cndl_y['currency']=='rub']

        # проблемы с кодировкой русских символов при сохранении в CSV
        # при чтении  значений баров не учитывается что данные отдали за весь год, 
        # т.е. в список попадают акции которые не имеют полной информации за год
        # ВСЕ акции, разделитель точка с запятой
        f_name = f'year_{year_1}_to_{year_2}_calc_office.csv'
        df_cndl_y.to_csv(f_name, sep=';', encoding = 'cp1251',  decimal=',', float_format='%.2f')
        
        # ВСЕ акции. Разделитель запятая для ГуглТаблиц
        f_name_zpt = f'year_{year_1}_to_{year_2}_calc_googl_zpt.csv'
        df_cndl_y.to_csv(f_name_zpt, sep=',')

        # Российские акции, разделитель точка с запятой
        rub_f_name = f'year_{year_1}_to_{year_2}_RUB_calc_office.csv'
        rub_df_stoks.to_csv(rub_f_name, sep=';', encoding = 'cp1251',  decimal=',', float_format='%.2f')
        # вывод в чат
        try:
            reg_msg()
            T_bot.send_document(ID_ch, document=open(f_name, 'rb'), disable_notification=True, 
                                caption = f"Список всех акций: {len(df_cndl_y)} шт.\n(разделитель [;] для Excel)")
            
            reg_msg()
            T_bot.send_document(ID_ch, document=open(f_name_zpt, 'rb'), disable_notification=True,  
                                caption = f"Список всех акций: {len(df_cndl_y)} шт.\n(разделитель [,] для ГуглТаблиц)")
            
            reg_msg()
            T_bot.send_document(ID_ch, document=open(rub_f_name, 'rb'), disable_notification=True, 
                                caption = f"Список только российских акций: {len(rub_df_stoks)} шт.\n(разделитель [;])")


        except Exception as e:
            telega_error (e)


def find_future(T_bot: telebot.TeleBot, ID_ch, grpc_client: services.Services, f_name):
    """
    ### Поиск FIGI фьючерса по его полному имени
    :[f_name] полное имя фьючерса
    :[grpc_client] для подключения к платформе
    """
    global global_f_opt, g_df_p
    # загружаем список фьючерсов
    # блок настроек
    futures_instr = []  # список фьючерсов
    flag_r = True  # повторять загружать пока не получиться загрузить
    stop_while = 300  # Количество повторов
    stop_while_counter = 0  # счетчик повторов
    print_date_time_now()
    print(f'Поиск фьючерса с именем: {f_name}')
    # загрузка всего списка фьючерсов
    while flag_r:
        try:
            # список фьючерсов
            futures_instr = grpc_client.instruments.futures(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE).instruments
            flag_r = False
            stop_while_counter = 0
            print(f'Всего доступно фьючерсов: {len(futures_instr)}')
        except Exception as ebx:
            print_date_time_now()
            print('\nВОЗНИКЛА ОШИБКА загрузки списка фьючерсов find_future_figi')
            print('futures=client.instruments.futures'
                    '(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)')
            print(ebx)
            print()
            try:
                if stop_while_counter == 0: # одного сообщения достаточно
                    reg_msg()
                    T_bot.send_message(ID_ch, text="ВОЗНИКЛА ОШИБКА загрузки списка фьючерсов", disable_notification = True)
                if stop_while_counter == 300: # неудача
                    reg_msg()
                    T_bot.send_message(ID_ch, text=f"Загрузка не удалась, после {stop_while} попыток", disable_notification = True)
                    return 0
            except Exception as e:
                telega_error (e)
            stop_while_counter += 1
            flag_r = True

    # поиск FIGI для требуемого фьючерса
    future_find_dict = {}  # текстовый список фьючерсов
    future_find_objct = []  # список объектов фьючерсов
    for i in futures_instr:
        if f_name in i.name:
            # словарь с информацией о ФИГИ, тикере, имени фьючерса
            future_find_dict = {'figi': i.figi, 'tiker': i.ticker, 'name': i.name}
            future_find_objct.append(i)
            # какой фьючерс грузить
            full_FIGI_load = future_find_dict['figi']
            # GetFuturesMarginRequest получаем описание фьючерса
            future_info = grpc_client.instruments.get_futures_margin(figi=full_FIGI_load)
            print(f"Найден фьючерс: {future_find_dict['name']}")
            break
    return full_FIGI_load, future_find_dict, future_find_objct, future_info


def calc_load_from(candl_interval: str, load_period: int):
    '''
    Вычисление даты начала загрузки от текущей даты и времени: 
    candl_interval: интервал баров: 1m, 5m, 15m, 30m, 1h, 4h, 1D, 1W, 1Mth, 1Q, 1Y
    \nload_period: количество интервалов

    '''
    global global_f_opt, g_df_p
    if candl_interval == '1W':
        load_inter = 'WEEK'
        show_weeks = load_period
        load_to = datetime.now(timezone.utc).astimezone()
        if show_weeks == 0:
            show_weeks = 1
        load_from = load_to - timedelta(weeks=(show_weeks-1))
        n_w_day= load_from.weekday()
        if n_w_day !=0:
            load_from = load_from - timedelta(days=n_w_day)
        print(load_from)
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_DAY
    elif candl_interval == '1D':
        load_inter = 'DAY'
        load_from = datetime.now(timezone.utc).astimezone() - timedelta(days=load_period)
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_DAY
    elif candl_interval == '1h':
        load_inter = 'HOUR'
        load_from = datetime.now(timezone.utc).astimezone() - timedelta(hours=load_period)
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_HOUR
    elif candl_interval == '4h':
        load_inter = '4_HOUR'
        load_from = datetime.now(timezone.utc).astimezone() - timedelta(hours=load_period)
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_HOUR
    elif candl_interval == '15m':
        load_inter = '15_MIN'
        load_from = datetime.now(timezone.utc).astimezone() - timedelta(minutes=load_period * 15)
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_15_MIN
    elif candl_interval == '5m':
        load_inter = '5_MIN'
        load_from = datetime.now(timezone.utc).astimezone() - timedelta(minutes=load_period * 5)
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_5_MIN
    elif candl_interval == '1m' :
        load_inter = '1_MIN'
        load_from = datetime.now(timezone.utc).astimezone() - timedelta(minutes=load_period)
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_1_MIN
    else:
        load_inter = 'DAY'
        load_from = datetime.now(timezone.utc).astimezone() - timedelta(days=load_period)
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_DAY
    return load_from, load_inter, load_bar_inter

def analize_graf(Tbot: telebot.TeleBot, ID_ch, name_future, candl_interval, load_period, df333):
    '''# В разработке
    ФУНКЦИЯ: Автоматическое описание завершенного бара
    Описание должно содержать какой бар: продаж, покупок, пикообразный
    Должно быть описание хвоста если он есть: хвост покупок, хвост продаж
    Сообщение по типу: 
        новый максимум 1000 выше предыдущего 950 на ххх% или 50 пунктов
        новый миниму 800 выше предыдущего 750 на ххх% или 50 пунктов
    Должна быть информация где находится значени в области продаж или в области покупок

    Должно должно быть предсказание следущего бара 

    '''
    
    ''' Пример сообщения:
    За прошедший период [15мин, 1 час, 4 часа, День, Неделя, Месяц, Квартал] 
    сформировался бар [покупок, продаж, крестообразный бар продаж, пикообразный бар покупок]
    [с [небольшим, большим] хвостом [продаж, покупок]].
    Цена в области [покупок, продаж]. 
    [[Покупатель, продавец] [силный, слабый]]
    Следудщий бар ожидается бар [покупок, продаж].
    Локальный тренд [вверх, вниз].   
    '''
    o1=1
    h1=2
    l1=3
    c1=4
    lines, rows = df333.shape
    max_lines = lines -1
    # https://translated.turbopages.org/proxy_u/en-ru.ru.8537bdbb-63fa65f3-57e85c18-74722d776562/https/www.geeksforgeeks.org/how-to-get-cell-value-from-pandas-dataframe/
    print (df333['Open'].loc[df333.index[max_lines]])
    print (df333['Open'].iloc[max_lines])
    o1 = df333['Open'].iloc[max_lines]
    h1 = df333['High'].iloc[max_lines]
    l1 = df333['Low'].iloc[max_lines]
    c1 = df333['Close'].iloc[max_lines]
    v1 = df333['Volume'].iloc[max_lines]
    
    s_line = max_lines - 1
    o2 = df333['Open'].iloc[s_line]
    h2 = df333['High'].iloc[s_line]
    l2 = df333['Low'].iloc[s_line]
    c2 = df333['Close'].iloc[s_line]
    v2 = df333['Volume'].iloc[s_line]

    d_c12 = round((c1-c2)/c1*100, 2)


def graf_2(Tbot: telebot.TeleBot, ID_ch, name_future, candl_interval, load_period):
    '''
    ФУНКЦИЯ: единовременное отображение барного графика в чате за выбранный период
    [name_future] какой фьючерс отобразить, имя в формате MXI-3.23, имя, месяц экспирации, год
    [candl_interval] какой интервал отображаемых баров: 1m, 5m, 15m, 30m, 1h, 4h, 1D, 1W, 1Mth, 1Q, 1Y
    [load_period] сколько бар отобразить на графике
    '''
    global global_f_opt, g_df_p
    print('\nКОМАНДА одномоментного ОТОБРАЖЕНИЯ графика фьючерса за требуемый период')
    # выводим текущую дату и время
    print_date_time_now()

    # от какой даты загрузить, номер интервала CandleInterval, наименование для отображения
    load_from, name_period, ti_candl_int = calc_load_from (candl_interval, load_period)

    # до какой даты загрузить
    load_to = datetime.now(timezone.utc).astimezone()

    print('Подключаемся к Tinkoff для чтения фьючерсов')
    with Client(TOKEN) as grpc_client:
        # загружаем список фьючерсов
        print('Подключились к Tinkoff')
        FIGI_full, future_lst, future_find_objct, future_info = find_future (Tbot, ID_ch, grpc_client, name_future)
        print('Получили после поиска')
        # процесс загрузки баров
        try:
            bars = grpc_client.market_data.get_candles(
                figi=FIGI_full,
                from_=load_from,
                to=load_to,
                interval=ti_candl_int
            )
        except Exception as ebx:
            print(ebx)
            try:
                reg_msg()
                Tbot.send_message(ID_ch,
                              '⚡️ОШИБКА⚡️ \nЧто-то пошло не так при баров  из платформы Тинькофф.'
                              '\nПопробуйте вернуть настройки на первоначальные⚡️'
                              f'\n{ebx}')
            except Exception as e:
                telega_error (e)
            return 0

        canl_shop = bars.candles  # загруженные бары
        # преобразуем данные в dateframe для построения графика
        if len(canl_shop):
            print('Преобразуем данные в dateframe для построения графика')
            df333 = create_df_bars_set(canl_shop)
            
            # доработка в случае недельных интервалов
            if candl_interval == 'Q':
                ohlc = {
                        'Open': 'first',
                        'High': 'max',
                        'Low': 'min',
                        'Close': 'last',
                        'Volume': 'sum'
                    }
                b_df333 = df333.copy
                df333 = df333.resample('Q').agg(ohlc)


            if candl_interval == 'M':
                ohlc = {
                        'Open': 'first',
                        'High': 'max',
                        'Low': 'min',
                        'Close': 'last',
                        'Volume': 'sum'
                    }
                b_df333 = df333.copy
                df333 = df333.resample('M').agg(ohlc)

            if candl_interval == '1W':
                ohlc = {
                        'Open': 'first',
                        'High': 'max',
                        'Low': 'min',
                        'Close': 'last',
                        'Volume': 'sum'
                    }
                b_df333 = df333.copy
                df333 = df333.resample('1W').agg(ohlc)
            elif candl_interval == '4h':
                ohlc = {
                        'Open': 'first',
                        'High': 'max',
                        'Low': 'min',
                        'Close': 'last',
                        'Volume': 'sum'
                    }
                b_df333 = df333.copy
                df333 = df333.resample('4h').agg(ohlc)
                df333 = df333.dropna()

            # строим график
            print('Строим график')
            f_tiker = future_lst['tiker']
            name_file_img = f'images/img-gr2-{f_tiker}.png'
            try:
                clo_1 = df333.iloc[-2]['Close']
                clo_2 = df333.iloc[-1]['Close']
                mrk_prc = round((clo_2 - clo_1) / clo_1 * 100, 2)
                mrk_abs = round((clo_2 - clo_1), 2)
                mpf.plot(df333, style='mike', figsize=(7.2, 12.80),
                        title=f"{name_future} [{name_period}]"
                            f"\n{df333.iloc[-1]['Close']} пт. [{df333.shape[0]} bars]", volume=True,
                        savefig=name_file_img)
            except Exception as e:
                print()
                print('ВОЗНИКЛА ОШИБКА mpf.plot')
                print(datetime.now(timezone.utc).astimezone())
                print("Текст ошибки:")
                print(e)
                print()
            # отправляем график в чат
            print("Отправляем график в чат")
            caption_msg = f'{name_future}:[{name_period}]\n\n[{clo_2}]   {mrk_prc} %    {mrk_abs}\n'
            try:
                reg_msg()
                Tbot.send_photo(ID_ch, photo=open(name_file_img, 'rb'), caption=caption_msg,
                            disable_notification=True)
            except Exception as e:
                telega_error (e)
        else:
            try:
                reg_msg()
                Tbot.send_message(ID_ch,'Нет данных для отображения', disable_notification=True)
            except Exception as e:
                telega_error (e)

        # запускаем анализ загруженных баров
        analize_graf(Tbot, ID_ch, name_future, '1h', load_period, df333)
        print('Функция выполнена graf_2. Ждем следующую команду.')


# однократное отображение без повтора при нажатии кнопки "Без_повтора"
def graf_1(self: telebot.TeleBot, any):
    global global_f_opt, g_df_p
    print('\nКОМАНДА однократного ОТОБРАЖЕНИЯ ГРАФИКОВ')

    # получаем текущую дату и время
    curr_time = datetime.now(timezone.utc).astimezone()
    # переводим в текстовый вид
    print_date_time_now()
    
    # рисование графиков
    # основные настройки
    activ_contr_name = "-12.23"
    name_from_load = "MXI"
    full_name_load = name_from_load + activ_contr_name
    full_name_load = global_f_opt['full_future_name']
    # определяем количество баров для загрузки
    # количество интервалов для загрузки
    load_period = global_f_opt['depth_load_bars']
    # определяем заданный интервал загрузки
    if global_f_opt['candl_interval'] == CandleInterval.CANDLE_INTERVAL_DAY:
        load_inter = 'DAY'
        load_from = datetime.now(timezone.utc).astimezone() - timedelta(days=load_period)
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_DAY
    elif global_f_opt['candl_interval'] == CandleInterval.CANDLE_INTERVAL_HOUR:
        load_inter = 'HOUR'
        load_from = datetime.now(timezone.utc).astimezone() - timedelta(hours=load_period)
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_HOUR
    elif global_f_opt['candl_interval'] == CandleInterval.CANDLE_INTERVAL_15_MIN:
        load_inter = '15_MIN'
        load_from = datetime.now(timezone.utc).astimezone() - timedelta(minutes=load_period * 15)
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_15_MIN
    elif global_f_opt['candl_interval'] == CandleInterval.CANDLE_INTERVAL_5_MIN:
        load_inter = '5_MIN'
        load_from = datetime.now(timezone.utc).astimezone() - timedelta(minutes=load_period * 5)
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_5_MIN
    elif global_f_opt['candl_interval'] == CandleInterval.CANDLE_INTERVAL_1_MIN:
        load_inter = '1_MIN'
        load_from = datetime.now(timezone.utc).astimezone() - timedelta(minutes=load_period)
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_1_MIN
    else:
        load_inter = 'DAY'
        load_from = datetime.now(timezone.utc).astimezone() - timedelta(days=load_period)
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_DAY
    print(f'Имя текущих контрактов: {activ_contr_name}')
    print('Подключаемся к Tinkoff для чтения фьючерсов')
    with Client(TOKEN) as client:
        # загружаем список фьючерсов
        print('Подключились к Tinkoff')
        futures_instr = []  # список фьючерсов
        flag_r = True  # повторят загружать пока не получиться загрузить
        print('Формирование списка фьючерсов')
        while flag_r:
            try:
                futures = client.instruments.futures(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)
                flag_r = False
                futures_instr = futures.instruments  # список фьючерсов
                print(f'Всего фьючерсов в списке: {len(futures_instr)}')
            except Exception as e:
                print(datetime.now(timezone.utc).astimezone())
                print('\nВОЗНИКЛА ОШИБКА загрузки списка фьючерсов')
                print('futures=client.instruments.futures(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)')
                print(e)
                print()
                try:
                    reg_msg()
                    self.send_message(any, text="ВОЗНИКЛА ОШИБКА загрузки списка фьючерсов")
                except Exception as e:
                    telega_error (e)
                flag_r = True

        # поиск FIGI для требуемого фьючерса
        future_find_dict = {}  # текстовый список фьючерсов
        future_find_objct = []  # список объектов фьючерсов
        for i in futures_instr:
            if full_name_load in i.name:
                future_find_dict = {'figi': i.figi, 'tiker': i.ticker, 'name': i.name}
                future_find_objct.append(i)
                break
        print(f"Найден фьючерс: {future_find_dict['name']}")

        # какой фьючерс грузить
        full_FIGI_load = future_find_dict['figi']

        if future_find_objct[0].trading_status == 4 and not (load_inter == 'DAY'):
            msg = 'ВНИМАНИЕ!!!\n'
            msg += f'Дата: {now_date_txt_file()}\nВремя: {now_time_txt_file()}'
            msg += f"\nИнструмент:\n     {future_find_objct[0].name}\nв данное время НЕ ДОСТУПЕН для торгов"
            print(msg)
            try:
                reg_msg()
                self.send_message(any, msg)
            except Exception as e:
                telega_error (e)
            return 0

        print(f'Начинаем загрузку баров')
        # до какой даты загрузить
        load_to = datetime.now(timezone.utc).astimezone()
        # процесс загрузки баров
        try:
            bars = client.market_data.get_candles(
                figi=full_FIGI_load,
                from_=load_from,
                to=load_to,
                interval=load_bar_inter
            )
        except Exception as e:
            print(e)
            try:
                reg_msg()
                self.send_message(any,
                              '⚡️ОШИБКА⚡️ graf_1 '
                              '\nЧто-то пошло не так при баров  из платформы Тинькофф.'
                              '\nПопробуйте вернуть настройки на первоначальные⚡️'
                              f"\n{e}")
            except Exception as e:
                telega_error (e)
            return 0

        canl_shop = bars.candles  # загруженные бары
        if len(canl_shop) > 0:
            # преобразуем данные в dateframe для построения графика
            print('Преобразуем данные в dateframe для построения графика')
            df333 = create_df_bars_set(canl_shop)
            # строим график
            print('Строим график')
            f_tiker = future_find_dict['tiker']
            name_file_img = f'images/img-gr-1-{f_tiker}.png'
            try:
                hmm_ld_time = datetime.strftime(load_to, '%H:%M:%S.%f')
                mpf.plot(df333, style='mike', figsize=(7.2, 12.80),
                         title=f"{full_name_load} [{load_inter}]\n{hmm_ld_time}\n{df333.iloc[-1]['Close']} пт.",
                         volume=True, savefig=name_file_img)
            except Exception as e:
                print()
                print('ВОЗНИКЛА ОШИБКА mpf.plot')
                print(datetime.now(timezone.utc).astimezone())
                print("Текст ошибки:")
                print(e)
                print()
            # отправляем график в чат
            print("Отправляем график в чат")
            msg_img = f"{full_name_load} [{load_inter}]\n{df333.iloc[-1]['Close']} пт."
            try:
                reg_msg()
                self.send_photo(any, photo=open(name_file_img, 'rb'), caption=msg_img)
            except Exception as e:
                telega_error (e)
        else:
            try:
                reg_msg()
                self.send_message(any.chat.id, 'Нет данных на текущее время')
            except Exception as e:
                telega_error (e)
        print('Функция выполнена. Ждем следующую команду.')


# Запуск циклической выдачи графика по настройкам по команде 'Цикл_gr'
def graf_3(t_bot: telebot.TeleBot, any):
    # настройки до цикла
    global global_f_opt, g_df_p
    limit_to = 8 # Отключение на время глубокой ночи
    if global_f_opt['In_process']:
        print("Цикл уже запущен")
        try:
            reg_msg()
            t_bot.send_message(any, "Цикл уже запущен", disable_notification=True)
        except Exception as e:
                telega_error (e)
        # не даем запуститься функции повторно
        return 0
    
    # Не запускаться если выходные
    dt_now = datetime.now(timezone.utc).astimezone()
    week_day = dt_now.isoweekday()
    if global_options ['run_in_weekends'] == False and (week_day == 6 or week_day == 7):
        msg = "Сегодня выходной!!!\n\n"
        msg += 'Автоматический цикл выдачи графика остановлен и не доступен для запуска до 6 утра понедельника'
        print ()
        print(msg)
        global_f_opt['In_process'] = False
        global_f_opt['repeat_flag'] = False
        show_run_repit_btn(t_bot, ADIMIN_ID_TG, 'Цикл_gr')
        try:
            reg_msg()
            t_bot.send_message(any, msg, disable_notification=True)
        except Exception as e:
                telega_error (e)
        return 0

    # Не работает глубокой ночью
    hour_now = dt_now.hour
    if global_options ['run_in_night'] == False and hour_now < limit_to:
        msg = f'ДО {limit_to} утра НЕ РАБОТАЕТ!!!\n\n'
        msg += f'Автоматический цикл выдачи графика остановлен и не доступен для запуска до {limit_to} утра.\n\nОстальные функции бота доступны.'
        print (msg)
        global_f_opt['In_process'] = False
        global_f_opt['repeat_flag'] = False
        show_run_repit_btn(t_bot, ADIMIN_ID_TG, 'Цикл_gr')
        try:
            reg_msg()
            t_bot.send_message(any, msg, disable_notification=True)
        except Exception as e:
                telega_error (e)
        return 0

    print('\nКОМАНДА ЦИКЛИЧЕСКОГО ОТОБРАЖЕНИЯ ГРАФИКОВ')
    print('global_f_opt[full_future_name]', global_f_opt['full_future_name'])
    print('global_f_opt[candl_interval]', global_f_opt['candl_interval'])
    print('global_f_opt[depth_load_bars]', global_f_opt['depth_load_bars'])
    print('global_f_opt[repeat_flag]', global_f_opt['repeat_flag'])

    global_f_opt['In_process'] = True
    print_date_time_now()
    # рисование графиков
    # основные настройки
    full_name_load = global_f_opt['full_future_name']
    # определяем количество баров для загрузки
    # количество интервалов для загрузки
    load_period = global_f_opt['depth_load_bars']

    # Определяем дату начала загрузки, т.е. от какой даты грузить
    load_from, load_inter, load_bar_inter = load_from_graf (load_period)
    
    print(f'Имя текущих контрактов: {full_name_load}')
    print('Подключаемся к Tinkoff для чтения фьючерсов')
    print(f'Дата и время начала загрузки:  \n{load_from}')
    print(f'load_inter: {load_inter}')
    print(f'load_bar_inter: {load_bar_inter}')
    with Client(TOKEN) as client:
        print('Подключились к Tinkoff для функции graf_3')
        
        # заменить на find_figi_of_name_future 
        if global_f_opt['type_analyse'] == 'future':
            # ПЕРЕДЕЛАТЬ используя функцию FutureBy. НО нужна тогда FIGI!!!!
            # https://tinkoff.github.io/investAPI/instruments/
            # https://tinkoff.github.io/investAPI/instruments/#instrumentrequest
            # загружаем список фьючерсов
            futures_instr = []  # список фьючерсов
            flag_r = True  # повторят загружать пока не получиться загрузить
            repit_cont = 10
            repit_n = 0
            print('Формирование списка фьючерсов')
            
            # 1.Получаем список фьючерсов, выходные данные: futures_instr
            while flag_r:
                try:
                    futures = client.instruments.futures(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)
                    flag_r = False
                    futures_instr = futures.instruments  # список фьючерсов
                    print(f'Всего фьючерсов в списке: {len(futures_instr)}')
                except Exception as e:
                    repit_n +=1
                    print(datetime.now(timezone.utc).astimezone())
                    print('\nВОЗНИКЛА ОШИБКА загрузки списка фьючерсов graf_3')
                    print('futures=client.instruments.futures'
                            '(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)')
                    print(e)
                    print()
                    if repit_n >= repit_cont:
                        flag_r = False
                    else: 
                        flag_r = True
            
            # поиск FIGI для требуемого фьючерса указанного в global_f_opt['full_future_name']
            future_find_dict = {}  # текстовый список фьючерсов
            future_find_objct = []  # список объектов фьючерсов
            for i in futures_instr:
                if full_name_load in i.name:
                    future_find_dict = {'figi': i.figi, 'tiker': i.ticker, 'name': i.name}
                    future_find_objct.append(i)
                    # какой фьючерс грузить
                    full_FIGI_load = future_find_dict['figi']
                    # GetFuturesMarginRequest получаем  описание ГО фьючерса
                    future_info = client.instruments.get_futures_margin(figi=full_FIGI_load)
                    print(f"Найден фьючерс: {future_find_dict['name']}\n")
                    global_f_opt['future_FIGI'] = full_FIGI_load
                    break
        else:
            for stock_item in global_bag_of_stocks:
                if global_f_opt['stocks_ticker'] == stock_item.ticker:
                    full_FIGI_load = stock_item.figi
                    print(f"Найдена акция: {stock_item.name}\n")
                    break
        
        # цикл периодического опроса
        while_go_flag = True
        print(f'Начинаем циклическую работу, с периодом:  {load_inter}')
        
        # ОСНОВНОЙ ЦИКЛ повторения вывода кнопок
        while while_go_flag:
            # Периодический опрос состояния доступности инструмента для совершения операций
            f_1_obg = client.instruments.future_by (id_type = InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, id = full_FIGI_load)
            trading_status_f = f_1_obg.instrument.trading_status
            # до какой даты загрузить
            load_to = datetime.now(timezone.utc).astimezone()
            name_file_img = ''
            
            #ВЫДАЧА ПЕРВОГО ГРАФИКА В ЧАТ
            # Так же необходимо обновлять load_from в соответствии с количество баров необходимых для отображения 
            # Если тоги ведуться и интервал циклического отображения отличный от дневки, то отобразить график с кнопками
            if trading_status_f == SecurityTradingStatus.SECURITY_TRADING_STATUS_NORMAL_TRADING and load_inter != 'DAY':
                # процесс загрузки баров
                try:
                    bars = client.market_data.get_candles(
                        figi=full_FIGI_load,
                        from_=load_from,
                        to=load_to,
                        interval=load_bar_inter
                    )
                except Exception as ebx:
                    global_f_opt['In_process'] = False
                    global_f_opt['repeat_flag'] = False
                    print('⚡️ОШИБКА в graf_3 (.get_candles)⚡️. Цикл будет остановлен. ', ebx)
                    try:
                        reg_msg()
                        t_bot.send_message(any,
                                        '⚡️ОШИБКА в graf_3 (.get_candles)⚡️. Цикл будет остановлен. '
                                        f'\n{ebx}')
                    except Exception as e:
                        telega_error (e)
                    show_repeat_btn(t_bot, any, 'Стоп_цикл_gr')
                    return 0
                # загруженные бары
                canl_shop = bars.candles
                # проверять, что баров столько, сколько требуется в соотв. с настройками
                if len(canl_shop) > 0:
                    # преобразуем данные в dataframe для построения графика
                    print('Преобразуем данные в DataFrame для построения графика')
                    s_time = time.time()
                    df333 = create_df_bars_set(canl_shop)
                    e_time = time.time()
                    d_time = e_time - s_time
                    print(f'Время работы с DataFrame заняло:  {d_time} сек')

                    # строим график
                    print('Строим график')
                    f_tiker = future_find_dict['tiker']
                    name_file_img = f'images/img{f_tiker}.png'
                    last_close = df333.iloc[-1]['Close']
                    try:
                        s_time = time.time()
                        hmm_ld_time = datetime.strftime(load_to, '%H:%M:%S.%f')
                        title_g = ""  # Надпись на графике
                        title_g += f"{full_name_load} [{load_inter}]"
                        title_g += f"\n{hmm_ld_time}   [{df333.shape[0]}bars]"
                        title_g += f"\n{last_close} пт."
                        # tight_layout=True если нужен график на всю ширину
                        mpf.plot(df333, style='mike', figsize=(7.2, 12.80),
                                 title=title_g, volume=True, tight_layout=False,
                                 savefig=name_file_img)
                        e_time = time.time()
                        d_time = e_time - s_time
                        print(f'Время сохранения картинки  барного графика на диск:  {d_time} сек')
                    except Exception as e:
                        print()
                        print('ВОЗНИКЛА ОШИБКА mpf.plot')
                        print(datetime.now(timezone.utc).astimezone())
                        print("Текст ошибки:")
                        print(e)
                        print()
                        try:
                            reg_msg()
                            t_bot.send_message(any, text='ВОЗНИКЛА ОШИБКА mpf.plot', disable_notification=True)
                        except Exception as e:
                            telega_error (e)
                    # отправляем график в чат
                    print("Отправляем график в чат")
                    # сообщение в чат
                    s_time = time.time()
                    hmm_ld_time = datetime.strftime(load_to, '%H:%M:%S.%f')
                    msg_img = f"{full_name_load} #{f_tiker}_{load_inter}" \
                              f"\n    {hmm_ld_time}" \
                              f"\n{last_close} пт."
                    hmm_ld_time_GA1 = datetime.strftime(load_to, '%H:%M:%S')
                    # msg_img_GA1 = f"{last_close}  {hmm_ld_time_GA1}\n" \
                    #               f"{full_name_load} ({load_inter})\n" \
                    #               f"{last_close} пт."
                    msg_img_GA1 = f"{last_close}  {hmm_ld_time_GA1}\n"
                                
                    try:
                        reg_msg()
                        # отправка первого графика в чат
                        t_bot.send_photo(any, photo=open(name_file_img, 'rb'), caption=msg_img)
                        graf_bot.send_photo(ADIMIN_ID_TG, photo=open(name_file_img, 'rb'), caption=msg_img_GA1)
                    except Exception as e:
                        telega_error (e)
                    e_time = time.time()
                    d_time = e_time - s_time
                    print(f'Время отправки сообщения в чат:  {d_time} сек')
                else:
                    try: 
                        reg_msg()
                        t_bot.send_message(any, 'Нет данных на текущее время')
                    except Exception as e:
                        telega_error (e)
            else:
                pass 
                # все тоже самое, но только дневной график

            # флаг управления циклом повторной отправки графика в чат
            if global_f_opt['repeat_flag']:
                # if load_inter == '15_MIN':
                print('Выполняем 15 минутный цикл')
                # вычисление паузы перед следующей выдачей графика в чат через 15 минут в основном
                dt1 = now_dtime()  # текущее дата и время
                min1 = dt1.minute  # минуты текущего времени
                sec1 = dt1.second  # секунды текущего времени
                t_sum = min1 * 60 + sec1  # общее время в секундах, которое прошло с начала часа
                t_view = 60  # время на принятие решения в секундах до окончания очередно 15 минутки
                # вычисление сколько осталось до конца очередной 15 минутки
                # за основу берется количество секунд с начала часа t_sum
                # расчет паузы, когда меньше или равно 15 минутам
                if t_sum < (15 * 60) or t_sum == (15 * 60):
                    delta1 = 15 * 60 - t_sum
                    stp_min = 15
                # расчет когда более 15 минут, но меньше или равно 30 минут
                elif (15 * 60) < t_sum < (30 * 60) or t_sum == (30 * 60):
                    delta1 = 30 * 60 - t_sum
                    stp_min = 30
                # расчет когда более 30 мин, но меньше или равно 45 мин
                elif (30 * 60) < t_sum < (45 * 60) or t_sum == (45 * 60):
                    delta1 = 45 * 60 - t_sum
                    stp_min = 45
                # расчет когда более 45 мин, но менее или равно 60 мин
                elif (45 * 60) < t_sum < (60 * 60) or t_sum == (60 * 60):
                    delta1 = 60 * 60 - t_sum
                    stp_min = 60
                # если расчет не попал ни в один интервал делаем 5 секундную задержку
                else:
                    delta1 = 5
                    stp_min = 14

                # если пауза до следующего интервала большая получилась, то уменьшаем эту паузу на принятие решения
                if delta1 > t_view:
                    delta1 -= t_view
                    # стоп_минута выхода из функции отображения и паузы на минуту меньше, чтобы принять решение
                    stp_min -= 1
                # если пауза меньше или равно 5 сек, то просто ждем. 
                # Неприятность в том что на это время ПОЗИЦИЯ ОСТАЕТСЯ БЕЗ УПРАВЛЕНИЯ
                if delta1 <= 5:
                    time.sleep(5)
                # при большей паузе выводим диалог с отображением
                else:
                    stp_sec = 0
                    sleep_and_show_msg(t_bot, any, client, full_FIGI_load, delta1, stp_min, stp_sec,
                                        name_file_img, load_from)

                # else:
                #     # Выход из цикла. Для остальных интервалов не придумано
                #     while_go_flag = False

            else:
                while_go_flag = False
                print('Повтора не будет')
        global_f_opt['In_process'] = False
        global_f_opt['repeat_flag'] = False
        print('Функция выполнена. Ждем следующую команду.')

# ОСНОВНАЯ функция циклического отображения графика с периодиеской перезагрузкой раз в 15 минут
def sleep_and_show_msg(t_bot: telebot.TeleBot, ID_ch, client: services.Services, FIGI, pause_sec, stop_minute, stop_sec,
                       start_f_name, load_from):
    """
    ОСНОВНАЯ функция 15 минутных циклов
    start_f_name путь к файлу графика для вывода когда тоги активны

    """
    global bot, global_options, global_bids_data, global_f_opt, g_long_count
    account_id=global_options['ac_id'] # ID счета с которым работаем
    pause_post =  global_options['pause_post'] # Время паузы выдачи графика
    no_edit = global_options['no_edit'] # признак того, что график и книпки надо  постоянно выдвать в чат, вместо редактирования статичного текста
    now_graf = True  # флаг для выдачи графика через раз , иначе телега ругается чё так много
    # Предыдущая цена которая последний раз выводилась на графике.
    # Нужно чтобы постоянно график не постить в момент когда цена стоит на месте
    back_show_price_gr = 0

    # Вывод LABELs в чат как перыичных сообщений, после окончания цикла они удаляются

    # ЗАТРАВКА label_graf с графиком
    # Картинка с графиком, затравка для поледующих циклических изменений. Приходит из функции graf_3
    if start_f_name != '':
        try:
            reg_msg()
            label_graf = t_bot.send_photo(ID_ch, photo=open(start_f_name, 'rb'), caption='старт label_graf', disable_notification=True)
        except Exception as e:
            telega_error (e)
    else:
        label_graf = ""

    # ЗАТРАВКА label_time с сообщением
    # сообщение с обратным отчетом до конца выбранного интервала
    # сообщение затравка от которого начинаются циклические изменения 
    try:
        reg_msg()
        label_time = t_bot.send_message(ID_ch, 'label_time', disable_notification=True)

    # ЗАТРАВКА label_oper для вывода перечня операций.
    # сделать отображение условным, если операций нет, то не отображать
    # по ФИГИ найти позицию через функцию.
        if global_f_opt['show_oper_in_chat']:
            reg_msg()
            label_oper = t_bot.send_message(ID_ch, 'label_oper', disable_notification=True)
    except Exception as e:
        telega_error (e)
    msg_oper_old = ''

    # Основной цикл паузы и отображения до конца текущего интервала
    cont_sec = range(pause_sec)
    show_wrk = True

    #Заготавливаем разные виды анимации
    time_list_3 =['🌕','🌖','🌗','🌘','🌑','🌒','🌓','🌔']
    count_time_icon = 0 #счетчик картинок для последовательного вывода
    mt1 = 0 # счетчик задержек

    # !!!!!!!!!!ОСНОВНОЙ ЦИКЛ секунд!!!!!!!!!!!!!!!!!!!!!!!!
    for item in cont_sec:
        cicrcle_time_start = time.time() #запоминаем секунды в начале
        # актуализируем значение настроек на случай их изменения 
        no_edit = global_options['no_edit']
        pause_post =  global_options['pause_post']


        # Не запускаться если выходные
        dt_now = datetime.now(timezone.utc).astimezone()
        week_day = dt_now.isoweekday()
        if global_options ['run_in_weekends'] == False and (week_day == 6 or week_day == 7):
            msg = "Сегодня выходной!!!\n\n"
            msg += 'Автоматический цикл выдачи графика остановлен и не доступен для запуска до 6 утра понедельника'
            print()
            print(msg)
            global_f_opt['In_process'] = False
            global_f_opt['repeat_flag'] = False
            show_run_repit_btn(t_bot, ADIMIN_ID_TG, 'Цикл_gr')
            try:
                reg_msg()
                t_bot.send_message(ID_ch, msg, disable_notification=True)
            except Exception as e:
                    telega_error (e)
            return 0

        # Не работает глубокой ночью
        hour_now = dt_now.hour
        if global_options ['run_in_night'] == False and hour_now <6:
            msg = 'ДО 6 утра НЕ РАБОТАЕТ!!!\n\n'
            msg += 'Автоматический цикл выдачи графика остановлен и не доступен для запуска до 6 утра.\n\nОстальные функции бота доступны.'
            print (msg)
            global_f_opt['In_process'] = False
            global_f_opt['repeat_flag'] = False
            show_run_repit_btn(t_bot, ADIMIN_ID_TG, 'Цикл_gr')
            try:
                reg_msg()
                t_bot.send_message(ID_ch, msg, disable_notification=True)
            except Exception as e:
                    telega_error (e)
            return 0

        # ЧТЕНИЕ необходимых данных
        # принудительный выход из цикла отображения графика, когда текущее время равно или больше stop_minute
        nw_time = datetime.now(timezone.utc).astimezone()
        if nw_time.minute >= stop_minute:
            print('Конец паузы:', nw_time)
            break
        # проверяем на изменение типа отображаемого инструмента при изменении настроек в процессе работы
        FIGI = global_f_opt['future_FIGI']
        # проверяем флаг повтора. При нажатии кнопки стоп или иных обстоятельствах выполняем принудительный выход
        if not global_f_opt['repeat_flag']:
            global_f_opt['In_process'] = False
            try:
                print(f'Цикл ОСТАНОВЛЕН\n')
                # reg_msg()
                # t_bot.send_message(ID_ch, f'Цикл ОСТАНОВЛЕН\n', disable_notification=True)
            except Exception as e:
                telega_error (e)
            # show_repeat_btn(t_bot, ID_ch, 'Стоп_цикл_gr')
            break
        # при установленном в True флаге циклического отображения графика, продолжаем работу
        show_price = 0
        try: 
            hmm_nw_time = datetime.strftime(now_dtime(), '%H:%M:%S')
            # читаем данные из платформы
            what_name_error_fun = ''
            reload_error_count = 1 # счетчик попыток автоматического повторого чтения (АПЧ)
            reload_limit = 5 # количество АПЧ
            reload_of_error = True # Необходимости многократного повтора чтения при ошибке
            # Загрузить еще раз если ошибка.
            while reload_of_error:# Но есть проблема, когда все время ошибки, то все зависает на этом месте
                try:
                    # торгуется или нет
                    what_name_error_fun = 'future_by (запрос на информацию о статусе торгов)'
                    f_1_obg = client.instruments.future_by (id_type = InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, 
                                                            id = FIGI)
                    trading_status_f = f_1_obg.instrument.trading_status

                    # последняя цена
                    what_name_error_fun = 'get_last_prices (запрос последней цены)'
                    lp = client.market_data.get_last_prices(figi=[FIGI]).last_prices  
                    last_price = cast_money(lp[0].price)
                    show_price = last_price

                    # стакан заявок
                    what_name_error_fun = 'get_order_book (стакан заявок)'
                    book = client.market_data.get_order_book(figi=FIGI, depth=5)
            
                    # поиск запрашиваемого инструмента в портфеле
                    what_name_error_fun = 'get_portfolio (запрос состояния портфеля)'
                    portfel = client.operations.get_portfolio(account_id=global_options['ac_id'])  # портфель по счету
                    pos_prt = portfel.positions

                    # загрузка исторических данных о цене для графика
                    what_name_error_fun = 'get_candles (запрос исторических баров)'
                    # готовим данные
                    # количество интервалов для загрузки
                    load_period = global_f_opt['depth_load_bars']
                    # интервал загрузки
                    load_interval = global_f_opt['candl_interval']
                    # Определяем дату начала загрузки, т.е. от какой даты грузить
                    load_from, load_inter, load_bar_inter = load_from_graf (load_period)
                    # Дата окончания загрузки
                    load_to = datetime.now(timezone.utc).astimezone()
                    # непосредственно сама загрузка исторических данных о цене                 
                    bars = client.market_data.get_candles(
                        figi=FIGI,
                        from_=load_from, # сделать согласно глобальных настроек количества баров
                        to=load_to,
                        interval= load_interval)
                    candl_shop = bars.candles  # загруженные бары

                    # загрузка информации о маржинальных параметрах фьючерса
                    what_name_error_fun = 'get_futures_margin (запрос о маржинальных параметрах фьючерса)'
                    f_inf = client.instruments.get_futures_margin(figi=FIGI)
                    
                    # загрузка последних операций для отображения составляющих позиции и доходности в чате с кнопками
                    # перенести в отдельную функцию
                    # саму загрузку перенести ниже и выполнять только при наличии позиции в портфеле
                    if global_f_opt ['show_oper_in_chat']:
                        # https://tinkoff.github.io/investAPI/operations/#getoperationsbycursor
                        what_name_error_fun = 'get_operations_by_cursor (список операций по счёту)'
                        # задание настроек для чтения операций
                        r1 = GetOperationsByCursorRequest()
                        r1.account_id = account_id
                        r1.instrument_id = FIGI
                        r1.from_ = datetime.now(timezone.utc).astimezone() - timedelta(days=20)
                        r1.to = datetime.now(timezone.utc).astimezone()
                        # количество операций загрузки за один раз
                        r1.limit = 100 
                        # 15	Покупка ЦБ.
                        # 16	Покупка ЦБ с карты.
                        # 18	Продажа в результате Margin-call.
                        # 20	Покупка в результате Margin-call.
                        # 22	Продажа ЦБ.
                        r1.operation_types = [OperationType.OPERATION_TYPE_BUY, OperationType.OPERATION_TYPE_SELL]
                        r1.state =  OperationState.OPERATION_STATE_EXECUTED     # 	1	Исполнена.
                        r1.without_commissions = True
                        r1.without_trades = True
                        r1.without_overnights = True
                        s_oper = client.operations.get_operations_by_cursor(r1)
                        s1_oper = s_oper.items
                        # print (s1_oper)

                    # загрузка активных  заявок имеющихся сейчас у пользователя (нуждается в разработке)
                        # akt_orders = client.orders.get_orders (account_id = account_id).orders
                        # if len(akt_orders) > 0:

                    
                    # проверка количества допустимых перезагрузок при ошибках
                        
                    # признаки того, что все загрузки выполнились без ошибок
                    reload_of_error = False
                    reload_error_count = 1
                    what_name_error_fun = 'NOT ERRORS'                    

                # обрабока, когда возникла ошибка при загрузке данных
                # приращение счетчика ошибок
                except Exception as e:
                    print_date_time_now()
                    print('\nВОЗНИКЛА ОШИБКА!!!')
                    print( f"в функции: {what_name_error_fun}")
                    print(e)
                    print(f"reload_error_count: {reload_error_count}")
                    print()
                    # работа с количеством ошибок
                    if reload_error_count >= reload_limit:
                        reload_of_error = False
                        reload_error_count = 1
                        print(f'Достигнут предел перезагрузок по ошибке: reload_error_count {reload_error_count} >= {reload_limit}')
                    else:
                        reload_of_error = True
                        reload_error_count += 1 

                    if e.code.name == 'INTERNAL':
                        limit_count = e.metadata.ratelimit_remaining
                        stop_time = e.metadata.ratelimit_reset + 2
                        if limit_count < 2:
                            print(f'Сон {stop_time} сек.....\n\n\n')
                            try:
                                reg_msg()
                                t_bot.send_message(ID_ch, text=f"\nПауза: {stop_time} сек...\n\n\n", disable_notification=True)
                            except Exception as e:
                                telega_error (e)
                            time.sleep(stop_time)

                    elif e.code.name == 'RESOURCE_EXHAUSTED':
                        stop_time = e.metadata.ratelimit_reset + 2
                        print()
                        print_date_time_now()
                        print(what_name_error_fun)
                        print(e)
                        print (f'сон {stop_time} сек...')
                        try:
                            reg_msg()
                            t_bot.send_message(ID_ch, text=f"#ОШИБКА!!! превышено количество запросов:" 
                                        f"\nфункция: {what_name_error_fun}" 
                                        f"\nтип ошибки: {e.code.name}"
                                        f"\nПауза: {stop_time} сек...\n\n\n", disable_notification=True)
                        except Exception as e:
                            telega_error (e)
                        time.sleep(stop_time)
                        print_date_time_now()
                        print()

                    elif e.code.name == 'Stream removed':
                        limit_count = e.metadata.ratelimit_remaining
                        stop_time = e.metadata.ratelimit_reset + 2
                        if limit_count < 2:
                            print(f'Сон {stop_time} сек.....\n\n\n')
                            try:
                                reg_msg()
                                t_bot.send_message(ID_ch, text=f"\nПауза: {stop_time} сек...\n\n\n", disable_notification=True)
                            except Exception as e:
                                telega_error (e)
                            time.sleep(stop_time)

            # ОБРАБОТКА загруженных данных
            # графические иконки для таймера
            if count_time_icon > (len (time_list_3)-1):
                count_time_icon = 0
            t_i = time_list_3[count_time_icon]  # иконка с одним из цифирблатов
            count_time_icon +=1

            # проверяем имеется ли позиция по активному инструменту
            pos_is_find = False
            for pos_f in pos_prt:
                if pos_f.figi == FIGI:
                    pos_avg_price = cast_money(pos_f.average_position_price_fifo)
                    pos_avg_price_pt = cast_money(pos_f.average_position_price_pt)
                    pos_quntaty = cast_money(pos_f.quantity)
                    pos_yeld = cast_money(pos_f.expected_yield)
                    pos_is_find = True
                    break

            # создаем клавиатуру в чате, где будем отображать текущую позицию и стакан по инструменту
            keyboard = types.InlineKeyboardMarkup(row_width=3)

            # при наличии позиции подготовить кнопки с данными о позиции из портфеля
            if pos_is_find:
                # кнопка со средней ценой
                b_pos_avg = types.InlineKeyboardButton(text=f'{round (pos_avg_price,3)}',
                                                       callback_data='pos_')
                if pos_avg_price == 0:
                    b_pos_avg = types.InlineKeyboardButton(text=f'{round (pos_avg_price_pt,3)}',
                                                       callback_data='pos_')
                # кнопка с количеством
                b_pos_quntaty = types.InlineKeyboardButton(text=f'{pos_quntaty}',
                                                           callback_data='pos_')
                # кнопка с доходностью
                # b_pos_yeld = types.InlineKeyboardButton(text=f'{pos_yeld}',
                #                                         callback_data='pos_')
                # Т.к. ТИНЬКОФФ не умеет считать доходность позиции по фьючерсам, выполняем пересчет
                #вычисление стоимости шага цены фьючерса
                if not (q_to_var(f_inf.min_price_increment) == 0): # для исключения ошибки деления на ноль
                    step_price = q_to_var(f_inf.min_price_increment_amount) / q_to_var(f_inf.min_price_increment)
                else:
                    step_price =1
                # расчет доходности через последнюю цену с учетом текущей стоимости пункта цены
                if pos_quntaty > 0:#расчет для лонга
                    pos_yeld_calc = (last_price - pos_avg_price) * step_price * pos_quntaty
                    total_cost_pos = pos_avg_price * step_price * pos_quntaty
                    if not(total_cost_pos == 0): # для исключения ошибки деления на ноль
                        pos_proc = round ((pos_yeld_calc / total_cost_pos)*100, 2)
                    else:
                        pos_proc = 0
                else:
                    pos_yeld_calc = (pos_avg_price - last_price) * step_price * pos_quntaty * -1
                    total_cost_pos = pos_avg_price * step_price * pos_quntaty
                    if not(total_cost_pos ==0): # для исключения ошибки деления на ноль
                        pos_proc = round ((pos_yeld_calc / total_cost_pos)*100, 2)
                    else:
                        pos_proc = 0
                # кнопка с рассчитанной доходностью
                if global_f_opt['show_oper_in_chat']:
                    b_pos_yeld = types.InlineKeyboardButton(text=f'{round(pos_yeld_calc, 2)}  {pos_proc}%',
                                                            callback_data='pos_')
                else:
                    b_pos_yeld = types.InlineKeyboardButton(text=f'{round(pos_yeld_calc, 2)}',
                                                            callback_data='pos_')

            # При наличии стакана для совершения операций 
            # подготовить кнопки с ценами и количеством покупателей и продавцов, иначе простой таймер отобразить без кнопок
            if len(book.bids) > 0:
                sell1, sell2, sell3, sell4, sell5 = book.asks[0], book.asks[1], book.asks[2], book.asks[3], book.asks[4]
                buy1 = book.bids[0]
                buy2 = book.bids[1]
                buy3 = book.bids[2]
                buy4 = book.bids[3]
                buy5 = book.bids[4]
                global_bids_data['buy1'] = sell1
                global_bids_data['sell1'] = buy1
                global_bids_data['FIGI'] = book.figi
                # вычисление доходности в зависимости от стакана и этой кнопки
                
                #вычисление позиции при наличии стакана. Результат вычисляется исходя из цены в стакане
                if pos_is_find:
                    #вычисление стоимости шага цены
                    if not( q_to_var(f_inf.min_price_increment) == 0):  # для исключения ошибки деления на ноль
                        step_price = q_to_var(f_inf.min_price_increment_amount) / q_to_var(f_inf.min_price_increment)
                    else:
                        step_price = 1
                    # вычисление доходности когда имеется информация из стакана
                    if pos_quntaty > 0:  # позиция лонг
                        buy1_price = cast_money(buy1.price)
                        show_price = buy1_price
                        last_price = show_price
                        pos_delta = (buy1_price - pos_avg_price) * pos_quntaty * step_price
                        total_cost_pos = pos_avg_price * pos_quntaty * step_price
                        pos_delta = round(pos_delta, 2)
                        if not (total_cost_pos == 0): # для исключения ошибки деления на ноль
                            pos_proc = round ((pos_delta / total_cost_pos)*100, 2)
                        else:
                            pos_proc = 0
                    else:  # позиция шорт
                        sell1_price = cast_money(sell1.price)
                        show_price = sell1_price
                        last_price = show_price
                        pos_delta = (pos_avg_price - sell1_price) * pos_quntaty * -1 * step_price
                        total_cost_pos = pos_avg_price * pos_quntaty * step_price * -1
                        pos_delta = round(pos_delta, 2)
                        if not (total_cost_pos == 0):
                            pos_proc = round ((pos_delta / total_cost_pos)*100, 2)
                        else:
                            pos_proc = 0
                    # кнопка с рассчитанной доходностью расчитанной через цену в стакане
                    if global_f_opt['show_oper_in_chat']:
                        b_pos_yeld = types.InlineKeyboardButton(text=f'{pos_delta}  {pos_proc}%', callback_data='tt')
                    else:
                        b_pos_yeld = types.InlineKeyboardButton(text=f'{pos_delta}', callback_data='tt')

                # ПРОДАВЦЫ В СТАКАНЕ (сверху)
                if global_set_from_orders['oper_block_bt']:
                    s1 = types.InlineKeyboardButton(text=f'🔒B: {round (cast_money(sell1.price),3)} [{sell1.quantity}]',
                                                    callback_data='buy1_bt')
                else:
                    s1 = types.InlineKeyboardButton(text=f'✅B: {round (cast_money(sell1.price),3)} [{sell1.quantity}]',
                                                    callback_data='buy1_bt')
                # s2 = types.InlineKeyboardButton(text=f'{cast_money(sell2.price)} [{sell2.quantity}]',
                #                                 callback_data='s2')
                # s3 = types.InlineKeyboardButton(text=f'{cast_money(sell3.price)} [{sell3.quantity}]',
                #                                 callback_data='s3')

                # ПОКУПАТЕЛИ в СТАКАНЕ (снизу). Покупатели нужны чтобы им продать
                if global_set_from_orders['oper_block_bt']:
                    b1 = types.InlineKeyboardButton(text=f'🔒S: {round (cast_money(buy1.price),3)} [{buy1.quantity}]',
                                                    callback_data='sell1_bt')
                else:
                     b1 = types.InlineKeyboardButton(text=f'✅S: {round (cast_money(buy1.price),3)} [{buy1.quantity}]',
                                                    callback_data='sell1_bt')
                # b2 = types.InlineKeyboardButton(text=f'{cast_money(buy2.price)} '
                #                                      f'[{buy2.quantity}]', callback_data='b2')
                # b3 = types.InlineKeyboardButton(text=f'{cast_money(buy3.price)} '
                #                                      f'[{buy3.quantity}]', callback_data='b3')

                # действие в зависимости ранее была созданы кнопки c позицией или нет
                if pos_is_find:  # если позиция есть в портфеле отобразить кнопки с доходностью и с ценами из стакана
                    keyboard.add(b_pos_avg, b_pos_quntaty, b_pos_yeld)
                    keyboard.row(s1, b1) # кнопки продажи и покупки
                else:  # иначе отобразить просто кнопки с ценами из стакана
                    keyboard.add(s1, b1) # кнопки продажи и покупки
                # keyboard.row(b1, b2, b3)

                # Отображение кнопок индикаторов функционирования бота при доступности стакана с ценами
                if show_wrk:
                    test_b1 = types.InlineKeyboardButton(text='---------🔹----------', callback_data='tst_b')
                    test_b2 = types.InlineKeyboardButton(text='---------------------', callback_data='tst_b')
                    test_b3 = types.InlineKeyboardButton(text='---------🔹----------', callback_data='tst_b')
                    show_wrk = False
                else:
                    test_b1 = types.InlineKeyboardButton(text='---------------------', callback_data='tst_b')
                    test_b2 = types.InlineKeyboardButton(text='---------🔹----------', callback_data='tst_b')
                    test_b3 = types.InlineKeyboardButton(text='---------------------', callback_data='tst_b')
                    show_wrk = True
                # не выводим эти признаки работы, когда режим не редактировать
                if no_edit:
                    pass
                else:
                    keyboard.row(test_b1, test_b2, test_b3)

                #Редактирование сообщения с кнопками с несколькими цитиклами повторения
                count_edit_msg = 0
                limit_edit_msg = 5
                repit_edit_msg = True
                # ВЫВОД ИНФОРМАЦИИ в чат если есть стакан заявок (торги ведутся)
                while repit_edit_msg:
                    try:
                        #  label_time сообщение отправленное ранее в том числе и как затравка при первом запуске
                        if isinstance(label_time, telebot.types.Message):
                            last_cl = round(cast_money(lp[0].price), 3)
                            last_q = global_f_opt['MXI_last_quartal_cl']
                            last_m = global_f_opt['MXI_last_moth_cl']
                            last_w = global_f_opt['MXI_last_week_cl']
                            goal_1_q = global_f_opt['MXI_g1_quart_sell']
                            goal_1_m = global_f_opt['MXI_g1_moth_sell']
                            goal_1_w = global_f_opt['MXI_g1_week_sell']
                            q_delta = round((last_cl - last_q), 2)
                            m_delta = round((last_cl - last_m), 2)
                            w_delta = round((last_cl - last_w), 2)
                            q_delta_p = round((last_cl - last_q)/ last_cl*100, 2)
                            m_delta_p = round((last_cl - last_m)/ last_cl*100, 2)
                            w_delta_p = round((last_cl - last_w)/ last_cl*100, 2)
                            goal_1_q_delta = round((goal_1_q - last_cl), 2)
                            goal_1_m_delta = round((goal_1_m - last_cl), 2)
                            goal_1_w_delta = round((goal_1_w - last_cl), 2)
                            goal_1_q_delta_p = round((goal_1_q - last_cl)/ last_cl*100, 2)
                            goal_1_m_delta_p = round((goal_1_m - last_cl)/ last_cl*100, 2)
                            goal_1_w_delta_p = round((goal_1_w - last_cl)/ last_cl*100, 2)
                            msg = f'\n{t_i} {hmm_nw_time}  [p:{pause_sec - item - 1} сек.]'\
                                                        f'\n{last_cl} [послед.]'\
                                                        f'\n---goal---'\
                                                        f'\ng_Q:[{goal_1_q}]  [{goal_1_q_delta}]  {goal_1_q_delta_p}%'\
                                                        f'\ng_M:[{goal_1_m}]  [{goal_1_m_delta}]  {goal_1_m_delta_p}%'\
                                                        f'\ng_W:[{goal_1_w}]  [{goal_1_w_delta}]  {goal_1_w_delta_p} %'\
                                                        f'\n---back---'\
                                                        f'\nQ:[{last_q}]  [{q_delta}]  {q_delta_p} %'\
                                                        f'\nM:[{last_m}]  [{m_delta}]  {m_delta_p} %'\
                                                        f'\nW:[{last_w}]  [{w_delta}]  {w_delta_p} %'
                            msg = f'\n{t_i} {hmm_nw_time}  [p:{pause_sec - item - 1} сек.]'\
                                                        f'\n{last_cl} [послед.]'
                            try:
                                reg_msg()
                                if no_edit:
                                    t_bot.send_message(chat_id=ID_ch, text = msg, reply_markup = keyboard, disable_notification=True)
                                else:
                                    t_bot.edit_message_text(chat_id=ID_ch,
                                                    message_id=label_time.id,
                                                    text=msg, 
                                                    reply_markup=keyboard
                                                    )
                            except Exception as e:
                                telega_error (e)
                        repit_edit_msg = False
                        count_edit_msg = 0
                    except Exception as exx:
                        print('ОШИБКА t_bot.edit_message_text при изменении label_time')
                        print ('label_time.id:  ', label_time.id)
                        print(exx)
                        if count_edit_msg >= limit_edit_msg:
                            global_f_opt['In_process'] = False
                            global_f_opt['repeat_flag'] = False
                            try:
                                reg_msg()
                                t_bot.send_message(chat_id=ID_ch, text='#ОШИБКА_изм_сообщен!!! с кнопками:'
                                                                f'\n{exx}\n'
                                                                f'\nlabel_time.id: {label_time.id}'
                                                                f'\ncount_edit_msg: {count_edit_msg}', disable_notification=True)
                            except Exception as e:
                                telega_error (e)
                            repit_edit_msg = False
                            count_edit_msg = 0
                            show_repeat_btn(t_bot, ID_ch, 'Стоп_цикл_gr')
                        else:
                            try:
                                reg_msg()
                                t_bot.send_message(chat_id=ID_ch, text='#ОШИБКА_изм_сообщен!!! с кнопками:'
                                                                    f'\n{exx}\n'
                                                                    f'\nlabel_time.id: {label_time.id}'
                                                                    f'\ncount_edit_msg: {count_edit_msg}', disable_notification=True)
                            except Exception as e:
                                telega_error (e)
                            count_edit_msg += 1
             # ВЫВОД ИНФОРМАЦИИ в чат если нет стакана (т.е торги не ведуться)
            else:  
                # Если нет стакана отобразить информацию о позиции. 
                # Если позиции нет, то просто сообщение с временем
                if pos_is_find:
                    keyboard.add(b_pos_avg, b_pos_quntaty, b_pos_yeld)
                
                #Редактирование сообщения с кнопками с несколькими циклами повторения
                count_edit_msg = 0
                limit_edit_msg = 5
                repit_edit_msg = True
                while repit_edit_msg:
                    # редактирование label_graf (только дневной график)
                    try:
                        if isinstance(label_graf, telebot.types.Message):
                            # если затравка есть, то редактируем график если на нем были изменения
                            pass
                        else:
                            # если нет затравки, то  загружаем информацию о барах, строим график и выводим его в чат
                            #  label_graf = t_bot.send_photo(ID_ch, photo=open(start_f_name, 'rb'), caption='старт label_graf', disable_notification=True)
                            # загрузить бары и отобразить график
                            load_bar_inter = CandleInterval.CANDLE_INTERVAL_DAY
                            load_period = 25
                            load_to = datetime.now(timezone.utc).astimezone()
                            load_from = load_to - timedelta(days=load_period)
                            try:
                                bars = client.market_data.get_candles(
                                    figi=FIGI,
                                    from_=load_from,
                                    to=load_to,
                                    interval=load_bar_inter
                                )
                                canl_shop = bars.candles
                            except Exception as ebx:
                                # в случае возникновения исключения грузить просто пустой рисунок с черным фоном

                                global_f_opt['In_process'] = False
                                global_f_opt['repeat_flag'] = False

                                print('⚡️ОШИБКА загрузки баров⚡️. Цикл будет остановлен.', ebx)
                                try:
                                    reg_msg()
                                    t_bot.send_message(any,
                                                '⚡️ОШИБКА загрузки баров⚡️. Цикл будет остановлен. '
                                                f'\n{ebx}')
                                except Exception as e:
                                    telega_error (e)
                                show_repeat_btn(t_bot, any, 'Стоп_цикл_gr')
                            
                            if len(canl_shop) > 0:
                                # преобразуем данные в dataframe для построения графика
                                df333 = create_df_bars_set(canl_shop)
                                # строим и сохраняем график
                                f_tiker = FIGI
                                name_file_img = f'images/DAYimg{f_tiker}.png'
                                last_close = df333.iloc[-1]['Close']
                                try:
                                    s_time = time.time()
                                    hmm_ld_time = datetime.strftime(load_to, '%H:%M:%S.%f')
                                    title_g = ""  # Надпись на графике
                                    title_g += f"{f_tiker} [{load_bar_inter}]"
                                    title_g += f"\n{hmm_ld_time}   [{df333.shape[0]}bars]"
                                    title_g += f"\n{last_close} пт."
                                    mpf.plot(df333, style='mike', figsize=(7.2, 12.80),
                                            title=title_g, volume=True,tight_layout=False,
                                            savefig=name_file_img)
                                except Exception as e:
                                    print()
                                    print('ВОЗНИКЛА ОШИБКА DAY mpf.plot')
                                    print(datetime.now(timezone.utc).astimezone())
                                    print("Текст ошибки:")
                                    print(e)
                                    print()
                                    try:
                                        reg_msg()
                                        t_bot.send_message(any, text='ВОЗНИКЛА ОШИБКА DAY mpf.plot', disable_notification=True)
                                    except Exception as e:
                                        telega_error (e)
                                
                                # отправляем график в чат
                                print("Отправляем график в чат")
                                # сообщение в чат
                                hmm_ld_time = datetime.strftime(load_to, '%H:%M:%S')
                                msg_img = f"{f_tiker}" \
                                        f"\n{hmm_ld_time}" \
                                        f"\n{last_close} пт."
                                reg_msg()
                                label_graf = t_bot.send_photo(ID_ch, photo=open(name_file_img, 'rb'), caption=msg_img, disable_notification=True)
                                start_f_name = name_file_img
                                
                        
                        # редактирование label_time (сообщение с временем)
                        if isinstance(label_time, telebot.types.Message):
                            # Расчет целей
                            last_cl = round(cast_money(lp[0].price), 3)
                            last_q = global_f_opt['MXI_last_quartal_cl']
                            last_m = global_f_opt['MXI_last_moth_cl']
                            last_w = global_f_opt['MXI_last_week_cl']
                            goal_1_q = global_f_opt['MXI_g1_quart_sell']
                            goal_1_m = global_f_opt['MXI_g1_moth_sell']
                            goal_1_w = global_f_opt['MXI_g1_week_sell']
                            q_delta = round((last_cl - last_q), 2)
                            m_delta = round((last_cl - last_m), 2)
                            w_delta = round((last_cl - last_w), 2)
                            q_delta_p = round((last_cl - last_q)/ last_cl*100, 2)
                            m_delta_p = round((last_cl - last_m)/ last_cl*100, 2)
                            w_delta_p = round((last_cl - last_w)/ last_cl*100, 2)
                            goal_1_q_delta = round((goal_1_q - last_cl), 2)
                            goal_1_m_delta = round((goal_1_m - last_cl), 2)
                            goal_1_w_delta = round((goal_1_w - last_cl), 2)
                            goal_1_q_delta_p = round((goal_1_q - last_cl)/ last_cl*100, 2)
                            goal_1_m_delta_p = round((goal_1_m - last_cl)/ last_cl*100, 2)
                            goal_1_w_delta_p = round((goal_1_w - last_cl)/ last_cl*100, 2)
                            # msg =                                   f'\n---goal---'
                            #                             f'\ng_Q:[{goal_1_q}]  [{goal_1_q_delta}]  {goal_1_q_delta_p}%'
                            #                             f'\ng_M:[{goal_1_m}]  [{goal_1_m_delta}]  {goal_1_m_delta_p}%'
                            #                             f'\ng_W:[{goal_1_w}]  [{goal_1_w_delta}]  {goal_1_w_delta_p} %'
                            #                             f'\n---back---'
                            #                             f'\nQ:[{last_q}]  [{q_delta}]  {q_delta_p} %'
                            #                             f'\nM:[{last_m}]  [{m_delta}]  {m_delta_p} %'
                                                        # f'\nW:[{last_w}]  [{w_delta}]  {w_delta_p} %'
                            # формирование сообщения на метку
                            msg = f'\n{t_i} {hmm_nw_time}  [p:{pause_sec - item - 1} сек.]'
                            if not (trading_status_f == SecurityTradingStatus.SECURITY_TRADING_STATUS_NORMAL_TRADING):
                                msg += "\n--ТОРГИ НЕ ВЕДУТСЯ--"
                            msg += f'\n{last_cl} [послед.]'
                            # корретировка сообщения с меткой label_time с обработкой исключения
                            try:
                                reg_msg() 
                                if  no_edit:
                                    t_bot.send_message(chat_id=ID_ch, text=msg, reply_markup=keyboard, disable_notification=True)
                                else:                              
                                    t_bot.edit_message_text(chat_id=ID_ch,
                                                    message_id=label_time.id,
                                                    text=msg, 
                                                    reply_markup=keyboard
                                                    )
                            except Exception as e:
                                telega_error (e)
                        repit_edit_msg = False
                        count_edit_msg = 0
                    except Exception as exx:
                        print('error t_bot.edit_message_text')
                        print ('label_time.id:  ', label_time.id)
                        print(exx)
                        try:
                            reg_msg()
                            t_bot.send_message(chat_id=ID_ch, text='#ОШИБКА_изм_сообщен!!! с кнопками:'
                                                                f'\n{exx}\n'
                                                                f'\nlabel_time.id: {label_time.id}'
                                                                f'\ncount_edit_msg: {count_edit_msg}', disable_notification=True)
                        except Exception as e:
                            telega_error (e)
                        if count_edit_msg >= limit_edit_msg:
                            try:
                                reg_msg()
                                t_bot.send_message(chat_id=ID_ch, text=f'Кол-во ошибок: {count_edit_msg}, достигло лимита: {limit_edit_msg}'
                                                f'\nЦИКЛ будет помечен на прекращение', disable_notification=True)
                            except Exception as e:
                                telega_error (e)
                            global_f_opt['In_process'] = False
                            global_f_opt['repeat_flag'] = False                            
                            repit_edit_msg = False
                            count_edit_msg = 0
                            show_repeat_btn(t_bot, ID_ch, 'Стоп_цикл_gr')
                        else:
                            count_edit_msg += 1
            
            # вывод списка набранной позиции с указанием доходности для каждой   не зависимо торги ведуться или нет
            # только при включенной настройке  global_f_opt['show_oper_in_chat']
            if global_f_opt['show_oper_in_chat']:
                # если позиции есть, то показать доходность от каждой операции
                if pos_is_find:
                    # перенести сюда операции чтения, чтобы грузить когда есть позиция
                    list_oper = []
                    # расчет остальных параметров
                    list_oper = pos_work (step_price, last_price, pos_quntaty, s1_oper)
                    msg_oper =''
                    msg_oper += F'{last_price} пт. [послед.]\n' # label_oper
                    for oper in list_oper:
                        oper_price = "%.2f" % oper[2]
                        msg_oper += f'{oper[0]}   {oper_price}  {oper[4]}  {oper[6]} р.   {oper[7]} %\n'
                    msg_oper += F'{last_price} пт. [послед.]'  # label_oper
                    edit_and_show_label_oper(t_bot, ID_ch, label_oper, msg_oper, msg_oper_old)
                    msg_oper_old = msg_oper
                # если позиций нет в портефеле, то просто показать последнюю цену при включенной настройке 'show_oper_in_chat'
                else:
                    msg_oper = F'{last_price} пт. [послед.]\n' # label_oper
                    edit_and_show_label_oper(t_bot, ID_ch, label_oper, msg_oper, msg_oper_old)
                    msg_oper_old = msg_oper

            # Вывод графика в чат
            if len(candl_shop) > 0:
                if now_graf:  # строим график через раз
                    now_graf = False
                    # передаем новый график если цена изменилась
                    if back_show_price_gr != show_price:
                        df333 = create_df_bars_set(candl_shop)
                        # Заменяем на последней свече на нужное закрытие из стакана
                        if show_price != 0:
                            df333.iloc[-1, 3] = show_price
                            # изменяем максимум high_br когда цена из стакана выше
                            # полученного максимума или ниже полученного минимума
                            high_br = df333.iloc[-1, 1]
                            low_br = df333.iloc[-1, 2]
                            if show_price > high_br:
                                df333.iloc[-1, 1] = show_price
                            if show_price < low_br:
                                df333.iloc[-1, 2] = show_price
                        else:
                            show_price = cast_money(lp[0].price)
                        # строим и сохраняем на диск график
                        res, file_path_img = save_graf(df333, FIGI)
                        last_d_time = now_dtime()
                        hmm_ld_time = datetime.strftime(last_d_time, '%H:%M:%S')
                        # при удачном сохранении картинки с графиком отправляем в чат
                        if res:
                            try:
                                img = open(file_path_img, 'rb')
                                if isinstance(label_graf, telebot.types.Message):
                                    try:
                                        reg_msg()
                                        if no_edit:
                                            t_bot.send_photo(chat_id = ID_ch, photo = img, caption= f'{hmm_ld_time}'
                                                              f'  [{show_price}]', 
                                                              disable_notification=True)                                                                                   
                                        else:
                                            t_bot.edit_message_media(
                                            media=telebot.types.InputMedia(type='photo', media=img,
                                                                        caption=f'{hmm_ld_time}'
                                                                                f'  [{show_price}]'),
                                            chat_id=ID_ch, message_id=label_graf.message_id)
                                    except Exception as e:
                                        telega_error (e)
                                back_show_price_gr = show_price
                            except Exception as ebx:
                                global_f_opt['In_process'] = False
                                global_f_opt['repeat_flag'] = False
                                err_msg = f"#ОШИБКА: Бот не смог изменить картинку! label_graf"
                                err_msg += f"\n{ebx}\n"
                                err_msg += f"\nЦикл будет остановлен"
                                print(err_msg)
                                try:
                                    reg_msg()
                                    t_bot.send_message(ID_ch, err_msg, disable_notification=True)
                                except Exception as e:
                                    telega_error (e)
                                show_repeat_btn(t_bot, ID_ch, 'Стоп_цикл_gr')
                                return 0
                else:
                    now_graf = True
        except Exception as exx:
            global_f_opt['In_process'] = False
            global_f_opt['repeat_flag'] = False
            print('ОШИБКА в работе периодического цикла')
            print(exx)
            show_repeat_btn(t_bot, ID_ch, 'Стоп_цикл_gr')
            return 0
        # функция ежедневного отчета при переходе через сутки
        now_h_m = now_dtime()
        current_hour = now_h_m.hour  # Получение текущего часа
        current_min = now_h_m.minute  # Получение текущей минуты
        current_sec = now_h_m.second  # Получение текущей секунды
        # set_h_m = '00:05:00'
        set_h_m = '22:01:00'
        alarm_hour = int(set_h_m[0:2])
        alarm_min = int(set_h_m[3:5])
        alarm_sec = int(set_h_m[6:8])
        if alarm_hour == current_hour: 
            if alarm_min == current_min:
                if alarm_sec == current_sec:
                    print(now_h_m)
                    print (set_h_m)
        time.sleep(pause_post)
        cicrcle_time_end = time.time() # сколько секунд в конце цикла
        circle_time_delta = cicrcle_time_end - cicrcle_time_start
        # борьба с телегой
        if circle_time_delta > 2:
            err_msg = f'Время цикла: {round(circle_time_delta, 3)} сек.'
            err_out(err_msg)
            g_long_count += 1

    try:
        # удаление сообщений после завершения цикла
        if no_edit:
            pass
        else:
            reg_msg()
            t_bot.delete_message(chat_id=ID_ch, message_id=label_time.id)
            if not (start_f_name == '') and isinstance(label_graf, telebot.types.Message):
                reg_msg()
                t_bot.delete_message(chat_id=ID_ch, message_id=label_graf.id)
            if global_f_opt['show_oper_in_chat']:
                reg_msg()
                t_bot.delete_message(chat_id=ID_ch, message_id=label_oper.id)
    except Exception as exx:
        global_f_opt['In_process'] = False
        global_f_opt['repeat_flag'] = False
        print('error bot.delete_message')
        print(exx)
        telega_error (exx)
        try:               
            reg_msg()
            t_bot.send_message(ID_ch, f'Бот не смог удалить сообщение!'
                                    f'\n{exx}'
                                    f'\nЦикл будет остановлен', disable_notification=True)
        except Exception as e:
            telega_error (e)
        show_repeat_btn(t_bot, ID_ch, 'Стоп_цикл_gr')
        return 0

# Действия над портфелем после отработки нажатия кнопок управления позицией
def operation_go(t_bot: telebot.TeleBot, ID_ch, ID_usr, FIGI: str, oper_direct: OrderDirection, oper_price: Quotation, quan: int):
    global global_set_from_orders, g_df, g_df_p
    price_oper = q_to_var(oper_price)
    commis_t1 = 0.004
    # идентифицировать пользователя
    if int(ID_usr) == int(global_set_from_orders['user_id']):
        # проверить что совершение операция по кнопкам разрешено
        if global_set_from_orders['oper_block_bt']:
            # оформить отдельной функцией
            print(f'Операции с кнопками заблокированы!!!')
            try:
                reg_msg()
                t_bot.send_message(ID_ch, f'Операции с кнопками заблокированы!!!',disable_notification=True)
            except Exception as e:
                telega_error (e)
            msg_1 = '0'
            quan_v = quan
            if oper_direct == OrderDirection.ORDER_DIRECTION_BUY:
                msg_1 = 'покупка'
                quan_v = quan
            elif oper_direct == OrderDirection.ORDER_DIRECTION_SELL:
                msg_1 = 'продажа'
                quan_v = quan*(-1)
            try:
                reg_msg()
                t_bot.send_message(ID_ch, f'#Виртуальная_сделка {msg_1}: {price_oper}',disable_notification=True)
            except Exception as e:
                telega_error (e)
            #new_row = {'figi': f'{FIGI}', 'direction': f'{oper_direct}', 'price': f'{price_oper}', 'quantity': f'{quan}', 'time': str(datetime.utcnow().timestamp())}
            new_row = pd.Series({'figi': f'{FIGI}', 
                                'direction': f'{msg_1}', 
                                'price': f'{price_oper}', 
                                'quantity': f'{quan_v}',
                                'time': datetime.utcnow().timestamp(),
                                'comis': f'{round(price_oper*commis_t1, 2)}'
                                })
            # time.strftime('%d %b %Y %H:%M:%S',time.gmtime(1681998434.943453))
            g_df = pd.concat([g_df, new_row.to_frame().T])
            g_df.to_csv('df_oper.csv', index = False)

            # ИЗМЕНЕНИЕ ВИРТУАЛЬНОГО ПОРТФЕЛЯ
            # 1.Найти имеется ли в протфеле такое ФИГИ
            # 2.Загрузить количество 
            # 3.Загрузить среднюю цену
            # 4.Расчитать цену за 1 шт. в портфеле
            # 5.Прирастить или убавить количество
            # 6.Пересчитать среднюю цену
            # 7.Сохранить на диск

            # df[df[‘column_name’] == value_you_are_looking_for]
            
            # Если виртуальный портфель пустой добавляем первую позицию и все
            if g_df_p.empty:
                    g_df_p.loc[len(g_df_p.index)] = [FIGI, price_oper, quan]
                    g_df_p.to_csv('df_portf.csv', index = False)
                    return 0
            

            # Если портфель не пустой ищем нужный FIGI
            df_new = pd.DataFrame()
            if FIGI in g_df_p.values:
                print ('yes')
                df_new = g_df_p[g_df_p['figi'] == FIGI]
                # операция покупки, т.е. добавление к уже существующей позиции
                if oper_direct == OrderDirection.ORDER_DIRECTION_BUY:
                    msg_1 = 'покупка'
                    p_quan = df_new['quantity'].iloc[0]
                    p_price = df_new['avg_price'].iloc[0]
                    p_avg_price_n = (p_price*p_quan + price_oper)/p_quan+quan
                    p_quan_n = p_quan+quan
                    # вносим измененные данные в df
                    g_df_p.loc[g_df_p["figi"] == FIGI, "quantity"] = p_quan_n
                    g_df_p.loc[g_df_p["figi"] == FIGI, "avg_price"] = p_avg_price_n
                    g_df_p.to_csv('df_portf.csv', index = False)
                    return 0
               
                # операция продажи
                elif oper_direct == OrderDirection.ORDER_DIRECTION_SELL:
                    msg_1 = 'продажа'
                    p_quan = df_new['quantity'].iloc[0]
                    p_price = df_new['avg_price'].iloc[0]
                    p_avg_price_n = (p_price*p_quan - price_oper)/p_quan-quan
                    p_quan_n = p_quan-quan
                    # вносим измененные данные в df
                    g_df_p.loc[g_df_p["figi"] == FIGI, "quantity"] = p_quan_n
                    g_df_p.loc[g_df_p["figi"] == FIGI, "avg_price"] = p_avg_price_n
                    g_df_p.to_csv('df_portf.csv', index = False)
                    return 0
                    
            else:
                print ('not')
            return 0
        # имеется ли позиция в портфеле?
        # позиция шорт или лог
        # проверить, требуется ли подтвердить выполнение операции?
        if global_set_from_orders['oper_confirm']:
            print(f"Подтверждаете что нужно сделать операцию?")
        else:
            print(f'Сделка без подтверждения')
        # выполнить соответствующую операцию
        # если нажата кнопка с ценой продажи значит продать по указанной цене
        # если нажата кнопка с ценой покупки значит купить по указанной цене
        with Client(TOKEN) as g_client:
            res = g_client.orders.post_order(
                order_id=str(datetime.utcnow().timestamp()),
                figi=FIGI,
                quantity=quan,
                price=oper_price,
                account_id=global_set_from_orders['oper_ac_ID'],
                direction=oper_direct,
                order_type=OrderType.ORDER_TYPE_LIMIT
            )
            msg = ''
            if oper_direct == OrderDirection.ORDER_DIRECTION_SELL:
                msg += f'ПРОДАЖА!!!! #СДЕЛКА #ПРОДАЖА'
            else:
                msg += f'ПОКУПКА!!!! #СДЕЛКА #ПОКУПКА'
            msg += f'\nЦена: {q_to_var(res.initial_order_price_pt)} пт.' \
                   f'\nзаявка на: {res.figi}  ' \
                   f'\nзапрошено:  {res.lots_requested} лотов' \
                   f'\nстоимость 1-го лота:  {cast_money(res.initial_security_price)} руб.' \
                   f'\nстоимость всего:  {cast_money(res.initial_order_price)} руб.' \
                   f'\nкомиссия:  {cast_money(res.initial_commission)} руб.' \
                   f'\norder_id:  {res.order_id}'
            print(msg)
            time.sleep(1)
            print(res)
            try:
                reg_msg()
                t_bot.send_message(ID_ch, msg)
            except Exception as e:
                telega_error (e)
    else:
        print(f'Нет доступа для пользователя {ID_usr}')
        try:
            reg_msg()
            t_bot.send_message(ID_ch, f'Нет доступа для пользователя {ID_usr}')
        except Exception as e:
            telega_error (e)
        return 0


def save_graf(df333: pd.DataFrame, ticker: str):
    global global_f_opt, g_df_p
    name_file_img = f'images/img{ticker}.png'
    last_close = df333.iloc[-1]['Close']
    last_d_time = now_dtime()
    hmm_ld_time = datetime.strftime(last_d_time, '%H:%M:%S')
    full_name_load = global_f_opt['full_future_name']
    load_inter = what_interval()
    if len (df333)>2:
        close1 = df333.iloc[-1]['Close']
        close2 = df333.iloc[-2]['Close']
        delta_cl = close1 - close2
        if close2 != 0:
            delta_prcnt = round((close1 - close2)/close2*100, 2)
        else:
            delta_prcnt = 0
    else:
        delta_cl = 0
        delta_prcnt = 0
    try:
        title_g = ""  # Надпись на графике
        title_g += f"{full_name_load} [{load_inter}]  {ticker}"
        title_g += f"\n{hmm_ld_time}   [{df333.shape[0]} bars]"
        title_g += f"\n{last_close} пт.   {round(delta_cl,2)} пт.  {delta_prcnt}%"
        mpf.plot(df333, style='mike', figsize=(7.2, 12.80),
                 title=title_g, volume=True, tight_layout=False,
                 savefig=name_file_img)
        return True, name_file_img
    except Exception as e:
        print()
        print('ВОЗНИКЛА ОШИБКА mpf.plot')
        print(datetime.now(timezone.utc).astimezone())
        print("Текст ошибки:")
        print(e)
        print()
        return False, name_file_img


def create_df_bars_set(candl_shop):
    df = pd.DataFrame([{
        'Date': c.time + timedelta(hours=3),
        'Open': cast_money(c.open),
        'High': cast_money(c.high),
        'Low': cast_money(c.low),
        'Close': cast_money(c.close),
        'Volume': c.volume
    } for c in candl_shop])
    df = df.set_index(['Date'])
    return df


#Создание DataFrame по загруженному списку акций из gRPC_Tinkoff_API
def create_df_stoks_list(stoks: Share):
    df = pd.DataFrame([{
        'figi': p.figi,  # Figi-идентификатор инструмента
        'ticker': p.ticker,  # Тикер инструмента
        'name': p.name,  # Название инструмента
        'class_code': p.class_code,  # Класс-код (секция торгов)
        'isin': p.isin,  # Isin-идентификатор инструмента.
        'lot': p.lot,  # Лотность инструмента
        'currency': p.currency,  # Валюта расчётов
        'issue_size': p.issue_size,  # Размер выпуска
        'sector': p.sector,  # Сектор экономики
        'min_price_increment': q_to_var(p.min_price_increment),  # Шаг цены
        'otc_flag': p.otc_flag,  # Признак внебиржевой ценной бумаги
        'for_qual_investor_flag': p.for_qual_investor_flag,  # только для квалифицированных
        #
        # Подробнее: https://www.tinkoff.ru/invest/help/brokerage/account/margin/about/#q5
        'klong': get_data_q(p.klong),  # Коэффициент ставки риска длинной позиции по инструменту.
        'dlong': get_data_q(p.dlong),  # Ставка риска минимальной маржи в лонг. 
        'dlong_min': get_data_q(p.dlong_min),  # Ставка риска начальной маржи в лонг. Подробнее: ставка риска в лонг
        #
        'kshort': get_data_q(p.kshort),  # Коэффициент ставки риска короткой позиции по инструменту.
        'dshort': get_data_q(p.dshort),  # Ставка риска минимальной маржи в шорт.
        'dshort_min': get_data_q(p.dshort_min),  # Ставка риска начальной маржи в шорт.
        'short_enabled_flag': p.short_enabled_flag,  # Признак доступности для операций в шорт
        'exchange': p.exchange,  # Торговая площадка
        'ipo_date': p.ipo_date,  # Дата IPO акции в часовом поясе UTC
        'country_of_risk': p.country_of_risk,  # Код страны, в которой компания ведёт основной бизнес.
        'country_of_risk_name': p.country_of_risk_name,  #  Наименование страны, в которой компания ведёт основной бизнес
        'issue_size_plan': p.issue_size_plan, # Плановый размер выпуска
        'nominal': q_to_var(p.nominal),  #  Номинал MoneyValue
        'trading_status': p.trading_status,  # Текущий режим торгов инструмента SecurityTradingStatus
        'buy_available_flag': p.buy_available_flag,  # Признак доступности для покупки
        'sell_available_flag': p.sell_available_flag,  # Признак доступности для продажи
        'div_yield_flag': p.div_yield_flag,  # Признак наличия дивидендной доходности
        'share_type': p.share_type,  # Тип акции. Возможные значения: ShareType
        'api_trade_available_flag': p.api_trade_available_flag,  # возможность торговать инструментом через API
        'uid': p.uid,  # Уникальный идентификатор инструмента
        'real_exchange': p.real_exchange,  # Реальная площадка исполнения расчётов
        'position_uid': p.position_uid,  # Уникальный идентификатор позиции инструмента
        'for_iis_flag': p.for_iis_flag,  # Признак доступности для ИИС
        'first_1min_candle_date': p.first_1min_candle_date,  # Дата первой минутной свечи
        'first_1day_candle_date': p.first_1day_candle_date # Дата первой дневной свечи.        
    } for p in stoks])
    return df

#Создание DataFrame по загруженному списку фьючерсов
def create_df_future_list(futures: Future):
    df = pd.DataFrame([{
        'figi': p.figi,
        'ticker': p.ticker,
        'name': p.name,
        'asset_type': p.asset_type,
        'last_trade_date': p.last_trade_date.astimezone(),
        'class_code': p.class_code,
        'lot': p.lot,
        'currency': p.currency,
        'klong': get_data_q(p.klong),
        'kshort': get_data_q(p.kshort),
        'dlong': get_data_q(p.dlong),
        'dshort': get_data_q(p.dshort),
        'dlong_min': get_data_q(p.dlong_min),
        'dshort_min': get_data_q(p.dshort_min),
        'short_enabled_flag': p.short_enabled_flag,
        'exchange': p.exchange,
        "futures_type": p.futures_type,
        'basic_asset': p.basic_asset,
        'basic_asset_size': get_data_q(p.basic_asset_size),
        'country_of_risk': p.country_of_risk,
        'country_of_risk_name': p.country_of_risk_name,
        'sector': p.sector,
        'trading_status': p.trading_status,
        'otc_flag': p.otc_flag,
        'buy_available_flag': p.buy_available_flag,
        'sell_available_flag': p.sell_available_flag,
        'min_price_increment': get_data_q(p.min_price_increment),
        'api_trade_available_flag': p.api_trade_available_flag,
        'uid': p.uid,
        'real_exchange': p.real_exchange,
        'position_uid': p.position_uid,
        'basic_asset_position_uid': p.basic_asset_position_uid,
        'first_trade_date': p.first_trade_date.astimezone(),

        'expiration_date': p.expiration_date.astimezone()
    } for p in futures])
    return df

# преобразование позиций из портфеля в DataFrame
def cr_df_pos(positions: PortfolioPosition):
    """
    преобразование позиций из портфеля в DataFrame
    """
    df = pd.DataFrame([{
        'figi': p.figi,
        'type': p.instrument_type,
        'quantity': cast_money(p.quantity),
        'avg_pos_price': cast_money(p.average_position_price),
        'cur': 'rub',
        'yield': cast_money(p.expected_yield),
        'avg_pos_price_ft': cast_money(p.average_position_price_pt),
        'current_price': cast_money(p.current_price),
        'avg_pos_price_fifo': cast_money(p.average_position_price_fifo),
        'quantity_lots': cast_money(p.quantity_lots)
    } for p in positions])
    return df

def create_df(candles: HistoricCandle):
    df = pd.DataFrame([{
        'time': c.time,
        'volume': c.volume,
        'open': cast_money(c.open),
        'close': cast_money(c.close),
        'high': cast_money(c.high),
        'low': cast_money(c.low),
    } for c in candles])

    return df

def cast_money(v):
    """    
    # Перевод объектов MoneyValue и Quotation в численную форму
    https://tinkoff.github.io/investAPI/faq_custom_types/
    """
    return v.units + v.nano / 1e9  # nano - 9 нулей

def var_to_q(v) -> Quotation:
    begin_point = v // 1  # получаем что до запятой
    pos_point = v % 1  # получаем то что после запятой
    return Quotation(units=int(begin_point), nano=int(pos_point * 10e8))

def q_to_var(v):
    return v.units + v.nano / 1e9  # nano - 9 нулей

def get_data_q(v):
    return v.units + v.nano / 1e9  # nano - 9 нулей

def gRPC_Load_List():
    '''
    # функция загрузки списка акций через gRPC
    '''
    print('Работает функция загрузки списка акций через gRPC')
    print('\nПодключаемся к gRPC Tikoff')
    with Client(TOKEN) as client2:
        print('Подключение: Выполнено')
        # акции
        flag_r = True
        while flag_r:
            try:
                shares = client2.instruments.shares(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)
                flag_r = False
            except Exception as e:
                print(datetime.now(timezone.utc).astimezone())
                print('\nВОЗНИКЛА ОШИБКА')
                print('shares=client2.instruments.shares(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)')
                print(e)
                print()
                flag_r = True

        print('Акции загружены через gRPC Tikoff')
        sh = shares.instruments
        print('Количество акций gRPC Tikoff в базовом варианте:', len(sh))
        return sh

# функция выдачи операций с активом при наличии его в портфеле. 
# Количество операций равно количеству актива в портфеле 
def pos_work (step_price, last_price, pos_quntaty, s1_oper: list):
    # возможно ввести переменную определяещую количество одновременно отображаемых позиций в списке
    """
    ПОЛУЧАЕМ параметры:
    \n  step_price стоимости шага цены
    \n  last_price последняя цена
    \n  pos_quntaty количество актива
    \n  s1_oper список объектов в виде операций
    \nВЫДЕМ обработанный список для отображения
    """
    # : List["OperationItem"]
    # стоимости шага цены step_price (ренее при расчете позиции вычисляется)
    # step_price = q_to_var(f_inf.min_price_increment_amount) / q_to_var(f_inf.min_price_increment)

    # количество актива pos_quntaty
    if pos_quntaty > 0:  # позиция лонг
        # задается что операции покупки смотреть
        sel_oper_type = OperationType.OPERATION_TYPE_BUY
    else:  # позиция шорт
        # операции продажи смотреть
        sel_oper_type = OperationType.OPERATION_TYPE_SELL

    list_oper = []
    oper = OperationItem()
    # oper.type
    oper_count = 0
    
    for oper in s1_oper:
        l_list = []
        # как дозагружать если не все позиции удалось обработать, выделить в функцию
        if oper.type == sel_oper_type:
            #дата
            l_list.append(str(datetime.strftime((oper.date + timedelta(hours=3)), '%d.%m %H:%M') ))
            # тип операции
            l_list.append (oper.type)
            oper_price = cast_money (oper.price)
            l_list.append (oper_price)
            l_list.append (last_price)
            l_list.append(oper.quantity_done)
            oper_rez = round(last_price-oper_price,2)
            oper_rez_val = round (oper_rez * step_price, 2)
            oper_rez_prc = round ((oper_rez/ oper_price)*100, 2)
            l_list.append(oper_rez)
            l_list.append(oper_rez_val)
            l_list.append(oper_rez_prc)
            
            list_oper.append(l_list)
            oper_count += oper.quantity_done
            # print (oper_count, l_list)
            # при достижении придела перкращаем цикл
            i_list = list_oper
            if oper_count == pos_quntaty:
                i_list = list(reversed(list_oper))
                # print ('\npos_quntaty:', pos_quntaty)
                # for i in i_list:
                #     print (i)
                # print()
                
                # все позиции загружены поэтому можно выходить из цикла
                break
    # возвращаем результат работы функции
    return i_list

# Поиск отклонения фьючерсов
def show_delta_futures(t_bot: telebot.TeleBot, ID_ch):
    start_count_sec = time.time()  # счетчик секунд для определения общего времени загрузки
    print('Запущена функция: Поиск отклонения фьючерсов')
    with Client(TOKEN) as client:
        # ФЬюЧЕРСЫ
        futures_instr = []
        flag_r = True
        # Бесконечное количество попыток загрузить список пока не достигнем успеха
        while flag_r:
            try:
                futures = client.instruments.futures(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)
                futures_instr = futures.instruments
                flag_r = False
                print(f'Загружен список из: {len(futures_instr)} фьючерсов, для обработки и сортировки')
            except Exception as ebx:
                print(datetime.now(timezone.utc).astimezone())
                print('\nВОЗНИКЛА ОШИБКА')
                print(
                    'futures=client.instruments.'
                    'futures(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)')
                print(ebx)
                print()
                flag_r = True
        # отбор в список  фьючерсов на акции
        future_list = []
        future_filter_instr = []
        future_actual = global_f_opt['activ_contr_name']
        
        for i in futures_instr:
            if i.asset_type == 'TYPE_SECURITY':
                future_list.append(f'{i.figi} \t {i.ticker} \t {i.name} \t {i.basic_asset} \t {i.figi}')
                future_filter_instr.append(i)
        future_list.sort()
        
  
        df_futur_assets = pd.DataFrame(future_filter_instr)
        df_assets_tikers = pd.DataFrame()
        df_assets_tikers = df_futur_assets[['basic_asset']]
        df_assets_tikers = df_assets_tikers.drop_duplicates ()
        df_futur_assets = df_futur_assets.sort_values(by='last_trade_date')
        print(f'Всего фьючерсов на акции: {len(future_filter_instr)}')
        print(f'Всего тикеров на акции: {len(df_assets_tikers)}')
        try:
            t_bot.send_message(ID_ch,
                            f'Фьючерсов всего: {len(futures_instr)} шт.'
                            f'\nФьючерсов на акции: {len(future_filter_instr)} шт.'
                            f'\nТикеров акций имеющих фьючерсы: {len(df_assets_tikers)} шт.',
                            disable_notification=True)
        except Exception as e:
            telega_error (e)            
        if len(df_assets_tikers) >0:
            INSTRUMENT_ID_TYPE_TICKER = 2
            # https://euvgub.github.io/quik_user_manual/ch8_12_1.html КЛАСС коды
            # instr = Share
            instr_dict = []
            # список последних цен
            lp_FIGi=[] 
            for index, row in df_assets_tikers.iterrows():
                ticker_n = row['basic_asset']
                print (index, ticker_n)
                if not (ticker_n == 'ISKJ' ):
                    instr = client.instruments.share_by(id_type = 2,class_code='TQBR',id=ticker_n)
                    instr_dict.append(instr)
                    lp_FIGi.append(instr.instrument.figi)
                    print (index, ticker_n, instr.instrument.figi)
            # собираем последние цены на акции
            lps = client.market_data.get_last_prices(figi=lp_FIGi).last_prices  # последние цены для списка ФИГИ на акции
            # последние цены на фьчерсы
            lpsf = client.market_data.get_last_prices(figi=df_futur_assets['figi'].tolist()).last_prices # последние цены на фючерсы
            # имя футурса
            dict_tiker_f = df_futur_assets['ticker'].tolist()
            # имя футурса
            dict_name_f = df_futur_assets['name'].tolist()
            # кратность фьючерса по отношению к базе
            dict_tiker_ba_s = df_futur_assets['basic_asset_size'].tolist()
            # тикер базового актива
            dict_tiker_ba_ticker = df_futur_assets['basic_asset'].tolist()
            # id базового актива
            dict_tiker_ba_uid = df_futur_assets['basic_asset_position_uid'].tolist()
            # перебор акций
            last_pr_dict = []
            for p in range(len(lps)):
                lp = lps[p]
                ins_i = instr_dict[p]
                # ins_i = ShareResponse
                last_pr_dict.append({'bs_ass_figi': lp.figi,
                                    'bs_ass_l_price': q_to_var(lp.price),
                                    'bs_ass_ticker': ins_i.instrument.ticker,
                                    'bs_ass_name': ins_i.instrument.name,
                                    'bs_ass_instr_ID': lp.instrument_uid,
                                    'bs_ass_position_uid': ins_i.instrument.position_uid
                                    })
            # перебор фьючерсов
            last_pr_dict_f = []
            for p in range(len(lpsf)):
                lp = lpsf[p]
                pos_uid = dict_tiker_ba_uid[p]
                f_tick = dict_tiker_f[p]
                f_name = dict_name_f[p]
                f_ba_s = dict_tiker_ba_s[p]                       
                last_pr_dict_f.append({'futur_figi': lp.figi, 
                                        'futur_l_price': q_to_var(lp.price),
                                        'futur_tick': f_tick,
                                        'futur_name': f_name,
                                        'futur_ba_s': f_ba_s["units"] + f_ba_s["nano"] / 1e9, # КРАТНОСТЬ БАЗЫ  v.units + v.nano / 1e9
                                        'futur_instr_ID': lp.instrument_uid,
                                        'bs_ass_position_uid':pos_uid
                                        })
            df_last_pr_f = pd.DataFrame(last_pr_dict_f)
            df_last_pr_shr = pd.DataFrame(last_pr_dict)
            # объединение датафреймов с последними ценами
            df_append = pd.merge(df_last_pr_f, df_last_pr_shr, on="bs_ass_position_uid")
            df_append['kx'] = round ((df_append['futur_l_price'] - (df_append['bs_ass_l_price']*df_append['futur_ba_s']))/(df_append['bs_ass_l_price']*df_append['futur_ba_s'])*100, 2)
            df_append['delta_kx'] = round ((df_append['futur_l_price'] - (df_append['bs_ass_l_price']*df_append['futur_ba_s'])), 2)
            df_sort_kx = df_append.sort_values(by = 'kx', ascending=False)
            m22 = df_append[df_append.futur_name.str.startswith('GAZR')]
            print(df_append)
            print ('\n\n\n\nПервые 10 записей:')
            print (df_sort_kx.head(10))
            print ('\n\n\n\nПоследние 10 записей')
            print (df_sort_kx.tail(10))
            print(m22)
            
            # Подготовка к выводу сообщения о результатах разницы между акциями и фьючерсами
            msg = ''
            msg = f'СПИСОК отклонений ВСЕХ  {len(future_filter_instr)}  фьючерсов на акции:\n\n'
            for p in last_pr_dict:
                # имя и прочие параметры акции
                b_name = p['bs_ass_name']
                b_ticker = p['bs_ass_ticker']
                b_l_price = p['bs_ass_l_price']
                msg += f'{b_name}\n {b_ticker}   {b_l_price} руб.\n'
                msg += '--------------------------\n'
                # датафрейм со всеми фьючерсами для  этой акции
                s_df = df_append[df_append.bs_ass_ticker.str.startswith(b_ticker)]
                # цикл по строкам dataframe
                l_df = len(s_df) # количество записей в DF
                for indx in range(l_df):
                    f_tick = s_df['futur_tick'].iloc[indx]
                    f_name = s_df['futur_name'].iloc[indx]
                    f_l_price = s_df['futur_l_price'].iloc[indx]
                    f_kx = s_df['kx'].iloc[indx]
                    delta_kx = s_df['delta_kx'].iloc[indx]
                    msg += f'{f_name}\n  {f_l_price} пт.  {f_kx} %   D:{delta_kx}\n'
                msg += '\n'

            # определяем первые 10 фьючерсов с самым большим положительным отклонением
            msg2 = ''
            msg2 = "Первые 10 фьючерсов с самым большим ПОЛОЖИТЕЛЬНЫМ отклонением."
            msg2 += "\nФьючерсы ДОРОЖЕ акций,"
            msg2 += "\nт.е. сейчас АКЦИИ ДЕШЕВЛЕ прогнозируемых цен на фьючерсы."
            msg2 += "\nВозможен рост цен акций в будущем:\n\n"
            l_df = 10 # количество для отображения
            for indx in range(l_df):
                f_tick = df_sort_kx['futur_tick'].iloc[indx]
                f_name = df_sort_kx['futur_name'].iloc[indx]
                f_l_price = df_sort_kx['futur_l_price'].iloc[indx]
                f_kx = df_sort_kx['kx'].iloc[indx]
                delta_kx = df_sort_kx['delta_kx'].iloc[indx]
                msg2 += f'{f_name}\n  {f_l_price} пт.  {f_kx} %   D:{delta_kx}\n'
                msg2 += '--------------------------\n'
            
            # Готовим последние 10 фьючерсов с самым большим отрицательным отклонением
            msg2 += "\n\nПоследние 10 фьючерсов с самым большим ОТРИЦАТЕЛЬНЫМ отклонением."
            msg2 += "\nФьючерсы ДЕШЕВЛЕ акций,"
            msg2 += "\nт.е. сейчас АКЦИИ ДОРОЖЕ прогнозируемых цен на фьючерсы."
            msg2 += "\nВозможно снижение цен акций в будущем:\n\n"
            # размер датафрейма
            l_df = len(df_sort_kx)
            end_l_df = 10 # количество для отображения
            indx = l_df-1 # индекс для перебора
            counter_in = 0 # счетчик
            while counter_in < end_l_df:
                f_tick = df_sort_kx['futur_tick'].iloc[indx]
                f_name = df_sort_kx['futur_name'].iloc[indx]
                f_l_price = df_sort_kx['futur_l_price'].iloc[indx]
                f_kx = df_sort_kx['kx'].iloc[indx]
                delta_kx = df_sort_kx['delta_kx'].iloc[indx]
                indx -= 1
                if f_l_price !=0:
                    msg2 += f'{f_name}\n  {f_l_price} пт.  {f_kx} %   D:{delta_kx}\n'
                    msg2 += '--------------------------\n'
                    counter_in += 1
            # ВЫВОДИМ первые 10 фьючерсов с самым большим положительным и отрицательным отклонением
            print(msg2)        
            for message1 in util.smart_split(msg2, 4000): # выдача сообщений о результатах обработки не более 4000 символов за раз
                try:
                    t_bot.send_message(ID_ch, message1, disable_web_page_preview=True, disable_notification=True)
                except Exception as e:
                    telega_error (e)
            # Выводим все отклонение подробно
            for message1 in util.smart_split(msg, 4000):  # выдача сообщений о результатах обработки не более 4000 символов за раз    
                try:
                    t_bot.send_message(ID_ch, message1, disable_web_page_preview=True, disable_notification=True)
                except Exception as e:
                    telega_error (e)

def what_interval ():
    '''Возвращает какой сейчас глобальный интевал отображения циклического графика, удобный для чтения человеком
    '''
    if global_f_opt['candl_interval'] == CandleInterval.CANDLE_INTERVAL_DAY:
        load_inter = 'DAY'
    elif global_f_opt['candl_interval'] == CandleInterval.CANDLE_INTERVAL_HOUR:
        load_inter = 'HOUR'
    elif global_f_opt['candl_interval'] == CandleInterval.CANDLE_INTERVAL_15_MIN:
        load_inter = '15_MIN'
    elif global_f_opt['candl_interval'] == CandleInterval.CANDLE_INTERVAL_5_MIN:
        load_inter = '5_MIN'
    elif global_f_opt['candl_interval'] == CandleInterval.CANDLE_INTERVAL_1_MIN:
        load_inter = '1_MIN'
    else:
        load_inter = 'UNSPECIFIED' # не задан
    return load_inter

# Расчет даты начала загрузки баров
def load_from_graf (load_period):
    '''Определяем дату начала загрузки,\n 
    дата вычисляется от текущего времени на глубину load_period\n
    load_inter наименование интервала для человека (в виде текста)\n
    load_bar_inter интервал для машины (в виде числа)
    '''
    if global_f_opt['candl_interval'] == CandleInterval.CANDLE_INTERVAL_DAY:
        load_inter = 'DAY'
        load_from = datetime.now(timezone.utc).astimezone() - timedelta(days=load_period)
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_DAY
    elif global_f_opt['candl_interval'] == CandleInterval.CANDLE_INTERVAL_HOUR:
        load_inter = 'HOUR'
        load_from = datetime.now(timezone.utc).astimezone() - timedelta(hours=load_period)
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_HOUR

    elif global_f_opt['candl_interval'] == CandleInterval.CANDLE_INTERVAL_15_MIN:
        load_inter = '15_MIN'
        load_from = datetime.now(timezone.utc).astimezone() - timedelta(minutes=load_period * 15)
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_15_MIN

    elif global_f_opt['candl_interval'] == CandleInterval.CANDLE_INTERVAL_5_MIN:
        load_inter = '5_MIN'
        load_from = datetime.now(timezone.utc).astimezone() - timedelta(minutes=load_period * 5)
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_5_MIN
    elif global_f_opt['candl_interval'] == CandleInterval.CANDLE_INTERVAL_1_MIN:
        load_inter = '1_MIN'
        load_from = datetime.now(timezone.utc).astimezone() - timedelta(minutes=load_period)
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_1_MIN
    else:
        load_inter = 'DAY'
        load_from = datetime.now(timezone.utc).astimezone() - timedelta(days=load_period)
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_DAY
    return load_from, load_inter, load_bar_inter

def edit_and_show_label_oper(t_bot: telebot.TeleBot, ID_ch, label_oper, msg_oper, msg_oper_old):
    """Редактирование вывод сообщения с ярлыком label_oper в циклическом отображении графика"""
    try:
        if isinstance(label_oper, telebot.types.Message):
            if not (msg_oper_old == msg_oper):
                try:
                    reg_msg()
                    t_bot.edit_message_text(chat_id=ID_ch,
                                    message_id=label_oper.id,
                                    text= msg_oper
                                    )
                except Exception as e:
                    telega_error (e)
                msg_oper_old = msg_oper

    except Exception as exx:
        global_f_opt['In_process'] = False
        global_f_opt['repeat_flag'] = False
        print('ОШИБКА t_bot.edit_message_text при изменении label_oper ')
        print(exx)
        try:
            reg_msg()
            t_bot.send_message(chat_id=ID_ch, text='#ОШИБКА изменения label_oper'
                                                f'\n{exx}'
                                                f'\nlabel_oper.id: {label_oper.id}'
                                                f'\nЦикл будет остановлен', disable_notification=True)
        except Exception as e:
            telega_error (e)
        show_repeat_btn(t_bot, ID_ch, 'Стоп_цикл_gr')

def what_bar_close (cl1, cl2, name_inter):
    msg = ''
    close_delta = round ((cl2 - cl1), 2)
    close_delta_pr = round (((cl2 - cl1)/cl1*100), 2)
    if cl2 > cl1:
        msg += f'За прошедший {name_inter} образовался бар покупок:'
        msg += f'\n\nновое закрытие {cl2} пт.  \nвыше предыдущего {cl1} пт.  \nна {close_delta} пт.  или {close_delta_pr} %;'
    elif cl2 < cl1:
        msg += f'За прошедший {name_inter} образовался бар продаж:'
        msg += f'\n\nновое закрытие {cl2} пт.  \nниже предыдущего {cl1} пт.  \nна {close_delta} пт.  или {close_delta_pr} %;'
    elif cl2 == cl1:
        msg += f'За прошедший {name_inter} закрытие равно предыдущему:'
        msg += f'\n\nновое закрытие {cl2} пт.  равно предыдущему {cl1} пт.;'
    else:
        msg += f'За прошедший {name_inter} не понятно, что произошло?'
    return msg

def what_max(hi2, hi1):
    msg = ''
    max_delta = round ((hi2 - hi1), 2)
    max_delta_pr = round (((hi2 - hi1)/hi1*100), 2)
    if hi2 > hi1:
        msg += f'\n\nновый максимум {hi2} пт.  \nвыше предыдущего {hi1} пт.  \nна {max_delta} пт.  или {max_delta_pr} %;'
    elif hi2 < hi1:
        msg += f'\n\nновый максимум {hi2} пт.  \nниже предыдущего {hi1} пт.  \nна {max_delta} пт.  или {max_delta_pr} %;'
    elif hi2 == hi1:
        msg += f'\n\nновый максимум {hi2} пт.  равен предыдущему {hi1} пт.'
    else:
        msg += '\nпо максимуму вообще не понятно, что происходит;'
    return msg

def what_hight_close (hi2, cl2, lo2):
    msg = ''
    hi_cl_delta = round (cl2 - hi2, 2)
    hi_cl_delta_pr = round (((cl2 - hi2)/hi2*100), 2)
    hi_lo_delta = round (hi2 - lo2, 2)
    hi_cl_pr_of_hi_lo = round ((abs(cl2 - hi2)/hi_lo_delta*100), 2)
    # msg += f"\n\nрасстояние от максимума {hi2} пт. \nдо закрытия {cl2} пт. \nравно {hi_cl_delta} пт.  или {hi_cl_delta_pr}%;"
    msg += f"\n\nрасстояние от максимума {hi2} пт. \nдо закрытия {cl2} пт. \nравно {abs(hi_cl_delta)} пт.  или {hi_cl_pr_of_hi_lo}% от все высоты бара;"
    return msg

def what_low_close (lo2, cl2, hi2):
    msg = ''
    cl_lo_delta = round (cl2 - lo2, 2)
    cl_lo_delta_pr = round (((cl2 - lo2)/lo2*100), 2)
    hi_lo_delta = round (hi2 - lo2, 2)
    cl_lo_pr_hi_lo = round (((cl2 - lo2)/hi_lo_delta*100), 2)
    # msg += f"\n\nрасстояние от минимума {lo2} пт. \nдо закрытия {cl2} пт. \nравно {cl_lo_delta} пт.  или {cl_lo_delta_pr}% от значения закрытия;"
    msg += f"\n\nрасстояние от минимума {lo2} пт. \nдо закрытия {cl2} пт. \nравно {cl_lo_delta} пт.  или {cl_lo_pr_hi_lo}% от всей высоты бара;"
    return msg

def what_min(lo1, lo2):
    msg = ''
    min_delta = round ((lo2 - lo1), 2)
    min_delta_pr = round (((lo2 - lo1)/lo1*100), 2)
    if lo2 > lo1:
        msg += f'\n\nновый минимум {lo2} пт.  \nвыше предыдущего {lo1} пт.  \nна {min_delta} пт.  или {min_delta_pr} %;'
    elif lo2 < lo1:
        msg += f'\n\nновый минимум {lo2} пт.  \nниже предыдущего {lo1} пт.  \nна {min_delta} пт.  или {min_delta_pr} %;'
    elif lo2 == lo1:
        msg += f'\n\nновый максимум {lo2} пт.  равен предыдущему {lo1} пт.'
    else:
        msg += '\nпо максимуму вообще не понятно, что происходит;'
    return msg

def what_open_close(op2, cl2):
    msg = ''
    op_cl_delta = round (cl2 - op2, 2)
    op_cl_delta_pr = round (((cl2 - op2)/op2*100), 2)
    msg += f"\n\nрасстояние от открытия {op2} пт. \nдо закрытия {cl2} пт. \nравно {op_cl_delta} пт.  или {op_cl_delta_pr}%;"
    return msg

def what_low_hight(lo2, hi2):
    msg = ''
    delta_abs = round (hi2 - lo2, 2)
    delta_pr = round (((hi2 - lo2)/lo2*100), 2)
    msg += f"\n\nрасстояние от минимума {lo2} пт. \nдо максимума {hi2} пт. \nравно {delta_abs} пт.  или {delta_pr}%;"
    return msg

def what_1_2(lo2, hi2):
    msg = ''
    level_1_2 = round ((hi2 + lo2)/2, 2)
    msg += f"\n\nуровень 1/2:  {level_1_2} пт."
    return msg

def graf_analitiks (figi):
    """ #Функция возвращает текст с информацией о текущем баре в виде конкретных значений
    """
    FIGI = figi
    load_period = 7 # количество баров для загрузки
    load_to = datetime.now(timezone.utc).astimezone() # текущее время
    load_enum_inter = CandleInterval.CANDLE_INTERVAL_DAY # анализируемый интервал (дневный бары)
    # load_from, name_inter, enum_inter = load_from_graf (load_period) # глубина загрузки
    load_from = datetime.now(timezone.utc).astimezone() - timedelta(days=load_period)
    name_inter = 'день' 
    
    msg = ''
    list_cdl=[]
    list_obj_cdl=[]
    print('Подключаемся к Tinkoff для graf_analitiks')
    # загрузка исторических данных о цене
    with Client(TOKEN) as g_client:
        print('ПОДКЛЮЧИЛИСЬ к Tinkoff для graf_analitiks')
        try:
            # непосредственно сама загрузка исторических данных о цене                 
            bars = g_client.market_data.get_candles(
                figi=figi,
                from_=load_from, # сделать согласно глобальных настроек количества баров
                to=load_to,
                interval= load_enum_inter)
            candl_shop = bars.candles  # загруженные бары
        except:
            print('Что-то пошло не так')
        msg = ''
        if len(candl_shop) > 1:
            # преобразуем данные в dataframe
            print('Преобразуем данные в DataFrame ')
            df_cndl = create_df_bars_set(candl_shop)
            
            cl2 = df_cndl.iloc[-1]['Close']
            op2 = df_cndl.iloc[-1]['Open']
            hi2 = df_cndl.iloc[-1]['High']
            lo2 = df_cndl.iloc[-1]['Low']
            # если интервал день то выводить только дату баз часов и минут
            dt2= (candl_shop[-1].time.astimezone())
            dt2 = datetime.strftime(dt2, '%d.%m.%Y')

            cl1 = df_cndl.iloc[-2]['Close']
            op1 = df_cndl.iloc[-2]['Open']
            hi1 = df_cndl.iloc[-2]['High']
            lo1 = df_cndl.iloc[-2]['Low']

            dl_cl = cl2 - cl1
            dl_hi = hi2 - hi1
            dl_lo = lo2 - lo1
            dl_lo_hi = hi2-lo2

            # информация о фьчерсе
            futur_info = g_client.instruments.future_by (id_type = InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, id=FIGI).instrument
            futur_name = futur_info.name
            futur_ticker = futur_info.ticker

            msg += f"{futur_name}\n{futur_ticker} \nот  {dt2}\n\n"
            msg += what_bar_close (cl1, cl2, name_inter)
            msg += what_low_hight (lo2, hi2)
            msg += what_1_2 (lo2, hi2)
            msg += what_max (hi2, hi1)
            msg += what_min (lo1, lo2)
            msg += what_low_close (lo2, cl2, hi2)
            msg += what_hight_close (hi2, cl2,lo2)
            msg += what_open_close (op2, cl2)


            print (df_cndl)
            print()
            print (msg)
        if len(msg) > 1:
            return msg
        else: 
            return 0

def tiho ():
    subprocess.call("TASKKILL /f  /IM  CHROME.EXE")
    subprocess.call("TASKKILL /f  /IM  CHROMEDRIVER.EXE")
    subprocess.call("TASKKILL /f  /IM  SKYPE.EXE")
    subprocess.call("TASKKILL /f  /IM  opera.EXE")
    subprocess.call("TASKKILL /f  /IM  Telegram.EXE")
    subprocess.call("TASKKILL /f  /IM  AdobeCollabSync.exe")

#Определение уровней
#метод 1: фрактальная свеча
# определение бычьего фрактала
def is_support(df,i):
  cond1 = df['Low'][i] < df['Low'][i-1]
  cond2 = df['Low'][i] < df['Low'][i+1]
  cond3 = df['Low'][i+1] < df['Low'][i+2]
  cond4 = df['Low'][i-1] < df['Low'][i-2]
  return (cond1 and cond2 and cond3 and cond4)

# определение медвежьего фрактал
def is_resistance(df,i):
  cond1 = df['High'][i] > df['High'][i-1]
  cond2 = df['High'][i] > df['High'][i+1]
  cond3 = df['High'][i+1] > df['High'][i+2]
  cond4 = df['High'][i-1] > df['High'][i-2]
  return (cond1 and cond2 and cond3 and cond4)

# чтобы проверить, что область нового уровня еще не существует
def is_far_from_level(value, levels, df):
  ave =  np.mean(df['High'] - df['Low'])
  return np.sum([abs(value-level)<ave for _,level in levels])==0

# список для хранения уровней сопротивления и поддержки
def find_levels (df: pd):
    levels = []
    for i in range(2, df.shape[0] - 2):
        if is_support(df, i):
            low = df['Low'][i]
            if is_far_from_level(low, levels, df):
                levels.append((i, low)) 
        elif is_resistance(df, i):
            high = df['High'][i]
            if is_far_from_level(high, levels, df):
                levels.append((i, high))
    return levels

# для визуализаций
def plot_all(levels, df, actual, period):
  print(matplotlib.get_backend())
  graf_path = f"start_levels_{period}.png"
  mpf_levels =[]
  for level in levels:
      mpf_levels.append(level[1])
  hlines=dict(hlines=mpf_levels, colors=['y'], linestyle='-', linewidths=(0.8))
  title_graf = f'{actual}  {period} {mpf_levels}'
  mpf.plot(df, title=title_graf, style='mike', hlines=hlines, tight_layout=False, ylabel='', savefig=graf_path)

# get stock prices using yfinance library
def get_stock_price(symbol,df):
#   df = yf.download(symbol, start='2023-02-01', threads= False)
  df['Date'] = pd.to_datetime(df.index)
  df['Date'] = df['Date'].apply(mpl_dates.date2num)
  df = df.loc[:,['Date', 'Open', 'High', 'Low', 'Close']]
  return df

# get prices using TI
def get_price_TI(period='15min'):
    full_FIGI_load = global_f_opt['future_FIGI']
    actual = global_f_opt['full_future_name']
    dt_now = datetime.now(timezone.utc).astimezone()
    if period == '15min':        
        load_from = dt_now - timedelta (minutes=15*4*24)
        load_to = dt_now
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_15_MIN
    elif period == '1h':
        load_from = dt_now - timedelta (hours=24*5)
        load_to = dt_now
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_HOUR
    elif period == '1D':
        load_from = dt_now - timedelta (days=60)
        load_to = dt_now
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_DAY
    else:
        dt_now = datetime.now(timezone.utc).astimezone()
        load_from = dt_now - timedelta (minutes=15*4*24)
        load_to = dt_now
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_15_MIN
        
    with Client(TOKEN) as client:
        try:
            bars = client.market_data.get_candles(
                figi=full_FIGI_load,
                from_=load_from,
                to=load_to,
                interval=load_bar_inter
            )
        except Exception as ebx:
            print("ОШИБКА!!!")
            print(ebx)
            return 0
    canl_shop = bars.candles
    if len(canl_shop) > 0:
        # преобразуем данные в dataframe
        df = create_df_bars_set(canl_shop)
        df['Date'] = pd.to_datetime(df.index)
        df['Date'] = df['Date'].apply(mpl_dates.date2num)
        df = df.loc[:,['Date', 'Open', 'High', 'Low', 'Close']]
        levels = []
        levels = find_levels (df)
        print('Найдены уровни:')
        print(levels)
        plot_all(levels, df, actual, period)

def ATR_calc (interval, quantity_bars):
    '''Вычисление дневного ATR для активного фьючерса'''
    full_FIGI_load = global_f_opt['future_FIGI']
    actual = global_f_opt['full_future_name']
    dt_now = datetime.now(timezone.utc).astimezone()
    start_point = dt_now

    if interval == "15min":
        load_from = start_point - timedelta(minutes=15*quantity_bars)
        load_enum_inter = CandleInterval.CANDLE_INTERVAL_15_MIN
    elif interval == "30min":
        load_from = start_point - timedelta(minutes=30*quantity_bars)
        load_enum_inter = CandleInterval.CANDLE_INTERVAL_30_MIN
    elif interval == "1h":
        load_from = start_point - timedelta(minutes=60*quantity_bars)
        load_enum_inter = CandleInterval.CANDLE_INTERVAL_HOUR
    elif interval == "4h":
        load_from = start_point - timedelta(minutes=4*60*quantity_bars)
        load_enum_inter = CandleInterval.CANDLE_INTERVAL_4_HOUR
    elif interval == "DAY":
        load_from = start_point - timedelta(days=1*quantity_bars)
        load_enum_inter = CandleInterval.CANDLE_INTERVAL_DAY
    elif interval == "WEEK":
        load_from = start_point - timedelta(weeks=1*quantity_bars)
        load_enum_inter = CandleInterval.CANDLE_INTERVAL_WEEK
    elif interval == "MONTH":
        load_from = start_point - timedelta(weeks=4*quantity_bars)
        load_enum_inter = CandleInterval.CANDLE_INTERVAL_MONTH
    else:
        interval = "DAY"
        load_from = start_point - timedelta(days=1*quantity_bars)
        load_enum_inter = CandleInterval.CANDLE_INTERVAL_DAY
    
    load_to = start_point - timedelta (days=1)

    with Client(TOKEN) as client:
        try:
            bars = client.market_data.get_candles(
                figi=full_FIGI_load,
                from_=load_from,
                to=load_to,
                interval=load_enum_inter
            )
        except Exception as ebx:
            print("ОШИБКА!!!")
            print(ebx)
            return 0
    canl_shop = bars.candles
    if len(canl_shop) > 0:
        # преобразуем данные в dataframe
        df = create_df_bars_set(canl_shop)
        df_delta = df['High']  - df['Low']
        # сделать выборку 5 баров, т.к. сейчас могут быть пустые бары когда торги не велись

        ATR_D = df_delta.mean()
        print(df_delta)
        print(round(ATR_D, 2))
        print()
        return df_delta, ATR_D

def reg_msg(): # счетчик обращений к телеге
    g_reg_msg['msg_count'] +=1
    g_reg_msg['mg_time'].append(time.time()) # спискок хранения времени каждого обращения относительного глобального секундомера
    g_reg_msg['msg_dt'].append(datetime.now(timezone.utc).astimezone())
    dt_now = datetime.now(timezone.utc).astimezone()
    print (dt_now, 'Обращение к TG')
    max_reqests = 30
    msg_count = g_reg_msg['msg_count']
    if msg_count == max_reqests:
        print(f'{max_reqests} обращений')
        ri_msg(str(max_reqests))
    elif msg_count == 20:
        t1 = g_reg_msg['mg_time'][0]
        t2 = g_reg_msg['mg_time'][-1]
        t=round(t2-t1, 2)
        msg = '\n'
        msg += f'Количество обращений: {msg_count}\n'
        msg += f'время прошло: {t} сек.\n'
        if t <= 60.0:
            msg += f'#{msg_count}_обращений_менее_минуты\n'
        msg += f'#20_обращений\n'
        
        # print_msg(msg)
        print(msg)
        
# печать в консоль и телегу
def print_msg(msg):
    print(msg)
    try:
        err_bot.send_message(ADIMIN_ID_TG, msg)
    except Exception as e:
        telega_error_2 (e)

# очистка статистики сообщений
def ri_msg(msg_cn):
    t1 = g_reg_msg['mg_time'][0]
    t2 = g_reg_msg['mg_time'][-1]
    t=round(t2-t1, 2)
    print(f'время прошло: {t} сек.')
    if msg_cn =='30':
        g_reg_msg['msg_t_30'].append(t) # записываем период, который потребовался на 30 обращений
        # print ('Таймауты 30 сообщений', g_reg_msg)
        try:
            err_msg = f'Всего  {msg_cn}  обращений за время  {t} сек.\n'
            err_msg += f'#30_обращений'
            # err_bot.send_message(ADIMIN_ID_TG, err_msg) #пока приглушить данные сообщения
            print (err_msg)
        except Exception as e:
            telega_error_2 (e)
    else:
        g_reg_msg['msg_t_x'].append(t)
    g_reg_msg['msg_count'] = 0 # очищаем статистику
    g_reg_msg['mg_time'].clear()
    g_reg_msg['msg_dt'].clear()

def load_bars (figi_l, period, date_start, bar_depth):
    '''# В разработке  
    Загрузить требуемое количество бар по фьючерсам, с требуемым интервалом
        figi_l: что грузить
        period: требуемый интервал для загрузки, день, час и т.д.
        date_start: дата начала загрузки 
        bar_depth: количество бар для загрузки        
    '''
    dt_now = datetime.now(timezone.utc).astimezone()
    if period == '15min':        
        load_from = dt_now - timedelta (minutes=15*4*24)
        load_to = dt_now
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_15_MIN
    elif period == '1h':
        load_from = dt_now - timedelta (hours=24*5)
        load_to = dt_now
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_HOUR
    elif period == '1D':
        load_from = dt_now - timedelta (days=60)
        load_to = dt_now
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_DAY
    else:
        dt_now = datetime.now(timezone.utc).astimezone()
        load_from = dt_now - timedelta (minutes=15*4*24)
        load_to = dt_now
        load_bar_inter = CandleInterval.CANDLE_INTERVAL_15_MIN
        
    with Client(TOKEN) as client:
        try:
            bars = client.market_data.get_candles(
                figi=figi_l,
                from_=load_from,
                to=load_to,
                interval=load_bar_inter
            )
        except Exception as ebx:
            print("ОШИБКА!!!")
            print(ebx)
            return 0
    canl_shop = bars.candles
    if len(canl_shop) > 0:
        # преобразуем данные в dataframe
        df = create_df_bars_set(canl_shop)
        df['Date'] = pd.to_datetime(df.index)
        df['Date'] = df['Date'].apply(mpl_dates.date2num)

def find_figi_of_name_future (name_future):
    '''# ПОИСК FIGI фьючерса по его имени, 
    а так же остальных параметров фьючерса'''
    full_name_load = name_future
    # загрузка списка фьючерсов и поиск требуемого  для отображения 
    # или загрузка списка акций и поиск требуемой акции для отображения        
    with Client(TOKEN) as client:
        # 1.Получаем список всех фьючерсов. На выходе выдаем: futures_instr
        futures_instr = []  # список фьючерсов
        flag_r = True  # ФЛАГ: повторят загружать пока не получиться загрузить
        print('Формирование списка фьючерсов')
        while flag_r:
            try:
                futures = client.instruments.futures(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)
                flag_r = False # загрузилось поэтому не повторять
                futures_instr = futures.instruments  # список фьючерсов
                print(f'Всего фьючерсов в списке: {len(futures_instr)}')
            except Exception as e:
                print(datetime.now(timezone.utc).astimezone())
                print('\nВОЗНИКЛА ОШИБКА загрузки списка доступных фьючерсов, в функции find_figi_of_name_future')
                print(e)
                print()
                flag_r = True

        # 2.Перебираем список фьючерсов futures_instr 
        # пока не найдем соотв. наименованию full_name_load
        # на выходе: 
        #       future_find_dict словарь с найденным фьючерсом (figi, tiker, name)
        #       future_find_objct словарь с объектом класса Future найденного фьючерса
        #       full_FIGI_load требуемое найденное FIGI по имени фьючера
        #       global_f_opt['future_FIGI'] = full_FIGI_load устанавливается глобальное FIGI
        future_find_dict = {}  # текстовый список фьючерсов
        future_find_objct = []  # список объектов фьючерсов
        len_name = len(full_name_load)
        for i in futures_instr:
            len_i_name = len(i.name)
            if len_i_name >= len_name:
                i_name = i.name[:len_name]
                if full_name_load in i_name:
                    future_find_dict = {'figi': i.figi, 'tiker': i.ticker, 'name': i.name}
                    future_find_objct.append(i)
                    full_FIGI_load = future_find_dict['figi']
                    print(f"Найден фьючерс: {future_find_dict['name']}\n")
                    return full_FIGI_load, future_find_dict, full_FIGI_load
    return 0 # если ни чего неь найдено то будет ошибка в функции выше

def test_switch(sw):
    global bot, G_VALID_BOT
    
    if sw > 120:
        try:
            print ('попытка переключить бота')
            bot.stop_bot()
            del bot
            switch_bot()
        except Exception as e:
            dt = datetime.now(timezone.utc).astimezone()
            msg = ''
            msg += f'\n{dt}\n'
            msg += f"НЕ УДАЧНАЯ попытка переключить бота\n\n"
            err_out(msg)
    elif sw == 50:
        try:
            print ('попытка вызвать ошибку 429 бота')
            label1 = bot.send_message(ADIMIN_ID_TG, "Test error 429")
            n=1
            while True:
                msg11 = f'Test error 429. Edit #{n}'
                bot.edit_message_text( chat_id = ADIMIN_ID_TG, message_id=label1.id, text=msg11 )
                n +=1
        except Exception as e:
            print (e)
            telega_error(e)


def telega_error (e):
    global bot, G_VALID_BOT
    bot_name_s = bot.get_my_name()
    bot_tok = bot.token
    print (f'{bot_name_s}, {bot_tok}')
    dt = datetime.now(timezone.utc).astimezone()
    msg = ''
    msg += f'\n{dt}\n'
    msg += f'для бота: {bot_name_s}\n'
    msg += f'ВОЗНИКЛА ОШИБКА:\n'
    msg += f'{e}\n'
    err_out(msg)
    
    if hasattr (e, 'error_code'):
        if e.error_code == 429:
            res_e = e.result_json
            dt = datetime.now(timezone.utc).astimezone()
            time_sleep =  int(res_e['parameters']['retry_after']) + 1
            msg = ''
            msg += f'{dt}\n'
            msg += f"Код ошибки: {e.error_code}\n"
            msg += f"Функция, где возникла ошибка: TeleBot.{e.function_name}\n\n"
            msg += f'Описание ошибки: {e.result.reason}\n\n'
            print_time_sleep = time_sleep
            time_unit = 'сек.'
            if print_time_sleep > 60:
                print_time_sleep = print_time_sleep/60
                time_unit = 'мин.'
                if print_time_sleep > 60:
                    print_time_sleep = print_time_sleep/60
                    time_unit = 'час.'
                    if print_time_sleep > 24:
                        print_time_sleep = print_time_sleep/24
                        time_unit = 'дн.'
            msg += f"Требуется пауза {round(print_time_sleep, 2)} {time_unit}\n"
            if time_sleep > 0:
                msg += f"\nПопытка переключения бота\n"
                err_out(msg) # вывод сообщения в консоль
                try:
                    print ('Начало переключения бота')
                    bot.stop_bot()
                    # del bot
                    switch_bot()
                except Exception as e:
                    dt = datetime.now(timezone.utc).astimezone()
                    msg = ''
                    msg += f'{dt}\n'
                    msg += f"НЕ УДАЧНАЯ попытка переключить бота\n\n"
                    err_out(msg)

                    msg += f"Запускается пауза\n"
                    err_out(msg) # вывод сообщения
                    time.sleep(time_sleep)
                    dt = datetime.now(timezone.utc).astimezone()
                    msg = ''
                    msg += f'{dt}\n'
                    msg += f"КОНЕЦ паузы\n\n"
                    err_out(msg)

                
            else:
                msg += f"Запускается пауза\n"
                err_out(msg) # вывод сообщения в консоль
                time.sleep(time_sleep)
                dt = datetime.now(timezone.utc).astimezone()
                msg = ''
                msg += f'{dt}\n'
                msg += f"КОНЕЦ паузы\n\n"
                err_out(msg)
        else:
            msg = ''
            msg += f'{e}\n'
            msg += f"Обработчик данной ошибки не предусмотрен\n\n"
            err_out(msg)

def err_out(err_msg):
    print(err_msg)
    try:
        err_bot.send_message(ADIMIN_ID_TG, err_msg)
    except Exception as e:
        telega_error_2 (e)

def telega_error_2 (e):
    # telebot.apihelper.ApiTelegramException
    # logging.error(f"Ошибка: {str(e)}")
    dt = datetime.now(timezone.utc).astimezone()
    msg = ''
    msg += f'\n{dt}\n'
    msg += f'ВОЗНИКЛА ОШИБКА:\n'
    msg += f'{e}\n'
    print(msg)
    if hasattr (e, 'error_code'):
        if e.error_code == 429:
            res_e = e.result_json
            dt = datetime.now(timezone.utc).astimezone()
            time_sleep =  int(res_e['parameters']['retry_after']) + 1
            msg = ''
            msg += f"Код ошибки: {e.error_code}\n"
            msg += f"Функция, при обращении к которой возникла ошибка: TeleBot.{e.function_name}\n"
            msg += f'Описание ошибки: {e.result.reason}\n'
            msg += f'{dt}\n'
            msg += f"Запускаем паузу {time_sleep} сек.\n"
            print(msg)
            time.sleep(time_sleep)
            dt = datetime.now(timezone.utc).astimezone()
            print(dt)
            print("КОНЕЦ паузы")
            print()
        else:
            print()
            print(res_e)
            print("Обработчик данной ошибки не предусмотрен")
            print()

# вычисление взлетов и падений из ранее загруженного списка акций из global_all_list
def calc_hight():
    top_hight = []
    top_low = []
    for k in global_all_list:
        # '@GS' исключение неактуальных российских ГДР
        if len(k) > 4 and not ('@GS' in k[0].ticker) and not ('MSST' in k[0].ticker) and not (
                'POGR' in k[0].ticker):
            izm = round((cast_money(k[-1].close) - cast_money(k[-2].close)) / cast_money(k[-2].close) * 100, 2)
            top_hight.append([izm, k[0].ticker, k[0].name, cast_money(k[-1].close)])
    top_hight.sort(reverse=True)
    top_low = top_hight.copy()
    top_low.sort()
    i = 0
    j = 15
    msg = f'Взлёты:(интервал {global_interval_load_s})\n'
    for h in top_hight:
        msg += f'{i + 1}. {h[1]}   {h[0]}%\n'
        # msg+=f'  {h[2]} [закр: {h[3]} {global_val_nom}]\n'
        msg += f'  https://www.tinkoff.ru/invest/stocks/{h[1]}\n'
        # msg+=f'\n'
        i += 1
        if i == j:
            break
    i = 0
    j = 15
    msg_lw = f'Падения:(интервал {global_interval_load_s})\n'
    for lw in top_low:
        msg_lw += f'{i + 1}. {lw[1]}   {lw[0]}%\n'
        # msg_lw+=f'  {lw[2]} [закр: {lw[3]} {global_val_nom}]\n'
        msg_lw += f'  https://www.tinkoff.ru/invest/stocks/{lw[1]}\n'
        # msg_lw+=f'\n'
        i += 1
        if i == j:
            break
    return msg, msg_lw

def find_ups_and_downs(t_bot: telebot.TeleBot, ID_ch):
    '''анализ взлетов и падений акций'''
    if len(global_all_list) != 0:
                msg, msg_lw = calc_hight()
                msg += '\n#P1A_взлеты'
                msg_lw += "\n#P1A_падения"
                # взлеты
                for message1 in util.smart_split(msg, 4000):
                    try:
                        reg_msg()
                        to_pin = t_bot.send_message(ID_ch, message1, disable_web_page_preview=True)
                    except Exception as e:
                        telega_error (e)

                # падения
                for message1 in util.smart_split(msg_lw, 4000):
                    try:
                        t_bot.send_message(ID_ch, message1, disable_web_page_preview=True)
                    except Exception as e:
                        telega_error (e)
    else:
        try:
            t_bot.send_message(ID_ch, text=f'Значение цен не загружены. Необходимо запустить через команду /begin')
        except Exception as e:
            telega_error (e) 

def load_bars_f (FIGI: str, how: int, time_frame: str):
    how = how or 5
    time_frame = time_frame or 'DAY'
    if time_frame == 'DAY' :
        load_interval=CandleInterval.CANDLE_INTERVAL_DAY
        to_date = datetime.now(timezone.utc).astimezone()
        from_date = to_date - timedelta(days = how)
    else:
        return 0
    bar_list =[]
    repit_flag = True
    try:
        with Client(TOKEN) as grpc_client:
            bars = grpc_client.market_data.get_candles(
                figi=FIGI,
                from_ = from_date,
                to = to_date,
                interval=load_interval
                ).candles
            return bars
    except Exception as ex:
       print(ex)
       return 0

def find_futures(FIGI: str):
    '''
    Поиск по FIGI когда три интервала подряд: 
    новый максимум выше предыдущего, 
    новый минимум выше предыдущего, 
    каждое новое закрытие выше предыдущего
    '''
    # Загрузка баров 
    bars = load_bars_f (FIGI=FIGI, how = 10, time_frame = 'DAY')

    bar1 = bars[-1]
    bar2 = bars[-2]
    bar3 = bars[-3]

    hight_1 = cast_money(bar1.high)
    low_1 = cast_money(bar1.low)
    close_1 = cast_money(bar1.close)
    open_1 = cast_money(bar1.open)
    vol_1 = bar1.volume
    date_1 = bar1.time

    hight_2 = cast_money(bar2.high)
    low_2 = cast_money(bar2.low)
    close_2 = cast_money(bar2.close)
    open_2 = cast_money(bar2.open)
    vol_2 = bar2.volume
    date_2 = bar2.time

    hight_3 = cast_money(bar3.high)
    low_3 = cast_money(bar3.low)
    close_3 = cast_money(bar3.close)
    open_3 = cast_money(bar3.open)
    vol_3 = bar3.volume
    date_3 = bar3.time    

    if (hight_1 > hight_2 and hight_2 > hight_3) and (low_1 > low_2 and low_2 > low_3) and (close_1 > close_2 and close_2 > close_3):
        return True
    else:
        return False

def switching_set(name_set,bot_t, id_ch):
    '''функция переключения активного инструмента на требуемый в глобальной настройке бота'''
    global_f_opt['full_future_name'] = name_set + global_f_opt['activ_contr_name']
    figi_future = find_figi_of_name_future (global_f_opt['full_future_name'])
    global_f_opt['future_FIGI'] = figi_future[0]
    show_run_repit_btn(bot_t, id_ch, 'name_set')


def find_patterns(g_client:services.Services, FIGI:str, start_point: datetime, interval, quantity_bars):
    '''
    # В разработке
    Поиск характерных паттернов на графике
        FIGI: требуемый инструмент
        start_point: начальная дата и время от которой в глубину загружать бары
        interval: какие интервалы анализировать 15мин, 1час, 4часа, 1 день
        quantity_bars: количество баров для загрузки в глубину
    '''
    load_to = start_point
    if interval == "15min":
        load_from = start_point - timedelta(minutes=15*quantity_bars)
        load_enum_inter = CandleInterval.CANDLE_INTERVAL_15_MIN
    elif interval == "30min":
        load_from = start_point - timedelta(minutes=30*quantity_bars)
        load_enum_inter = CandleInterval.CANDLE_INTERVAL_30_MIN
    elif interval == "1h":
        load_from = start_point - timedelta(minutes=60*quantity_bars)
        load_enum_inter = CandleInterval.CANDLE_INTERVAL_HOUR
    elif interval == "4h":
        load_from = start_point - timedelta(minutes=4*60*quantity_bars)
        load_enum_inter = CandleInterval.CANDLE_INTERVAL_4_HOUR
    elif interval == "DAY":
        load_from = start_point - timedelta(days=1*quantity_bars)
        load_enum_inter = CandleInterval.CANDLE_INTERVAL_DAY
    elif interval == "WEEK":
        load_from = start_point - timedelta(weeks=1*quantity_bars)
        load_enum_inter = CandleInterval.CANDLE_INTERVAL_WEEK
    elif interval == "MONTH":
        load_from = start_point - timedelta(weeks=4*quantity_bars)
        load_enum_inter = CandleInterval.CANDLE_INTERVAL_MONTH
    else:
        interval = "DAY"
        load_from = start_point - timedelta(days=1*quantity_bars)
        load_enum_inter = CandleInterval.CANDLE_INTERVAL_DAY

    # загрузка исторических данных о цене
    try:
        # непосредственно сама загрузка исторических данных о цене                 
        bars = g_client.market_data.get_candles(
            figi=FIGI,
            from_=load_from, 
            to=load_to,
            interval= load_enum_inter)
        candl_shop = bars.candles  # загруженные бары
    except Exception as ebx:
        print('Что-то пошло не так')
        print(ebx)
        if ebx.code.name == 'RESOURCE_EXHAUSTED':
            stop_time = ebx.metadata.ratelimit_reset + 2
            print()
            print_date_time_now()
            print(ebx)
            print (f'Пауза {stop_time} сек...')
            time.sleep(stop_time)
            print_date_time_now()
            print()

            bars = g_client.market_data.get_candles(
             figi=FIGI,
                from_=load_from, 
                to=load_to,
                interval= load_enum_inter)
            candl_shop = bars.candles
    if len(candl_shop) >= 4:
        # преобразуем данные в dataframe
        df_cndl = create_df_bars_set(candl_shop)
        # Анализ
        # Чтение ячеек Pandas DataFrame. Последние 3 закрытия из DataFrame
        # https://translated.turbopages.org/proxy_u/en-ru.ru.35e8478b-65f575b9-4075875f-74722d776562/https/www.geeksforgeeks.org/how-to-get-cell-value-from-pandas-dataframe/
        cl1 = df_cndl['Close'].iloc[-1]
        cl2 = df_cndl['Close'].iloc[-2]
        cl3 = df_cndl['Close'].iloc[-3]
        cl4 = df_cndl['Close'].iloc[-4]
        
        op1 = df_cndl['Open'].iloc[-1]
        op2 = df_cndl['Open'].iloc[-2]
        op3 = df_cndl['Open'].iloc[-3]
        op4 = df_cndl['Open'].iloc[-4]
        
        # Часть 1
        # Поиск 2-х закрытий подряд выше предыдущих
        if (cl1 > cl2) and (cl2 > cl3):
            close_2_up = True
        else:
            close_2_up = False
        # Поиск 3-х закрытий подряд выше предыдущих
        if (cl1 > cl2) and (cl2 > cl3) and (cl3 > cl4):
            close_3_up = True
        else:
            close_3_up = False

        # Часть 2
        # Поиск 2-х закрытий подряд выше 2-х открытий 
        if (cl1 > op1) and (cl2 > op2):
            close_2_up_2 = True
        else:
            close_2_up_2 = False
        # Поиск 3-х закрытий подряд выше выше 3-х открытий
        if (cl1 > op1) and (cl2 > op2) and (cl3 > op3):
            close_3_up_3 = True
        else:
            close_3_up_3 = False
        
        # Поиск 2-х закрытий подряд ниже предыдущих
        if (cl1 < cl2) and (cl2 < cl3):
            close_2_down = True
        else:
            close_2_down = False

        # Поиск 3-х закрытий подряд ниже предыдущих
        if (cl1 < cl2) and (cl2 < cl3) and (cl3 < cl4):
            close_3_down = True
        else:
            close_3_down = False
    else:
        close_2_up = False
        close_3_up = False
        close_2_up_2 = False
        close_3_up_3 = False
        close_2_down = False
        close_3_down = False
    
    return close_2_up, close_3_up, close_2_down, close_3_down, close_2_up_2, close_3_up_3 
            
def sort_by_capitalization(stoks_arr):
    stoks_arr_sort = []
    figi_arr = []
    st1: Share
    figi1:Share
    for figi1 in stoks_arr:
        figi_arr.append(figi1.figi)
    print('Подключаемся к Tinkoff')    
    with Client(TOKEN) as g_client:
        print('ПОДКЛЮЧИЛИСЬ к Tinkoff')
        # загрузка загрузка всех последних цен
        try:
            # список последних цен
            last_prices = g_client.market_data.get_last_prices(figi=figi_arr).last_prices
        except Exception as ebx:
            print_date_time_now()
            print('\nВОЗНИКЛА ОШИБКА загрузки списка последних цен')
            print(ebx)
            print()
        m=0
        capital_tuples = []
        for lp1 in last_prices:
            # получить последнюю цену
            price = cast_money(lp1.price)
            # получить количество акций
            st1 = stoks_arr[m]
            m +=1
            size = st1.issue_size
            # вычислить капитализацию
            if lp1.figi == st1.figi:
                capital = size*price
                # занести в список размер капитализации
                    # capital_tuples = [
                    #             ('BBG000FWGSZ5', '63.55', obj_share),
                    #             ('BBG004S68CV8', '34760.0', obj_share),
                    #             ('figi', 'capital', obj_share),
                    #         ]
                capital_tuples.append((st1.name, st1.figi, capital, st1.currency, st1))            
        
        
        # отсортировать список по размеру капитализации
        # https://docs.python.org/3/howto/sorting.html
        sort = sorted(capital_tuples, key=lambda cptl: cptl[2], reverse=True)
        # вернуть отсортированный список акций по капитализации
        stoks_arr=[]
        for i in sort:
            stoks_arr.append(i[4])

    stoks_arr_sort = stoks_arr
    return stoks_arr_sort



def sort_out_stoks(interval):
    '''# Поиск паттернов в АКЦИЯХ\n
            interval: MONTH, WEEK, DAY, 4h, 1h, 30min, 15min'''
    # определить список для анализа: или все активные фьючерсы, все имеющиеся фьючерсы, избранный фьючерсы
    print('Подключаемся к Tinkoff')    
    with Client(TOKEN) as g_client:
        print('ПОДКЛЮЧИЛИСЬ к Tinkoff')
        # загрузка всего списка фьючерсов
        try:
            # список фьючерсов
            shares_instr = g_client.instruments.shares(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE).instruments
        except Exception as ebx:
            print_date_time_now()
            print('\nВОЗНИКЛА ОШИБКА загрузки списка акций')
            print(ebx)
            print()
        # сделать только актуальные
        figi_array = []
        start_point = datetime_now()
        quantity_bars = 10
        close_2_up_arr =[]
        close_3_up_arr = []
        close_2_up_2_arr =[]
        close_3_up_3_arr = []
        close_2_down_arr =[]
        close_3_down_arr =[]
        print(f'Анализ списка из {len(shares_instr)} шт. акций')
        curr_time = datetime.now(timezone.utc).astimezone()
        сurr_year = curr_time.year
        curr_moth = curr_time.month
        curr_day = curr_time.day
        # выбо доступных акций для анализа
        shares_arr=[]
        for ft1 in shares_instr:
            if  'NOMPP' in ft1.ticker: # пропустить внебирживые бумаги
                print ("Внеберживая бумага:",ft1.ticker, ft1.for_qual_investor_flag, ft1.exchange)
                print ('Пропускаем')
                continue
            if 'otc_ncc' in ft1.exchange:  # признак внебирживые бумаги
                print ("Внеберживая бумага:",ft1.ticker, ft1.for_qual_investor_flag, ft1.exchange)
                if not(ft1.for_qual_investor_flag):
                    print('АААААААААААААААААААААААААА  ВСЁЁЁЁЁЁЁЁЁЁЁЁЁЁЁЁЁЁЁЁЁЁЁЁ пропалоООООО!!!!!!!!!!!!!!!!!!!!!!!!!')
                print ('Пропускаем')
                continue
            if ft1.currency == 'rub' and not(ft1.for_qual_investor_flag):
                print (ft1.name, ft1.position_uid, ft1.exchange)
                shares_arr.append(ft1)
                
        if len(shares_arr)>0:
            shares_arr = sort_by_capitalization(shares_arr)

        for ft1 in shares_arr:
            try:
                close_2_up, close_3_up, close_2_down, close_3_down, close_2_up_2, close_3_up_3 = find_patterns (g_client, ft1.figi, start_point, interval, quantity_bars)
            except Exception as ebx:
                print_date_time_now()
                print('\nВОЗНИКЛА ОШИБКА поиска паттернов')
                print(ebx)
                print()
            # Часть 1
            if close_2_up:
                close_2_up_arr.append(ft1)
            if close_3_up:
                close_3_up_arr.append(ft1)
            # Часть 2
            if close_2_up_2:
                close_2_up_2_arr.append(ft1)
            if close_3_up_3:
                close_3_up_3_arr.append(ft1)

            if close_2_down:
                close_2_down_arr.append(ft1)
            if close_3_down:
                close_3_down_arr.append(ft1)
        
        # получаем текущую дату и время
        curr_time = datetime.now(timezone.utc).astimezone()
        # переводим в текстовый вид
        d1 = datetime.strftime(curr_time, '%d.%m.%Y')
        ht1 = datetime.strftime(curr_time, '%H:%M:%S')
        print()
        print ("Количество close_2_up_arr:",len(close_2_up_arr))

        msg_2_up = f'---АКЦИИ от  {d1} ---\n'
        msg_2_up += f"ДВА дня подряд закрытия выше предыдущих: {len(close_2_up_arr)} шт.\n"
        for i in close_2_up_arr:
            print(f'https://www.tinkoff.ru/invest/stocks/{i.ticker}')
            msg_2_up += f'{i.name}\n'
            msg_2_up += f'https://www.tinkoff.ru/invest/stocks/{i.ticker}\n\n'            
        print()
        print ("Количество close_2_up_2arr:",len(close_2_up_2_arr))

        msg_2_up_2 = f'--------АКЦИИ от  {d1}--------\n'
        msg_2_up_2 += f"ДВА дня подряд закрытия выше открытий (два зелёных бара):\n{len(close_2_up_2_arr)} шт.\n\n"
        
        msg_2_up_2_TW = f'---------ССЫЛКИ в TW---------\n--------АКЦИИ от  {d1}--------\n'
        msg_2_up_2_TW += f"ДВА дня подряд закрытия выше открытий (два зелёных бара): {len(close_2_up_2_arr)} шт.\n"

        # https://www.tinkoff.ru/terminal/?template=purchase&template_settings=instrument,d90cacdd-7e99-4e5e-8b24-ffe52c39d831
        msg_2_up_2_penk = f'-----ССЫЛКИ на дерминал ПИНЬКОфФffffff----\n--------АКЦИИ от  {d1}--------\n'
        msg_2_up_2_penk += f"ДВА дня подряд закрытия выше открытий (два зелёных бара): {len(close_2_up_2_arr)} шт.\n"

        for i in close_2_up_2_arr:
            print(f'https://www.tinkoff.ru/invest/stocks/{i.ticker}')
            hiter_dot = f'{i.name}\n'
            msg_2_up_2 += hiter_dot
            msg_2_up_2 += f'https://www.tinkoff.ru/invest/stocks/{i.ticker}\n\n'

            # msg_2_up_2_TW += hiter_dot
            # msg_2_up_2_TW += f"https://ru.tradingview.com/chart/njEAbHth/?symbol={i.ticker}\n\n"

            # msg_2_up_2_penk += hiter_dot
            # msg_2_up_2_penk +=f'https://www.tinkoff.ru/terminal/?template=purchase&template_settings=instrument,{i.position_uid}\n\n'
    return msg_2_up_2, msg_2_up_2_TW, msg_2_up_2_penk, msg_2_up

def send_message_split(msg, bot: telebot.TeleBot, ID_ch):
    '''Вывод длинных сообщений в чат'''
    for message1 in util.smart_split(msg, 4000):
        try:
            reg_msg()
            bot.send_message(ID_ch, message1, disable_web_page_preview=True, disable_notification = True)
        except Exception as e:
            telega_error (e)

def send_msg (msg, bot: telebot.TeleBot, ID_ch):
    '''Вывод сообщений в чат'''
    if len(msg) < 4000:
        try:
            reg_msg()
            bot.send_message(ID_ch, msg, disable_web_page_preview=True, disable_notification = True)
        except Exception as e:
            telega_error (e)
    else:
        send_message_split(msg, bot, ID_ch)

def sort_out(interval):
    '''Поиск паттернов в ФЬЮЧЕРСАХ\n
            interval: MONTH, WEEK, DAY, 4h, 1h, 30min, 15min'''
    # определить список для анализа: или все активные фьючерсы, все имеющиеся фьючерсы, избранный фьючерсы
    print('Подключаемся к Tinkoff')    
    with Client(TOKEN) as g_client:
        print('ПОДКЛЮЧИЛИСЬ к Tinkoff')
        # загрузка всего списка фьючерсов
        try:
            # список фьючерсов
            futures_instr = g_client.instruments.futures(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE).instruments
            print(f'Всего доступно фьючерсов: {len(futures_instr)}')
        except Exception as ebx:
            print_date_time_now()
            print('\nВОЗНИКЛА ОШИБКА загрузки списка фьючерсов')
            print(ebx)
            print()
        # сделать только актуальные
        figi_array = []
        start_point = datetime_now()
        quantity_bars = 10
        close_2_up_arr =[]
        close_3_up_arr = []
        close_2_down_arr =[]
        close_3_down_arr =[]    
        print(f'Анализ')
        curr_time = datetime.now(timezone.utc).astimezone()
        сurr_year = curr_time.year
        curr_moth = curr_time.month
        curr_day = curr_time.day
        for ft1 in futures_instr:
            last_trade_date_f = ft1.last_trade_date.astimezone()
            year_last_date = last_trade_date_f.year
            month_last_trade = last_trade_date_f.month
            day_last_trade = last_trade_date_f.day
            # анализ
            # print('анализ')
            # print(ft1.name, ft1.last_trade_date.astimezone())
            if year_last_date == сurr_year and month_last_trade >= curr_moth and not("WHEAT-" in ft1.name) and not("HOME-" in ft1.name)\
                  and not("MMI-" in ft1.name) and not("RVI-" in ft1.name) and not("Co-" in ft1.name) and not("SUGAR-" in ft1.name)\
                  and not("UCHF-" in ft1.name):
                # проверка, что дата экспирации фьючерса не наступила d ntreotv vtczwt
                if month_last_trade == curr_moth and day_last_trade < curr_day:
                    continue
                try:
                    close_2_up, close_3_up, close_2_down, close_3_down, close_2_up_2, close_3_up_3 = find_patterns (g_client, ft1.figi, start_point, interval, quantity_bars)
                except Exception as ebx:
                    print_date_time_now()
                    print('\nВОЗНИКЛА ОШИБКА загрузки списка фьючерсов')
                    print(ebx)
                    print()
                if close_2_up:
                    close_2_up_arr.append(ft1)
                    # print('close_2_up',ft1.name)
                if close_3_up:
                    close_3_up_arr.append(ft1)
                    # print('close_3_up',ft1.name)
                if close_2_down:
                    close_2_down_arr.append(ft1)
                if close_3_down:
                    close_3_down_arr.append(ft1)
        
        # Преобразуем в DataFrame
        close_2_up_df = create_df_future_list(close_2_up_arr)
        close_2_up_df = close_2_up_df.sort_values(by = 'last_trade_date')

        close_3_up_df = create_df_future_list(close_3_up_arr)
        close_3_up_df = close_3_up_df.sort_values(by = 'last_trade_date')

        # Исключить из close_2_up_df строки которые есть в close_3_up_df
        # https://ru.stackoverflow.com/questions/919047/%D0%9D%D0%B0%D0%B9%D1%82%D0%B8-%D1%81%D1%82%D1%80%D0%BE%D0%BA%D0%B8-%D0%B2-dataframe-%D0%BE%D1%82%D1%81%D1%83%D1%82%D1%81%D1%82%D0%B2%D1%83%D1%8E%D1%89%D0%B8%D0%B5-%D0%B2-%D0%B4%D1%80%D1%83%D0%B3%D0%BE%D0%BC-dataframe
        # res = (cur.merge(old, indicator=True, how='outer')
        #            .query("_merge == 'left_only'")
        #            .drop('_merge',1))
        close_2_up_df = (close_2_up_df.merge(close_3_up_df, indicator=True, how='outer')
                   .query("_merge == 'left_only'"))
        # получаем текущую дату и время
        curr_time = datetime.now(timezone.utc).astimezone()
        # переводим в текстовый вид
        d1 = datetime.strftime(curr_time, '%d.%m.%Y')
        ht1 = datetime.strftime(curr_time, '%H:%M:%S')
        msg_2_up = '---------------------\n'
        msg_2_up += f'[{interval}] ДВА подряд закрытия ВЫШЕ предыдущих:\n'
        msg_2_up += f'от {d1}\n   количество {len(close_2_up_df)} шт.\n\n'        

        for i, row in close_2_up_df.iterrows():            
            msg_2_up += row['name']
            t_s_f = row['ticker']
            msg_2_up += f'\nhttps://www.tinkoff.ru/invest/futures/{t_s_f}\n'
            if row['asset_type'] == 'TYPE_SECURITY':                
                t_s_s = row['basic_asset']
                msg_2_up += f'Акция:  https://www.tinkoff.ru/invest/stocks/{t_s_s}\n\n'
            else:
                msg_2_up +='\n'

        msg_3_up = '---------------------\n'
        msg_3_up += f'[{interval}] ТРИ подряд закрытия ВЫШЕ предыдущих [{interval}]:\n'
        msg_3_up += f'от {d1}\n количество {len(close_3_up_arr)} шт.\n\n'        
        for i, row in close_3_up_df.iterrows():
            msg_3_up += row['name']
            t_s_f = row['ticker']
            msg_3_up += f'\nhttps://www.tinkoff.ru/invest/futures/{t_s_f}\n'
            if row['asset_type'] == 'TYPE_SECURITY':
                t_s_s = row['basic_asset']
                msg_3_up += f'Акция:  https://www.tinkoff.ru/invest/stocks/{t_s_s}\n\n'
            else:
                msg_3_up += '\n'
        
        msg_2_down = '---------------------\n'      
        msg_2_down += f'Два подряд закрытия НИЖЕ предыдущих [{interval}]:\n'
        msg_2_down += f'от {d1}\n\n'
        for unt in close_2_down_arr:
            msg_2_down += unt.name
            msg_2_down += f'\nhttps://www.tinkoff.ru/invest/futures/{unt.ticker}\n\n'
        
        msg_3_down = '---------------------\n'
        msg_3_down += f'Три подряд закрытия НИЖЕ предыдущих [{interval}]:\n'
        msg_3_down += f'от {d1}\n\n'
        for unt in close_3_down_arr:
            msg_3_down += unt.name
            msg_3_down += f'\nhttps://www.tinkoff.ru/invest/futures/{unt.ticker}\n\n'
        
        return msg_2_up, msg_3_up, msg_2_down, msg_3_down

def switch_bot():
    global G_VALID_BOT, TG_TOKEN1, TG_TOKEN2
    if G_VALID_BOT == TG_TOKEN1:
        G_VALID_BOT = TG_TOKEN2        
    else:
        G_VALID_BOT = TG_TOKEN1
    print (f'Установлен токен бота: {G_VALID_BOT}')
    print()


def tick_of_cap(message):
        tiker_name = message.text
        # Получаем список всех акций через APIv2
        # full_list_sh2=gRPC_Load_List()
        for j in g_full_list_sh2:
            # ищем запрошенный тикер в списке акций
            if j.ticker == tiker_name:
                # ищем свечу с последним закрытием имеющую такой же figi  как и запрошенный тикер
                # из глобального списка загруженных свечей
                for k in global_all_list:
                    if k[-1].figi == j.figi:
                        market_cap = round(j.issue_size * k[-1].c / 1000000000, 2)
                        msg = f'Отчет о капитализации компании: {j.ticker}'
                        msg += f'\nНаименование: {j.name}'
                        msg += f'\n1. Капитализация: {market_cap} млрд. {global_val_nom}'
                        msg += f'\n2. Последнее закрытие: {k[-1].c} {global_val_nom}'
                        msg += f'\n3. Количество акций: {j.issue_size} шт.'
                        try:
                            reg_msg()
                            bot.send_message(message.chat.id, msg)
                        except Exception as e:
                            telega_error (e)

def calc_rez(message):
        msg = ''
        global global_options
        pos_qt = 1
        avrg = message.text
        stop = global_options['pos_cl_stop']
        terget = global_options['pos_cl_target']
        global_options['pos_cl_avg'] = avrg  # сохраняем среднюю

        try:
            terget_var = float(terget)
            stop_var = float(stop)
            avrg_var = float(avrg)
            pos_qt_var = float(pos_qt)

        except ValueError:
            reg_msg()
            bot.send_message(message.from_user.id, "ОШИБКА! Это неправильный ввод. Необходимо число.")

        if terget_var > avrg_var:
            # лонг позиция
            targ_clc_pr = round((terget_var - avrg_var) / avrg_var * 100, 2)  # расчет в процентах
            stop_clc_pr = round((stop_var - avrg_var) / avrg_var * 100, 2)  # расчет стопа в процентах
            targ_clc = round(terget_var - avrg_var, 2)  # расчет абс значений
            stop_clc = round(stop_var - avrg_var, 2)
        else:
            # шорт позиция
            targ_clc_pr = round((avrg_var - terget_var) / avrg_var * 100, 2)  # расчет в процентах
            stop_clc_pr = round((avrg_var - stop_var) / avrg_var * 100, 2)  # расчет стопа в процентах
            targ_clc = round(avrg_var - terget_var, 2)  # расчет абс значений
            stop_clc = round(avrg_var - stop_var, 2)
        pos_q = pos_qt_var * avrg_var

        msg += f'Цель: {terget}  {targ_clc_pr}%  {targ_clc}\n'
        msg += f'Средняя: {avrg}\n'
        msg += f'Стоп: {stop}  {stop_clc_pr}%  {stop_clc}\n'
        reg_msg()
        bot.send_message(message.from_user.id, msg)

def get_avrg(message):
    global global_options
    stop = message.text
    global_options['pos_cl_stop'] = stop  # сохраняем стоп
    bot.send_message(message.from_user.id, f'Средняя:')
    bot.register_next_step_handler(message, calc_rez)


# Расчет позиции функции
def calc_pos2(message):
    global global_options
    # в этой переменной цель
    global_options['pos_cl_target'] = message.text  # в этой переменной цель
    try:
        reg_msg()
        bot.send_message(message.from_user.id, f'Какой Стоп?')
        reg_msg()
        bot.register_next_step_handler(message, get_avrg)
    except Exception as e:
        telega_error (e)

def create_bot():
    # Создаем экземпляр бота
    global bot, G_VALID_BOT
    print(f'Создаем экземпляр бота {G_VALID_BOT}')
    bot = telebot.TeleBot(G_VALID_BOT, num_threads=5)
    # Настраиваем комманды
    # Удаляем старые   
    try:
        print('Удалаяем команды бота')
        reg_msg()
        bot.delete_my_commands(scope=None, language_code=None)
    except Exception as e:
        telega_error (e)
    # Задаем новые команды
    try:
        print('Устанавливаем команды бота')
        reg_msg()
        bot.set_my_commands(
            commands=[
                telebot.types.BotCommand("/menu", "стартовое меню"),
                telebot.types.BotCommand("/begin", "запуск анализа акций"),
                telebot.types.BotCommand("/options", "настройки анализа акций"),
                telebot.types.BotCommand("/hi_low", "взлеты и падения в акциях"),
                telebot.types.BotCommand("/start", "информация о пользователе"),
                telebot.types.BotCommand("/show_go", "размер ГО для фьючерсов"),
                telebot.types.BotCommand("/stoks_year_23_24", "изм. 23 к 24 году акции"),
                telebot.types.BotCommand("/stoks_year_22_23", "изм. 22 к 23 году"),
                telebot.types.BotCommand("/stoks_year_21_22", "изм. 21 к 22 году"),
                telebot.types.BotCommand("/show_stoks_year", " все изм. 21 к 22 году, 22 к 23 году"),
                telebot.types.BotCommand("/calc", "расчет позиции")
                # telebot.types.BotCommand("/help_adv", "доп. команды")                              
            ]
        )
    except Exception as e:
        telega_error (e)

    # Функция, обрабатывающая команду /start, т.е. при первом старте бота
    @bot.message_handler(commands=["start"])
    def start(message: telebot.types.Message):
        user_id = message.from_user.id
        user_fist_name = message.from_user.first_name
        user_username = message.from_user.username
        msg_chat_id = message.chat.id
        try:
            reg_msg()
            bot.send_message(message.chat.id, f'Данные пользователя:'
                                            f'\n_user_id = {user_id}'
                                            f'\n_fist_name = {user_fist_name}'
                                            f'\n_username = {user_username}'
                                            f'\n_chat_id = {msg_chat_id}')
            cmd = bot.get_my_commands(scope=None, language_code=None)
        except Exception as e:
                    telega_error (e)
        cmd_lst = [[c.command, c.description] for c in cmd]
        print(cmd_lst)
        msg = 'Команды бота:\n'
        for c in cmd_lst:
            msg += f'/{c[0]}  {c[1]}\n'
        try:
            reg_msg()
            bot.send_message(message.chat.id, msg)
        except Exception as e:
            telega_error (e)
       
        if int(user_id) != int(global_set_from_orders['user_id']):
            try:
                bot.send_message(user_id, f'detect:'
                                          f'Данные пользователя:'
                                          f'\n_user_id = {user_id}'
                                          f'\n_fist_name = {user_fist_name}'
                                          f'\n_username = {user_username}')
            except Exception as e:
                telega_error (e)

    # Функция, обрабатывающая команду анализа изменения акций за год
    @bot.message_handler(commands=["show_stoks_year"])
    def show_stoks_year(message):
        ID_ch = message.chat.id
        # show_stoks_year_fun(bot,ID_ch,2023, 2024)
        show_stoks_year_fun(bot,ID_ch,2022, 2023)
        show_stoks_year_fun(bot,ID_ch,2021, 2022)        
    
    @bot.message_handler(commands=["stoks_year_23_24"])
    def stoks_year_23_24(message):
        ID_ch = message.chat.id
        show_stoks_year_fun(bot,ID_ch,2023, 2024)
    
    @bot.message_handler(commands=["stoks_year_22_23"])
    def stoks_year_22_23(message):
        ID_ch = message.chat.id
        show_stoks_year_fun(bot,ID_ch,2022, 2023)
    
    @bot.message_handler(commands=["stoks_year_21_22"])
    def stoks_year_21_22(message):
        ID_ch = message.chat.id
        show_stoks_year_fun(bot,ID_ch,2021, 2022)
    
    # Функция, обрабатывающая команду /show_GO
    # информации о ГО фьючерсов
    @bot.message_handler(commands=["show_go"])
    def show_go (message):
        '''
        # информации о ГО фьючерсов
        '''
        # подключаемся к платформе
        global global_f_opt, g_df_p
        ID_ch = message.chat.id
        print('\nКОМАНДА информации о ГО фьючерсов')
        # try:
        #     reg_msg()
        #     bot.send_message(ID_ch, "Информация о ГО фьючерсов", disable_notification=True)
        # except Exception as e:
        #     telega_error (e)

        print_date_time_now()

        print('Подключаемся к Tinkoff для чтения фьючерсов')
        with Client(TOKEN) as client:
            print('Подключились к Tinkoff')
            # загружаем список фьючерсов
            futures_instr = []  # список фьючерсов
            flag_r = True  # повторять попытки загрузки пока не получиться загрузить
            print('Загрузка списка фьючерсов')
            while flag_r:
                try:
                    futures = client.instruments.futures(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)
                    flag_r = False  # получилось загрузить и поэтому повтора не требуется
                    # требуемый список фьючерсов
                    full_futures_instr = futures.instruments
                    print(f'Всего фьючерсов в списке: {len(full_futures_instr)}')
                except Exception as ebx:
                    print(datetime.now(timezone.utc).astimezone())
                    print('\nВОЗНИКЛА ОШИБКА загрузки списка фьючерсов от платформы Tinkoff при обработке команды /show_go. Цикл будет бесконечен пока не получится подключиться.')
                    print(ebx)
                    print()
                    try:
                        reg_msg()
                        bot.send_message(ID_ch, text=f"ВОЗНИКЛА ОШИБКА загрузки списка фьючерсов с платформы Tinkoff"
                                                    f"\n{ebx}"
                                                    f"\nПопробуем ещё раз загрузить")
                    except Exception as e:
                        telega_error (e)
                    flag_r = True
            
            # выбор только текущих контрактов
            activ_contr_name = global_f_opt['activ_contr_name']
            print(f'Имя текущих контрактов: {activ_contr_name}')
            try:
                reg_msg()
                msg = "Информация о ГО фьючерсов\n"
                msg += f'Всего загружено фьючерсов: {len(full_futures_instr)}\n'
                msg += f'Имя текущих контрактов: {activ_contr_name}\n'
                bot.send_message(ID_ch, msg, disable_notification=True)
            except Exception as e:
                telega_error (e)
            future_find_dict = []  # набор фьючерсов в виде списка  словарей
            future_find_obj = []  # набор фьючерсов в виде списка объектов
            future_mrg_dict = []  # набор информации о марже фьючерсов в виде словаря
            future_mrg_obj = []
            lp_FIGi = []
            for i in full_futures_instr:
                # включаем в список только активные фьючерсы
                if activ_contr_name in i.name:
                    future_find_dict.append({'figi': i.figi, 'ticker': i.ticker, 'name': i.name})
                    future_find_obj.append(i)
                    lp_FIGi.append(i.figi)
                    # получаем описание о ГО фьючерса
                    # https://tinkoff.github.io/investAPI/instruments/#getfuturesmarginrequest
                    f_inf = client.instruments.get_futures_margin(figi=i.figi)
                    future_mrg_dict.append({'name_f': i.name,  # 0
                                            'ticker': i.ticker,  # 1
                                            'figi': i.figi,  # 2
                                            'margin_buy': cast_money(f_inf.initial_margin_on_buy),  # 3 Размер ГО Лонг
                                            'margin_shell': cast_money(f_inf.initial_margin_on_sell),  # 4 ГО шорт
                                            'margin_cur': f_inf.initial_margin_on_buy.currency,  # 5 валюта
                                            'step_price_pt': q_to_var(f_inf.min_price_increment),  # 6 шаг цены
                                            # 7 стоимость шага
                                            'step_price': q_to_var(f_inf.min_price_increment_amount),
                                            #8 стоимость пункта цены. На это значение надо упножать значение в пунктах
                                            'step_cost_curr': q_to_var(f_inf.min_price_increment_amount) /
                                                              q_to_var(f_inf.min_price_increment),
                                            'asset_type': i.asset_type,  # 9
                                            'link': f'https://www.tinkoff.ru/invest/futures/{i.ticker}'  # 10
                                            })
                    future_mrg_obj.append(f_inf)
            try:
                reg_msg()
                bot.send_message(ID_ch, f'Фьючерсов с именем {activ_contr_name} после фильтрации: {len(future_find_obj)}', disable_notification=True)
            except Exception as e:
                telega_error (e)
            df_f_mrg = pd.DataFrame(future_mrg_dict)
            # добавить реакцию на превышение лимитов запросов с минуту
            lps = client.market_data.get_last_prices(figi=lp_FIGi).last_prices  # последняя цена
            last_pr_dict = []
            for p in lps:
                last_pr_dict.append({'figi': p.figi,
                                     'l_price': q_to_var(p.price),
                                     'instr_ID': p.instrument_uid
                                     })
            df_lp_f = pd.DataFrame(last_pr_dict)
            # https://pandas.pydata.org/pandas-docs/stable/user_guide/merging.html#database-style-dataframe-or-named-series-joining-merging
            df_f_mrg = df_f_mrg.merge(df_lp_f, how='right', on='figi')
            df_f_mrg_sort = df_f_mrg.sort_values(by='margin_buy', ascending=True)
            df_f_mrg_sort['l_price_rub']=round(df_f_mrg_sort.l_price*df_f_mrg_sort.step_cost_curr, 2)
            # расчет во всколько раз ГО меньще цены (плечо) 
            df_f_mrg_sort['x_f']=round(df_f_mrg_sort.l_price_rub/df_f_mrg_sort.margin_buy, 2)
            df_xf = df_f_mrg_sort.sort_values(by = 'x_f', ascending=False)
            # раделяем списки для вывода по типам фьючерсов 
            df_sec=df_f_mrg_sort.loc[df_f_mrg_sort['asset_type'] == 'TYPE_SECURITY']
            df_indx=df_f_mrg_sort.loc[df_f_mrg_sort['asset_type'] == 'TYPE_INDEX']
            df_cur=df_f_mrg_sort.loc[df_f_mrg_sort['asset_type'] == 'TYPE_CURRENCY']
            df_com=df_f_mrg_sort.loc[df_f_mrg_sort['asset_type'] == 'TYPE_COMMODITY']
            # выполнение сортировки по величине ГО на покупку, от меньшего к большему
            df_sec = df_sec.sort_values(by='margin_buy', ascending=True)
            df_indx = df_indx.sort_values(by='margin_buy', ascending=True)
            df_cur = df_cur.sort_values(by='margin_buy', ascending=True)
            df_com = df_com.sort_values(by='margin_buy', ascending=True)
             # выполнение сортировки по величине соотношения ГО к цене, от большего к меньшему
            df_sec = df_sec.sort_values(by='x_f', ascending=False)
            df_indx = df_indx.sort_values(by='x_f', ascending=False)
            df_cur = df_cur.sort_values(by='x_f', ascending=False)
            df_com = df_com.sort_values(by='x_f', ascending=False)

            df_f_mrg_sort.to_excel('df_f_MRG.xlsx')
            try:
                reg_msg()
                bot.send_document(ID_ch, document=open('df_f_MRG.xlsx', 'rb'), disable_notification=True)
            except Exception as e:
                telega_error (e)
            #  20 самых рискованных            
            len_df = df_xf.shape[0]
            if len_df > 15:
                len_df =15
            msg = f'Перечень из {len_df} наиболее рискованных фьючерсов.'
            msg = f'\nСоотношение ГО к цене, от большего к меньшего.\n'
            for m in range(len_df):
                msg += f'\n[{m}]{df_xf.iloc[m, 0]}' \
                       f'\nГО меньше цены, раз: {df_xf.iloc[m, 14]} ' \
                       f'\n{df_xf.iloc[m, 10]}'
                msg += f'\n'
            print(msg)
            # выдача сообщений о результатах обработки не более 4000 символов за раз
            for message1 in util.smart_split(msg, 4000):
                try:
                    reg_msg()
                    bot.send_message(ID_ch, message1, disable_web_page_preview=True, disable_notification=True)
                except Exception as e:
                    telega_error (e)

            # Фьючерсы на акции
            msg = 'Результат:  \n#ГО_фьючерсы_на_акции\n'\
                    f'Фьючерсы на акции {df_sec.shape[0]} шт.:\n'\
                    '(сортировка по величине соотношения ГО к цене, от большего к меньшему)\n\n'
            # предусмотреть сортировку по либо по размеру ГО, либо по размеру коэффициента
            for m in range(df_sec.shape[0]):
                msg += f'\n{df_sec.iloc[m, 0]}' \
                       f'\n{df_sec.iloc[m, 1]}   {df_sec.iloc[m, 2]}' \
                       f'\nПосл.цена:  {df_sec.iloc[m, 13]}   {df_sec.iloc[m, 5]}' \
                       f'\nРазмер ГО buy: {df_sec.iloc[m, 3]} {df_sec.iloc[m, 5]}' \
                       f'\nГО меньше цены, раз: {df_sec.iloc[m, 14]} ' \
                       f'\nСтоимость пункта: {round(df_sec.iloc[m, 8], 2)} {df_sec.iloc[m, 5]}' \
                       f'\n{df_sec.iloc[m, 10]}'
                msg += f'\n'
            msg += '\n#ГО_фьючерсы_на_акции'\
                    f'\nФьючерсы на акции {df_sec.shape[0]} шт.'\
                     '\n------------------------------------------'
            print(msg)
            # выдача сообщений о результатах обработки не более 4000 символов за раз
            for message1 in util.smart_split(msg, 4000):
                try:
                    reg_msg()
                    bot.send_message(ID_ch, message1, disable_web_page_preview=True, disable_notification=True)
                except Exception as e:
                    telega_error (e)
            
            # Фьючерсы на индексы
            msg = 'Результат:  \n#ГО_фьючерсы_на_индексы'\
                    f'\nФьючерсы на индексы {df_indx.shape[0]} шт.:\n'\
                    '(сортировка по величине соотношения ГО к цене, от большего к меньшему)\n\n'
            for m in range(df_indx.shape[0]):
                msg += f'\n{df_indx.iloc[m, 0]}' \
                       f'\n{df_indx.iloc[m, 1]}   {df_indx.iloc[m, 2]}' \
                       f'\nПосл.цена:  {df_indx.iloc[m, 13]}   {df_indx.iloc[m, 5]}' \
                       f'\nРазмер ГО buy: {df_indx.iloc[m, 3]} {df_indx.iloc[m, 5]}' \
                       f'\nГО меньше цены, раз: {df_indx.iloc[m, 14]} ' \
                       f'\nСтоимость пункта: {round(df_indx.iloc[m, 8], 2)} {df_indx.iloc[m, 5]}' \
                       f'\nТип:  {df_indx.iloc[m, 9]}' \
                       f'\n{df_indx.iloc[m, 10]}'
                msg += f'\n'
            msg += '\n#ГО_фьючерсы_на_индексы'\
                    f'\nФьючерсы на индексы {df_indx.shape[0]} шт.'\
                     '\n------------------------------------------'
            print(msg)
            # выдача сообщений о результатах обработки не более 4000 символов за раз
            for message1 in util.smart_split(msg, 4000):
                try:
                    reg_msg()
                    bot.send_message(ID_ch, message1, disable_web_page_preview=True, disable_notification=True)
                except Exception as e:
                    telega_error (e)
            
            #  Фьючерсы на валюты
            msg = 'Результат:  \n#ГО_фьючерсы_на_валюты'\
                    f'\nФьючерсы на валюты {df_cur.shape[0]} шт.:\n'\
                    '(сортировка по величине соотношения ГО к цене, от большего к меньшему)\n\n'
            for m in range(df_cur.shape[0]):
                msg += f'\n{df_cur.iloc[m, 0]}' \
                       f'\n{df_cur.iloc[m, 1]}   {df_cur.iloc[m, 2]}' \
                       f'\nПосл.цена:  {df_cur.iloc[m, 13]}   {df_cur.iloc[m, 5]}' \
                       f'\nРазмер ГО buy: {df_cur.iloc[m, 3]} {df_cur.iloc[m, 5]}' \
                       f'\nГО меньше цены, раз: {df_cur.iloc[m, 14]} ' \
                       f'\nСтоимость пункта: {round(df_cur.iloc[m, 8], 2)} {df_cur.iloc[m, 5]}' \
                       f'\nТип:  {df_cur.iloc[m, 9]}' \
                       f'\n{df_cur.iloc[m, 10]}'
                msg += f'\n'
            msg += '\n#ГО_фьючерсы_на_валюты'\
                    f'\nФьючерсы на валюты {df_cur.shape[0]} шт.'\
                     '\n------------------------------------------'
            print(msg)
            # выдача сообщений о результатах обработки не более 4000 символов за раз
            for message1 in util.smart_split(msg, 4000):
                try:
                    reg_msg()
                    bot.send_message(ID_ch, message1, disable_web_page_preview=True, disable_notification=True)
                except Exception as e:
                    telega_error (e)
            
            # Фьючерсы на материалы
            msg = 'Результат:  \n#ГО_фьючерсы_на_комодити'\
                    f'\nФьючерсы на комодити {df_com.shape[0]} шт.:\n'\
                    '(сортировка по величине соотношения ГО к цене, от большего к меньшему)\n\n'
            for m in range(df_com.shape[0]):
                msg += f'\n{df_com.iloc[m, 0]}' \
                       f'\n{df_com.iloc[m, 1]}   {df_com.iloc[m, 2]}' \
                       f'\nПосл.цена:  {df_com.iloc[m, 13]}   {df_com.iloc[m, 5]}' \
                       f'\nРазмер ГО buy: {df_com.iloc[m, 3]} {df_com.iloc[m, 5]}' \
                       f'\nГО меньше цены, раз: {df_com.iloc[m, 14]} ' \
                       f'\nСтоимость пункта: {round(df_com.iloc[m, 8], 2)} {df_com.iloc[m, 5]}' \
                       f'\nТип:  {df_com.iloc[m, 9]}' \
                       f'\n{df_com.iloc[m, 10]}'
                msg += f'\n'
            msg += '\n#ГО_фьючерсы_на_комодити'\
                    f'\nФьючерсы на комодити {df_com.shape[0]} шт.'\
                     '\n------------------------------------------'
            print(msg)
            # выдача сообщений о результатах обработки не более 4000 символов за раз
            for message1 in util.smart_split(msg, 4000):
                try:
                    reg_msg()
                    bot.send_message(ID_ch, message1, disable_web_page_preview=True, disable_notification=True)
                except Exception as e:
                    telega_error (e)
            # выдача финального сообщения с тыгами для навигации
            msg = 'ТЭГИ:\n\n'
            msg += '#ГО_фьючерсы_на_акции\n\n'\
                '#ГО_фьючерсы_на_индексы\n\n'\
                '#ГО_фьючерсы_на_валюты\n\n'\
                '#ГО_фьючерсы_на_комодити'
            try:
                reg_msg()
                bot.send_message(ID_ch, msg, disable_web_page_preview=True, disable_notification=True)
            except Exception as e:
                    telega_error (e)

    # Функция, обрабатывающая команду /help_adv
    @bot.message_handler(commands=["help_adv"])
    def help_adv(message):
        msg = ''
        msg += f'КНОПКИ:\n'
        msg += f'f1 - фьючерсы, начисления за день\n'
        msg += f'f2 - отчет по позиции сбера или текущей при отсутствии позиции\n'
        msg += f'f3 - список текущих позиций\n'
        msg += f's1 - показать ссылки на мосбиржу для всех фьючерсов   ссылки на тынкофф тоже есть\n'
        msg += f'333 - показать стакан по фьючерсу на СБЕР\n'
        msg += f'F8 - безостановочный отчет о цене сбера\n'
        msg += f'by5o - покупка одного фьючерса СБЕР по рынку\n'
        msg += f'sl5o - продажа одного фьючерса СБЕР по рынку\n'
        msg += f'c_Sp_f5 - закрыть ВСЮ шорт позицию по фьючам на СБЕР по рынку\n'
        try:
            reg_msg()
            bot.send_message(message.chat.id, msg)
        except Exception as e:
                telega_error (e)

    # Функция, обрабатывающая команду /begin
    @bot.message_handler(commands=["begin"])
    def begin(m: telebot.types.Message, res=False):
        '''
        m +  обзательный параметр;
        res - неиспользуется;
        end_time - не используется;
        it1 - не используется
        '''
        global global_f_opt, glodal_inp_interval, global_interval_load, global_interval_load_s, g_df, m1, g_df_p
        global global_max_range, global_inp_var, global_val_nom, global_bag_of_stocks, global_finaly_bag_of_stocks
        global global_options, global_all_list, all_list, g_full_list_sh2, global_list_sel3, global_list_sel2
        global_in_progress_state = True
        subprocess.call("TASKKILL /f  /IM  CHROME.EXE")
        subprocess.call("TASKKILL /f  /IM  CHROMEDRIVER.EXE")
        user_id = m.from_user.id
        user_fist_name = m.from_user.first_name
        user_username = m.from_user.username

        if int(user_id) != int(global_set_from_orders['user_id']):
            try:
                reg_msg()
                bot.send_message(user_id, f'detect:'
                                          f'Данные пользователя:'
                                          f'\n_user_id = {user_id}'
                                          f'\n_fist_name = {user_fist_name}'
                                          f'\n_username = {user_username}')
            except Exception as e:
                telega_error (e)

        #    пишем приветствие
        try:
            reg_msg()
            bot.send_message(m.chat.id, '🤖', disable_notification=True)
        except Exception as e:
            telega_error (e)
        # Медленно.
        # получаем список всех акций через APIv2
        try:
            full_list_sh2 = gRPC_Load_List()
            g_full_list_sh2 = full_list_sh2.copy()
        except Exception as e:
            print(datetime.now(timezone.utc).astimezone())
            print('\nВОЗНИКЛА ОШИБКА  gRPC_Load_List()')
            print(e)
            print()

        # выборка акций по секторам
        list_sectors = []
        for im in g_full_list_sh2:
            if im.sector not in list_sectors:
                list_sectors.append(im.sector)
        list_sectors.sort()
        # print()
        # print('Сектора:')
        # for itm in list_sectors:
        #     print(itm)
        # print(f"Всего: {len(list_sectors)}")
        # print()
        # рассчитываем дату отстающую в глубину от текущей даты и времени
        curr_time = datetime.now(timezone.utc).astimezone()
        end_time = curr_time
        # Расчет конечную дату до которой в глубину будет загружены бары
        # максимальное количество баров доступных для загрузки в зависимости от выбранного интервала
        depth_i = global_max_range - 2  # размер глубины
        if global_interval_load == CandleInterval.CANDLE_INTERVAL_1_MIN:
            start_time = curr_time + timedelta(minutes=-depth_i)
            # print('Интервал: 1 минута')
        elif global_interval_load == CandleInterval.CANDLE_INTERVAL_2_MIN:
            start_time = curr_time + timedelta(minutes=-depth_i * 2)
            # print('Интервал: 2 минуты')
        elif global_interval_load == CandleInterval.CANDLE_INTERVAL_3_MIN:
            start_time = curr_time + timedelta(minutes=-depth_i * 3)
            # print('Интервал: 3 минуты')
        elif global_interval_load == CandleInterval.CANDLE_INTERVAL_5_MIN:
            start_time = curr_time + timedelta(minutes=-depth_i * 5)
            # print('Интервал: 5 минут')
        elif global_interval_load == CandleInterval.CANDLE_INTERVAL_10_MIN:
            start_time = curr_time + timedelta(minutes=-depth_i * 10)
            # print('Интервал: 10 минут')
        elif global_interval_load == CandleInterval.CANDLE_INTERVAL_15_MIN:
            start_time = curr_time + timedelta(minutes=-depth_i * 15)
            # print('Интервал: 15 минут')
        elif global_interval_load == CandleInterval.CANDLE_INTERVAL_30_MIN:
            start_time = curr_time + timedelta(minutes=-depth_i * 30)
            # print('Интервал: 30 минут')
        elif global_interval_load == CandleInterval.CANDLE_INTERVAL_HOUR:
            start_time = curr_time + timedelta(hours=-depth_i)
            # print('Интервал: 1 час')
        elif global_interval_load == CandleInterval.CANDLE_INTERVAL_DAY:
            start_time = curr_time + timedelta(days=-depth_i)
            # print('Интервал: 1 день')
        elif global_interval_load == CandleInterval.CANDLE_INTERVAL_WEEK:
            start_time = curr_time + timedelta(weeks=-depth_i)
            # print('Интервал: 1 неделя')
        elif global_interval_load == CandleInterval.CANDLE_INTERVAL_MONTH:
            start_time = curr_time + timedelta(weeks=-depth_i * 4)
            # print('Интервал: 1 месяц')
        else:
            start_time = curr_time + timedelta(weeks=-depth_i)
            # print('Интервал: 1 неделя')

        # Приветственные сообщения
        start_time_s = datetime.strftime(start_time, '%d.%m.%Y') + "   " + datetime.strftime(start_time, '%H:%M:%S')
        end_time_s = datetime.strftime(end_time, '%d.%m.%Y') + "   " + datetime.strftime(end_time, '%H:%M:%S')
        msg = ''
        msg = f'Запускаем загрузку и обработку:\n'
        msg += f'Интервал:   [{global_interval_load_s} к {global_interval_load_s}]'
        msg += f'\nКоличество акций:   [{len(global_finaly_bag_of_stocks)}]\nноминированных в:   [{global_val_nom}]'
        msg += f'\n\nначальная дата загрузки котировок:\n'
        msg += f'    от {start_time_s}\n\n'
        msg += f'конечная дата загрузки котировок:\n'
        msg += f'    до {end_time_s}'

        # инициализация кнопок
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        b1 = types.KeyboardButton("stoks")
        b2 = types.KeyboardButton("futures")
        markup.add(b1, b2)
        try:
            reg_msg()
            bot.send_message(m.chat.id, msg, reply_markup=markup,disable_notification=True)
        except Exception as e:
            telega_error (e)
        # попытка организовать повторения цикла загрузки и обработки каждые 30 мин
        flag_loop = True

        # ===============================ОСНОВНОЙ ЦИКЛ ЗАГРУЗКИ И ОБРАБОТКИ+++++++++++++++++++
        while flag_loop:
            # ФУНКЦИЯ загрузки исторических свечей
            # Вход
            # список акции для загрузки, Начало загрузки, окончание загрузки, интервал загрузки
            # Выход
            # DF с историческими свечами
            start_count_sec = time.time()  # счетчик секунд
            print('Запускаем загрузку и обработку:')
            print(f' Дата и время начала загрузки исторических баров:\n от {end_time}')
            print(f' Дата и время окончания загрузки исторических баров:\n до {start_time}')
            print(f' Интервал: {global_interval_load_s}')
            print(f' Количество акций: {len(global_finaly_bag_of_stocks)} ')

            # Загрузка информации.
            # Начинаем ожидать начало минуты
            start1 = datetime.now(timezone.utc).astimezone()
            scnd1 = start1.second
            if len(global_finaly_bag_of_stocks) > 239:
                try:
                    reg_msg()
                    label1 = bot.send_message(m.chat.id,
                                            'Ограничение платформы ТинькоффAPI:'
                                            '\n240 запросов в минуту .'
                                            '\nОжидайте начала минуты.....',
                                            disable_notification=True)
                except Exception as e:
                    telega_error (e)
                print('Ожидание, до начала следующей минуты, сек:', round(60 - scnd1, 0))
                timelist = range(60 - scnd1)
                bar = Bar(' ожидание', max=len(timelist))

                keyboard = types.InlineKeyboardMarkup(row_width=2)
                b1 = types.InlineKeyboardButton(text=f'-', callback_data='test')  # пишем текст на кнопке
                keyboard.add(b1)
                try:
                    reg_msg()
                    label2 = bot.send_message(m.chat.id,
                                          text=f'ОЖИДАНИЕ: {len(timelist)} сек.',
                                          disable_notification=True,
                                          reply_markup=keyboard)
                except Exception as e:
                    telega_error (e)
                for item in timelist:
                    bar.next()
                    try:
                        reg_msg()
                        bot.send_chat_action(m.chat.id, action='typing')
                    except Exception as e:
                        telega_error (e)
                    keyboard = types.InlineKeyboardMarkup(row_width=2)
                    b1 = types.InlineKeyboardButton(text=f'{item + 1}', callback_data='test')
                    keyboard.add(b1)
                    try:
                        reg_msg()
                        bot.edit_message_text(chat_id=m.chat.id,
                                              message_id=label2.id,
                                              text=f'ОЖИДАНИЕ: {len(timelist)} сек.',
                                              reply_markup=keyboard)
                    except Exception as e:
                        print('error bot.edit_message_text')
                        print(e)
                        telega_error (e)
                    time.sleep(1)
                bar.finish()
            else:
                try:
                    reg_msg()
                    label1 = bot.send_message(m.chat.id, 'Загрузка.....', disable_notification=True)
                except Exception as e:
                    telega_error (e)

            # дата и время начала работы по загрузке информации
            total_start = datetime.now(timezone.utc).astimezone()
            print('\nВремя начала загрузки информации: ', datetime.strftime(total_start, '%H:%M:%S'))
            # Cекундомер начала очередной партии запросов.
            # Одна партия запросов не более 249 в минуту
            start = time.time()
            start1 = datetime.now(timezone.utc).astimezone()  # дата и время начала очередного сеанса запросов
            print('\nВремя начала очередной партии запросов: ', datetime.strftime(start1, '%H:%M:%S'))
            # прогресс бар выполнения
            stoks_status_bar = IncrementalBar(' ЗАГРУЗКА', max=len(global_finaly_bag_of_stocks))
            it1 = 0  # счетчик загруженных записей в текущей партии запросов
            it2 = 0  # счетчик уже загруженных записей (общий счетчик запросов)
            # ОСНОВНОЙ ЦИКЛ
            #
            all_list = []  # список со всеми барами для обрабатываемых тикеров
            start_show_proc = time.time()  # начало секундомера отображения статуса бота
            msg_udpt_time_start = time.time()  # начало очередного периода обновления сообщения о загрузке
            try:
                reg_msg()
                bot.send_chat_action(m.chat.id, action='upload_document')
                bot.edit_message_text(chat_id=m.chat.id, message_id=label1.id,
                                  text=f'\nЗагружено:   {it2} stocks.'
                                       f'\nОсталось:   {len(global_finaly_bag_of_stocks)} stocks.')
            except Exception as e:
                    telega_error (e)
            with Client(TOKEN) as client_g:
                for fav_stock in global_finaly_bag_of_stocks:              

                    # Проверка и отработка ограничения количества запросов
                    # /market	240 запросов на пользователя.
                    # Интервал ограничения 1 минута
                    # Останавливаемся на 239 запросе
                    if it1 == 239:
                        # время окончания запросов
                        end = time.time()
                        # сколько времени потребовалось на отработку запросов в секундах
                        delta = end - start
                        print('\nОстановка, прошло 239 запросов')
                        print(' Время начала этой партии запросов: ', datetime.strftime(start1, '%H:%M:%S'))
                        # дата и время остановки запросов
                        end1 = datetime.now(timezone.utc).astimezone()
                        print(' Время остановки этой партии запросов: ', datetime.strftime(end1, '%H:%M:%S'))
                        print(' Прошло, сек: ', round(delta, 0))
                        print(' До конца минуты осталось, сек:',
                            round(60 - datetime.now(timezone.utc).astimezone().second, 0))
                        print(' Всего загрузили:', it2, 'записей')
                        
                        # Пишем на label1 что осталось
                        try:
                            reg_msg()
                            bot.edit_message_text(chat_id=m.chat.id, message_id=label1.id,
                                                text=f'\nЗагружено:   {it2} stocks.'
                                                    f'\nОсталось:   {len(global_finaly_bag_of_stocks) - it2} stocks.')
                            bot.send_chat_action(m.chat.id, action='typing')
                        except Exception as e:
                            print('error bot.edit_message_text')
                            print(e)
                            telega_error (e)
                        
                        # Пауза. Ограничение минута, но для надежности после 249 запроса ждем 2 минуты
                        # delta время загрузки баров в секундах
                        if delta > 110:
                            delta2 = 120
                        else:
                            delta2 = 120 - delta

                        if delta2 > 0:
                            print(' Включаем сон, сек: ', int(round(delta2, 0)))
                            timelist = range(int(round(delta2, 0)))
                            # индикатор времени ожидания после каждой порции загрузки
                            timebar = Bar(' ожидание', max=len(timelist))
                            keyboard = types.InlineKeyboardMarkup(row_width=2)
                            b1 = types.InlineKeyboardButton(text=f'-', callback_data='test')
                            keyboard.add(b1)
                            try:
                                reg_msg()
                                bot.edit_message_text(chat_id=m.chat.id,
                                                message_id=label2.id,
                                                text=f'ОЖИДАНИЕ: {len(timelist)} сек.',
                                                reply_markup=keyboard
                                                )
                            except Exception as e:
                                telega_error (e)
                            for item in timelist:
                                timebar.next()
                                keyboard = types.InlineKeyboardMarkup(row_width=2)
                                b1 = types.InlineKeyboardButton(text=f'{item + 1}', callback_data='test')
                                keyboard.add(b1)
                                try:
                                    reg_msg()
                                    bot.send_chat_action(m.chat.id, action='typing')
                                    bot.edit_message_text(chat_id=m.chat.id,
                                                        message_id=label2.id,
                                                        text=f'ОЖИДАНИЕ: {len(timelist)} сек.',
                                                        reply_markup=keyboard)
                                except Exception as e:
                                    telega_error (e)
                                time.sleep(1)
                            timebar.finish()
                            keyboard = types.InlineKeyboardMarkup(row_width=2)
                            b1 = types.InlineKeyboardButton(text=f'-', callback_data='test')
                            keyboard.add(b1)
                            try:
                                reg_msg()
                                bot.edit_message_text(chat_id=m.chat.id,
                                                message_id=label2.id,
                                                text=f'ЗАГРУЗКА....',
                                                reply_markup=keyboard)
                            except Exception as e:
                                telega_error (e)
                        # после сна обнуляем счетчик запросов (it1), который не должен превышать 239 запросов в минуту
                        it1 = 0
                        # запускаем таймер очередной партии запросов
                        start = time.time()  # запускает заново таймер и делаем метку времени запуска таймера
                        start1 = datetime.now(timezone.utc).astimezone()
                        print('\nВремя начала очередной партии запросов: ',
                            datetime.strftime(start1, '%H:%M:%S'))

                    # запускаем загрузку в режиме отработки исключений из-за ограничений 249 запросов в минуту
                    try:
                        # загрузку заданных интервалов
                        # старые тикеры не смотреть иначе ошибка
                        if not ('old' in fav_stock.ticker) and not (
                                fav_stock.figi == 'BBG000PRJCX9') and not (
                                fav_stock.figi =='BBG000H6HNW3') and not ( 
                                fav_stock.figi == 'BBG000CMRVH1') and not (
                                fav_stock.figi =="BBG000QQPXZ5") and not(
                                fav_stock.figi =="BBG00HT224Q7"):
                            # inst_s = client.get_market_candles(fav_stock.figi, start_time, end_time, global_interval_load)
                            inst_s = client_g.market_data.get_candles(figi=fav_stock.figi, from_=start_time, to=end_time,interval=global_interval_load)
                        stoks_status_bar.next()
                        # раз в 5сек отправляем статус обработки
                        cur_show_proc = time.time() - start_show_proc
                        if cur_show_proc > 5:
                            try:
                                reg_msg()
                                bot.send_chat_action(m.chat.id, action='upload_document')
                            except Exception as e:
                                telega_error (e)
                            start_show_proc = time.time()

                        # формируем список с загруженными барами
                        li1 = []
                        if len(inst_s.candles) != 0:
                            li1 = inst_s.candles
                            li1.insert(0, fav_stock)
                            # print (f' {li1[0].ticker}')
            
                            ######ФОРМИИРОВАНИЕ СПИСКА АКЦИЙ для обработки!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!11
                            all_list.append(li1)

                            # all_list.insert (0,fav_stock)

                        #  увеличиваем общий счетчик уже загруженных записей
                        it2 += 1
                        # увеличиваем счетчик запросов имеющий предел 239 в минуту
                        it1 += 1
                        # в чате пишем сколько загрузили и сколько осталось раз в две сек
                        msg_udpt_time = time.time() - msg_udpt_time_start
                        if msg_udpt_time > 1:
                            try:
                                reg_msg()
                                bot.edit_message_text(chat_id=m.chat.id, message_id=label1.id,
                                                text=f'\nЗагружено:   {it2} stoks.'
                                                    f'\nОсталось:   {len(global_finaly_bag_of_stocks) - it2} stoks.')
                            except Exception as e:
                                telega_error (e)
                            msg_udpt_time_start = time.time()

                    # обработка исключения связанного с превышением запросов
                    except ti.exceptions.TooManyRequestsError:
                        #  проблему лечим ожиданием
                        end = time.time()  # останавливаем секундомер
                        print("\n\nОШИБКА:Много запросов в единицу времени (TooManyRequestsError)")
                        print(' Время начала этой партии запросов: ',
                            datetime.strftime(start1, '%H:%M:%S'))
                        print(' Время окончания этой партии запросов: ',
                            datetime.strftime(datetime.now(timezone.utc).astimezone(), '%H:%M:%S'))
                        delta = end - start
                        print(' Прошло, сек: ', round(delta, 0))
                        print(' До конца минуты осталось, сек:',
                            round(60 - datetime.now(timezone.utc).astimezone().second, 0))
                        print(' Всего загрузили:', it2, 'записей')
                        print(
                            ' Включаем сон на 6 минут после возникновения исключения.'
                            '\nВозможно ограничение биржи 750 действий в 5 мин.')
                        try:
                            reg_msg()
                            label3 = bot.send_message(m.chat.id,
                                                'Включаем сон на 6 минут после возникновения исключения.'
                                                '\nВозможно ограничение биржи 750 действий программы в 5 мин.',
                                                disable_notification=True
                                                )
                        except Exception as e:
                            telega_error (e)

                        timelist = range(6 * 60)
                        timebar = Bar(' ожидание', max=len(timelist))
                        l_timelist = len(timelist)
                        keyboard = types.InlineKeyboardMarkup(row_width=2)
                        b1 = types.InlineKeyboardButton(text=f'-', callback_data='test')  # текст на кнопке
                        keyboard.add(b1)
                        try:
                            reg_msg()
                            label4 = bot.send_message(m.chat.id, text=f'ОЖИДАНИЕ: {l_timelist} сек.',
                                                    reply_markup=keyboard, disable_notification=True)
                        except Exception as e:
                            telega_error (e)
                        for item in timelist:
                            timebar.next()
                            
                            keyboard = types.InlineKeyboardMarkup(row_width=2)
                            b1 = types.InlineKeyboardButton(text=f'{item + 1}', callback_data='test')
                            keyboard.add(b1)
                            try:
                                reg_msg()
                                bot.send_chat_action(m.chat.id, action='typing')
                                reg_msg()
                                bot.edit_message_text(chat_id=m.chat.id, message_id=label4.id,
                                                    text=f'ОЖИДАНИЕ: {l_timelist} сек.', reply_markup=keyboard)
                            except Exception as e:
                                telega_error (e)
                            time.sleep(1)
                        timebar.finish()
                        try:
                            reg_msg()
                            bot.delete_message(chat_id=m.chat.id, message_id=label4.id)
                            reg_msg()
                            bot.delete_message(chat_id=m.chat.id, message_id=label3.id)
                        except Exception as e:
                            telega_error (e)
                    except Exception as e:
                        print(e, fav_stock.figi, fav_stock.ticker)
                        msg = ""
                        msg += f"{e}\n\n"
                        msg += f'{fav_stock.figi}\n{fav_stock.ticker}\n{fav_stock.name}\n start_time:{start_time}' \
                            f'\n end_time:{end_time}\n {global_interval_load}\n'
                        msg += f'https://www.tinkoff.ru/invest/stocks/{fav_stock.ticker}\n'
                        try:
                            reg_msg()
                            bot.send_message(m.chat.id,
                                        '⚡️ОШИБКА⚡️ \nЧто-то пошло не так при загрузке данных из платформы Тинькофф.\n'
                                        'Попробуйте вернуть настройки на первоначальные⚡️')
                            reg_msg()
                            bot.send_message(m.chat.id, msg, disable_web_page_preview=True)
                        except Exception as e:
                                telega_error (e)

            stoks_status_bar.finish()  # остановка прогресс бара
            # Сообщение в конце, что все загрузили
            try:
                bot.edit_message_text(chat_id=m.chat.id, message_id=label1.id,
                                      text=f'\nЗагружено:   {it2} stocks.'
                                           f'\nОсталось:   {len(global_finaly_bag_of_stocks) - it2} stocks.')
            except Exception as e:
                print('error bot.edit_message_text')
                print(e)
                telega_error (e)

            print('Загрузка окончена')
            print(' Время начала загрузки: ',
                  datetime.strftime(total_start, '%H:%M:%S'))
            print(' Время окончания загрузки: ',
                  datetime.strftime(datetime.now(timezone.utc).astimezone(), '%H:%M:%S'))
            stop_count_sec = time.time()
            delta = stop_count_sec - start_count_sec
            delta_min = delta / 60
            print(f'\n\nВсего прошло с момента запуска: {int(delta)} сек')
            print(f'в минутах с момента запуска: {int(delta_min)} мин')
            msg = 'Загрузка выполнена за: '
            if int(delta_min) < 1:
                msg += f'{int(round(delta, 0))} сек'
            else:
                msg += f'{int(delta_min)} мин'
            try:
                reg_msg()
                bot.send_message(m.chat.id, msg)
            except Exception as e:
                telega_error (e)
            # Окончание функции загрузки
            global_all_list = all_list.copy()

            # Расчеты
            #   • Фильтрация общего списка:
            #   • 1-я выборка из общего списка в (fist_list),
            #       где 3 недели подряд новый минимум выше предыдущего (т.е. минимумы не обновляются) m3>m2>m1
            #   • 2-я выборка из общего списка в (second_list),
            #       где закрытия выше предыдущих c3>c2>c1.
            #   • 3-я выборка из общего списка в (thrid_list),
            #       где новый максимум выше предыдущего (т.е. обновляются максимумы),

            minimums = []
            fist_list_long = []
            fist_list_long_m0 = []
            fist_list_short = []
            second_list_long = []
            second_list_short = []
            thrid_list_long = []
            thrid_list_short = []
            stock = []
            calc_list = []  # список с рачетами
            # df_candle=pd.DataFrame(all_list)
            # сортирока
            # статус выполнения
            bar = IncrementalBar('Сортировка', max=len(all_list))

            # Текущий интервал расчитываем или нет. 
            # В зависимости от настройки 'last_interval_calc'
            if global_options['last_interval_calc']:
                kf_delta = 0 # берем текущий интервал в расчет
            else:
                kf_delta = -1 # не берем текущий формирующийся интервал в расчет
            sindx1 = -1 + kf_delta
            sindx2 = -2 + kf_delta
            sindx3 = -3 + kf_delta
            sindx4 = -4 + kf_delta

            # цикл по всему списку акций
            for stock in all_list:
                bar.next()
                #  получаем значения Low Close Hight с конца загруженного массива свечей 
                # для инструмента в нулевом [0] индексе массива
                if len(stock) > 4 - kf_delta:
                    m3 = cast_money(stock[sindx1].low)
                    m2 = cast_money(stock[sindx2].low)
                    m1 = cast_money(stock[sindx3].low)
                    m0 = cast_money(stock[sindx4].low)

                    c3 = cast_money(stock[sindx1].close)
                    c2 = cast_money(stock[sindx2].close)
                    c1 = cast_money(stock[sindx3].close)
                    c0 = cast_money(stock[sindx4].close)

                    h3 = cast_money(stock[sindx1].high)
                    h2 = cast_money(stock[sindx2].high)
                    h1 = cast_money(stock[sindx3].high)
                    h0 = cast_money(stock[sindx4].high)

                    # Расчет разницу между закрытиями в %
                    close_delta = (c2 - c3) / c2 * 100

                    # добавляем в список тикеры у которых 3 минимума подряд выше предыдущего
                    if m3 > m2 > m1 > m0:
                        fist_list_long.append(stock)
                    # выборка когда минимумы перестали обновляться три раза подряд
                    if m3 > m2 > m1 > m0:
                        fist_list_long_m0.append(stock)

                    # добавляем в список тикеры у которых 3 раза подряд закрытия выше предыдущих
                    if c3 > c2 > c1 > c0:
                        second_list_long.append(stock)

                    # добавляем в список тикеры у которых 3 раза подряд происходит обновление максимумов
                    if h3 > h2 > h1 > h0:
                        thrid_list_long.append(stock)

                    # информация для шорт листа
                    # добавляем в другой список тикеры, которые 3 раза подряд обновляют минимумы
                    if m3 < m2 < m1 < m0:
                        fist_list_short.append(stock)
                    # добавляем в другой список тикеры, у которых 3 раза подряд закрытия ниже предыдущих
                    if c3 < c2 < c1 < c0:
                        second_list_short.append(stock)
                    # добавляем в другой список тикеры, у которых 3 раза подряд максимумы не обновляются
                    if h3 < h2 < h1 < h0:
                        thrid_list_short.append(stock)
            bar.finish()

            # список в котором свечи акций три интервала подряд
            # обновление максимумов без обновления минимумов с закрытиями выше предыдущи
            long_list = []
            new_hight = []
            # ВЫБОРКА1. Если акция из списка 1 есть в списке 2 и в списке 3 добавляем в лонг лист
            for long1 in fist_list_long:
                if long1 in second_list_long and long1 in thrid_list_long:
                    long_list.append(long1)
                # ВЫБОРКА2: список акций в которых обновляются минимумы и обновляются максимумы.
                # На закрытия внимание не обращаем
                if long1 in thrid_list_long:
                    new_hight.append(long1)
                # Выборка 3: когда минимумы перестали обновляться
                long_list_3 = fist_list_long.copy()

            # Составление шорт листа
            short_list = []
            for short1 in fist_list_short:
                if short1 in second_list_short and short1 in thrid_list_short:
                    short_list.append(short1)

            print()
            print()
            print('Результат обработки:')
            print(f' Начало обработки:{end_time}')
            print(f' Окончание обработки:{start_time}')
            print(f' Интервал: {global_interval_load_s}')
            print(f' Количество обработанных акций: {len(global_finaly_bag_of_stocks)}')
            # идентификация инструмента по figi
            # ДОБАВИТЬ сортировку по капитализации
            msg = ''
            msg1 = ''
            msg2 = ''
            msg1 = f"ВЫБОРКА 1: от {now_date_txt_file()}"
            msg1 += "\nкогда три интервала подряд:"
            msg1 += f'\n   новый максимум выше предыдущего,' \
                    f'\n   новый минимум выше предыдущего,' \
                    f'\n   закрытие выше предыдущего' \
                    f'\n   #P1A_выборка1_{global_interval_load_s}_{global_val_nom}'
            #             msg1="""ВЫБОРКА 1: \nдля возможной покупки в Лонг, \nпо условиям, когда три интервала подряд:
            #     новый максимум выше предыдущего,
            #     новый минимум выше предыдущего,
            #     новое закрытие выше предыдущего,
            # т.е. происходит обновление максимумов без обновления минимумов с закрытиями выше предыдущих\n\n"""
            # сортировка списка long_list по алфавиту
            # сортировка списка long_list по лонг с плечом
            # сортировка списка long_list по капитализации

            # расчет капитализации  списка long_list
            capitaliz_list = []
            for long1 in long_list:
                for z_dict in full_list_sh2:
                    if z_dict.figi == long1[0].figi:
                        capitaliz_list.append([z_dict.issue_size * cast_money(long1[-1].close), long1[0].figi, z_dict.name])
            capitaliz_list.sort(reverse=True)
            # сортировка списка long_list по капитализации
            sort_capitaliz_list = []
            for z_dict in capitaliz_list:
                for long1 in long_list:
                    if z_dict[1] == long1[0].figi:
                        sort_capitaliz_list.append(long1)

            # выбрать из списка sort_capitaliz_list доступных в лонг с плечом

            list_marg_long = []
            list_marg_long = myutils.select_margin_long_stoks(full_list_sh2)  # выбрать только маржинальные в лонг
            long_list_margin = []
            if global_options['list1_margin_only']:
                # выстраиваем список по капитализации и доступные в лонг с плечом
                for long1 in sort_capitaliz_list:
                    for z_dict in list_marg_long:
                        if z_dict.figi == long1[0].figi:
                            long_list_margin.append(long1)  # создаем новый лонг лист только с маржинальными акциями
            else:
                # выстраиваем список только по капитализации
                long_list_margin = sort_capitaliz_list.copy()

            # добавляем для ВЫБОРКИ 1 позиции в сообщение
            for long1 in long_list_margin:
                for z_dict in global_finaly_bag_of_stocks:
                    if z_dict.figi == long1[0].figi:
                        # разделить на создание списка, сортировка и принтинг
                        print(f'[1]:', z_dict.ticker, z_dict.figi, z_dict.name, ' закр:', cast_money(long1[-1].close))
                        # msg=msg+ f'{z_dict.figi} {z_dict.ticker} {z_dict.name}  ' \
                        #          f'\n [+]цена последнего зарытия: {long1[-1].c}\n\n'
                        msg += f'[1]: {z_dict.ticker}   {z_dict.name}    [закр.: {cast_money(long1[-1].close)} {global_val_nom}]\n'

                        # if  global_val_nom=="RUB":
                        # msg+=f'https://www.moex.com/ru/issue.aspx?board=TQBR&code={z_dict.ticker}\n'
                        msg += f'https://www.tinkoff.ru/invest/stocks/{z_dict.ticker}\n'
                        # msg+=f'https://bcs-express.ru/kotirovki-i-grafiki/{z_dict.ticker}\n'
                        msg += '\n'

            print('Всего:', len(long_list), "\n")
            msg2 = f'\nИнтервал: {global_interval_load_s} к {global_interval_load_s}, три подряд.\n'
            msg2 = msg2 + f'\nОбработано: {len(global_finaly_bag_of_stocks)} акций.\nВыбрано {len(long_list)} акций:\n'
            msg = msg1 + msg2 + msg

            # выдача сообщений о результатах обработки не более 4000 символов за раз
            for message1 in util.smart_split(msg, 4000):
                try:
                    reg_msg()
                    bot.send_message(m.chat.id, message1, disable_web_page_preview=True)
                except Exception as e:
                    telega_error (e)
            # ВЫБОРКА 2
            # ======ОТОБРАЖЕНИЕ СПИСКА, когда есть обновления максимумов в без обновления минимумов,
            # три подряд, независимо от закрытий.================
            # new_hight - набор свечей
            # global_finaly_bag_of_stocks - список анализируемых акций
            if len(new_hight) < 16:  # когда 15 акций список еще выводим, если больше, то только по кнопке
                msg = ''
                list1 = []
                list2 = []  # для сообщений telegram список
                msglst = ''  # переменная для сбора сообщения
                msg = "ВЫБОРКА 2: \nкогда три интервала подряд: " \
                      "\nпроисходят обновления максимумов без обновления минимумов, без учета закрытий.\n"
                print(
                    "\n\nСписок акций, когда три интервала подряд:"
                    "\n происходят обновления максимумов без обновления минимумов, без учета закрытий.")
                for zap1 in new_hight:
                    for z_dict in global_finaly_bag_of_stocks:
                        if z_dict.figi == zap1[0].figi:
                            list1.append(f'[2]: {z_dict.ticker} {z_dict.figi} {z_dict.name} [закр: {cast_money(zap1[-1].close)}]')

                            msglst = f'[2]: {z_dict.ticker}   {z_dict.name}   [закр: {cast_money(zap1[-1].close)} {global_val_nom}]\n'
                            # if  global_val_nom=="RUB":
                            # msglst+=f'https://www.moex.com/ru/issue.aspx?board=TQBR&code={z_dict.ticker}\n'
                            msglst += f'https://www.tinkoff.ru/invest/stocks/{z_dict.ticker}\n'
                            msglst += '\n'
                            list2.append(msglst)
                list1.sort()
                list2.sort()

                for zap1 in list1:
                    print(zap1)

                msg = msg + f'\nВсего выбрано {len(list2)} акций:\n'
                for zap2 in list2:
                    msg += zap2

                try:
                    reg_msg()
                    bot.send_message(m.chat.id, '📊')
                except Exception as e:
                    telega_error (e)
                # выдача сообщений о результатах обработки не более 4000 символов за раз
                for message1 in util.smart_split(msg, 4000):
                    try:
                        reg_msg()
                        bot.send_message(m.chat.id, message1, disable_web_page_preview=True)
                    except Exception as e:
                        telega_error (e)
            else:
                global_list_sel2 = new_hight.copy()
                msg = f'ВЫБОРКА 2:  ({len(global_list_sel2)}шт.)\n'
                msg += f'Когда ТРИ интервала подряд:\n'
                msg += "    происходят обновления максимумов без обновления минимумов, без учета закрытий.\n"
                keyboard = types.InlineKeyboardMarkup(row_width=2)
                b1 = types.InlineKeyboardButton("Показать", callback_data='show_sel_2')
                keyboard.add(b1)
                try:
                    reg_msg()
                    bot.send_message(m.from_user.id, msg, reply_markup=keyboard)
                except Exception as e:
                    telega_error (e)

            # Выборка 3 когда минимумы перестали обновляться
            # fist_list_long_m0
            global_list_sel3 = fist_list_long_m0.copy()
            msg = f'ВЫБОРКА 3:  ({len(global_list_sel3)}шт.)\nКогда перестали обновляться минимумы 4 интервала подряд:'
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            b1 = types.InlineKeyboardButton("Показать", callback_data='show_sel_3')
            keyboard.add(b1)
            try:
                reg_msg()
                bot.send_message(m.from_user.id, msg, reply_markup=keyboard)
                reg_msg()
                bot.send_message(m.chat.id,
                                f'ОБРАБОТАНО.\nДо конца минуты допустимо еще не более: {240 - it1} запросов. '
                                f'\nДолжно быть не более 240 в минуту. '
                                f'\nПодождите 2 минуты перед запуском следущей команды /begin')
            except Exception as e:
                telega_error (e)
            global_all_list = all_list.copy()
            g_df_2 = pd.DataFrame(all_list)
            flag_loop = False
            global_in_progress_state = False
            return global_all_list
        
    # ====================ОБРАБОТКА ТЕКСТОВЫХ КОМАНД==================
    # https://docs-python.ru/packages/biblioteka-python-telegram-bot-python/menju-klaviatury/
    @bot.message_handler(content_types=['text'])
    def text_commands(message: telebot.types.Message):
        global global_f_opt, glodal_inp_interval, global_interval_load, global_interval_load_s, g_df, g_df_p
        global global_max_range, global_inp_var, global_val_nom, global_bag_of_stocks, global_finaly_bag_of_stocks
        global global_bids_data, global_all_list, all_list, g_full_list_sh2, global_list_sel3, global_list_sel2
        global global_set_from_orders
        global bot
        # обработка команды главное меню
        if (message.text == "Главное меню" or message.text == "главное меню" or
                message.text == "меню" or message.text == "Меню" or message.text == "/menu"):
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
            b1 = types.KeyboardButton("stoks")
            b2 = types.KeyboardButton("futures")
            markup.add(b1, b2)
            try:
                reg_msg()
                bot.send_message(message.chat.id, text="Вы вернулись в главное меню", reply_markup=markup)
            except Exception as e:
                telega_error (e)
        
        elif message.text == 'stoks':
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
            b2 = types.KeyboardButton("Настройки")
            b3 = types.KeyboardButton("/begin")
            b4 = types.KeyboardButton("⬆️ ⬇️")
            b5 = types.KeyboardButton('Меню')
            b_find = types.KeyboardButton('find_v2')
            markup.add(b2, b3, b4, b_find, b5)
            try:
                reg_msg()
                bot.send_message(message.chat.id, text="Функции для анализа акций", reply_markup=markup)
            except Exception as e:
                telega_error (e)
        
        elif message.text == 'futures':
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
            b1 = types.KeyboardButton("Доп.функции")
            b2 = types.KeyboardButton('graf')
            b3 = types.KeyboardButton('ℹ️F')
            b4 = types.KeyboardButton('Меню')
            markup.add(b1, b3, b2, b4)
            try:
                reg_msg()
                bot.send_message(message.chat.id, text="Функции для анализа фьючерсов", reply_markup=markup)
            except Exception as e:
                telega_error (e)

        elif message.text == "find_v2":            
            res_t = sort_out_stoks('DAY')
            ID_ch = message.chat.id
            for msg in res_t:
                send_message_split(msg, bot, ID_ch)

        
        elif message.text == "АиФ":
            show_btn_analitiks (bot, message.chat.id, 'graf')
        
        elif message.text == 'set_pause_graf':
            show_pause_btn (bot, message.chat.id, 'graf')
        
        elif message.text == 'p1s':
            set_pause_graf (1, bot, message.chat.id, 'graf')
        
        elif message.text == 'p2s':
            set_pause_graf (2, bot, message.chat.id, 'graf')

        elif message.text == 'p3s':
            set_pause_graf (3, bot, message.chat.id, 'graf')
        
        elif message.text == 'p4s':
            set_pause_graf (4, bot, message.chat.id, 'graf')

        elif message.text == 'p5s':
            set_pause_graf (5, bot, message.chat.id, 'graf')
        

        elif message.text == 'тэги':
            # основные тэги
            msg = 'Основные тэги:\n\n'
            msg += '#позиции_физиков_фьючерсы\n\n#P1A_взлеты\n\n#P1A_падения\n\n#P1A_выборка1_НЕДЕЛЯ_RUB\n\n#P1A_выборка1_1\n\n'
            msg += '#MMH4_15_MIN\n\n#комиссии_итог\n\n#ГО_фьючерсы_на_акции\n\n#ГО_фьючерсы_на_индексы\n\n#ГО_фьючерсы_на_валюты\n\n#ГО_фьючерсы_на_комодити'
            try:
                reg_msg()
                bot.send_message(message.chat.id, msg)
            except Exception as e:
                telega_error (e)

        elif message.text == 'set_no_edit':
            set_no_edit = global_options['no_edit']
            if set_no_edit:
                global_options['no_edit'] = False
                msg = 'Статичный график и кнопки'                
            else:
                global_options['no_edit'] = True
                msg = 'Постоянные сообщения с графиком и кнопками'
            send_msg(msg, bot, message.chat.id)

        elif message.text == 'set_pause_graf':
            show_btn_set_pause_graf (bot, message.chat.id, 'graf')

            
            
        elif message.text == "Показать капитализацию":
            if len(global_all_list) != 0:
                try:
                    reg_msg()
                    bot.send_message(message.chat.id, text=f'Введите тикер:')
                    reg_msg()
                    bot.register_next_step_handler(message, tick_of_cap)
                except Exception as e:
                    telega_error (e)
            else:
                try:
                    bot.send_message(message.chat.id, text=f'Значение цен не загружены. Необходимо запустить через команду /begin')
                except Exception as e:
                    telega_error (e)
        elif message.text == 'Характеристики бара':
            full_FIGI_load = global_f_opt['future_FIGI']
            # загрузить бар текущего дня
            # сообщение в формате 
            # HLOC
            

        elif message.text == "Показать настройки":
            msg = f'Интервал загрузки и обработки: {global_interval_load_s}\n'
            msg += f'Обработка списка акций номинированных в: {global_val_nom}\n'
            if global_options["last_interval_calc"]:
                msg += f'Учитывать текущий интервал: ДА\n'
            else:
                msg += f'Учитывать текущий интервал: НЕТ\n'

            if global_options["list1_show"]:
                msg += f'Показывать ВЫБОРКУ 1: ДА\n'
            else:
                msg += f'Показывать ВЫБОРКУ 1: НЕТ\n'

            if global_options["list1_margin_only"]:
                msg += f'Выборка 1, показать акции с плечом: ДА\n'
            else:
                msg += f'Выборка 1, показать акции с плечом: НЕТ\n'

            if global_options["list1_sort_capital"]:
                msg += f'Выборка 1, сортировать по капиталлизации: ДА\n'
            else:
                msg += f'Выборка 1, сортировать по капиталлизации: НЕТ\n'

            if global_options["list2_show"]:
                msg += f'Показывать ВЫБОРКУ 2: ДА\n'
            else:
                msg += f'Показывать ВЫБОРКУ 2: НЕТ\n'

            if global_options["short_list_show"]:
                msg += f'Показывать шорт лист: ДА\n'
            else:
                msg += f'Показывать шорт лист: НЕТ\n'

            msg += f'Всего в списке для загрузки и обработки: {len(global_finaly_bag_of_stocks)} акций\n'
            msg += f'из доступных: {len(global_bag_of_stocks)}'
            try:
                reg_msg()
                bot.send_message(message.chat.id, text=msg)
            except Exception as e:
                telega_error (e)
            # with open("settings.json", "w") as write_file:
            #     json.dump(global_options, write_file)
            #     print (f'Настройки сохранены в json')

        elif message.text == "Изменить расширенные настройки":
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            msg = 'Выберите какие настройки изменить:'
            b1 = types.InlineKeyboardButton("Интервал", callback_data='Set_Interval')
            b2 = types.InlineKeyboardButton("Валюта", callback_data='Set_VAL')
            b3 = types.InlineKeyboardButton("⚙️Настройка отображения результата", callback_data='Rez_Show')
            b4 = types.InlineKeyboardButton("Дата и время", callback_data='Set_Date')
            keyboard.add(b1, b2, b3, b4)

            try:
                reg_msg()
                bot.send_message(message.from_user.id, msg, reply_markup=keyboard)
            except Exception as e:
                telega_error (e)

        elif message.text == "Настройки" or message.text == "настройки" or message.text == "/options":
            msg = f"Выберите настройки: интервал и валюта"
            keyboard = types.InlineKeyboardMarkup(row_width=3)
            if global_interval_load == CandleInterval.CANDLE_INTERVAL_30_MIN:
                b1 = types.InlineKeyboardButton(text='✅30  мин', callback_data='30min')
            else:
                b1 = types.InlineKeyboardButton(text='30  мин', callback_data='30min')

            if global_interval_load == CandleInterval.CANDLE_INTERVAL_HOUR:
                b2 = types.InlineKeyboardButton(text='✅1 час', callback_data='1hour')
            else:
                b2 = types.InlineKeyboardButton(text='1 час', callback_data='1hour')

            b3 = types.InlineKeyboardButton(text='❌4 часа', callback_data='4hour')

            if global_interval_load == CandleInterval.CANDLE_INTERVAL_DAY:
                b4 = types.InlineKeyboardButton(text='✅День', callback_data='1day')
            else:
                b4 = types.InlineKeyboardButton(text='День', callback_data='1day')

            if global_interval_load == CandleInterval.CANDLE_INTERVAL_WEEK:
                b5 = types.InlineKeyboardButton(text='✅Неделя', callback_data='week')
            else:
                b5 = types.InlineKeyboardButton(text='Неделя', callback_data='week')

            if global_interval_load == CandleInterval.CANDLE_INTERVAL_MONTH:
                b6 = types.InlineKeyboardButton(text='✅Месяц', callback_data='month')
            else:
                b6 = types.InlineKeyboardButton(text='Месяц', callback_data='month')

            b7 = types.InlineKeyboardButton(text='❌1 квартал', callback_data='quartal')
            if global_val_nom == 'RUB':
                b8 = types.InlineKeyboardButton(text='USD', callback_data='USD')
                b9 = types.InlineKeyboardButton(text='✅RUB', callback_data='RUB')
            else:
                b8 = types.InlineKeyboardButton(text='✅USD', callback_data='USD')
                b9 = types.InlineKeyboardButton(text='RUB', callback_data='RUB')

            keyboard.add(b1, b2, b3, b4, b5, b6, b7)
            keyboard.row(b8, b9)
            br = types.InlineKeyboardButton("⚙️Настройка отображения результата", callback_data='Rez_Show')
            keyboard.row(br)
            try:
                reg_msg()
                bot.send_message(message.from_user.id, msg, reply_markup=keyboard)
            except Exception as e:
                telega_error (e)

        elif message.text == "Расчет позиции" or message.text == "/calc":
            try:
                reg_msg()
                bot.send_message(message.chat.id, text="Цель:")
                reg_msg()
                bot.register_next_step_handler(message, calc_pos2)
            except Exception as e:
                telega_error (e)

        elif message.text == "Доп.функции" or message.text == "доп.функции":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            # кнопки для последущего переноса куда нибудь
            old_b = types.KeyboardButton("old_b")
            # остальные кнопки которые можно и оставить
            b1 = types.KeyboardButton("⭐️Показать фьючерсы")
            bw = types.KeyboardButton("⭐️WEEK фьючерсы")
            b2 = types.KeyboardButton("Показать все фьючерсы")
            b3 = types.KeyboardButton("Показать абсолютно все фьючерсы")
            back_b = types.KeyboardButton("Меню")
            pMx = types.KeyboardButton("pMOEX")
            fnd_btn = types.KeyboardButton("Поиск отклонения фьючерсов")
            markup.add(b3, b2, b1, fnd_btn, pMx)
            markup.row(old_b, bw, back_b)
            try:
                reg_msg()
                bot.send_message(message.chat.id, text="Выберите вариант, кнопки ниже:", reply_markup=markup)
            except Exception as e:
                telega_error (e)
        elif message.text == "old_b":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
            # мало используемые кнопки для последущего переноса куда нибудь
            b1 = types.KeyboardButton("Расчет позиции")
            b2 = types.KeyboardButton("fkb")  # фьючерсы по сберу
            b3 = types.KeyboardButton("fmnl")  # фьючерса по SP
            b4 = types.KeyboardButton("Показать капитализацию")
            back_b = types.KeyboardButton("Меню")
            markup.add(b4, b1, b2, b3)
            markup.row(back_b)
            try:
                reg_msg()
                bot.send_message(message.chat.id, text="Выберите вариант, кнопки ниже:", reply_markup=markup)
            except Exception as e:
                telega_error (e)
        elif message.text == "fmnl":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=8)
            b1 = types.KeyboardButton("LD1")  # загрузить стакан
            b2 = types.KeyboardButton("by1spR")  # купить один лот на SP по рынку
            b3 = types.KeyboardButton("sl1spR")  # продать один лот на SP gj hsyre
            b4 = types.KeyboardButton("f3")  # показать список текущих позиций
            b5 = types.KeyboardButton("fsl")  # продажа одного фьючерса по рынку
            # b6 = types.KeyboardButton("Ak") # сумасшедшая покупка-продажа амер акций дешовых
            # b7 = types.KeyboardButton("F7") #циклическая покупка
            # b8 = types.KeyboardButton("F8") #циклический отчет о цене сбера
            # показать ссылки на мосбиржу для всех фьючерсов   ссылки на тынкофф тоже есть
            # b9 = types.KeyboardButton("s1")
            # b10 = types.KeyboardButton("c_Sp_f5") #закрыть ВСЮ шорт позицию по фьючам на сбер по рынку
            back = types.KeyboardButton("меню")
            markup.add(b1, b2, b3, b4, b5, back)
            try:
                reg_msg()
                bot.send_message(message.chat.id, text="Выберите вариант, кнопки ниже:", reply_markup=markup)
            except Exception as e:
                telega_error (e)
        elif message.text == "LD1":
            # print ('ближайшая цена покупки и продажи')
            FIGI = 'FUTSPYF12220'  # SP фьючерс
            try:
                with Client(TOKEN) as client:
                    flag_r = True
                    while flag_r:
                        try:
                            book = client.market_data.get_order_book(figi=FIGI, depth=10)
                            flag_r = False
                        except Exception as e:
                            print(datetime.now(timezone.utc).astimezone())
                            print('\nВОЗНИКЛА ОШИБКА')
                            print('book = client.market_data.get_order_book(figi=FIGI, depth=10)')
                            print(e)
                            print()
                            flag_r = True

                    if not (len(book.asks) == 0) and not (len(book.bids) == 0):
                        # print(book)
                        # best_price_sell, best_price_buy = cast_money(book.asks[-1].price), \
                        #     cast_money(book.bids[-1].price)
                        # края стакана, макс спред
                        fast_price_sell, fast_price_buy = book.asks[0], book.bids[0]  # центр стакана, мин спред

                        # print(best_price_sell, best_price_buy)
                        # print(fast_price_sell, fast_price_buy)
                        msg = ""
                        # msg+=f'best_price_sell:{best_price_sell}\n'
                        # msg+=f"best_price_buy:{best_price_buy}\n"
                        msg += f'b: {cast_money(fast_price_sell.price)}  ({fast_price_sell.quantity}шт.)\n'
                        msg += f's: {cast_money(fast_price_buy.price)}  ({fast_price_buy.quantity}шт.)'

                        try:
                            reg_msg()
                            bot.send_message(message.chat.id, text=msg)
                        except Exception as e:
                            telega_error (e)
                    else:
                        try:
                            reg_msg()
                            bot.send_message(message.chat.id, text='стакан пуст')
                        except Exception as e:
                            telega_error (e)
            except RequestError as ebx:
                print(str(ebx))

        elif message.text == "fkb":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=6)
            b1 = types.KeyboardButton("f1")  # отчет по фьючерсам за сегодня
            b2 = types.KeyboardButton("f11")  # отчет по комиссииям за год
            # b2 = types.KeyboardButton("f2")  # отчет по позиции сбера или текущей при отсутствии позиции
            b3 = types.KeyboardButton("f3")  # список текущих позиций
            b4 = types.KeyboardButton("by5o")  # покупка одного фьючерса по рынку
            b5 = types.KeyboardButton("sl5o")  # продажа одного фьючерса по рынку
            b6 = types.KeyboardButton("Ak")  # сумашедшая покупка-продажа амер акций дешовых
            b7 = types.KeyboardButton("F_sber_stakan")  # показать стакан по сберу
            b8 = types.KeyboardButton("F8")  # циклический отчет о цене сбера
            b9 = types.KeyboardButton(
                "s1")  # показать ссылки на мосбиржу для всех фьючерсов ссылки на тынкофф тоже есть
            b10 = types.KeyboardButton("c_Sp_f5")  # закрыть ВСЮ шорт позицию по фьючам на сбер по рынку
            back = types.KeyboardButton("Меню")
            markup.add(b1, b2, b3, b4, b5, b10)
            markup.row(b6, b8, back, b9, b7)
            try:
                reg_msg()
                bot.send_message(message.chat.id, text="Выберите вариант, кнопки ниже:", reply_markup=markup)
            except Exception as e:
                telega_error (e)
        elif message.text == "F_sber_stakan":
            # print ('ближайшая цена покупки и продажи')
            FIGI = 'FUTSBRF12220'

            try:
                with Client(TOKEN) as client:
                    flag_r = True
                    while flag_r:
                        try:
                            book = client.market_data.get_order_book(figi=FIGI, depth=10)
                            flag_r = False
                        except Exception as e:
                            print(datetime.now(timezone.utc).astimezone())
                            print('\nВОЗНИКЛА ОШИБКА')
                            print(' book = client.market_data.get_order_book(figi=FIGI, depth=10)')
                            print(e)
                            print()
                            flag_r = True

                    if not (len(book.asks) == 0) and not (len(book.bids) == 0):
                        fast_price_sell, fast_price_buy = book.asks[0], book.bids[0]  # центр стакана, мин спред
                        msg = ""
                        msg += f'b: {cast_money(fast_price_sell.price)}  ({fast_price_sell.quantity}шт.)\n'
                        msg += f's: {cast_money(fast_price_buy.price)}  ({fast_price_buy.quantity}шт.)'
                        try:
                            reg_msg()
                            bot.send_message(message.chat.id, text=msg)
                        except Exception as e:
                            telega_error (e)
                    else:
                        try:
                            reg_msg()
                            bot.send_message(message.chat.id, text='в стакане пусто')
                        except Exception as e:
                            telega_error (e)
            except RequestError as e:
                print(str(e))

        elif message.text == "🟢mOrd_Купить":
            global_bids_data ['manual_order_direct'] = OrderDirection.ORDER_DIRECTION_BUY
            mOrd_price_btn (bot, message.chat.id, 'graf')
        
        elif message.text == "🟥mOrd_Продать":
            global_bids_data ['manual_order_direct'] = OrderDirection.ORDER_DIRECTION_SELL
            mOrd_price_btn (bot, message.chat.id, 'graf')
                   
        # результат по зачислению и списания по фьючам и комиссию за день по глобальному account_id
        elif message.text == "f1" or message.text == "F1" or message.text == "А1"  or message.text == "а1" or message.text == "f11" \
            or message.text == "f1-" or message.text == "F1-" or message.text == "А1-"  or message.text == "а1-" or message.text == "f1--" \
            or message.text == "f1--" or message.text == "F1--" or message.text == "А1--"  or message.text == "а1--" \
            or message.text == "f1---" or message.text == "F1---" or message.text == "А1---"  or message.text == "а1---":
            comiss_report (bot,message.chat.id, message.text, show_dds = False)          
            
        # вывод в чат зачислений и списаний со счета
        elif message.text == 'f15':
            comiss_report (bot,message.chat.id, 'f11', show_dds = True)
        
        elif message.text == '5555':
            # останавливаем ЦИКЛ
            global_f_opt['repeat_flag'] = False
            global_f_opt['In_process'] = False
            show_repeat_btn(bot, message.chat.id, 'Стоп_цикл_gr')
            # запускаем отчеты
            res_t = sort_out('MONTH')
            ID_ch = message.chat.id
            for msg in res_t:
                send_message_split(msg, bot, ID_ch)

            res_t = sort_out('WEEK')
            ID_ch = message.chat.id
            for msg in res_t:
                send_message_split(msg, bot, ID_ch)

            res_t = sort_out('DAY')
            ID_ch = message.chat.id
            for msg in res_t:
                send_message_split(msg, bot, ID_ch)

            res_t = sort_out_stoks('DAY')
            ID_ch = message.chat.id
            for msg in res_t:
                send_message_split(msg, bot, ID_ch)

            show_good_day_report (bot,message,'graf')
            show_go (message)

            a1, a2 = ATR_calc("WEEK", 6)
            if a2 != None:
                try:
                    reg_msg()
                    bot.send_message(message.chat.id, text=round(a2,2), disable_notification=True)
                    msg = global_f_opt['full_future_name']
                    msg += '\n'
                    msg += a1.to_string()
                    reg_msg()
                    bot.send_message(message.chat.id, text = msg, disable_notification=True)
                except Exception as e:
                    telega_error (e)
            # запуск анализа акций на дневках /begin
            begin(m=message)

            # запуск выдачи взетов и падений за выбранный интервал
            find_ups_and_downs(bot, message.chat.id)

            subprocess.call("TASKKILL /f  /IM  CHROME.EXE")
            subprocess.call("TASKKILL /f  /IM  CHROMEDRIVER.EXE")
            tiho()

            #снова запускаем цикл55555555
            interval = what_interval()
            try:
                reg_msg()
                bot.send_message(message.chat.id, text=f"Запуск цикла с настройками:"
                                                   f"\nАктив: {global_f_opt['full_future_name']}"
                                                   f"\nИнтервал: {interval}"
                                                   f"\nКоличество баров: {global_f_opt['depth_load_bars']}", 
                                                   disable_notification=True)
            except Exception as e:
                telega_error (e)
            show_run_repit_btn(bot, message.chat.id, 'Цикл_gr')
            graf_3(bot, message.chat.id)

        elif message.text == 'Аналитика бара':
           figi = global_f_opt['future_FIGI']
           msg = graf_analitiks(figi=figi)
           if len(msg) > 0:
            try:
                reg_msg()
                bot.send_message(message.chat.id, text=msg, disable_notification=True)
            except Exception as e:
                telega_error (e)

        elif message.text == '3333':
            tiho()
           
        # отчет о портфеле
        elif message.text == "f3" or message.text == "F3" or message.text == "а3" or message.text == "А3" \
            or message.text == "💼F3"  or message.text == "💼f3":
            porfolio_report (bot, message.chat.id)

        # отчет о позициях с сохранением с CSV
        elif message.text == "f3m":
            with Client(TOKEN) as client_gs:
                portfel = client_gs.operations.get_portfolio(account_id=global_options['ac_id'])
                pos_prt = portfel.positions
                df = cr_df_pos(pos_prt)
                df.to_csv('porfolio.csv', encoding = 'cp1251')
                msg = ''
                for m in range(df.shape[0]):
                    msg += f'[{m}] {df.iloc[m, 0]}  {df.iloc[m, 2]}  ' \
                           f'{df.iloc[m, 8]}>>{df.iloc[m, 7]}  [{df.iloc[m, 5]}]\n'

                    print(f'[{m}] {df.iloc[m, 0]}  {df.iloc[m, 1]}   {df.iloc[m, 2]}  {df.iloc[m, 3]}>>{df.iloc[m, 7]}'
                          f'   [{df.iloc[m, 5]}]  {df.iloc[m, 6]}   {df.iloc[m, 8]}   {df.iloc[m, 9]}')

                try:
                    reg_msg()
                    bot.send_message(message.chat.id, text=msg)   
                except Exception as e:
                    telega_error (e)

        

        elif message.text == "Как меня зовут?":
            try:
                reg_msg()
                bot.send_message(message.chat.id, "У меня нет имени..")
            except Exception as e:
                telega_error (e)
        elif message.text == "Что я могу?":
            try:
                reg_msg()
                bot.send_message(message.chat.id, text="Поздороваться")
            except Exception as e:
                telega_error (e)
        elif message.text == "Запустить загрузку":
            try: 
                reg_msg()
                bot.send_message(message.chat.id, text="/begin")
            except Exception as e:
                telega_error (e)
        elif message.text == "⬆️ ⬇️" or message.text == 'взлеты' or message.text == 'Взлеты' or \
                message.text == 'падения' or message.text == '/hi_low':
            find_ups_and_downs(bot, message.chat.id)
        
        elif message.text == "s1": # показать ссылки на мосбиржу для всех фьючерсов ссылки на тынкофф тоже есть
            with Client(TOKEN) as client:
                # accounts = client.users.get_accounts()
                # print("\nСписок текущих аккаунтов\n")
                # for account in accounts.accounts:
                #     print("\t", account.id, account.name, account.access_level.name)

                # ФЬюЧЕРСЫ
                futures_instr = []
                futures = client.instruments.futures(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)
                futures_instr = futures.instruments

                # отбор в список фьючерсов, активно торгуемых в данный момент
                future_list = []
                future_filter_instr = []
                for i in futures_instr:
                    # future_list.append(f'{i.ticker} \t {i.figi} \t {i.name}')
                    if "-12.23" in i.name:
                        future_list.append(f'{i.figi} \t {i.ticker} \t {i.name}')
                        #
                        future_filter_instr.append(i)
                future_list.sort()

                for j in future_list:
                    print(j)
                print(len(future_list))

                # загружаем бары
                print(f'Начинаем загрузку баров для всех {len(future_filter_instr)} фьючерсов ')
                try:
                    reg_msg()
                    bot.send_message(message.chat.id,
                                 f'Изменение за день.\nНачинаем загрузку баров для всех {len(future_filter_instr)} фьючерсов ',
                                 disable_web_page_preview=True)
                except Exception as e:
                    telega_error (e)

                start_count_sec = time.time()  # счетчик секунд для определения общего вермени загрузки
                stoks_status_bar = IncrementalBar(' ЗАГРУЗКА', max=len(future_filter_instr))
                count_res = 0
                # получаем текущую дату и время
                curr_time = datetime.now(timezone.utc).astimezone()
                # переводим в текстовый вид
                d1 = datetime.strftime(curr_time, '%d.%m.%Y')
                ht1 = datetime.strftime(curr_time, '%H:%M:%S')
                print(f'Текущая дата: {d1} \nВремя: {ht1}')

                # if len(future_filter_instr)>280:
                count_end_minute = (60 - curr_time.second)  # количество секунд до конца текущей минуты
                print(f'До начала следующей минуты: {count_end_minute} сек')
                print(f'Засыпаем на {count_end_minute} сек ')
                try:
                    reg_msg()
                    bot.send_message(message.chat.id, f'Засыпаем на {count_end_minute} сек ', disable_web_page_preview=True)
                    reg_msg()
                    bot.send_chat_action(message.chat.id, action='typing')
                except Exception as e:
                    telega_error (e)
                time.sleep(count_end_minute)  # ждем конца минутыq

                print(f'Всего фьючерсов для чтения: {len(future_filter_instr)}')
                try:
                    reg_msg()
                    bot.send_message(message.chat.id, f'Всего фьючерсов для чтения: {len(future_filter_instr)}',
                                 disable_web_page_preview=True, disable_notification=True)
                except Exception as e:
                    telega_error (e)

                # CANDLE_INTERVAL_UNSPECIFIED	0	Интервал не определён.
                # CANDLE_INTERVAL_1_MIN	1	1 минута.
                # CANDLE_INTERVAL_5_MIN	2	5 минут.
                # CANDLE_INTERVAL_15_MIN	3	15 минут.
                # CANDLE_INTERVAL_HOUR	4	1 час.
                # CANDLE_INTERVAL_DAY	5	1 день.

                # интервал
                load_inter = 'DAY'
                # количество интервалов для загрузки
                load_period = 7
                # от какой даты загрузить
                if load_inter == 'DAY':
                    load_from = datetime.now(timezone.utc).astimezone() - timedelta(days=load_period)
                # до какой даты загрузить
                load_to = datetime.now(timezone.utc).astimezone()

                bars_list = []
                bar_items = []
                # Основной цикл загрузки
                for k in future_filter_instr:
                    bar_items = []
                    if count_res == 300:
                        stop_count_sec = time.time()
                        delta = stop_count_sec - start_count_sec
                        print(f'\nC момента запуска прошло {int(delta)} сек')
                        print("Достигнут предел: 300 запросов в минуту")
                        try:
                            reg_msg()
                            bot.send_message(message.chat.id, "Достигнут предел: 300 запросов в минуту")
                        except Exception as e:
                            telega_error (e)

                        wait_end_minute = (60 - datetime.now(
                            timezone.utc).astimezone().second + 5)  # количество секунд до конца текущей
                        # минуты плюс небольшой запас
                        print(f'Засыпаем на {wait_end_minute} сек\n')
                        time.sleep(wait_end_minute)  # ждем конца минуты
                        count_res = 0  # обнуляем счетчик запросов в минуту

                    try:
                        bars = client.market_data.get_candles(
                            figi=k.figi,
                            from_=load_from,
                            to=load_to,
                            interval=CandleInterval.CANDLE_INTERVAL_DAY
                        )
                    except Exception as e:
                        print(e)
                        try:
                            reg_msg()
                            bot.send_message(message.chat.id,
                                         '⚡️ОШИБКА⚡️ \nЧто-то пошло не так при загрузке данных из платформы Тинькофф.'
                                         '\nПопробуйте вернуть настройки на первоначальные⚡️')
                            reg_msg()
                            bot.send_message(message.chat.id, e)
                        except Exception as e:
                            telega_error (e)                        
                        return 0

                    bar_items.append(bars.candles)
                    bar_items[0].insert(0, k)
                    bars_list.append(bar_items)
                    count_res += 1  # счетчик обращений
                    stoks_status_bar.next()
                    print(' ', k.name, k.ticker)
                msg = ''
                for m in bars_list:
                    print(f'https://www.moex.com/ru/contract.aspx?code={m[0][0].ticker}')

                for m in bars_list:
                    print(m[0][0].ticker)
                print()
                for m in bars_list:
                    print(m[0][0].name)
                print()

                for m in bars_list:
                    if len(m[0]) > 3:
                        izm = round((cast_money(m[0][-1].close) - cast_money(m[0][-2].close)) / cast_money(
                            m[0][-2].close) * 100, 2)
                        msg += f'{m[0][0].name}\n{m[0][0].ticker}   {cast_money(m[0][-2].close)}   ' \
                               f'{cast_money(m[0][-1].close)}   {izm} % \n'
                        msg += f'https://www.tinkoff.ru/invest/futures/{m[0][0].ticker}\n'
                        msg += f'https://www.moex.com/ru/contract.aspx?code={m[0][0].ticker}\n'
                        msg += f'\n'

                stop_count_sec = time.time()
                delta = stop_count_sec - start_count_sec
                delta_min = delta / 60
                print(f'\n\nВсего прошло с момента запуска: {int(delta)} сек')
                print(f'в минутах с момента запуска: {int(delta_min)} мин')
                # выдача сообщений о результатах обработки не более 4000 символов за раз
                for message1 in util.smart_split(msg, 4000):
                    try:
                        reg_msg()
                        bot.send_message(message.chat.id, message1, disable_web_page_preview=True)
                    except Exception as e:
                        telega_error (e)
       
        # ФУНКЦИЯ построние графиков и циклиеская выдача в чат и управление позицией
        elif message.text == 'graf':
            show_run_repit_btn (bot, message.chat.id, 'graf')
        
        # ФУНКЦИЯ отображения кнопок с доп. функциями
        elif message.text == 'Доп.2':
            show_info_2_btn (bot, message.chat.id, 'graf')
        
        # выбор типа актива
        elif message.text == 'Акции_gr':
            global_f_opt['type_analyse'] = 'stock'
            show_stocks_btn(bot, message.chat.id, 'Акции_gr')
        elif message.text == 'Фьючерсы_gr':
            global_f_opt['type_analyse'] = 'future'
            show_futures_btn(bot, message.chat.id, 'Фьючерсы_gr')

        #  для фьючерсов блок выбора контракта
        # ММВБ мини
        elif message.text == 'MXI_gr':
            switching_set('MXI', bot, message.chat.id)
        # ММВБ мини следующий за текущим контракт
        elif message.text == 'MXI_n_gr':
            global_f_opt['full_future_name'] = 'MXI' + global_f_opt['next_activ_contr_name']
            figi_future = find_figi_of_name_future (global_f_opt['full_future_name'])
            global_f_opt['future_FIGI'] = figi_future[0]
            show_run_repit_btn(bot, message.chat.id, 'MXI')
        elif message.text == 'SPYF_gr':
            switching_set('SPYF', bot, message.chat.id)
        elif message.text == 'Si_gr':
            switching_set('Si', bot, message.chat.id)
        elif message.text == 'NG_gr':
            switching_set('NG', bot, message.chat.id)
        elif message.text == 'SBRF_F_gr':
            switching_set('SBRF', bot, message.chat.id)
        elif message.text == 'GAZPR_gr':
            switching_set('GAZPR', bot, message.chat.id)
        elif message.text == 'LKOH_F_gr':
            switching_set('LKOH', bot, message.chat.id)
        elif message.text == 'YNDF_n_gr':
            switching_set('YNDF', bot, message.chat.id)
        elif message.text == 'ED_gr':
            switching_set('ED', bot, message.chat.id)
        elif message.text == 'MIX_gr': 
            switching_set('MIX', bot, message.chat.id)
        elif message.text == 'RTSM_gr':
            switching_set('RTSM', bot, message.chat.id)
        elif message.text == 'RTS_gr':
            switching_set('RTS', bot, message.chat.id)
        

        # блок выбора временного интервала
        elif message.text == '1min_gr':
            global_f_opt['candl_interval'] = CandleInterval.CANDLE_INTERVAL_1_MIN
            # show_step_btn(bot, message.chat.id, '1min_gr')
            show_run_repit_btn(bot, message.chat.id, '1min_gr')
        elif message.text == '5min_gr':
            global_f_opt['candl_interval'] = CandleInterval.CANDLE_INTERVAL_5_MIN
            show_run_repit_btn(bot, message.chat.id, '5min_gr')
        elif message.text == '15min_gr':
            global_f_opt['candl_interval'] = CandleInterval.CANDLE_INTERVAL_15_MIN
            show_run_repit_btn(bot, message.chat.id, '15min_gr')
        elif message.text == '1hour_gr':
            global_f_opt['candl_interval'] = CandleInterval.CANDLE_INTERVAL_HOUR
            show_run_repit_btn(bot, message.chat.id, '1hour_gr')
        elif message.text == '1day_gr':
            global_f_opt['candl_interval'] = CandleInterval.CANDLE_INTERVAL_DAY
            show_run_repit_btn(bot, message.chat.id, '1day_gr')
        
        # блок количества баров для отображения на графике
        elif message.text == '5b_gr':
            global_f_opt['depth_load_bars'] = 5
            show_repeat_btn(bot, message.chat.id, '5b_gr')
        elif message.text == '7b_gr':
            global_f_opt['depth_load_bars'] = 7
            show_repeat_btn(bot, message.chat.id, '7b_gr')
        elif message.text == '10b_gr':
            global_f_opt['depth_load_bars'] = 10
            show_repeat_btn(bot, message.chat.id, '10b_gr')
        elif message.text == '15b_gr':
            global_f_opt['depth_load_bars'] = 15
            show_repeat_btn(bot, message.chat.id, '15b_gr')
        elif message.text == '20b_gr':
            global_f_opt['depth_load_bars'] = 20
            show_repeat_btn(bot, message.chat.id, '20b_gr')
        elif message.text == '30b_gr':
            global_f_opt['depth_load_bars'] = 30
            show_repeat_btn(bot, message.chat.id, '30b_gr')
        elif message.text == '40b_gr':
            global_f_opt['depth_load_bars'] = 40
            show_repeat_btn(bot, message.chat.id, '40b_gr')
        elif message.text == '50b_gr':
            global_f_opt['depth_load_bars'] = 50
            show_repeat_btn(bot, message.chat.id, '50b_gr')
       
        # кнопки управления в цикле
        elif message.text == 'Цикл_gr':
            # get_price_TI()
            global_f_opt['repeat_flag'] = True
            try:
                reg_msg()
                bot.send_message(message.chat.id, text=f"Запуск цикла с настройками:"
                                                   f"\nАктив: {global_f_opt['full_future_name']}"
                                                   f"\nИнтервал: {global_f_opt['candl_interval']}"
                                                   f"\nКоличество баров: {global_f_opt['depth_load_bars']}")
            except Exception as e:
                telega_error (e)
            show_run_repit_btn(bot, message.chat.id, 'Цикл_gr')
            graf_3(bot, message.chat.id)
        
        elif message.text == 'Без повтора_gr':
            graf_1(bot, message.chat.id)
        elif message.text == '❌Стоп_цикл_gr':
            global_f_opt['repeat_flag'] = False
            global_f_opt['In_process'] = False
            show_repeat_btn(bot, message.chat.id, 'Стоп_цикл_gr')
        elif message.text== '⚙️Настроки_gr':
            show_type_set (bot, message.chat.id, 'graf')
        elif message.text== 'ℹ️F':
            show_info_futures_btn (bot, message.chat.id, 'graf')
        elif message.text == 'Инфо_счет':
            show_btn_port_info (bot, message.chat.id, 'ℹ️F')
        # ручная заявка
        elif message.text == '🤘R' or message.text == 'rrr' or message.text == 'RRR':
            # индентификация пользователя
            ID_user = message.from_user.id
            user_fist_name = message.from_user.first_name
            user_username = message.from_user.username
            user_true_id = global_set_from_orders['user_id']
            if int(ID_user) == int(user_true_id):
                manual_orders_btn (bot, message, 'graf')

        # обработка нажатия кнопок с настройками:
        elif message.text == 'Тип_актива_gr':
            show_type_instr_btn(bot, message.chat.id, 'graf')
        elif message.text == 'Фьючерсы_gr':
            show_futures_btn(bot, message.chat.id, 'graf')
        elif message.text == 'Интервал_gr':
            what_param_is_now (bot, message.chat.id, 'Интервал_gr')
            show_interval_btn (bot, message.chat.id, 'graf')
        elif message.text == 'Кол-во_бар_gr':
            show_step_btn(bot, message.chat.id, 'graf')
        elif message.text == 'st_bt_opr':
            oper_selector(bot, message.chat.id, 'graf')
        elif message.text == 'show_pos_s':
            show_pos_selector(bot, message.chat.id, 'graf')
        
        # кнопки раздела ℹ️F информации о фьчерсах
        elif message.text == 'ℹ️ГО':
            show_info_of_G_O(bot, message.chat.id, 'graf')
        elif message.text == 'ℹ️М':
            show_margin_status(bot, message.chat.id, 'graf')
        elif message.text == 'рсчт':
            show_info_2_btn (bot, message.chat.id, 'graf')
        elif message.text == 'show_aktiv_Ord' or message.text == 'shAZ':
            show_aktiv_orders (bot, message.chat.id, 'graf')
        elif message.text == 'mOrd':
            manual_orders_btn (bot, message, 'graf')
        # поиск уровней на графике
        elif message.text == 'ur' or message.text == 'уровни_futures':
            # телега не допускает очень частое отправление картинок в чат
            # time.sleep(2)
            fav_periods = ['15min', '1h', '1D']
            media_group = []
            for perion in fav_periods:
                get_price_TI(perion)
                graf_path = f"start_levels_{perion}.png"
                try:
                    media_group.append(types.InputMediaPhoto(media=open(graf_path, 'rb'), caption=f'{perion}_lines'))                
                except Exception as e:
                    telega_error (e)                
                # time.sleep(1)

                
            try:
                reg_msg()
                bot.send_media_group(message.chat.id, media = media_group )
            except Exception as e:
                telega_error (e)
        
        # клавиатура с выбором интервала для отображения ATR
        elif message.text == 'ATR(i)':
            show_ATR_btn (bot, message.chat.id, 'graf')
        
        # клавиатура с выбором интервала для поиска паттернов на графике фьючерсов
        elif message.text == 'find_ptrn(i)':
            show_find_ptrn_btn (bot, message.chat.id, 'graf')
        
        elif message.text == 'find_ptrn' or message.text =='find_ptrn(D)':
            res_t = sort_out('DAY')
            ID_ch = message.chat.id
            for msg in res_t:
                send_message_split(msg, bot, ID_ch)

        elif message.text == 'find_ptrn(W)':
            res_t = sort_out('WEEK')
            ID_ch = message.chat.id
            for msg in res_t:
                send_message_split(msg, bot, ID_ch)
        
        elif message.text == 'find_ptrn(M)':
            res_t = sort_out('MONTH')
            ID_ch = message.chat.id
            for msg in res_t:
                send_message_split(msg, bot, ID_ch)

        elif message.text == 'find_ptrn(4h)':
            res_t = sort_out('4h')
            ID_ch = message.chat.id
            for msg in res_t:
                send_message_split(msg, bot, ID_ch)
        
        elif message.text == 'find_ptrn(1h)':
            res_t = sort_out('1h')
            ID_ch = message.chat.id
            for msg in res_t:
                send_message_split(msg, bot, ID_ch)
        
        elif message.text == 'find_ptrn(30min)':
            res_t = sort_out('30min')
            ID_ch = message.chat.id
            for msg in res_t:
                send_message_split(msg, bot, ID_ch)
        
        elif message.text == 'find_ptrn(15min)':
            res_t = sort_out('15min')
            ID_ch = message.chat.id
            for msg in res_t:
                send_message_split(msg, bot, ID_ch)            

        #расчет ATR за 5 дней 
        elif message.text == 'ATR' or message.text =='ATR(D)':
            a1, a2 = ATR_calc("DAY", 6)
            if a2 != None:
                try:
                    reg_msg()
                    bot.send_message(message.chat.id, text=round(a2,2), disable_notification=True)
                    msg = global_f_opt['full_future_name']
                    msg += '\n'
                    msg += a1.to_string()
                    reg_msg()
                    bot.send_message(message.chat.id, text = msg, disable_notification=True)
                except Exception as e:
                    telega_error (e)
            
        
        elif message.text == 'sw_bot':
            print('Переключаем бота')
            print('Остановка бота')
            bot.stop_bot()
            print('Удаление бота')
            del bot
            print('Переключение токена бота')
            switch_bot()
        
        elif message.text == 'tst_sw_bot':
            print('Тест переключения бота')
            try:
                test_switch(50)
            except Exception as e:
                telega_error (e)
            
        #расчет ATR
        elif message.text == 'ATR(W)':
            a1, a2 = ATR_calc("WEEK", 6)
            if a2 != None:
                try:
                    reg_msg()
                    bot.send_message(message.chat.id, text=round(a2,2), disable_notification=True)
                    msg = global_f_opt['full_future_name']
                    msg += '\n'
                    msg += a1.to_string()
                    reg_msg()
                    bot.send_message(message.chat.id, text = msg, disable_notification=True)
                except Exception as e:
                    telega_error (e)
        
        elif message.text == 'ATR(4h)':
            a1, a2 = ATR_calc("4h", 6)
            if a2 != None:
                try:
                    reg_msg()
                    bot.send_message(message.chat.id, text=round(a2,2), disable_notification=True)
                    msg = global_f_opt['full_future_name']
                    msg += '\n'
                    msg += a1.to_string()
                    reg_msg()
                    bot.send_message(message.chat.id, text = msg, disable_notification=True)
                except Exception as e:
                    telega_error (e)
        
        elif message.text == 'ATR(1h)':
            a1, a2 = ATR_calc("1h", 6)
            if a2 != None:
                try:
                    reg_msg()
                    bot.send_message(message.chat.id, text=round(a2,2), disable_notification=True)
                    msg = global_f_opt['full_future_name']
                    msg += '\n'
                    msg += a1.to_string()
                    reg_msg()
                    bot.send_message(message.chat.id, text = msg, disable_notification=True)
                except Exception as e:
                    telega_error (e)
        
        elif message.text == 'ATR(M)':
            a1, a2 = ATR_calc("MONTH", 5)
            if a2 != None:
                try:
                    reg_msg()
                    bot.send_message(message.chat.id, text=round(a2,2), disable_notification=True)
                    msg = global_f_opt['full_future_name']
                    msg += '\n'
                    msg += a1.to_string()
                    reg_msg()
                    bot.send_message(message.chat.id, text = msg, disable_notification=True)
                except Exception as e:
                    telega_error (e)

        # Показать графики избранных фьючерсов
        elif message.text == "⭐️Показать фьючерсы" or message.text == "f2":
            load_period = 20 # глубина отображения серии 
            # load_inter = 15min, 30min, 1h, 4h, DAY, WEEK, MONTH
            load_inter = 'DAY'
            show_futur_graf (bot, message.chat.id, message.text, load_period, load_inter, 'graf')
        
        # Показать графики избранных фьючерсов
        elif message.text == "⭐️WEEK фьючерсы":
            load_period = 20 # глубина отображения 
            load_inter = 'WEEK'
            show_futur_graf (bot, message.chat.id, '⭐️Показать фьючерсы', load_period, load_inter, 'graf')
            

        # Поиск отклонения фьючерсов
        elif message.text == "Поиск отклонения фьючерсов":
            show_delta_futures (bot, message.chat.id)
       
        # ------------------------------------------------------------------------------------------------
        elif message.text == "Показать все фьючерсы":
            start_count_sec = time.time()  # счетчик секунд для определения общего времени загрузки
            try:
                reg_msg()
                bot.send_chat_action(message.chat.id, action='typing')
            except Exception as e:
                telega_error (e)
            with Client(TOKEN) as client:
                # ФЬюЧЕРСЫ
                futures_instr = []
                flag_r = True
                # Бесконечное количество попыток загрузить список пока не достигнем успеха
                while flag_r:
                    try:
                        futures = client.instruments.futures(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)
                        flag_r = False
                    except Exception as ebx:
                        print(datetime.now(timezone.utc).astimezone())
                        print('\nВОЗНИКЛА ОШИБКА')
                        print(
                            'futures=client.instruments.'
                            'futures(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)')
                        print(ebx)
                        print()
                        flag_r = True
                futures_instr = futures.instruments
                try:
                    reg_msg()
                    bot.send_message(message.chat.id,
                                    f'Загружен список из: {len(futures_instr)} фьючерсов для выбора актуальных',
                                    disable_web_page_preview=True, disable_notification=True)
                except Exception as e:
                    telega_error (e)
                # отбор в список  фьючерсов с имененм актуального контрактного имени global_f_opt['activ_contr_name']
                future_list = []
                future_filter_instr = []
                # выбираем только активные фьючерсы
                future_actual = global_f_opt['activ_contr_name']
                for i in futures_instr:
                    if future_actual in i.name:
                        future_list.append(f'{i.figi} \t {i.ticker} \t {i.name}')
                        future_filter_instr.append(i)
                future_list.sort()
               
                # загружаем бары
                print(f'Начинаем загрузку баров для всех {len(future_filter_instr)} фьючерсов с арт.{future_actual} ')
                try:
                    reg_msg()
                    bot.send_message(message.chat.id,
                                    f'Начинаем загрузку дневных баров для выбранных {len(future_filter_instr)} фьючерсов с арт.{future_actual}',
                                    disable_web_page_preview=True, disable_notification=True)
                except Exception as e:
                    telega_error (e)
                stoks_status_bar = IncrementalBar(' ЗАГРУЗКА', max=len(future_filter_instr))
                count_res = 0
                # получаем текущую дату и время
                curr_time = datetime.now(timezone.utc).astimezone()
                # переводим в текстовый вид
                d1 = datetime.strftime(curr_time, '%d.%m.%Y')
                ht1 = datetime.strftime(curr_time, '%H:%M:%S')
                print(f'Текущая дата: {d1} \nВремя: {ht1}')

                print(f'Всего фьючерсов для чтения: {len(future_filter_instr)}')
                # try:
                #     reg_msg()
                #     bot.send_message(message.chat.id, f'Всего фьючерсов для чтения: {len(future_filter_instr)}',
                #                     disable_web_page_preview=True, disable_notification=True)
                # except Exception as e:
                #     telega_error (e)
                # CANDLE_INTERVAL_UNSPECIFIED	0	Интервал не определён.
                # CANDLE_INTER VAL_1_MIN	    1	1 минута.
                # CANDLE_INTERVAL_5_MIN	        2	5 минут.
                # CANDLE_INTERVAL_15_MIN	    3	15 минут.
                # CANDLE_INTERVAL_HOUR	        4	1 час.
                # CANDLE_INTERVAL_DAY	        5	1 день.

                # интервал
                load_inter = 'DAY'
                # количество интервалов для загрузки
                load_period = 20
                # от какой даты загрузить
                if load_inter == 'DAY':
                    load_from = datetime.now(timezone.utc).astimezone() - timedelta(days=load_period)
                # до какой даты загрузить
                load_to = datetime.now(timezone.utc).astimezone()

                # список объектов с выходным результатом загрузки
                bars_list = []
                f_inf_list_obj = []
                # Основной цикл загрузки
                for k in future_filter_instr:
                    # загрузка баров
                    try:
                        bars = client.market_data.get_candles(
                            figi=k.figi,
                            from_=load_from,
                            to=load_to,
                            interval=CandleInterval.CANDLE_INTERVAL_DAY
                        )
                        # информация о ГО
                        f_inf = client.instruments.get_futures_margin(figi=k.figi)
                    except Exception as ebx:
                        if ebx.code.name == 'RESOURCE_EXHAUSTED':
                            stop_time = ebx.metadata.ratelimit_reset + 2
                            print()
                            print_date_time_now()
                            print(ebx)
                            print (f'Пауза {stop_time} сек...')
                            time.sleep(stop_time)
                            print_date_time_now()
                            print()
                            bars = client.market_data.get_candles(
                                figi=k.figi,
                                from_=load_from,
                                to=load_to,
                                interval=CandleInterval.CANDLE_INTERVAL_DAY
                            )
                            # информация о ГО
                            f_inf = client.instruments.get_futures_margin(figi=k.figi)

                        else:
                            print(ebx)
                            try:
                                reg_msg()
                                bot.send_message(message.chat.id,
                                                '⚡️ОШИБКА⚡️ \nЧто-то пошло не так при баров  из платформы Тинькофф.'
                                                '\nПопробуйте вернуть настройки на первоначальные⚡️')
                                reg_msg()
                                bot.send_message(message.chat.id, ebx)
                            except Exception as e:
                                telega_error (e)
                            return 0

                    # инициируем строку-список для добавления в итоговый список
                    bar_items = []
                    # добавляем в строку-список бары в виде объектов
                    bar_items.append(bars.candles)
                    # добавляем нулевым элементом объект фьючерса
                    bar_items[0].insert(0, k)
                    # добавляем итоговый список
                    bars_list.append(bar_items)
                    f_inf_list_obj.append(f_inf)
                    count_res += 1  # счетчик обращений
                    stoks_status_bar.next()
                    print(' ', k.name, k.ticker)

                # расчет и формирование DF_F
                # итоговый список который получится после обработки
                df_f_lst = []
                count_lst = 0
                for m in bars_list:
                    ftr_mrg_once = f_inf_list_obj[count_lst]
                    count_lst += 1
                    if len(m[0]) > 3:
                        name_f = m[0][0].name
                        ticker_f = m[0][0].ticker
                        close_1 = cast_money(m[0][-1].close) # значение стало
                        close_2 = cast_money(m[0][-2].close) # значение было
                        # расчет абс изм.
                        izm_abs = (close_1 - close_2)
                        # расчет в % изменения
                        izm = round(izm_abs / close_2 * 100, 2)
                        izm_abs = round(izm_abs, 2)
                        # добавляем очередную строку к списку
                        df_f_lst.append([name_f, ticker_f, close_2, close_1, izm_abs, izm, cast_money(ftr_mrg_once.initial_margin_on_buy),
                              f'https://www.tinkoff.ru/invest/futures/{ticker_f}'])
                # создаем dataframe
                df_f = pd.DataFrame(df_f_lst,
                                    columns=['name', 'tiker', 'close1', 'close2', 'izm_abs', 'izm_pr', 'margin_buy', 'link'])

                # сортировка по проценту изменения за день от большего к меньшему
                sort_df_f = df_f.sort_values(by='izm_pr', ascending=False)
                sort_df_f_name = f'report_table/future_izm_pr {now_date_txt_file()}_{now_time_txt_file()}.xlsx'
                sort_df_f.to_excel(sort_df_f_name)
                try:
                    reg_msg()
                    bot.send_document(message.chat.id, document=open(sort_df_f_name, 'rb'), disable_notification=True)
                    reg_msg()
                    bot.send_message(message.chat.id, '🚩')
                except Exception as e:
                    telega_error (e)
                
                msg = ''
                msg += 'Интервал: ДЕНЬ' \
                       '\n[сортировка по % изменения]\n\n'
                for m in range(sort_df_f.shape[0]):
                    # '0 -name', '1- tiker', '2- close1', '3- close2', '4-izm_abs', '5-izm_pr', '6-margin_buy', '7-link'
                    msg += f'{sort_df_f.iloc[m, 0]}' \
                           f'\n${sort_df_f.iloc[m, 1]}   {round(sort_df_f.iloc[m, 2],2)}   ' \
                           f'{round(sort_df_f.iloc[m, 3],2)}   {sort_df_f.iloc[m, 4]}   {sort_df_f.iloc[m, 5]}%'\
                           f'\nГО_buy:  {sort_df_f.iloc[m, 6]} руб.' 
                    msg += f'\n{sort_df_f.iloc[m, 7]}\n'
                    msg += f'\n'
                for message1 in util.smart_split(msg, 4000):
                    try:
                        reg_msg()
                        bot.send_message(message.chat.id, message1, disable_web_page_preview=True,
                                        disable_notification=True)
                    except Exception as e:
                        telega_error (e)

            stop_count_sec = time.time()
            delta = stop_count_sec - start_count_sec
            delta_min = delta / 60
            print()
            print(f'\n\nВсего прошло с момента запуска: {int(delta)} сек')
            print(f'в минутах с момента запуска: {int(delta_min)} мин')

        elif message.text == "pMOEX":
            print("запускаем чтение страниц")
            try:
                reg_msg()
                bot.send_message(message.chat.id, "запускаем чтение страниц", disable_notification=True)
            except Exception as e:
                telega_error (e)
            klst = []
            msg = ''
            msg = pM.parsMOEX(bot, message.chat.id, klst)
            for message1 in util.smart_split(msg, 4000):
                try:
                    reg_msg()
                    bot.send_message(message.chat.id, message1, disable_web_page_preview=True)
                except Exception as e:
                    telega_error (e)
        
        elif message.text == "ℹ️pMOEX1" or message.text == "pMOEX1":
            full_name_load = global_f_opt['full_future_name']
            print("запускаем чтение страниц")
            try:
                reg_msg()
                bot.send_message(message.chat.id, f"запускаем чтение страницы для {full_name_load}", disable_notification=True)
            except Exception as e:
                telega_error (e)
            f_lnk_1 = f'https://www.moex.com/ru/contract.aspx?code={full_name_load}'
            klst = []
            klst.append(f_lnk_1)
            msg = ''
            msg = pM.parsMOEX(bot, message.chat.id, klst)
            # for message1 in util.smart_split(msg, 4000):
            #     bot.send_message(message.chat.id, message1, disable_web_page_preview=True)

        elif message.text == 'show_oper':
            show_last_operation (bot,message.chat.id,'full','graf')
        
        elif message.text == 'show_oper_yeld':
            show_last_operation (bot,message.chat.id,'show_oper_yeld','graf')

        elif message.text == 'month_yeld':
            show_last_operation (bot,message.chat.id,'show_month_yeld_now','graf')


        elif message.text == "Показать абсолютно все фьючерсы":
            SHOW_ALL_FUTURES_ALL = 0
            # первичные настройки
            # интервал
            load_inter = 'DAY'
            # количество интервалов для загрузки
            load_period = 7
            with Client(TOKEN) as client:
                # загрузка списка всех доступных фьючерсов
                futures_instr = []
                flag_r = True
                while flag_r:
                    try:
                        futures = client.instruments.futures(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)
                        flag_r = False
                    except Exception as e:
                        print(datetime.now(timezone.utc).astimezone())
                        print('\nВОЗНИКЛА ОШИБКА ')
                        print(
                            'futures=client.instruments.futures'
                            '(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)')
                        print(e)
                        print()
                        flag_r = True # долбать систему до посинения пока не отдаст данные

                # преобразование списка фьючерсов в DataFrame и сохранения на диск в формате Excel
                futures_instr = futures.instruments
                df_f_l = create_df_future_list(futures_instr)
                df_drop = df_f_l.drop(columns=['first_trade_date', 'last_trade_date', 'expiration_date'])
                df_drop_f_name = f'report_table/future_full_list_{now_date_txt_file()}_{now_time_txt_file()}.xlsx'
                df_drop.to_excel(df_drop_f_name)

                # подготовка списка фьючерсов необходимого для загрузки баров
                future_list = []
                future_filter_instr = []
                for i in futures_instr:
                    future_list.append(f'{i.figi} \t {i.ticker} \t {i.name}')
                    future_filter_instr.append(i)
                future_list.sort()

                for j in future_list:
                    print(j)
                print(len(future_list))

                # загружаем бары
                print(f'Начинаем загрузку [{load_inter}] баров для всех {len(future_filter_instr)} фьючерсов')
                try:
                    reg_msg()
                    bot.send_message(message.chat.id,
                                    f'Начинаем загрузку [{load_inter}] баров абсолютно для всех {len(future_filter_instr)} фьючерсов ',
                                    disable_notification=True)
                except Exception as e:
                    telega_error (e)
                start_count_sec = time.time()  # счетчик секунд для определения общего времени загрузки
                stoks_status_bar = IncrementalBar(' ЗАГРУЗКА', max=len(future_filter_instr))
                count_res = 0
                # получаем текущую дату и время
                curr_time = datetime.now(timezone.utc).astimezone()
                # переводим в текстовый вид
                d1 = datetime.strftime(curr_time, '%d.%m.%Y')
                ht1 = datetime.strftime(curr_time, '%H:%M:%S')
                print(f'Текущая дата: {d1} \nВремя: {ht1}')
                try:
                    reg_msg()
                    bot.send_chat_action(message.chat.id, action='typing')
                except Exception as e:
                    telega_error (e)
                # определение даты начала и конца загрузки
                # от какой даты загрузить
                if load_inter == 'DAY':
                    load_from = datetime.now(timezone.utc).astimezone() - timedelta(days=load_period)
                # до какой даты загрузить
                load_to = datetime.now(timezone.utc).astimezone()
                bars_list = []
                bar_items = []
                # Основной цикл загрузки
                for k in future_filter_instr:
                    bar_items = []
                    repit = True # при возникновении ошибки предела запроса, если ТРУ то продолжить
                    while repit:
                        try:
                            bars = client.market_data.get_candles(
                                figi=k.figi,
                                from_=load_from,
                                to=load_to,
                                interval=CandleInterval.CANDLE_INTERVAL_DAY
                            )
                            repit = False
                        except Exception as ebx:
                            if ebx.code.name == 'RESOURCE_EXHAUSTED':
                                # вычисляем сколько секунд осталось до снятия блокировки на загрузки
                                stop_time = ebx.metadata.ratelimit_reset + 3
                                print()
                                print_date_time_now()
                                print(ebx)
                                print (f'сон {stop_time} сек...')
                                time.sleep(stop_time)
                                print_date_time_now()
                                print()
                                repit = True # попробовать загрузиться еще раз после выдержки времени блокировки
                            else:
                                print(ebx)
                                try:
                                    reg_msg()
                                    bot.send_message(message.chat.id,
                                                    '⚡️ОШИБКА⚡️ \nЧто-то пошло не так при загрузке данных из платформы Тинькофф.'
                                                    '\nВыполнение этой функции закончено⚡️', disable_notification=True)
                                    
                                    reg_msg()
                                    bot.send_message(message.chat.id, str(ebx), disable_notification=True)
                                except Exception as e:
                                    telega_error (e)
                                repit = False
                                return 0 # заканчиваем выполнение функции
                    
                    bar_items.append(bars.candles)
                    bar_items[0].insert(0, k)
                    bars_list.append(bar_items)
                    count_res += 1  # счетчик обращений
                    stoks_status_bar.next()
                    print(' ', k.name, k.ticker)

                # расчет и формирование DF_F

                df_f_lst = []

                for m in bars_list:
                    if len(m[0]) > 3:
                        izm = round((cast_money(m[0][-1].close) - cast_money(m[0][-2].close)) / cast_money(
                            m[0][-2].close) * 100, 2)
                        izm_abs = round((cast_money(m[0][-1].close) - cast_money(m[0][-2].close)), 2)
                        df_f_lst.append(
                            [m[0][0].name, m[0][0].ticker, cast_money(m[0][-2].close), cast_money(m[0][-1].close),
                             izm_abs, izm, f'https://www.tinkoff.ru/invest/futures/{m[0][0].ticker}'])

                df_f = pd.DataFrame(df_f_lst,
                                    columns=['name', 'tiker', 'close1', 'close2', 'izm_abs', 'izm_pr', 'link'])
                df_f.insert(7, "futures_type", 0)
                df_f.insert(8, "sector", 0)

                # Формирование сообщения с результатами расчетов
                msg = ''
                for m in bars_list:
                    if len(m[0]) > 3:
                        izm = round((cast_money(m[0][-1].close) - cast_money(m[0][-2].close)) / cast_money(
                            m[0][-2].close) * 100, 2)
                        izm_abs = round((cast_money(m[0][-1].close) - cast_money(m[0][-2].close)), 2)

                        print(m[0][0].ticker, '\t', cast_money(m[0][-2].close), '\t', cast_money(m[0][-1].close), '\t',
                              izm, '%\t', izm_abs, '\t', m[0][0].name)
                        msg += f'{m[0][0].name}\n{m[0][0].ticker}   {cast_money(m[0][-2].close)}   ' \
                               f'{cast_money(m[0][-1].close)}   {izm_abs}   {izm} %\n'
                        msg += f'https://www.tinkoff.ru/invest/futures/{m[0][0].ticker}\n'
                        msg += f'\n'
                stop_count_sec = time.time()
                delta = stop_count_sec - start_count_sec
                delta_min = delta / 60
                print(f'\n\nВсего прошло с момента запуска: {int(delta)} сек')
                print(f'в минутах с момента запуска: {int(delta_min)} мин')
                # выдача сообщений о результатах обработки не более 4000 символов за раз
                # for message1 in util.smart_split(msg,4000):
                #     bot.send_message(message.chat.id, message1, disable_web_page_preview=True)

                # сортировка по проценту изменения за день от большего к меньшему
                sort_df_f = df_f.sort_values(by='izm_pr', ascending=False)
                print(sort_df_f)
                sort_df_f_name = f'report_table/future_izm_pr {now_date_txt_file()}_{now_time_txt_file()}.xlsx'
                sort_df_f.to_excel(sort_df_f_name)
                try:
                    reg_msg()
                    bot.send_document(message.chat.id, document=open(sort_df_f_name, 'rb'))
                    reg_msg()
                    bot.send_message(message.chat.id, '🚩',disable_notification=True)
                except Exception as e:
                    telega_error (e)
                msg = ''
                msg += 'Интервал: ДЕНЬ (сорт. по % изм.)\n\n'
                for m in range(sort_df_f.shape[0]):
                    msg += f'{sort_df_f.iloc[m, 0]}\n{sort_df_f.iloc[m, 1]}   {sort_df_f.iloc[m, 2]}   ' \
                           f'{sort_df_f.iloc[m, 3]}   {sort_df_f.iloc[m, 4]}   {sort_df_f.iloc[m, 5]}%\n'
                    msg += f'{sort_df_f.iloc[m, 6]}\n'
                    msg += f'\n'
                for message1 in util.smart_split(msg, 4000):
                    try:
                        reg_msg()
                        bot.send_message(message.chat.id, message1, disable_web_page_preview=True)
                    except Exception as e:
                        telega_error (e)

        # комманды одномоментного графика
        elif message.text == "1gr":
            show_1gr_btn (bot, message.chat.id, "graf")
           
        # комманды одномоментного графика
        elif message.text == "15m1g":
            m_15_1gr = 0
            full_name_load = global_f_opt['full_future_name']
            depth_bars = global_f_opt ['depth_bars_1gr']
            graf_2(bot, message.chat.id, full_name_load, '15m', depth_bars)
            
        elif message.text == "1h1g":
            h_1_1gr = 0
            full_name_load = global_f_opt['full_future_name']
            depth_bars = global_f_opt ['depth_bars_1gr']
            graf_2(bot, message.chat.id, full_name_load, '1h', depth_bars)
            

        elif message.text == "4h1g":
                    h_4_1gr = 0
                    full_name_load = global_f_opt['full_future_name']
                    depth_bars = global_f_opt ['depth_bars_1gr']
                    graf_2(bot, message.chat.id, full_name_load, '4h', depth_bars)

        elif message.text == "1D1g":
            D_1_1gr = 0
            full_name_load = global_f_opt['full_future_name']
            depth_bars = global_f_opt ['depth_bars_1gr']
            graf_2(bot, message.chat.id, full_name_load, '1D', depth_bars)

        elif message.text == "1W1g":
            W_1_1gr = 0
            full_name_load = global_f_opt['full_future_name']
            depth_bars = global_f_opt ['depth_bars_1gr']
            graf_2(bot, message.chat.id, full_name_load, '1W', depth_bars)

        elif message.text == 'set1g':
            set_1gr = 0
            show_set_1gr_btn(bot, message.chat.id, '1gr')

        elif message.text == 'set2g':
            set_1gr = 0
            show_what_inter_1gr_bt(bot, message.chat.id, 'graf')
        # интервал для едтиничного графика
        elif message.text == '10_1g':
            global_f_opt ['depth_bars_1gr'] = 10
            show_1gr_btn (bot, message.chat.id, "graf")
        elif message.text == '20_1g':
            global_f_opt ['depth_bars_1gr'] = 20
            show_1gr_btn (bot, message.chat.id, "graf")
        elif message.text == '30_1g':
            global_f_opt ['depth_bars_1gr'] = 30
            show_1gr_btn (bot, message.chat.id, "graf")
        elif message.text == '40_1g':
            global_f_opt ['depth_bars_1gr'] = 40
            show_1gr_btn (bot, message.chat.id, "graf")
        elif message.text == '50_1g':
            global_f_opt ['depth_bars_1gr'] = 50
            show_1gr_btn (bot, message.chat.id, "graf")
        elif message.text == '60_1g':
            global_f_opt ['depth_bars_1gr'] = 60
            show_1gr_btn (bot, message.chat.id, "graf")
        elif message.text == '70_1g':
            global_f_opt ['depth_bars_1gr'] = 70
            show_1gr_btn (bot, message.chat.id, "graf")
        elif message.text == '80_1g':
            global_f_opt ['depth_bars_1gr'] = 80
            show_1gr_btn (bot, message.chat.id, "graf")

        # настройки глубины отображения для каждого интервала индивидуально
        elif message.text == '15m_1s':
            show_set_15m_1s_btn  (bot, message.chat.id, 'set2g')
        elif message.text == '1h_1s':
            show_set_1h_1s_btn  (bot, message.chat.id, 'set2g')
        elif message.text == '1D_1s':
            show_set_1D_1s_btn  (bot, message.chat.id, 'set2g')    
        elif message.text == '1W_1s':
            show_set_1W_1s_btn  (bot, message.chat.id, 'set2g') 
        # настройка отображения количества бар для часового графика для одномоментного отображения
        elif message.text == '10g1h':
            global_f_opt ['depth_bars_1gr_1h'] = 10
            show_run_repit_btn (bot, message.chat.id, '1h_1s')
        elif message.text == '20g1h':
            global_f_opt ['depth_bars_1gr_1h'] = 20
            show_run_repit_btn (bot, message.chat.id, '1h_1s')
        elif message.text == '30g1h':
            global_f_opt ['depth_bars_1gr_1h'] = 30
            show_run_repit_btn (bot, message.chat.id, '1h_1s')
        elif message.text == '40g1h':
            global_f_opt ['depth_bars_1gr_1h'] = 40
            show_run_repit_btn (bot, message.chat.id, '1h_1s')
        elif message.text == '50g1h':
            global_f_opt ['depth_bars_1gr_1h'] = 50
            show_run_repit_btn (bot, message.chat.id, '1h_1s')
        elif message.text == '60g1h':
            global_f_opt ['depth_bars_1gr_1h'] = 60
            show_run_repit_btn (bot, message.chat.id, '1h_1s')
        elif message.text == '70g1h':
            global_f_opt ['depth_bars_1gr_1h'] = 70
            show_run_repit_btn (bot, message.chat.id, '1h_1s')
        elif message.text == '80g1h':
            global_f_opt ['depth_bars_1gr_1h'] = 80
            show_run_repit_btn (bot, message.chat.id, '1h_1s')
        
        else:
            try:
                reg_msg()
                bot.send_message(message.chat.id, text=f"На команду [{message.text}] я не запрограммирован")
            except Exception as e:
                telega_error (e)

    # Обработчик нажатий на inline кнопки
    @bot.callback_query_handler(func=lambda call: True)
    def callback_worker(call):
        global global_f_opt, glodal_inp_interval, global_interval_load, global_interval_load_s, g_df, g_df_p
        global global_max_range, global_inp_var, global_val_nom, global_bag_of_stocks, global_finaly_bag_of_stocks
        global global_options, global_all_list, g_full_list_sh2, global_list_sel3, global_list_sel2
        # Управление покупкой и продажей
        if call.data == "sell1_bt":
            price_obj = global_bids_data['sell1']
            price = cast_money(price_obj.price)
            price_q = price_obj.price
            try:
                reg_msg()
                bot.send_message(chat_id=call.message.chat.id,
                                text=f'Нажата кнопка sell1 со значением: {price}')
            except Exception as e:
                telega_error (e)
            ID_ch = call.message.chat.id
            ID_user = call.from_user.id
            FIGI = global_bids_data['FIGI']
            oper_to = OrderDirection.ORDER_DIRECTION_SELL
            operation_go(bot, ID_ch, ID_user, FIGI, oper_to, price_q, 1)
        elif call.data == "buy1_bt":
            price_obj = global_bids_data['buy1']
            price = cast_money(price_obj.price)
            price_q = price_obj.price
            try:
                reg_msg()
                bot.send_message(chat_id=call.message.chat.id,
                                text=f'Нажата кнопка buy1 со значением: {price}')
            except Exception as e:
                telega_error (e)
            ID_ch = call.message.chat.id
            ID_user = call.from_user.id
            FIGI = global_bids_data['FIGI']
            oper_to = OrderDirection.ORDER_DIRECTION_BUY
            operation_go(bot, ID_ch, ID_user, FIGI, oper_to, price_q, 1)

        # Если нажали на одну из inline кнопок меняем список по которому потом производится загрузка и обработка
        elif call.data == "Set_Interval" and not global_in_progress_state:
            msg = f"------\nТекущие настройки: {global_interval_load_s}\nВыберите дискретность интервала обработки:"
            # Готовим кнопки
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            # По очереди готовим текст и обработчик для каждого знака зодиака
            b1 = types.InlineKeyboardButton(text='30  мин', callback_data='30min')
            b2 = types.InlineKeyboardButton(text='1 час', callback_data='1hour')
            b3 = types.InlineKeyboardButton(text='4 часа', callback_data='4hour')
            b4 = types.InlineKeyboardButton(text='День', callback_data='1day')
            b5 = types.InlineKeyboardButton(text='Неделя', callback_data='week')
            b6 = types.InlineKeyboardButton(text='Месяц', callback_data='month')
            b7 = types.InlineKeyboardButton(text='1 квартал', callback_data='quartal')
            keyboard.add(b1, b2, b3, b4, b5, b6, b7)
            try:
                reg_msg()
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=msg,
                                  reply_markup=keyboard)
                reg_msg()
                bot.answer_callback_query(call.id)
            except Exception as e:
                telega_error (e)

        elif call.data == "Set_VAL" and not global_in_progress_state:
            msg = f"------\nТекущие настройки: {global_val_nom}\nВыберите способ фильтрации списка акций:"
            # Готовим кнопки
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            # По очереди готовим текст и обработчик для каждого знака зодиака
            b1 = types.InlineKeyboardButton(text='USD', callback_data='USD')
            b2 = types.InlineKeyboardButton(text='RUB', callback_data='RUB')
            b3 = types.InlineKeyboardButton(text='С плечом', callback_data='plet')

            keyboard.add(b1, b2)
            try:
                reg_msg()
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=msg,
                                  reply_markup=keyboard)
            except Exception as e:
                telega_error (e)

        elif call.data == "USD" and not global_in_progress_state:
            if not (global_val_nom == "USD"):
                global_val_nom = "USD"
                global_finaly_bag_of_stocks = []
                for i in global_bag_of_stocks:
                    if i.currency == ti.Currency.usd:
                        global_finaly_bag_of_stocks.append(i)
                        # Формируем сообщение
                msg = ''
                msg = "в списке акции: USD"
                msg += f'\nПосле фильтрации: {len(global_finaly_bag_of_stocks)} акций.'
                msg += f'\nКоманда перезапуска загрузки /begin'
                print(msg)

                msg = f"Выберите настройки: интервал и валюта"
                keyboard = types.InlineKeyboardMarkup(row_width=3)
                if global_interval_load == CandleInterval.CANDLE_INTERVAL_30_MIN:
                    b1 = types.InlineKeyboardButton(text='✅30  мин', callback_data='30min')
                else:
                    b1 = types.InlineKeyboardButton(text='30  мин', callback_data='30min')
                if global_interval_load == CandleInterval.CANDLE_INTERVAL_HOUR:
                    b2 = types.InlineKeyboardButton(text='✅1 час', callback_data='1hour')
                else:
                    b2 = types.InlineKeyboardButton(text='1 час', callback_data='1hour')
                b3 = types.InlineKeyboardButton(text='❌4 часа', callback_data='4hour')
                if global_interval_load == CandleInterval.CANDLE_INTERVAL_DAY:
                    b4 = types.InlineKeyboardButton(text='✅День', callback_data='1day')
                else:
                    b4 = types.InlineKeyboardButton(text='День', callback_data='1day')
                if global_interval_load == CandleInterval.CANDLE_INTERVAL_WEEK:
                    b5 = types.InlineKeyboardButton(text='✅Неделя', callback_data='week')
                else:
                    b5 = types.InlineKeyboardButton(text='Неделя', callback_data='week')
                if global_interval_load == CandleInterval.CANDLE_INTERVAL_MONTH:
                    b6 = types.InlineKeyboardButton(text='✅Месяц', callback_data='month')
                else:
                    b6 = types.InlineKeyboardButton(text='Месяц', callback_data='month')
                b7 = types.InlineKeyboardButton(text='❌1 квартал', callback_data='quartal')
                b8 = types.InlineKeyboardButton(text='✅USD', callback_data='USD')
                b9 = types.InlineKeyboardButton(text='RUB', callback_data='RUB')
                br = types.InlineKeyboardButton("⚙️Настройка отображения результата", callback_data='Rez_Show')
                keyboard.add(b1, b2, b3, b4, b5, b6, b7)
                keyboard.row(b8, b9)
                keyboard.row(br)
                try:
                    reg_msg()
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=msg,
                                      reply_markup=keyboard)
                except Exception as e:
                    telega_error (e)

        elif call.data == "RUB" and not global_in_progress_state:
            if not (global_val_nom == "RUB"):
                global_val_nom = "RUB"
                global_finaly_bag_of_stocks = []
                for i in global_bag_of_stocks:
                    if i.currency == ti.Currency.rub:
                        global_finaly_bag_of_stocks.append(i)
                msg = ''
                msg = f"В списке акции в: {global_val_nom}"
                msg += f'\nПосле фильтрации: {len(global_finaly_bag_of_stocks)} акций.'
                msg += f'\nКоманда перезапуска загрузки /begin'
                print(msg)

                msg = f"Выберите настройки: интервал и валюта"
                keyboard = types.InlineKeyboardMarkup(row_width=3)
                if global_interval_load == CandleInterval.CANDLE_INTERVAL_30_MIN:
                    b1 = types.InlineKeyboardButton(text='✅30  мин', callback_data='30min')
                else:
                    b1 = types.InlineKeyboardButton(text='30  мин', callback_data='30min')
                if global_interval_load == CandleInterval.CANDLE_INTERVAL_HOUR:
                    b2 = types.InlineKeyboardButton(text='✅1 час', callback_data='1hour')
                else:
                    b2 = types.InlineKeyboardButton(text='1 час', callback_data='1hour')
                b3 = types.InlineKeyboardButton(text='❌4 часа', callback_data='4hour')
                if global_interval_load == CandleInterval.CANDLE_INTERVAL_DAY:
                    b4 = types.InlineKeyboardButton(text='✅День', callback_data='1day')
                else:
                    b4 = types.InlineKeyboardButton(text='День', callback_data='1day')
                if global_interval_load == CandleInterval.CANDLE_INTERVAL_WEEK:
                    b5 = types.InlineKeyboardButton(text='✅Неделя', callback_data='week')
                else:
                    b5 = types.InlineKeyboardButton(text='Неделя', callback_data='week')
                if global_interval_load == CandleInterval.CANDLE_INTERVAL_MONTH:
                    b6 = types.InlineKeyboardButton(text='✅Месяц', callback_data='month')
                else:
                    b6 = types.InlineKeyboardButton(text='Месяц', callback_data='month')
                b7 = types.InlineKeyboardButton(text='❌1 квартал', callback_data='quartal')
                b8 = types.InlineKeyboardButton(text='USD', callback_data='USD')
                b9 = types.InlineKeyboardButton(text='✅RUB', callback_data='RUB')
                br = types.InlineKeyboardButton("⚙️Настройка отображения результата", callback_data='Rez_Show')
                keyboard.add(b1, b2, b3, b4, b5, b6, b7)
                keyboard.row(b8, b9)
                keyboard.row(br)
                try:
                    reg_msg()
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=msg,
                                      reply_markup=keyboard)
                except Exception as e:
                    telega_error (e)

        elif call.data == "EUR" and not global_in_progress_state:
            try:
                reg_msg()
                bot.send_message(call.message.chat.id, "Еще не сделано")
            except Exception as e:
                telega_error (e)

        elif call.data == "ALL" and not global_in_progress_state:
            try:
                reg_msg()
                bot.send_message(call.message.chat.id, "Еще не сделано")
            except Exception as e:
                telega_error (e)

        elif call.data == "FAV" and not global_in_progress_state:
            try:
                reg_msg()
                bot.send_message(call.message.chat.id, "Еще не сделано")
            except Exception as e:
                telega_error (e)

        # ИЗМЕНЕНИЕ ИНТЕРВАЛА после выбора
        elif call.data == "30min" and not global_in_progress_state:
            if not (global_interval_load == CandleInterval.CANDLE_INTERVAL_30_MIN):
                global_interval_load = CandleInterval.CANDLE_INTERVAL_30_MIN
                global_interval_load_s = '30 минут'
                global_max_range = round(24 * 60 / 30, 0)
                print(f'Выбран интервал: {global_interval_load_s}')
                msg = f'Выбран интервал: {global_interval_load_s}'
                msg += f'\nКоманда перезапуска загрузки /begin'
                # bot.send_message(call.message.chat.id, msg)

                msg = f"Выберите настройки: интервал и валюта"
                # Готовим кнопки
                keyboard = types.InlineKeyboardMarkup(row_width=3)
                b1 = types.InlineKeyboardButton(text='✅30  мин', callback_data='30min')
                b2 = types.InlineKeyboardButton(text='1 час', callback_data='1hour')
                b3 = types.InlineKeyboardButton(text='❌4 часа', callback_data='4hour')
                b4 = types.InlineKeyboardButton(text='День', callback_data='1day')
                b5 = types.InlineKeyboardButton(text='Неделя', callback_data='week')
                b6 = types.InlineKeyboardButton(text='Месяц', callback_data='month')
                b7 = types.InlineKeyboardButton(text='❌1 квартал', callback_data='quartal')

                if global_val_nom == 'RUB':
                    b8 = types.InlineKeyboardButton(text='USD', callback_data='USD')
                    b9 = types.InlineKeyboardButton(text='✅RUB', callback_data='RUB')
                else:
                    b8 = types.InlineKeyboardButton(text='✅USD', callback_data='USD')
                    b9 = types.InlineKeyboardButton(text='RUB', callback_data='RUB')

                br = types.InlineKeyboardButton("⚙️Настройка Отображения результата", callback_data='Rez_Show')

                keyboard.add(b1, b2, b3, b4, b5, b6, b7)
                keyboard.row(b8, b9)
                keyboard.row(br)
                try:
                    reg_msg()
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=msg,
                                      reply_markup=keyboard)
                except Exception as e:
                    telega_error (e)

        elif call.data == "1hour" and not global_in_progress_state:
            if not (global_interval_load == CandleInterval.CANDLE_INTERVAL_HOUR):
                global_interval_load = CandleInterval.CANDLE_INTERVAL_HOUR
                global_max_range = round(24 * 7, 0)
                global_interval_load_s = '1 ЧАС'
                print(f'Выбран интервал: {global_interval_load_s}')
                msg = f'Выбран интервал: {global_interval_load_s}'
                msg += f'\nКоманда перезапуска загрузки /begin'
                # bot.send_message(call.message.chat.id, msg)

                msg = f"Выберите настройки: интервал и валюта"
                # Готовим кнопки
                keyboard = types.InlineKeyboardMarkup(row_width=3)
                b1 = types.InlineKeyboardButton(text='30  мин', callback_data='30min')
                b2 = types.InlineKeyboardButton(text='✅1 час', callback_data='1hour')
                b3 = types.InlineKeyboardButton(text='❌4 часа', callback_data='4hour')
                b4 = types.InlineKeyboardButton(text='День', callback_data='1day')
                b5 = types.InlineKeyboardButton(text='Неделя', callback_data='week')
                b6 = types.InlineKeyboardButton(text='Месяц', callback_data='month')
                b7 = types.InlineKeyboardButton(text='❌1 квартал', callback_data='quartal')

                if global_val_nom == 'RUB':
                    b8 = types.InlineKeyboardButton(text='USD', callback_data='USD')
                    b9 = types.InlineKeyboardButton(text='✅RUB', callback_data='RUB')
                else:
                    b8 = types.InlineKeyboardButton(text='✅USD', callback_data='USD')
                    b9 = types.InlineKeyboardButton(text='RUB', callback_data='RUB')

                br = types.InlineKeyboardButton("⚙️Настройка отображения результата", callback_data='Rez_Show')

                keyboard.add(b1, b2, b3, b4, b5, b6, b7)
                keyboard.row(b8, b9)
                keyboard.row(br)
                try:
                    reg_msg()
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=msg,
                                      reply_markup=keyboard)
                except Exception as e:
                    telega_error (e)

        elif call.data == "4hour" and not global_in_progress_state:
            pass

        elif call.data == "1day" and not global_in_progress_state:
            if not (global_interval_load == CandleInterval.CANDLE_INTERVAL_DAY):
                global_interval_load = CandleInterval.CANDLE_INTERVAL_DAY
                global_max_range = 365
                global_interval_load_s = 'ДЕНЬ'
                print(f'Выбран интервал: {global_interval_load_s}')
                # msg = f'Выбран интервал: {global_interval_load_s}'
                # msg+=f'\nКоманда перезапуска загрузки /begin'
                # bot.send_message(call.message.chat.id, msg)
                msg = f"Выберите настройки: интервал и валюта"
                # Готовим кнопки
                keyboard = types.InlineKeyboardMarkup(row_width=3)
                b1 = types.InlineKeyboardButton(text='30  мин', callback_data='30min')
                b2 = types.InlineKeyboardButton(text='1 час', callback_data='1hour')
                b3 = types.InlineKeyboardButton(text='❌4 часа', callback_data='4hour')
                b4 = types.InlineKeyboardButton(text='✅День', callback_data='1day')
                b5 = types.InlineKeyboardButton(text='Неделя', callback_data='week')
                b6 = types.InlineKeyboardButton(text='Месяц', callback_data='month')
                b7 = types.InlineKeyboardButton(text='❌1 квартал', callback_data='quartal')
                if global_val_nom == 'RUB':
                    b8 = types.InlineKeyboardButton(text='USD', callback_data='USD')
                    b9 = types.InlineKeyboardButton(text='✅RUB', callback_data='RUB')
                else:
                    b8 = types.InlineKeyboardButton(text='✅USD', callback_data='USD')
                    b9 = types.InlineKeyboardButton(text='RUB', callback_data='RUB')
                br = types.InlineKeyboardButton("⚙️Настройка отображения результата", callback_data='Rez_Show')
                keyboard.add(b1, b2, b3, b4, b5, b6, b7)
                keyboard.row(b8, b9)
                keyboard.row(br)
                try:
                    reg_msg()
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=msg,
                                      reply_markup=keyboard)
                except Exception as e:
                    telega_error (e)

        elif call.data == "week" and not global_in_progress_state:
            if not (global_interval_load == CandleInterval.CANDLE_INTERVAL_WEEK):
                global_interval_load = CandleInterval.CANDLE_INTERVAL_WEEK
                global_max_range = 52 * 2
                global_interval_load_s = 'НЕДЕЛЯ'
                print(f'Выбран интервал: {global_interval_load_s}')
                # msg = f'Выбран интервал: {global_interval_load_s}'
                # msg+=f'\nКоманда перезапуска загрузки /begin'
                # bot.send_message(call.message.chat.id, msg)
                msg = f"Выберите настройки: интервал и валюта"
                # Готовим кнопки
                keyboard = types.InlineKeyboardMarkup(row_width=3)
                b1 = types.InlineKeyboardButton(text='30  мин', callback_data='30min')
                b2 = types.InlineKeyboardButton(text='1 час', callback_data='1hour')
                b3 = types.InlineKeyboardButton(text='❌4 часа', callback_data='4hour')
                b4 = types.InlineKeyboardButton(text='День', callback_data='1day')
                b5 = types.InlineKeyboardButton(text='✅Неделя', callback_data='week')
                b6 = types.InlineKeyboardButton(text='Месяц', callback_data='month')
                b7 = types.InlineKeyboardButton(text='❌1 квартал', callback_data='quartal')
                if global_val_nom == 'RUB':
                    b8 = types.InlineKeyboardButton(text='USD', callback_data='USD')
                    b9 = types.InlineKeyboardButton(text='✅RUB', callback_data='RUB')
                else:
                    b8 = types.InlineKeyboardButton(text='✅USD', callback_data='USD')
                    b9 = types.InlineKeyboardButton(text='RUB', callback_data='RUB')
                br = types.InlineKeyboardButton("⚙️Настройка отображения результата", callback_data='Rez_Show')
                keyboard.add(b1, b2, b3, b4, b5, b6, b7)
                keyboard.row(b8, b9)
                keyboard.row(br)
                try:
                    reg_msg()
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=msg,
                                      reply_markup=keyboard)
                except Exception as e:
                    telega_error (e)

        elif call.data == "month" and not global_in_progress_state:
            if not (global_interval_load == CandleInterval.CANDLE_INTERVAL_MONTH):
                global_interval_load = CandleInterval.CANDLE_INTERVAL_MONTH
                global_max_range = 12 * 10
                global_interval_load_s = 'МЕСЯЦ'
                print(f'Выбран интервал: {global_interval_load_s}')
                # msg = f'Выбран интервал: {global_interval_load_s}'
                # msg+=f'\nКоманда перезапуска загрузки /begin'
                # bot.send_message(call.message.chat.id, msg)
                msg = f"Выберите настройки: интервал и валюта"
                # Готовим кнопки
                keyboard = types.InlineKeyboardMarkup(row_width=3)
                b1 = types.InlineKeyboardButton(text='30  мин', callback_data='30min')
                b2 = types.InlineKeyboardButton(text='1 час', callback_data='1hour')
                b3 = types.InlineKeyboardButton(text='❌4 часа', callback_data='4hour')
                b4 = types.InlineKeyboardButton(text='День', callback_data='1day')
                b5 = types.InlineKeyboardButton(text='Неделя', callback_data='week')
                b6 = types.InlineKeyboardButton(text='✅Месяц', callback_data='month')
                b7 = types.InlineKeyboardButton(text='❌1 квартал', callback_data='quartal')
                if global_val_nom == 'RUB':
                    b8 = types.InlineKeyboardButton(text='USD', callback_data='USD')
                    b9 = types.InlineKeyboardButton(text='✅RUB', callback_data='RUB')
                else:
                    b8 = types.InlineKeyboardButton(text='✅USD', callback_data='USD')
                    b9 = types.InlineKeyboardButton(text='RUB', callback_data='RUB')
                br = types.InlineKeyboardButton("⚙️Настройка отображения результата", callback_data='Rez_Show')
                keyboard.add(b1, b2, b3, b4, b5, b6, b7)
                keyboard.row(b8, b9)
                keyboard.row(br)
                try:
                    reg_msg()
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=msg,
                                      reply_markup=keyboard)
                except Exception as e:
                    telega_error (e)

        elif call.data == "no_load_last_Y" and not global_in_progress_state:
            if global_options['last_interval_calc']:
                global_options['last_interval_calc'] = False
                # msg = f'Последний интервал не будет учтен при обработке'
                # bot.send_message(call.message.chat.id, msg)

                # меняем клавиатуру
                msg = f"Исключить текущий интервал из загрузки и обработки?"
                keyboard = types.InlineKeyboardMarkup(row_width=2)
                b1 = types.InlineKeyboardButton(text='✅Да', callback_data='no_load_last_Y')
                b2 = types.InlineKeyboardButton(text='Нет', callback_data='no_load_last_N')
                keyboard.add(b1, b2)
                try:
                    reg_msg()
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=msg,
                                      reply_markup=keyboard)
                except Exception as e:
                    telega_error (e)

        elif call.data == "no_load_last_N" and not global_in_progress_state:
            if not (global_options['last_interval_calc']):
                global_options['last_interval_calc'] = True
                # msg = f'Последний интервал будет учитываться при обработке'
                # bot.send_message(call.message.chat.id, msg)
                # меняем клавиатуру
                msg = f"Исключить текущий интервал из загрузки и обработки?"
                keyboard = types.InlineKeyboardMarkup(row_width=2)
                b1 = types.InlineKeyboardButton(text='Да', callback_data='no_load_last_Y')
                b2 = types.InlineKeyboardButton(text='✅Нет', callback_data='no_load_last_N')
                keyboard.add(b1, b2)
                try:
                    reg_msg()
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=msg,
                                      reply_markup=keyboard)
                except Exception as e:
                    telega_error (e)

        elif call.data == "quartal" and not global_in_progress_state:
            pass

        elif call.data == "Rez_Show" and not global_in_progress_state:
            # bot.edit_message_text(chat_id=call.message.chat.id,message_id=call.message.id,
            #                       text=f"НАСТРОЙКИ ОТОБРАЖЕНИЯ РЕЗУЛЬТАТА ОБРАБОТКИ")
            try:
                reg_msg()
                bot.send_message(call.message.chat.id, text=f"НАСТРОЙКИ ОТОБРАЖЕНИЯ РЕЗУЛЬТАТА ОБРАБОТКИ")
            except Exception as e:
                telega_error (e)

            msg = "Исключить текущий интервал из загрузки и обработки?"
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            # По очереди готовим текст и обработчик для каждого
            if global_options['last_interval_calc']:
                b1 = types.InlineKeyboardButton(text='Да', callback_data='no_load_last_Y')
                b2 = types.InlineKeyboardButton(text='✅Нет', callback_data='no_load_last_N')
            else:
                b1 = types.InlineKeyboardButton(text='✅Да', callback_data='no_load_last_Y')
                b2 = types.InlineKeyboardButton(text='Нет', callback_data='no_load_last_N')
            keyboard.add(b1, b2)
            try:
                reg_msg()
                bot.send_message(call.message.chat.id, text=msg, reply_markup=keyboard)
            except Exception as e:
                telega_error (e)

            msg = f"ВЫБОРКА:1 Показать только маржинальные акции"
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            if global_options['list1_margin_only']:
                b1 = types.InlineKeyboardButton(text='✅Да', callback_data='show_margin')
                b2 = types.InlineKeyboardButton(text='Нет', callback_data='no_show_margin')
            else:
                b1 = types.InlineKeyboardButton(text='Да', callback_data='show_margin')
                b2 = types.InlineKeyboardButton(text='✅Нет', callback_data='no_show_margin')
            keyboard.add(b1, b2)
            try:
                reg_msg()
                bot.send_message(call.message.chat.id, text=msg, reply_markup=keyboard)
            except Exception as e:
                telega_error (e)

            msg = f"❌Показывать: ВЫБОРКА:1"
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            if global_options['list1_show']:
                b1 = types.InlineKeyboardButton(text='✅Да', callback_data='Sort1')
                b2 = types.InlineKeyboardButton(text='Нет', callback_data='Sort2')
            else:
                b1 = types.InlineKeyboardButton(text='Да', callback_data='Sort1')
                b2 = types.InlineKeyboardButton(text='✅Нет', callback_data='Sort2')
            keyboard.add(b1, b2)
            try:
                reg_msg()
                bot.send_message(call.message.chat.id, text=msg, reply_markup=keyboard)
            except Exception as e:
                telega_error (e)

            msg = f"❌ВЫБОРКА:1. Сортировать  по капитализации"
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            # По очереди готовим текст и обработчик для каждого
            if global_options['list1_sort_capital']:
                b1 = types.InlineKeyboardButton(text='✅Да', callback_data='Sort1')
                b2 = types.InlineKeyboardButton(text='Нет', callback_data='Sort2')
            else:
                b1 = types.InlineKeyboardButton(text='Да', callback_data='Sort1')
                b2 = types.InlineKeyboardButton(text='✅Нет', callback_data='Sort1')
            keyboard.add(b1, b2)
            try:
                reg_msg()
                bot.send_message(call.message.chat.id, text=msg, reply_markup=keyboard)
            except Exception as e:
                telega_error (e)

            msg = f"❌ВЫБОРКА:1 Сортировать по цене"
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            if global_options['list1_sort_by_price']:
                b1 = types.InlineKeyboardButton(text='✅Да', callback_data='list1_sort_by_price_yes')
                b2 = types.InlineKeyboardButton(text='Нет', callback_data='list1_sort_by_price_no')
            else:
                b1 = types.InlineKeyboardButton(text='Да', callback_data='list1_sort_by_price_yes')
                b2 = types.InlineKeyboardButton(text='✅Нет', callback_data='list1_sort_by_price_no')
            keyboard.add(b1, b2)
            try:
                reg_msg()
                bot.send_message(call.message.chat.id, text=msg, reply_markup=keyboard)
            except Exception as e:
                telega_error (e)

            msg = f"❌Показывать: ВЫБОРКА:2"
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            if global_options['list2_show']:
                b1 = types.InlineKeyboardButton(text='✅Да', callback_data='Sort1')
                b2 = types.InlineKeyboardButton(text='Нет', callback_data='Sort2')
            else:
                b1 = types.InlineKeyboardButton(text='Да', callback_data='Sort1')
                b2 = types.InlineKeyboardButton(text='✅Нет', callback_data='Sort2')
            keyboard.add(b1, b2)
            try:
                reg_msg()
                bot.send_message(call.message.chat.id, text=msg, reply_markup=keyboard)
            except Exception as e:
                telega_error (e)

            msg = f"❌Показывать: Шорт лист"
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            if global_options['short_list_show']:
                b1 = types.InlineKeyboardButton(text='✅Да', callback_data='Sort1')
                b2 = types.InlineKeyboardButton(text='Нет', callback_data='Sort2')
            else:
                b1 = types.InlineKeyboardButton(text='Да', callback_data='Sort1')
                b2 = types.InlineKeyboardButton(text='✅Нет', callback_data='Sort2')
            keyboard.add(b1, b2)
            try:
                reg_msg()
                bot.send_message(call.message.chat.id, text=msg, reply_markup=keyboard)
            except Exception as e:
                telega_error (e)

        elif call.data == "show_margin" and not global_in_progress_state:
            if not (global_options['list1_margin_only']):
                global_options['list1_margin_only'] = True
                # msg = f'Для ВЫБОРКИ 1 будут обработаны акции доступные только для маржинальной торговли'
                # bot.send_message(call.message.chat.id, msg)
                # меняем флажок на кнопках
                msg = f"ВЫБОРКА:1 Показать только маржинальные акции"
                keyboard = types.InlineKeyboardMarkup(row_width=2)
                b1 = types.InlineKeyboardButton(text='✅Да', callback_data='show_margin')
                b2 = types.InlineKeyboardButton(text='Нет', callback_data='no_show_margin')
                keyboard.add(b1, b2)
                try:
                    reg_msg()
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=msg,
                                      reply_markup=keyboard)
                except Exception as e:
                    telega_error (e)

        elif call.data == "no_show_margin" and not global_in_progress_state:
            if global_options['list1_margin_only']:
                global_options['list1_margin_only'] = False
                # msg = f'Для ВЫБОРКИ 1 будут обработаны акции без учета маржинальной торговли'
                # bot.send_message(call.message.chat.id, msg)
                # меняем флажок на кнопках
                msg = f"ВЫБОРКА:1 Показать только маржинальные акции"
                keyboard = types.InlineKeyboardMarkup(row_width=2)
                b1 = types.InlineKeyboardButton(text='Да', callback_data='show_margin')
                b2 = types.InlineKeyboardButton(text='✅Нет', callback_data='no_show_margin')
                keyboard.add(b1, b2)
                try:
                    reg_msg()
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=msg,
                                      reply_markup=keyboard)
                except Exception as e:
                    telega_error (e)

        elif call.data == "show_sel_2":
            msg = f"ВЫБОРКА 2: ({len(global_list_sel2)}шт.)\nкогда три интервала подряд: \n"
            msg += "происходят обновления максимумов без обновления минимумов, без учета закрытий.\n"
            list2 = []  # для сообщений telegram список
            msglst = ''  # переменная для сбора сообщения
            for zap1 in global_list_sel2:
                for z_dict in global_finaly_bag_of_stocks:
                    if z_dict.figi == zap1[0].figi:
                        msglst += f'[2]: {z_dict.ticker}   {z_dict.name}   [закр: {cast_money(zap1[-1].close)} {global_val_nom}]\n'
                        # if  global_val_nom=="RUB":
                        # msglst+=f'https://www.moex.com/ru/issue.aspx?board=TQBR&code={z_dict.ticker}\n'
                        msglst += f'https://www.tinkoff.ru/invest/stocks/{z_dict.ticker}\n'
                        msglst += '\n'
                        list2.append(msglst)
            list2.sort()
            msg = msg + f'\nВсего выбрано {len(list2)} акций:\n'
            for zap2 in list2:
                msg += zap2
            try:
                reg_msg()
                bot.send_message(call.message.chat.id, '📊')
            except Exception as e:
                telega_error (e)
            # выдача сообщений о результатах обработки не более 4000 символов за раз
            for message1 in util.smart_split(msg, 4000):
                try:
                    reg_msg()
                    bot.send_message(chat_id=call.message.chat.id, text=message1, disable_web_page_preview=True)
                except Exception as e:
                    telega_error (e)

        elif call.data == "show_sel_3":
            msg = "ВЫБОРКА 3: \nКогда перестали обновляться минимумы 4 интервала подряд:\n\n"
            for itm1 in global_list_sel3:
                # в списке global_list_sel3 каждый входящий список имеет на 0 месте объект самого инструмента
                msg += f'[3]: {itm1[0].ticker}   {itm1[0].name}    [закр.: {cast_money(itm1[-1].close)} {itm1[0].currency}]\n'
                msg += f'https://www.tinkoff.ru/invest/stocks/{itm1[0].ticker}\n'
                msg += '\n'

            # выдача сообщений о результатах обработки не более 4000 символов за раз
            for message1 in util.smart_split(msg, 4000):
                try:
                    reg_msg()
                    bot.send_message(chat_id=call.message.chat.id, text=message1, disable_web_page_preview=True)
                except Exception as e:
                    telega_error (e)

        try:
            bot.answer_callback_query(callback_query_id=call.id)
        except Exception as e:
                telega_error (e)
        


if __name__ == '__main__':
    main()
