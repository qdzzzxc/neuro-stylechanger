from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

d = {50: 0, 100: 1, 200: 2, 400: 3,
     'Monet': 0, 'VanGogh': 1, 'Cezanne': 2, 'Ukiyo-e': 3,
     'femmes_dalger': 0, 'scream': 1, 'starry_night': 2}


def choose_algorithm():
    kb_builder = InlineKeyboardBuilder()
    button_names = ['StyleTransfer', 'CycleGAN']
    back_data = ['StyleTransfer', 'CycleGAN']
    buttons = [InlineKeyboardButton(text=text, callback_data=data) for text, data in zip(button_names, back_data)]
    kb_builder.row(*buttons, width=2)
    return kb_builder.as_markup(resize_keyboard=True)


def choose_styletransfer_parameter():
    kb_builder = InlineKeyboardBuilder()
    button_names = ['Количество шагов', 'Режим preset']
    back_data = ['StyleTransfer_steps', 'StyleTransfer_preset']
    buttons = [InlineKeyboardButton(text=text, callback_data=data) for text, data in zip(button_names, back_data)]
    buttons.append(InlineKeyboardButton(text='Назад', callback_data='menu'))
    kb_builder.row(*buttons, width=2)
    return kb_builder.as_markup(resize_keyboard=True)


def choose_num_steps(chosen):
    kb_builder = InlineKeyboardBuilder()
    button_names = ['50 шагов', '100 шагов', '200 шагов', '400 шагов']
    back_data = ['50_steps', '100_steps', '200_steps', '400_steps']
    button_names[d[chosen]] += ' ✅'
    back_data[d[chosen]] = 'chosen'
    buttons = [InlineKeyboardButton(text=text, callback_data=data) for text, data in zip(button_names, back_data)]
    buttons.append(InlineKeyboardButton(text='Назад', callback_data='StyleTransfer_menu'))
    kb_builder.row(*buttons, width=2)
    return kb_builder.as_markup(resize_keyboard=True)


def choose_preset_picture(chosen):
    kb_builder = InlineKeyboardBuilder()
    button_names = ['Алжирские женщины', 'Крик', 'Звёздная ночь']
    back_data = ['femmes_dalger', 'scream', 'starry_night']
    button_names[d[chosen]] += ' ✅'
    back_data[d[chosen]] = 'chosen'
    buttons = [InlineKeyboardButton(text=text, callback_data=data) for text, data in zip(button_names, back_data)]
    buttons.append(InlineKeyboardButton(text='Назад', callback_data='StyleTransfer_menu'))
    kb_builder.row(*buttons, width=1)
    return kb_builder.as_markup(resize_keyboard=True)


def choose_mode(chosen):
    kb_builder = InlineKeyboardBuilder()
    button_names = ['Клод Моне', 'Винсент Ван Гог', 'Поль Сезанн', 'стиль Укиё-э']
    back_data = ['Monet', 'VanGogh', 'Cezanne', 'Ukiyo-e']
    button_names[d[chosen]] += ' ✅'
    back_data[d[chosen]] = 'chosen'
    buttons = [InlineKeyboardButton(text=text, callback_data=data) for text, data in zip(button_names, back_data)]
    buttons.append(InlineKeyboardButton(text='Назад', callback_data='menu'))
    kb_builder.row(*buttons, width=2)
    return kb_builder.as_markup(resize_keyboard=True)
