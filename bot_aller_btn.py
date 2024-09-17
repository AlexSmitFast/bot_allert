print()
print('ЭТО ЗАГРУЖАЕТСЯ ОТДЕЛЬНЫЙ МОДУЛЬ с кнопками....')
print()
import telebot
from telebot import types, util  # для указания типов и переноса текста
from main_bot_allert import reg_msg, telega_error, gen_msg_actual_sets,mOrd_price_val
from bot_allert_globals import global_f_opt, global_bids_data, global_options
from main_bot_allert import global_set_from_orders
from tinkoff.invest import OrderDirection

# Отображение кнопок с тикерами акций для выбора
def show_btn_analitiks(bot: telebot.TeleBot, ID_ch, name_back_btn):
    '''#отображение кнопок с аналитикой баров фьючерсов'''
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
    b1 = types.KeyboardButton("Характеристики бара")
    b2 = types.KeyboardButton("Аналитика бара")
    ATR_b = types.KeyboardButton("ATR")
    iGO_b = types.KeyboardButton("ℹ️ГО")
    pMOEX1_b = types.KeyboardButton("pMOEX1")
    markup.add(b1, b2)
    markup.add(ATR_b, iGO_b, pMOEX1_b)
    menu_b = types.KeyboardButton("Меню")
    back_b = types.KeyboardButton(f"{name_back_btn}")
    markup.add(menu_b, back_b)
    try:
        reg_msg()
        bot.send_message(ID_ch, text="Выберите требуемое", reply_markup=markup)
    except Exception as e:
        telega_error (e)

def set_pause_graf (pause_rate, t_bot: telebot.TeleBot, ID_ch, name_back_btn):
    global  global_options
    global_options['pause_post'] = pause_rate # Время паузы выдачи графика
    try:
        reg_msg()
        t_bot.send_message(ID_ch, text=f"Установлена пауза вывода графика в чат: {global_options['pause_post']} сек.")
    except Exception as e:
        telega_error (e)




def show_pause_btn (t_bot: telebot.TeleBot, ID_ch, name_back_btn):
    global global_f_opt, global_options
    '''показать кнопки с вариантами задержки'''
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
    b1 = types.KeyboardButton("p1s")
    b2 = types.KeyboardButton("p2s")
    b3 = types.KeyboardButton("p3s")
    b4 = types.KeyboardButton("p4s")
    b5 = types.KeyboardButton("p5s")
    b6 = types.KeyboardButton("p6s")
    b7 = types.KeyboardButton("p7s")
    b8 = types.KeyboardButton("p8s")
    markup.add(b1, b2, b3, b4, b5, b6, b7, b8)
    menu_b = types.KeyboardButton("Меню")
    back_b = types.KeyboardButton(f"{name_back_btn}")
    markup.add(menu_b, back_b)
    try:
        reg_msg()
        t_bot.send_message(ID_ch, text=f"Настроить паузу выдачи графика и кнопок в чат.\nТекущее значение: {global_options['pause_post']} сек.", 
                       reply_markup=markup, disable_notification=True)
    except Exception as e:
        telega_error (e)


def show_1gr_btn (t_bot: telebot.TeleBot, ID_ch, name_back_btn):
    global global_f_opt
    '''показать кнопки одномоментного вывода графика'''
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
    b1 = types.KeyboardButton("15m1g")
    b2 = types.KeyboardButton("1h1g")
    b3 = types.KeyboardButton("4h1g")
    b4 = types.KeyboardButton("1D1g")
    b5 = types.KeyboardButton("1W1g")
    b6 = types.KeyboardButton("1M1g")
    b7 = types.KeyboardButton("1Q1g")
    b8 = types.KeyboardButton("set1g")
    markup.add(b1, b2, b3, b4, b5, b6, b7, b8)
    menu_b = types.KeyboardButton("Меню")
    back_b = types.KeyboardButton(f"{name_back_btn}")
    markup.add(menu_b, back_b)
    full_name_load = global_f_opt['full_future_name']
    depth_bars = global_f_opt ['depth_bars_1gr']
    try:
        reg_msg()
        t_bot.send_message(ID_ch, text=f"Показать график:\nинструмент: {full_name_load}, количество бар: {depth_bars}", 
                       reply_markup=markup, disable_notification=True)
    except Exception as e:
        telega_error (e)

