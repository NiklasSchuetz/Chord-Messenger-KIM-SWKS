"""
Class represents chats
"""
from __future__ import annotations

import sqlite3
from .databaseObject import DatabaseObject, DBException

tablenameChat = "chats"

class Chat(DatabaseObject):
    def __init__(self, ChatChordID, MessageChordID, internalID = 0):
        self.internalID = internalID
        self.ChatChordID = ChatChordID
        self.MessageChordID = MessageChordID 
        
    def update(self, con: sqlite3.Connection):
        if Chat.existsByInternalID(self.internalID, con) == False :
            raise DBException("Critical: Chat does not exist")
        cur = con.cursor()
        cur.execute('''UPDATE ''' + tablenameChat + ''' SET ChatChordID = \'''' + self.ChatChordID + '''\', MessageChordID = \'''' + 
                    self.MessageChordID + '''\' WHERE internalID == ''' + str(self.internalID))
        con.commit()
    
    def insert(self, con: sqlite3.Connection):
        if Chat.existsByInternalID(self.internalID, con) == True :
            raise DBException("Critical: Chat already exists")
        cur = con.cursor()
        cur.execute('''INSERT INTO ''' + tablenameChat + ''' (ChatChordID, MessageChordID) VALUES ( \'''' +
                     self.ChatChordID + '''\', \'''' + self.MessageChordID + '''\' )''' )
        con.commit()
        self.internalID = cur.lastrowid
    
    def delete(self, con: sqlite3.Connection):
        if Chat.existsByInternalID(self.internalID, con) == False :
            raise DBException("Critical: Chat does not exist")
        cur = con.cursor()
        cur.execute('''DELETE FROM ''' + tablenameChat + ''' WHERE (internalID == ''' + str(self.internalID) + ''')''')
        con.commit()
    
    def createTable(con: sqlite3.Connection):
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS ''' + tablenameChat + 
                    ''' (internalID INTEGER PRIMARY KEY AUTOINCREMENT, ChatChordID TEXT NOT NULL, MessageChordID TEXT NOT NULL)''')
        con.commit()

    @staticmethod
    def getChatByChordID(ChordID: str, con: sqlite3.Connection) -> list[Chat]:
        cur = con.cursor()
        cur.execute(''' SELECT * FROM ''' + tablenameChat + ''' WHERE ChatChordID == \'''' + ChordID + '''\'''')
        rows = cur.fetchall()
        result = []

        for x in rows:
            result.append(Chat(x[1], x[2], x[0]))
        return result 

    @staticmethod
    def getAll(con: sqlite3.Connection) -> list[Chat]:
        cur = con.cursor()
        cur.execute(''' SELECT * FROM ''' + tablenameChat)
        rows = cur.fetchall()
        result = []

        for x in rows:
            result.append(Chat(x[1], x[2], x[0]))
        return result 

    @staticmethod        
    def existsByInternalID(internalKeyID: int, con: sqlite3.Connection) -> bool:
        cur = con.cursor()
        cur.execute(''' SELECT * FROM ''' + tablenameChat + ''' WHERE internalID == ''' + str(internalKeyID))
        rows = cur.fetchall()
        if len(rows) >= 1 :
            return True
        return False
