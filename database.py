import sqlite3
class Database:
    def __init__(self) -> None:
        self.__conn = sqlite3.connect('db.sqlite3')
        self.__cur = self.__conn.cursor()
    
    def add_channel(self, name, description, provider_name, provider_phone, type):
        self.__cur.execute("INSERT INTO channels (name, description, provider_name, provider_phone, type) VALUES(?, ?, ?, ?, ?);", (name, description, provider_name, provider_phone, type))
        self.__conn.commit() 

    def del_channel(self, name):
        self.__cur.execute("DELETE FROM channels WHERE name=?", (name, ))
        self.__conn.commit() 
    
    def get_channel_list(self):
        self.__cur.execute('SELECT name, description, provider_name, provider_phone, type FROM channels')
        chnls =  self.__cur.fetchall()
        channels = []
        for channel in chnls:
            (name, description, provider_name, provider_phone, type) = channel
            channels.append({
                "name": name,
                "description" : description,
                "provider_name": provider_name,
                "provider_phone": provider_phone,
                "type": type
            })
        return channels