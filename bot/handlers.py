import os

from PIL import Image
from aiogram import F, Router
from aiogram.filters import Command, BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.types import BufferedInputFile
from aiogram.utils.media_group import MediaGroupBuilder

from keyboards import choose_num_steps, choose_algorithm, choose_mode, choose_styletransfer_parameter, \
    choose_preset_picture
from nats_response import request_to_neuro
from texts import texts
from io import BytesIO

storage = MemoryStorage()
router = Router()

d = {'Monet': 'стиль Клода Моне', 'VanGogh': 'стиль Винсента Ван Гога', 'Cezanne': 'стиль Поля Сезанна',
     'Ukiyo-e': 'японский стиль Укиё-э', 'Serov': 'стиль Валентина Серова',
     'femmes_dalger': 'Алжирские женщины', 'scream': 'Крик', 'starry_night': 'Звёздная ночь'}

example_photos = {}


class UserStates(StatesGroup):
    wait_for_response = State()
    have_pic = State()
    preset_wait_for_picture = State()
    dls = State()


class IsRegistered(BaseFilter):
    async def __call__(self, message: Message, dao) -> bool:
        if dao.data.get(str(message.chat.id), False):
            return False
        else:
            dao[str(message.chat.id)] = {"steps": 50, "mode": "Monet", "preset": "starry_night"}
            return True


