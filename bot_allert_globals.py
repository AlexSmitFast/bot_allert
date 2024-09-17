# модуль глобальных переменных
from tinkoff.invest import CandleInterval, OrderDirection

global_options = {
    'ac_id': '2142908538',  # номер счета
    'long_list_show': True,
    'short_list_show': False,
    'last_interval_calc': True,
    'list1_show': True,
    'list2_show': True,
    'list1_margin_only': False,
    'list1_sort_capital': True,
    'list1_sort_by_price': False,
    'val_nom': 'RUB',
    'interval_load': CandleInterval.CANDLE_INTERVAL_DAY,
    'pos_cl_target': 500000,
    'pos_cl_stop': 1000,
    'pos_cl_avg': 15000,
    'request_counter_grpc_of_m': 0,  # счетчик количества запросов к ГРПС платформе в минуту
    'request_counter_API_of_m': 0,  # счетчик количества запросов к API tincoff платформе в минуту
    'run_in_weekends': False, # признак того что, не надо автоматически запускать циклический график в выходные
    'run_in_night': False,  # признак того, что циклический график не будет работать глубокой ночью когда рынок закрыт
    'pause_post' : 3, # пауза вывода графика в чат
    'no_edit': False # признак того, что график и книпки надо  постоянно выдвать в чат, вместо редактирования статичного текста 

}

# глобальные настройки для регулярного вывода графика
global_f_opt = {
    'bot_err_count': 0,
    'activ_contr_name': '-9.24', # текущий активный контракт
    'next_activ_contr_name': '-12.24', # следующий контракт
    'full_future_name': 'MXI-9.24',
    'future_FIGI': 'FUTMXI092400',
    'future_ticker':'MMU4',
    'stocks_ticker': 'SBER',
    'type_analyse': 'future',
    'candl_interval': CandleInterval.CANDLE_INTERVAL_15_MIN,
    'depth_load_bars': 25, # количество баров для отображения
    'repeat_flag': False,  # Признак необходимости периодического повторения вывода графика в чат
                            # Признак выполнения функции с запросами к платформе, даже одиночного нециклического прохода.
                            # Необходим для того чтобы не было запущенно несколько параллельно одинаковых циклических процесса.
                            # По умочанию Telebot допускает до 2-х процессов одновременно, но можно и больше
    'In_process': False,  # признак того что выполняется циклическая функция отображения графика с кнопками управления
    'request_counter_f': 0,
    'depth_bars_1gr': 50, # количество баров для одномоментного отображения графика на заданном интервале
    'depth_bars_1gr_15min': 50, # количество баров для одномоментного отображения графика на 15 min интервале
    'depth_bars_1gr_1h': 30, # количество баров для одномоментного отображения графика на 1h интервале
    'depth_bars_1gr_1D': 25, # количество баров для одномоментного отображения графика на 1D интервале
    'depth_bars_1gr_1W': 10, # количество баров для одномоментного отображения графика на 1W интервале
    'show_oper_in_chat': False, # отображать или нет список операций сформировавших тек. позицию в чате с кнопками
    'MXI_last_quartal_cl': 3172.9, # последнее закрытие КВАРТАЛА по MXI
    'MXI_last_moth_cl': 3214.00, # последнее закрытие МЕСЯЦА по MXI
    'MXI_last_week_cl': 3209.95, # последнее закрытие НЕДЕЛИ по MXI
    'MXI_g1_moth_sell': 3300, # цель на месячных интервалах (уровень продаж)
    'MXI_g1_quart_sell': 3600, # цель на квартальных интервалах (уровень продаж)
    'MXI_g1_week_sell': 3333.5 # цель на недельных интервалах (уровень продаж)    
    }

# глобальные данные для покупок и продаж
global_bids_data = {
    'FIGI': '',
    'buy1': '0',
    'buy2': '0',
    'buy3': '0',
    'buy4': '0',
    'buy5': '0',
    'sale1': '0',
    'sale2': '0',
    'sale3': '0',
    'sale4': '0',
    'sale5': '0',
    'manual_order_figi': '',
    'manual_order_direct': OrderDirection.ORDER_DIRECTION_BUY,
    'manual_order_price': '0',
    'manual_order_quant': '0'
}