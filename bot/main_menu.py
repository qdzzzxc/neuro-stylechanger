from aiogram.types import BotCommand


async def set_main_menu(bot, mode):
    commands = {'/info': 'Информация о боте',
                '/menu': 'Выбрать режим',
                '/preset': 'Использовать одну из предоставленных стилевых картинок для генерации',
                '/contacts': 'Контакты создателя бота'}
    if mode == 'cpu':
        commands.pop('/preset')
    main_menu_commands = [BotCommand(
        command=command,
        description=description
    ) for command, description in commands.items()]
    await bot.set_my_commands(main_menu_commands)