def show_set_1gr_btn (t_bot: telebot.TeleBot, ID_ch, name_back_btn):
    global global_f_opt
    curr_delpth = global_f_opt ['depth_bars_1gr']
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=8)
    b1 = types.KeyboardButton("10_1g")
    b2 = types.KeyboardButton("20_1g")
    b3 = types.KeyboardButton("30_1g")
    b4 = types.KeyboardButton("40_1g")
    b5 = types.KeyboardButton("50_1g")
    b6 = types.KeyboardButton("60_1g")
    b7 = types.KeyboardButton("70_1g")
    b8 = types.KeyboardButton("80_1g")
    markup.add(b1, b2, b3, b4, b5, b6, b7, b8)
    menu_b = types.KeyboardButton("Меню")
    back_b = types.KeyboardButton(f"{name_back_btn}")
    markup.add(menu_b, back_b)
    try:
        reg_msg()
        t_bot.send_message(ID_ch, text=f"Выбор количества баров для отображения: \nтекущая настройка {curr_delpth}", 
                           reply_markup=markup, disable_notification=True)
    except Exception as e:
        telega_error (e)

def show_set_15m_1s_btn (t_bot: telebot.TeleBot, ID_ch, name_back_btn):
    global global_f_opt
    curr_delpth = global_f_opt ['depth_bars_1gr_15min']
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=8)
    b1 = types.KeyboardButton("10g15")
    b2 = types.KeyboardButton("20g15")
    b3 = types.KeyboardButton("30g15")
    b4 = types.KeyboardButton("40g15")
    b5 = types.KeyboardButton("50g15")
    b6 = types.KeyboardButton("60g15")
    b7 = types.KeyboardButton("70g15")
    b8 = types.KeyboardButton("80g15")
    markup.add(b1, b2, b3, b4, b5, b6, b7, b8)
    menu_b = types.KeyboardButton("Меню")
    back_b = types.KeyboardButton(f"{name_back_btn}")
    if global_f_opt['repeat_flag']:
        stop_b = types.KeyboardButton("❌Стоп_цикл_gr")
        markup.add(back_b, menu_b, stop_b)
    else:
        markup.add(back_b, menu_b  )
    try:
        reg_msg()
        t_bot.send_message(ID_ch, text=f"Выбор количества баров для отображения: \nтекущая настройка {curr_delpth}", 
                           reply_markup=markup, disable_notification=True)
    except Exception as e:
        telega_error (e)

def show_set_1h_1s_btn (t_bot: telebot.TeleBot, ID_ch, name_back_btn):
    global global_f_opt
    curr_delpth = global_f_opt ['depth_bars_1gr_1h']
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=8)
    b1 = types.KeyboardButton("10g1h")
    b2 = types.KeyboardButton("20g1h")
    b3 = types.KeyboardButton("30g1h")
    b4 = types.KeyboardButton("40g1h")
    b5 = types.KeyboardButton("50g1h")
    b6 = types.KeyboardButton("60g1h")
    b7 = types.KeyboardButton("70g1h")
    b8 = types.KeyboardButton("80g1h")
    markup.add(b1, b2, b3, b4, b5, b6, b7, b8)
    menu_b = types.KeyboardButton("Меню")
    back_b = types.KeyboardButton(f"{name_back_btn}")
    if global_f_opt['repeat_flag']:
        stop_b = types.KeyboardButton("❌Стоп_цикл_gr")
        markup.add(back_b, menu_b, stop_b)
    else:
        markup.add(back_b, menu_b  )
    try:
        reg_msg()
        t_bot.send_message(ID_ch, text=f"Выбор количества баров для отображения: \nтекущая настройка {curr_delpth}", 
                           reply_markup=markup, disable_notification=True)
    except Exception as e:
        telega_error (e)

