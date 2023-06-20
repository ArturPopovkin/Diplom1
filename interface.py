
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from config import comunity_token, acces_token
from core import VkTools
from database import check_user, add_user

import sqlalchemy as sq
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session
from config import db_url_object

class BotInterface():
    def __init__(self, comunity_token, acces_token):
        self.vk = vk_api.VkApi(token=comunity_token)
        self.longpoll = VkLongPoll(self.vk)
        self.vk_tools = VkTools(acces_token)
        self.params = {}
        self.worksheets = []
        self.offset = 0

    def message_send(self, user_id, message, attachment=None):
        self.vk.method('messages.send',
                       {'user_id': user_id,
                        'message': message,
                        'attachment': attachment,
                        'random_id': get_random_id()}
                       )



    def event_handler(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text.lower() == 'привет':
                    '''Логика для получения данных о пользователе'''
                    self.params = self.vk_tools.get_profile_info(event.user_id)
                    self.message_send(
                        event.user_id, f'Привет, {self.params["name"]}! Если хочешь найти пару, напиши команду "Поиск".')
                elif event.text.lower() == 'поиск':
                    '''Логика для поиска анкет'''
                    self.message_send(
                        event.user_id, 'Я нашёл для тебя пару!)')
                    if self.worksheets:
                        worksheet = self.worksheets.pop()
                        photos = self.vk_tools.get_photos(worksheet['id'])
                        photo_string = ''
                        for photo in photos:
                            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
                    else:
                        self.worksheets = self.vk_tools.search_worksheet(
                            self.params, self.offset)

                        worksheet = self.worksheets.pop()

                        while check_user(engine,event.user_id,worksheet["id"]) == True:
                            worksheet = self.worksheets.pop()

                        photos = self.vk_tools.get_photos(worksheet['id'])
                        photo_string = ''
                        for photo in photos:
                            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
                        self.offset += 10

                    self.message_send(
                        event.user_id,
                         f'Я нашёл для тебя {worksheet["name"]}! Вот ссылка: vk.com/id{worksheet["id"]}.',
                        attachment=photo_string
                    )


                    while add_user(engine,event.user_id, worksheet["id"]) == False:
                        worksheet = self.worksheets.append()


                elif event.text.lower() == 'пока':
                    self.message_send(
                        event.user_id, f'Пока, {self.params["name"]}.')
                else:
                    self.message_send(
                        event.user_id, 'Я тебя не понял(')

Base = declarative_base()

if __name__ == '__main__':
    engine = create_engine(db_url_object)
    Base.metadata.create_all(engine)
    bot_interface = BotInterface(comunity_token, acces_token)
    bot_interface.event_handler()