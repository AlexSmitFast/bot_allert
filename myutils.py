# -*- coding: utf8 -*-
# модуль с функционалом иммитирующим работу с виртуальным портфелем 
import os
import pandas as pd
from datetime import datetime, timedelta, timezone
import time
import json
import main_bot_allert
from tinkoff.invest import Client, InstrumentStatus, RequestError, OrderType, CandleInterval, \
    HistoricCandle, OperationType, PortfolioPosition, OrderDirection, Future, Quotation,Share, services
print('Запуск модуля с утилитами')

def cast_money(v):
    """    
    # Перевод объектов MoneyValue и Quotation в численную форму
    https://tinkoff.github.io/investAPI/faq_custom_types/
    """
    return v.units + v.nano / 1e9  # nano - 9 нулей

def create_df_bars_set(candl_shop):
    '''# Преобразование списка свечей Tinkoff в DataFrame'''
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

# выбрать акции только маржинальные в лонг
def select_margin_long_stoks(sh):  
    '''
    # выбрать акции только маржинальные в лонг
    '''
    sh_long_list = []
    for i in sh:
        if i.klong.units > 0:
            sh_long_list.append(i)
    print(f'Количество акций доступных в лонг с плечом: {len(sh_long_list)}')
    return sh_long_list