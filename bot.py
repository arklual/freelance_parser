import asyncio
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import aiogram
from aiogram import types
from telethon import TelegramClient, events
from telethon.errors.rpcerrorlist import SessionPasswordNeededError
from settings import *
from database import Database
import vk_api
import os

directory = os.getcwd()
client = TelegramClient(PHONE_NUMBER, API_ID, API_HASH)
bot = aiogram.Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = aiogram.Dispatcher(bot, storage=storage)

class AuthSG(StatesGroup):
    code = State()
    password = State()

class ChannelSG(StatesGroup):
    name = State()
    description = State()
    provider_name = State()
    provider_phone = State()

class DelChannelSG(StatesGroup):
    name = State()

async def get_channel_posts():
    @dp.message_handler(commands=['del_channel'])
    async def del_channel(message: types.Message):
        await message.answer('Введите название канала(текст после @).')
        await DelChannelSG.name.set()
    @dp.message_handler(state=DelChannelSG.name)
    async def get_name_for_del(message: types.Message, state: FSMContext):
        await state.update_data(name=message.text)
        data = await state.get_data()
        db = await Database.setup()
        await db.del_channel(name=data['name'])
        await db.close_connection()
        await message.answer("Канал успешно удалён!")
        await state.finish()
    @dp.message_handler(commands=['add_channel'])
    async def add_channel(message: types.Message):
        await message.answer('Введите название канала(текст после @).')
        await ChannelSG.name.set()
    @dp.message_handler(state=ChannelSG.name)
    async def get_channelname(message: types.Message, state: FSMContext):
        await state.update_data(name=message.text)
        await message.answer("Теперь введите описание канала.")
        await ChannelSG.description.set()
    @dp.message_handler(state=ChannelSG.description)
    async def get_description(message: types.Message, state: FSMContext):
        await state.update_data(description=message.text)
        await message.answer("Теперь введите имя продавца.")
        await ChannelSG.provider_name.set()
    @dp.message_handler(state=ChannelSG.provider_name)
    async def get_provider_name(message: types.Message, state: FSMContext):
        await state.update_data(provider_name=message.text)
        await message.answer("Теперь введите номер телефона продавца.")
        await ChannelSG.provider_phone.set()
    @dp.message_handler(state=ChannelSG.provider_phone)
    async def get_provider_phone(message: types.Message, state: FSMContext):
        await state.update_data(provider_phone=message.text)
        data = await state.get_data()
        db = await Database.setup()
        await db.add_channel(name=data['name'], description=data['description'], provider_name=data['provider_name'], provider_phone=data['provider_phone'])
        await db.close_connection()
        await message.answer("Канал успешно добавлен!")
        await state.finish()
    @dp.message_handler(commands=['start_polling'])
    async def start_polling(message: types.Message, state: FSMContext):
        await client.connect()
        if not await client.is_user_authorized():
            await client.send_code_request(PHONE_NUMBER)
            await message.answer('Введите код(поставьте "-" пред последней цифрой): ')
            await AuthSG.code.set()
        else:
            await start_monitoring()
    @dp.message_handler(state=AuthSG.code)
    async def get_code(message: types.Message, state: FSMContext):
        await state.update_data(code=message.text)
        data = await state.get_data()
        code = data['code'].replace('-', '')
        try:
            await client.sign_in(PHONE_NUMBER, code)
            await state.finish()
            await start_monitoring()
        except SessionPasswordNeededError:
            await message.answer('Введите пароль: ')
            await AuthSG.password.set()
    @dp.message_handler(state=AuthSG.password)
    async def get_password(message: types.Message, state: FSMContext):
        await state.update_data(password=message.text)   
        data = await state.get_data()
        await state.finish()
        password = data['password']
        await client.sign_in(password=password)
        await start_monitoring()
    async def start_monitoring(): 
        db = await Database.setup()
        channels = await db.get_channel_list()
        channel_entities = []
        await db.close_connection()
        for channel in channels:
            channel_entity = await client.get_entity(channel['name'])
            channel_entities.append(channel_entity)
        old_files = os.listdir(directory)
        media = []
        is_creating = False
        await client.start()
        @client.on(events.NewMessage(chats=channel_entities))
        async def handle_channel_post(event):
            nonlocal old_files, media, is_creating
            if channels == []: return
            if str(event.message.message) != '': return
            if is_creating: 
                await client.download_media(event.message)
                files = os.listdir(directory)
                for file in files:
                    if file not in old_files:
                        media.append(os.path.join(directory, file))
                old_files = os.listdir(directory)
                return
                
            is_creating = True

            t = 0
            while t < TIMEOUT and str((await client.get_messages(event.chat))[-1].message) == '':
                await asyncio.sleep(5)
                t += 5
            channel = event.chat.username
            for chl in channels:
                if str(chl['name']) == str(channel):
                    channel = chl
                    break
    
            message_text = ''
            text = str((await client.get_messages(event.chat))[-1].message)
            if text != '':
                message_text = str(channel['description'])+'\n'+text+'\nПо заказам пишите '+str(channel['provider_phone'])
            else:
                message_text = str(channel['description'])+'\nПо заказам пишите '+str(channel['provider_phone'])
            await client.download_media(event.message)
            files = os.listdir(directory)
            for file in files:
                if file not in old_files:
                    media.append(os.path.join(directory, file))
            old_files = os.listdir(directory)
            if media == []: return
            vk = vk_api.VkApi(VK_LOGIN, VK_PASSWORD)
            vk.auth()
            upload = vk_api.VkUpload(vk)
            photo_list = []
            for m in media:
                try:
                    photo = upload.photo_wall(photos=m, group_id=GROUP_ID)
                    photo_list.append(*photo)
                except:
                    pass
            attachment = ','.join('photo{owner_id}_{id}'.format(**item) for item in photo_list)
            vk.method('wall.post', {
                'owner_id': '-'+GROUP_ID,
                'message': message_text,
                'attachments': attachment,
                'from_group': 1,
            })
            for m in media:
                os.remove(m)
            old_files = os.listdir(directory)
            media = []
            is_creating = False
    await dp.start_polling()
    
asyncio.run(get_channel_posts())