def show_set_1D_1s_btn (t_bot: telebot.TeleBot, ID_ch, name_back_btn):
    global global_f_opt
    curr_delpth = global_f_opt ['depth_bars_1gr_1D']
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=6)
    b1 = types.KeyboardButton("10g1D")
    b2 = types.KeyboardButton("20g1D")
    b3 = types.KeyboardButton("30g1D")
    b4 = types.KeyboardButton("40g1D")
    b5 = types.KeyboardButton("50g1D")
    b6 = types.KeyboardButton("60g1D")
    markup.add(b1, b2, b3, b4, b5, b6)
    menu_b = types.KeyboardButton("Меню")
    back_b = types.KeyboardButton(f"{name_back_btn}")
    if global_f_opt['repeat_flag']:
        stop_b = types.KeyboardButton("❌Стоп_цикл_gr")
        markup.add(back_b, menu_b, stop_b)
    else:
        markup.add(back_b, menu_b  )
    try:
        reg_msg()
        t_bot.send_message(ID_ch, text=f"Выбор количества баров для отображения: \nтекущая настройка {curr_delpth}", 
                           reply_markup=markup, disable_notification=True)
    except Exception as e:
        telega_error (e)


def show_set_1W_1s_btn (t_bot: telebot.TeleBot, ID_ch, name_back_btn):
    global global_f_opt
    curr_delpth = global_f_opt ['depth_bars_1gr_1W']
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
    b1 = types.KeyboardButton("10g1W")
    b2 = types.KeyboardButton("20g1W")
    b3 = types.KeyboardButton("30g1W")
    b4 = types.KeyboardButton("40g1W")
    b5 = types.KeyboardButton("50g1W")
    markup.add(b1, b2, b3, b4, b5)
    menu_b = types.KeyboardButton("Меню")
    back_b = types.KeyboardButton(f"{name_back_btn}")
    if global_f_opt['repeat_flag']:
        stop_b = types.KeyboardButton("❌Стоп_цикл_gr")
        markup.add(back_b, menu_b, stop_b)
    else:
        markup.add(back_b, menu_b  )
    try:
        reg_msg()
        t_bot.send_message(ID_ch, text=f"Выбор количества баров для отображения: \nтекущая настройка {curr_delpth}", 
                           reply_markup=markup, disable_notification=True)
    except Exception as e:
        telega_error (e)

# отображение кнопок с интервалами для выбора периода построения графика фьючерсов
def show_interval_btn(bot: telebot.TeleBot, ID_ch, name_back_btn):
    global global_f_opt
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
    b1 = types.KeyboardButton("1min_gr")
    b2 = types.KeyboardButton("5min_gr")
    b3 = types.KeyboardButton("15min_gr")
    b4 = types.KeyboardButton("1hour_gr")
    b5 = types.KeyboardButton("1day_gr")
    markup.add(b1, b2, b3, b4, b5)
    menu_b = types.KeyboardButton("Меню")
    back_b = types.KeyboardButton(f"{name_back_btn}")
    if global_f_opt['repeat_flag']:
        stop_b = types.KeyboardButton("❌Стоп_цикл_gr")
        markup.add(back_b,menu_b, stop_b)
    else:
        markup.add(back_b, menu_b)
    try:
        reg_msg()
        bot.send_message(ID_ch, text="Выберите интервал", reply_markup=markup)
    except Exception as e:
        telega_error (e)


# отображение кнопок с выбором глубины загрузки и отображения
def show_step_btn(bot: telebot.TeleBot, ID_ch, name_back_btn):
    global global_f_opt
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=8)
    b1 = types.KeyboardButton("5b_gr")
    b2 = types.KeyboardButton("7b_gr")
    b3 = types.KeyboardButton("10b_gr")
    b4 = types.KeyboardButton("15b_gr")
    b5 = types.KeyboardButton("20b_gr")
    b6 = types.KeyboardButton("30b_gr")
    b7 = types.KeyboardButton("40b_gr")
    b8 = types.KeyboardButton("50b_gr")
    markup.add(b1, b2, b3, b4, b5, b6, b7, b8)
    menu_b = types.KeyboardButton("Меню")
    back_b = types.KeyboardButton(f"{name_back_btn}")
    if global_f_opt['repeat_flag']:
        stop_b = types.KeyboardButton("❌Стоп_цикл_gr")
        markup.add(back_b, menu_b, stop_b)
    else:
        markup.add(back_b,menu_b)
    try:
        reg_msg()
        bot.send_message(ID_ch, text="Выберите глубину", reply_markup=markup)
    except Exception as e:
        telega_error (e)


# отображение кнопок с выбором повтора
def show_repeat_btn(self: telebot.TeleBot, ID_ch, name_back_btn):
    show_run_repit_btn(self, ID_ch, name_back_btn)

