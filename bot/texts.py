texts = {
    'no filters': 'Я вас не понимаю :(',
    'info': 'Я бот, умеющий изменять стиль фотографий! '
            'Есть два режимы работы: \n'
            'перенос стиля с одной фотографии на другую и изменение фотографии под стиль какого-либо известного художника., '
            'Чтобы воспользоваться первым режимом, отправь сразу две фотографии, а чтобы вторым - одну.\n'
            'Также, вы можете использовать первый режим с одной из подобранных мной стилевых фотографий. '
            'Выбрать стилевую фотографию вы можете через команду /menu, а запустить генерацию через /preset \n'
            'Настроить режимы работы обеих моделей можно через /menu',
    'contacts': 'По всем вопросам и предложениям можете написать создателю бота: @qdzzzxc',
    'only two pics': 'Отправьте две либо одну фотографию!',
    'working_1': 'Картинка в обработке, подождите',
    'working_2': 'Картинки в обработке, подождите',
    'success': 'Полученный результат:',
    'preset_1step': 'В данный момент используется стилевая фотография: {}. \n'
                    'Для начала генерации просто отправьте фотографию, на которую будет перенесён стиль',
    'preset_only_1pic': 'Отправьте только одну фотографию, стиль которой хотите изменить',
    'error': 'Что-то пошло не так :( Повторите попытку и если ошибка повторится снова, напишите мне @qdzzzxc',
    'menu_style_transfer': 'Выберите, что вы хотите настроить: количество шагов в работе алгоритма'
                           ' или стилевую фотографию для команды /preset',
    'menu_style_transfer_preset': 'Выберите стилевую фотографию, использующуюся в команде /preset \n'
                                  'Представлены следующие варианты: Пабло Пикассо - Алжирские женщины,'
                                  'Эдвард Мунк - Крик, Винсент ван Гог - Звёздная ночь\n'
                                  'Эти картины представлены фотографиями ниже',
    'pic_for_preset': 'Отправьте картинку, на которую хотите перенести стиль с картины {}. \n'
                      'Чтобы изменить выбранную картины перейдите в /menu',
    'menu_style_transfer_steps': 'С помощью этих кнопок, вы можете установить количество шагов при работе алгоритма переноса стиля. \n'
                                 'Установка большого значения с использованием картинок большого размера очень затратно, из-за чего, '
                                 'скорее всего, алгоритм автоматически завершится досрочно.',
    'menu_cyclegan': 'Бот может преобразовать вашу картинку с использованием CycleGAN. \n'
                     'Есть 5 режимов работы, которые используют нейросети, обученные на картинах великих мировых художников. \n'
                     'Выберите между стилями картин Клода Моне, Винсента Ван Гога, Поля Сезанна или японским стилем Укиё-э. \n'
                     'Так же сейчас в процессе обучения находится нейросеть для стилистики картин Валентина Серова. '
                     'Данный режим в разработке, его результаты хуже, чем к других режимов \n'
                     'Пример работы алгоритма представлен на картинке ниже',
    'registration': 'Привет! \n'
                    'Я бот, умеющий переносить стиль с одной фотографии на другую! '
                    'Просто пришли мне две фотографии, '
                    'а я перенесу стиль со второй на первую и вышлю тебе результат :) \n'
                    'Настроить режим работы бота можно через /menu',
    'inner_timeout': 'Ваши картинки обрабатывались слишком долго и алгоритм был остановлен преждевременно. \n'
                     'Попробуйте уменьшить разрешение картинок или количество шагов через /menu',
    'menu': 'Выберите, какой из алгоритмов бота вы хотите настроить',
    'task_in_progress': 'Бот уже обрабатывает ваш запрос, подождите немного'
}