class IsAlonePhoto(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.photo and message.media_group_id is None


@router.message(IsRegistered())
async def welcome_message_response(message: Message):
    await message.reply(text=texts['registration'])


# требование по сдаче проекта
@router.message(Command(commands="transfer_style"))
async def dls_command_response(message: Message, state: FSMContext):
    await message.answer(text='Отправьте любую фотографию')
    await state.set_state(UserStates.dls)


@router.message(IsAlonePhoto(), UserStates.dls)
async def dls_command_response(message: Message, nats, dao, state: FSMContext):
    await alone_message_response(message, nats, dao, state)
    await state.clear()


@router.message(Command(commands=("start", "info")))
async def info_command_response(message: Message, mode):
    await message.answer(text=texts['info'][mode])


@router.message(Command(commands=("contacts", "help")))
async def help_command_response(message: Message):
    await message.answer(text=texts['contacts'])


@router.message(UserStates.preset_wait_for_picture, Command(commands="menu"))
async def menu_instead_of_preset(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(text=texts['menu'], reply_markup=choose_algorithm())


@router.message(Command(commands="menu"))
async def menu_command_response(message: Message, dao, mode):
    if mode == 'cpu':
        text = texts['menu_cyclegan']

        if not example_photos.get('cyclegan', False):
            photo = FSInputFile(f'./pictures/cyclegan/cyclegan_example.png')
            photo_message = await message.answer_photo(photo=photo, caption=text,
                                                       reply_markup=choose_mode(dao[str(message.from_user.id)]['mode'],
                                                                                back=False))
            example_photos['cyclegan'] = photo_message.photo[-1].file_id
        else:
            await message.answer_photo(photo=example_photos['cyclegan'], caption=text,
                                       reply_markup=choose_mode(dao[str(message.from_user.id)]['mode'], back=False))

    else:
        await message.answer(text=texts['menu'], reply_markup=choose_algorithm())


@router.message(UserStates.wait_for_response)
async def task_in_progress(message: Message):
    await message.reply(text=texts['task_in_progress'])


@router.message(Command(commands="preset"))
async def menu_command_response(message: Message, dao, mode, state: FSMContext):
    if mode == 'cpu':
        await message.answer(text=texts['cpu_mode_preset'])
    else:
        await message.answer(text=texts['pic_for_preset'].format(d[dao[str(message.chat.id)]['preset']]))
        await state.set_state(UserStates.preset_wait_for_picture)


@router.message(IsAlonePhoto(), UserStates.preset_wait_for_picture)
async def menu_instead_of_preset(message: Message, nats, dao, state: FSMContext):
    temp_message = await message.answer(text=texts['working_1'])

    await state.set_state(UserStates.wait_for_response)

    images = []

    temp_image = BytesIO()
    await message.bot.download(file=message.photo[-1].file_id, destination=temp_image)
    images.append(temp_image)

    img = Image.open(f'./pictures/styletransfer/{dao[str(message.chat.id)]["preset"]}.jpg')
    temp_image = BytesIO()
    img.save(temp_image, format='PNG')
    images.append(temp_image)

    res, error = await request_to_neuro(images, model="StyleTransfer", connection=nats,
                                        steps=dao[str(message.chat.id)]['steps'])

    if res:
        pillow_image = BufferedInputFile(res, filename="pillow_image.png")

        await temp_message.edit_text(text=texts['success'])

        await message.answer_photo(pillow_image)

        if error:
            await message.answer(text=texts[error])

    # nats timeout error
    else:
        await temp_message.edit_text(text=texts['error'])

    await state.clear()


@router.message(UserStates.preset_wait_for_picture)
async def menu_instead_of_preset(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(text=texts['preset_only_1pic'])


@router.callback_query(F.data == 'StyleTransfer_menu')
async def styletransfer_menu_callback_response(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state == UserStates.have_pic:
        data = await state.get_data()
        for pic in data['picture_message']:
            await pic.delete()

        await state.clear()

    await styletransfer_callback_response(callback)


@router.callback_query(F.data == 'menu')
async def menu_callback_response(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state == UserStates.have_pic:
        data = await state.get_data()
        await data['picture_message'].delete()
        await state.clear()
    await callback.message.edit_text(text=texts['menu'], reply_markup=choose_algorithm())


@router.callback_query(F.data == 'StyleTransfer')
async def styletransfer_callback_response(callback: CallbackQuery):
    text = texts['menu_style_transfer']
    await callback.message.edit_text(text=text, reply_markup=choose_styletransfer_parameter())


@router.callback_query(F.data == 'StyleTransfer_steps')
async def styletransfer_steps_callback_response(callback: CallbackQuery, dao):
    text = texts['menu_style_transfer_steps']
    await callback.message.edit_text(text=text, reply_markup=choose_num_steps(dao[str(callback.from_user.id)]['steps']))


@router.callback_query(F.data.in_({'50_steps', '100_steps', '200_steps', '400_steps'}))
async def steps_button_pressed(callback: CallbackQuery, dao):
    steps = int(str(callback.data).split('_')[0])
    dao[str(callback.from_user.id)]['steps'] = steps
    dao.save()
    text = f'Установлена глубина алгоритма в {steps} шагов'
    await callback.message.edit_text(text=text, reply_markup=choose_num_steps(steps))


@router.callback_query(F.data == 'StyleTransfer_preset')
async def styletransfer_preset_callback_response(callback: CallbackQuery, dao, state: FSMContext):
    text = texts['menu_style_transfer_preset']
    await callback.message.edit_text(text=text,
                                     reply_markup=choose_preset_picture(dao[str(callback.from_user.id)]['preset']))

    media_group = MediaGroupBuilder()

    if not example_photos.get('styletransfer', False):
        for pic in os.listdir(r'./pictures/styletransfer'):
            media_group.add_photo(FSInputFile(f'./pictures/styletransfer/{pic}'))

        photos_group = await callback.message.answer_media_group(media_group.build())
        example_photos['styletransfer'] = [pic.photo[-1].file_id for pic in photos_group]
    else:
        for pic in example_photos['styletransfer']:
            media_group.add_photo(pic)
        photos_group = await callback.message.answer_media_group(media_group.build())

    await state.set_state(UserStates.have_pic)
    await state.update_data(picture_message=photos_group)


@router.callback_query(F.data.in_({'femmes_dalger', 'scream', 'starry_night'}))
async def preset_button_pressed(callback: CallbackQuery, dao):
    dao[str(callback.from_user.id)]['preset'] = callback.data
    dao.save()
    text = f'В качестве стилевого изображения для команды /preset выбрана картина {d[callback.data]}'
    await callback.message.edit_text(text=text, reply_markup=choose_preset_picture(callback.data))


@router.callback_query(F.data == 'chosen')
async def chosen_button_pressed(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data == 'CycleGAN')
async def cyclegan_callback_response(callback: CallbackQuery, dao, state: FSMContext):
    text = texts['menu_cyclegan']
    await callback.message.edit_text(text=text, reply_markup=choose_mode(dao[str(callback.from_user.id)]['mode']))

    if not example_photos.get('cyclegan', False):
        photo = FSInputFile(f'./pictures/cyclegan/cyclegan_example.png')
        photo_message = await callback.message.answer_photo(photo)
        example_photos['cyclegan'] = photo_message.photo[-1].file_id
    else:
        photo_message = await callback.message.answer_photo(example_photos['cyclegan'])

    await state.set_state(UserStates.have_pic)
    await state.update_data(picture_message=photo_message)


@router.callback_query(F.data.in_({'Monet', 'VanGogh', 'Cezanne', 'Ukiyo-e', 'Serov'}))
async def mode_button_pressed(callback: CallbackQuery, dao, mode):
    dao[str(callback.from_user.id)]['mode'] = callback.data
    dao.save()
    text = f'CycleGan будет работать в режиме: {d[callback.data]}'
    if mode != 'cpu':
        await callback.message.edit_text(text=text, reply_markup=choose_mode(callback.data))
    else:
        await callback.message.edit_caption(caption=text, reply_markup=choose_mode(callback.data, back=False))

@router.message(IsAlonePhoto())
async def alone_message_response(message: Message, nats, dao, state: FSMContext):
    image = BytesIO()
    await message.bot.download(file=message.photo[-1].file_id, destination=image)

    temp_message = await message.reply(text=texts['working_1'])

    await state.set_state(UserStates.wait_for_response)

    res, error = await request_to_neuro([image], connection=nats, model="CycleGan",
                                        mode=dao[str(message.chat.id)]['mode'])

    if res:
        pillow_image = BufferedInputFile(res, filename="pillow_image.png")

        await temp_message.edit_text(text=texts['success'])

        await message.answer_photo(pillow_image)
    else:
        await temp_message.edit_text(text=texts['error'])

    await state.clear()


@router.message(F.photo)
async def photos_after_mw(message: Message, dao, nats, album, state: FSMContext):
    q = (len(album))
    if q != 2:
        return await message.reply(text=texts['only two pics'])

    images = []

    for mes in album:
        temp_image = BytesIO()
        await message.bot.download(file=mes.photo[-1].file_id, destination=temp_image)
        images.append(temp_image)

    temp_message = await message.reply(text=texts['working_2'])

    await state.set_state(UserStates.wait_for_response)

    res, error = await request_to_neuro(images, model="StyleTransfer", connection=nats,
                                        steps=dao[str(message.chat.id)]['steps'])

    if res:
        pillow_image = BufferedInputFile(res, filename="pillow_image.png")

        await temp_message.edit_text(text=texts['success'])

        await message.answer_photo(pillow_image)

        if error:
            await message.answer(text=texts[error])

    # nats timeout error
    else:
        await temp_message.edit_text(text=texts['error'])

    await state.clear()


@router.message()
async def any_message_response(message: Message):
    await message.reply(text='Я вас не понимаю :(')