# отображение кнопок с выбором
def show_run_repit_btn(t_bot: telebot.TeleBot, ID_ch, name_back_btn):
    global global_f_opt
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=6)
    b1 = types.KeyboardButton("1min_gr")
    b2 = types.KeyboardButton("5min_gr")
    b3 = types.KeyboardButton("15min_gr")
    b4 = types.KeyboardButton("1hour_gr")
    b5 = types.KeyboardButton("1day_gr")
    b6 = types.KeyboardButton("1gr")
    markup.add(b1, b2, b3, b4, b5, b6)
    menu_b = types.KeyboardButton("Меню")
    info_b = types.KeyboardButton("ℹ️F")
    m_oper_btn = types.KeyboardButton("🤘R")
    analiticks_btn = types.KeyboardButton('АиФ') # аналитика и информация о фьючерсах
    ATR_btn = types.KeyboardButton("ATR")
    set_b = types.KeyboardButton("⚙️Настроки_gr")
    back_b = types.KeyboardButton(f"{name_back_btn}")
    if global_f_opt['repeat_flag']:
        stop_b = types.KeyboardButton("❌Стоп_цикл_gr")
        markup.add(menu_b, ATR_btn, analiticks_btn, info_b, set_b, stop_b)
    else:
        circle_b = types.KeyboardButton("Цикл_gr")
        markup.add(menu_b, ATR_btn, analiticks_btn,  info_b, set_b, circle_b)
    msg =  gen_msg_actual_sets()
    try:
        reg_msg()
        t_bot.send_message(ID_ch, text=msg, reply_markup=markup)
    except Exception as e:
        telega_error (e) 
# отоюражение выбора интервала для расчета ATR
def show_ATR_btn (t_bot: telebot.TeleBot, ID_ch, name_back_btn):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=6)
    b15m = types.KeyboardButton('ATR(15min)')
    b30m = types.KeyboardButton('ATR(30min)')
    b1 = types.KeyboardButton("ATR(1h)")
    b2 = types.KeyboardButton("ATR(4h)")
    b3 = types.KeyboardButton("ATR(D)")
    b4 = types.KeyboardButton("ATR(W)")
    b5 = types.KeyboardButton("ATR(M)")
    markup.add(b15m, b30m, b1, b2, b3, b4, b5)
    menu_b = types.KeyboardButton("Меню")
    back_b = types.KeyboardButton(f"{name_back_btn}")
    markup.add(menu_b, back_b)
    try:
        reg_msg()
        t_bot.send_message(ID_ch, text=f"Кнопки для отображения доп. информации", reply_markup=markup)
    except Exception as e:
        telega_error (e)

# отоюражение выбора интервала для поиска паттернов на графике фьючерсов по команде find_ptrn
def show_find_ptrn_btn (t_bot: telebot.TeleBot, ID_ch, name_back_btn):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    b15m = types.KeyboardButton('find_ptrn(15min)')
    b30m = types.KeyboardButton('find_ptrn(30min)')
    b1 = types.KeyboardButton("find_ptrn(1h)")
    b2 = types.KeyboardButton("find_ptrn(4h)")
    b3 = types.KeyboardButton("find_ptrn(D)")
    b4 = types.KeyboardButton("find_ptrn(W)")
    b5 = types.KeyboardButton("find_ptrn(M)")
    markup.add(b1, b2, b3, b4, b5)
    menu_b = types.KeyboardButton("Меню")
    back_b = types.KeyboardButton(f"{name_back_btn}")
    markup.add(menu_b, back_b)
    try:
        reg_msg()
        t_bot.send_message(ID_ch, text=f"Кнопки для отображения доп. информации", reply_markup=markup)
    except Exception as e:
        telega_error (e)


# кнопок с отображением информации
def show_info_2_btn (t_bot: telebot.TeleBot, ID_ch, name_back_btn):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=6)
    b1 = types.KeyboardButton("💼f3")
    b2 = types.KeyboardButton("f11")
    b3 = types.KeyboardButton("f1")
    b4 = types.KeyboardButton("f1-")
    b5 = types.KeyboardButton("f1--")
    b6 = types.KeyboardButton("f1---")
    b7 = types.KeyboardButton("s1")
    b8 = types.KeyboardButton("f15")
    markup.add(b1, b2, b3, b4, b5, b6, b7, b8)
    menu_b = types.KeyboardButton("Меню")
    back_b = types.KeyboardButton(f"{name_back_btn}")
    info_b = types.KeyboardButton("ℹ️F")
    markup.add(menu_b, back_b, info_b)
    try:
        reg_msg()
        t_bot.send_message(ID_ch, text=f"Кнопки для отображения доп. информации", reply_markup=markup)
    except Exception as e:
        telega_error (e)


