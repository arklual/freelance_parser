import aiosqlite
class Database:
    def __init__(self, conn) -> None:
        self.__conn__ = conn
    
    @staticmethod
    async def setup():
        conn = await aiosqlite.connect('db.sqlite3')
        return Database(conn)
    
    async def close_connection(self):
        await self.__conn__.close()
    
    async def add_channel(self, name, description, provider_name, provider_phone):
        await self.__conn__.execute("INSERT INTO channels (name, description, provider_name, provider_phone) VALUES(?, ?, ?, ?);", (name, description, provider_name, provider_phone))
        await self.__conn__.commit() 

    async def del_channel(self, name):
        await self.__conn__.execute("DELETE FROM channels WHERE name=?", (name, ))
        await self.__conn__.commit() 
    
    async def get_channel_list(self):
        cur = await self.__conn__.execute('SELECT name, description, provider_name, provider_phone FROM channels')
        chnls = await cur.fetchall()
        channels = []
        for channel in chnls:
            (name, description, provider_name, provider_phone) = channel
            channels.append({
                "name": name,
                "description" : description,
                "provider_name": provider_name,
                "provider_phone": provider_phone
            })
        await cur.close()
        return channels