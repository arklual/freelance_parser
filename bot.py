from pyrogram import Client, filters, types
from settings import *
from database import Database
import vk_api
import os
import asyncio

db = Database()
directory = os.path.join(os.getcwd(), 'downloads')
SOURCE_PUBLICS = []
publics = db.get_channel_list()
old_files = os.listdir(directory)
media = []
is_creating = False
for public in publics:
    SOURCE_PUBLICS.append(public['name'])
 
app = Client("parser", api_id=API_ID, api_hash=API_HASH,
             phone_number=PHONE_NUMBER)

@app.on_message(filters.chat(SOURCE_PUBLICS))
async def new_channel_post(client, message):
    global old_files, media, is_creating
    channel = message.chat.username
    for chl in publics:
        if str(chl['name']) == str(channel):
            channel = chl
            break
    if int(channel['type']) == 1:
        if message.text is not None: return
        if is_creating: 
            await app.download_media(message)
            files = os.listdir(directory)
            for file in files:
                if file not in old_files:
                    media.append(os.path.join(directory, file))
            old_files = os.listdir(directory)
            return
        is_creating = True
        t = 0
        while t < TIMEOUT and (await get_last_message(message.chat.id)).text is None:
            await asyncio.sleep(5)
            t += 5

        message_text = ''
        text = (await get_last_message(message.chat.id)).text
        if text is not None:
            message_text = str(channel['description'])+'\n'+text+'\nТелефон продавца: '+str(channel['provider_phone'])
        else:
            message_text = str(channel['description'])+'\nТелефон продавца: '+str(channel['provider_phone'])
        await app.download_media(message)
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
            m = m.replace('.temp', '')
            try:
                os.remove(m)
            except:
                pass
        old_files = os.listdir(directory)
        media = []
        is_creating = False
    elif int(channel['type']) == 2:
        print('A')
        if message.caption is None: return
        print('B')
        message_text = str(channel['description'])+'\n'+message.caption+'\nТелефон продавца: '+str(channel['provider_phone'])
        messages = message.get_media_group()
        for message in messages:
            await app.download_media(message)
        files = os.listdir(directory)
        for file in files:
            if file not in old_files:
                media.append(os.path.join(directory, file))
        print('C')
        if media == []: return
        print('D')
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
            m = m.replace('.temp', '')
            try:
                os.remove(m)
            except:
                pass
        old_files = os.listdir(directory)
        media = []
        
 
@app.on_message(filters.chat(PRIVATE_PUBLIC))
async def post_request(client, message):
    db = Database()
    global SOURCE_PUBLICS, publics
    if'/add_channel' in message.text:
        # FORMAT: /add_channel|channel_link|description|provider_name|phone_number|type
        data = message.text.split('|')
        db.add_channel(data[1], data[2], data[3], data[4], data[5])
        SOURCE_PUBLICS = []
        publics = db.get_channel_list()
        for public in publics:
            SOURCE_PUBLICS.append(public['name'])
    if '/del_channel' in message.text:
        # FORMAT: /del_channel|channel_link
        data = message.text.split('|')
        db.del_channel(data[1])
        SOURCE_PUBLICS = []
        publics = db.get_channel_list()
        for public in publics:
            SOURCE_PUBLICS.append(public['name'])
 
async def get_last_message(chat_id):
    async for message in app.get_chat_history(chat_id, limit=1, offset_id=-1):
        return message
 
if __name__ == '__main__':
    app.run()