# кнопки с отображением направления для выставления лимитной заявки по желаемой цене
def manual_orders_btn (t_bot: telebot.TeleBot, msg_obj: telebot.types.Message, name_back_btn):
    global global_set_from_orders, global_f_opt
    
    ID_ch = msg_obj.chat.id
    user_id = msg_obj.from_user.id
    user_true_id = global_set_from_orders['user_id']
    if int (user_id) == int (user_true_id):
        # наименование актива для вывода в чат
        full_name_aktiv = global_f_opt['full_future_name']
        # Внести наименование актива в глобальный список для ручной операции
        global_bids_data['manual_order_figi'] = full_name_aktiv
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        b1 = types.KeyboardButton("🟢mOrd_Купить")
        b2 = types.KeyboardButton("🟥mOrd_Продать")
        midle_b = types.KeyboardButton(f"{full_name_aktiv}")
        markup.add(b2, midle_b, b1)
        menu_b = types.KeyboardButton("Меню")
        back_b = types.KeyboardButton(f"{name_back_btn}")
        markup.add(menu_b,back_b)
        try:
            reg_msg()
            t_bot.send_message(ID_ch, text=f"{full_name_aktiv}", reply_markup=markup)
            reg_msg()
            t_bot.send_message(ID_ch, text=f"Выбирите направление совершения сделки для {full_name_aktiv}", reply_markup=markup)
        except Exception as e:
            telega_error (e)

# кнопки с отображением значений цены для выполнения операции
def mOrd_price_btn (t_bot: telebot.TeleBot, ID_ch, name_back_btn):
    # определить цену из стакана и предложить значения на кнопках
    m_ord = global_bids_data ['manual_order_direct']
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=6)
        
    if m_ord == OrderDirection.ORDER_DIRECTION_BUY:
        m_ord = "КУПИТЬ"
        b1 = types.KeyboardButton('+++') # сделать значения цен на покупку
    elif m_ord == OrderDirection.ORDER_DIRECTION_SELL:
        m_ord = "ПРОДАТЬ"
        b1 = types.KeyboardButton('---') # сделать значения цен на продажу
    else:
        m_ord = "Не понятно"
        b1 = types.KeyboardButton('???') # вернуться назад
    print ("Направление операции:", m_ord)
    b2 = types.KeyboardButton('🙅Отмена_mOrd') # сделать значения цен на покупку
    markup.add(b1)
    markup.add(b2)
    msg = t_bot.send_message(ID_ch, f'Введите ЦЕНУ для операции: {m_ord}', reply_markup=markup)
    try:
        reg_msg()
        t_bot.register_next_step_handler(msg, mOrd_price_val, t_bot)
    except Exception as e:
        telega_error (e)

def show_what_inter_1gr_bt (t_bot: telebot.TeleBot, ID_ch, name_back_btn):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=8)
    b1 = types.KeyboardButton("15m_1s")
    b2 = types.KeyboardButton("1h_1s")
    b3 = types.KeyboardButton("1D_1s")
    b4 = types.KeyboardButton("1W_1s")
    markup.add(b1, b2, b3, b4)
    menu_b = types.KeyboardButton("Меню")
    back_b = types.KeyboardButton(f"{name_back_btn}")
    if global_f_opt['repeat_flag']:
        stop_b = types.KeyboardButton("❌Стоп_цикл_gr")
        markup.add(back_b, menu_b, stop_b)
    else:
        markup.add(back_b, menu_b  )
    try:
        reg_msg()
        t_bot.send_message(ID_ch, text=f"Выбор интервала", reply_markup=markup, disable_notification=True)
    except Exception as e:
        telega_error (e)

# Отображение кнопок с фьючерсами для выбора
def show_futures_btn(t_bot: telebot.TeleBot, ID_ch, name_btn):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
    b_luk = types.KeyboardButton("LKOH_F_gr")
    b2_sber = types.KeyboardButton("SBRF_F_gr")
    b3_gazprom = types.KeyboardButton("GAZP_F_gr")
    b_ydx = types.KeyboardButton('YNDF_n_gr')
    b_ng = types.KeyboardButton("NG_gr")
    b_ED = types.KeyboardButton("ED_gr")
    b_si = types.KeyboardButton("Si_gr")
    b_spy = types.KeyboardButton("SPYF_gr")
    b_mxi = types.KeyboardButton("MXI_gr")
    b_mxi_next = types.KeyboardButton("MXI_n_gr")
    b_mix_big = types.KeyboardButton("MIX_gr")
    b_rtc_mini = types.KeyboardButton("RTSM_gr")
    b_rtc_big =  types.KeyboardButton("RTS_gr")    
    menu_b = types.KeyboardButton("Меню")
    markup.add(b_si, b_spy, b_mxi_next, b_mxi)
    markup.add(b_luk, b3_gazprom, b2_sber,b_ydx)
    markup.add(b_ng, b_ED, b_mix_big, b_rtc_mini, b_rtc_big)
    if global_f_opt['repeat_flag']:
        graf_b = types.KeyboardButton("graf")
        markup.add(menu_b, graf_b)
    else:
        graf_b = types.KeyboardButton("graf")
        markup.add(menu_b, graf_b)
    try:
        reg_msg()
        t_bot.send_message(ID_ch, text="Выберите тип фьючерса", reply_markup=markup)
    except Exception as e:
        telega_error (e)


# Отображение кнопок с тикерами акций для выбора
def show_stocks_btn(bot: telebot.TeleBot, ID_ch, name_back_btn):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
    b1 = types.KeyboardButton("GAZP_gr")
    b2 = types.KeyboardButton("SBER_gr")
    b3 = types.KeyboardButton("LUKH_gr")
    b4 = types.KeyboardButton("NLMK_gr")
    b5 = types.KeyboardButton("ROSN_gr")
    markup.add(b1, b2, b3, b4, b5)
    menu_b = types.KeyboardButton("Меню")
    back_b = types.KeyboardButton(f"{name_back_btn}")
    if global_f_opt['repeat_flag']:
        stop_b = types.KeyboardButton("❌Стоп_цикл_gr")
        markup.add(back_b, menu_b, stop_b)
    else:
        markup.add(back_b, menu_b)
    try:
        reg_msg()
        bot.send_message(ID_ch, text="Выберите тикер", reply_markup=markup)
    except Exception as e:
        telega_error (e)

# кнопки раздела информации о фьючерсах
def show_info_futures_btn(t_bot: telebot.TeleBot, ID_ch, name_btn):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=6)
    b1 = types.KeyboardButton("Инфо_счет")
    b3 = types.KeyboardButton("ℹ️ГО") # информация о ГО для текущего фьючерса
    b4 = types.KeyboardButton("pMOEX1") # количество позиций физиков (соотношение) для текущего фьючерса
    b5 = types.KeyboardButton("/show_go") # размер ГО для всех фьчерсов
    b6 = types.KeyboardButton("⭐️Показать фьючерсы")
    bw = types.KeyboardButton("⭐️WEEK фьючерсы")
    b7 = types.KeyboardButton('Показать все фьючерсы')
    b8 = types.KeyboardButton('Показать абсолютно все фьючерсы')
    b9 = types.KeyboardButton('Поиск отклонения фьючерсов')
    b11 = types.KeyboardButton('pMOEX')
    b12 = types.KeyboardButton('тэги')
    ur_btn = types.KeyboardButton("ur") #атопоиск уровней
    atr_btn = types.KeyboardButton("ATR(i)")
    ptrn_btn = types.KeyboardButton("find_ptrn(i)")
    inter_antiks_btn = types.KeyboardButton("find_ptrn") 

    markup.add(b1, b3, b4,b5)
    markup.add(b7, b6)
    markup.add(b8, b9)
    markup.add(ur_btn, bw)
    markup.add(b12, b11)
    markup.add(atr_btn, inter_antiks_btn, ptrn_btn)
    menu_b = types.KeyboardButton("Меню") # вернуться в главное меню
    back_b = types.KeyboardButton('graf') # вернуться назад
    markup.add(menu_b, back_b)
    try:
        reg_msg()
        t_bot.send_message(ID_ch, text="Выберите настройку", reply_markup=markup)
    except Exception as e:
        telega_error (e)


#  кнопки информации о портфеле
def show_btn_port_info(t_bot: telebot.TeleBot, ID_ch, back_btn: str):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=6)
    b1 = types.KeyboardButton("ℹ️М") # Ликвидный портфель (liquid_portfolio)
    b2 = types.KeyboardButton("рсчт") # Кнопки для отображения доп. информации по портфелю
    b10 = types.KeyboardButton('show_oper') # Список операций по счету: 2142908538
    b_shAZ = types.KeyboardButton("shAZ") # Активные заявоки по счету 2142908538
    b_mOrd = types.KeyboardButton("mOrd") # ручная заявка с вводом требуемой цены
    b_op_yld = types.KeyboardButton ('show_oper_yeld') # Доходность_операций FUTMXI09230
    b_m_yld = types.KeyboardButton('month_yeld') # Результаты за месяц 1 по портфелю
    menu_b = types.KeyboardButton("Меню") # вернуться в главное меню
    back_b = types.KeyboardButton(back_btn) # вернуться назад
    markup.add(b1, b2, b10, b_shAZ, b_mOrd, b_op_yld, b_m_yld)
    markup.add(menu_b, back_b)
    try:
        reg_msg()
        t_bot.send_message(ID_ch, text="Кнопки данных о портфеле", reply_markup=markup)
    except Exception as e:
        telega_error (e) 

def show_btn_set_pause_graf (t_bot: telebot.TeleBot, ID_ch, name_btn):
    '''кнопки с периодами для паузы вывода графика'''
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=6)
    b1 = types.KeyboardButton("p_1s")
    b2 = types.KeyboardButton("p_2s")
    b3 = types.KeyboardButton("p_2.5s")
    b4 = types.KeyboardButton("p_3s")
    b5 = types.KeyboardButton("p_4s")
    markup.add(b1, b2, b3, b4,b5)
    try:
        reg_msg()
        t_bot.send_message(ID_ch, text="Выберите паузу", reply_markup=markup)
    except Exception as e:
        telega_error (e)

# кнопки раздела настроек
def show_type_set(t_bot: telebot.TeleBot, ID_ch, name_btn):    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    b1 = types.KeyboardButton("Тип_актива_gr")
    b3 = types.KeyboardButton("Фьючерсы_gr")
    b2 = types.KeyboardButton("Интервал_gr")
    b4 = types.KeyboardButton("Кол-во_бар_gr")
    show_pos_b = types.KeyboardButton("show_pos_s")
    show_b = types.KeyboardButton('st_bt_opr') # вкл/откл управления кнопками
    b_si = types.KeyboardButton("Si_gr")
    b_spy = types.KeyboardButton("SPYF_gr")
    b_mxi = types.KeyboardButton("MXI_gr")
    b_set_pause = types.KeyboardButton("set_pause_graf") # настройка: установить паузу вывода графика с кнопками в чат
    b_sw_bot = types.KeyboardButton("sw_bot")
    b_tst_sw_bot = types.KeyboardButton("tst_sw_bot")
    # d_set_no_edit = types.KeyboardButton("set_no_edit") # настройка: вывод в чат последовательно или через статичную редактируюмую картинку и кнопки
    markup.add(b_tst_sw_bot, b_sw_bot, b_set_pause)
    markup.add(show_b, show_pos_b)
    markup.add(b1, b2, b3, b4)
    markup.add(b_spy,b_si, b_mxi)
    menu_b = types.KeyboardButton('Меню') # вернуться назад
    graf_b = types.KeyboardButton("graf") # вернуться в главное меню
 
    if global_f_opt['repeat_flag']:
        stop_b = types.KeyboardButton("❌Стоп_цикл_gr")
        markup.add(menu_b, graf_b)
    else:
        markup.add(menu_b, graf_b)
    msg = gen_msg_actual_sets()
    try:
        reg_msg()
        t_bot.send_message(ID_ch, text=msg, reply_markup=markup)
    except Exception as e:
        telega_error (e)

print('Модуль с кнопками ЗАГРУЖЕН')