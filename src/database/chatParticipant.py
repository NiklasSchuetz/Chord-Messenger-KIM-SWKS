"""
Class storing participants of own chats
"""
from __future__ import annotations

import sqlite3
from .databaseObject import DatabaseObject, DBException
from .chat import Chat

tablenameChatParticipants = "chatparticipants"

class ChatParticipants(DatabaseObject):
    def __init__(self, ChordID, ParticipantChordID, internalID = 0):
        self.internalID = internalID
        self.ChordID = ChordID
        self.ParticipantChordID = ParticipantChordID 
        
    def update(self, con: sqlite3.Connection):
        if ChatParticipants.existsByInternalID(self.internalID, con) == False :
            raise DBException("Critical: Chat does not exist")
        cur = con.cursor()
        cur.execute('''UPDATE ''' + tablenameChatParticipants + ''' SET ChordID = \'''' + self.ChordID + '''\', ParticipantChordID = \'''' + 
                    self.ParticipantChordID + '''\' WHERE internalID == ''' + str(self.internalID))
        con.commit()
    
    def insert(self, con: sqlite3.Connection):
        if ChatParticipants.existsByInternalID(self.internalID, con) == True :
            raise DBException("Critical: Chat already exists")
        cur = con.cursor()
        cur.execute('''INSERT INTO ''' + tablenameChatParticipants + ''' (ChordID, ParticipantChordID) VALUES ( \'''' +
                     self.ChordID + '''\', \'''' + self.ParticipantChordID + '''\' )''' )
        con.commit()
        self.internalID = cur.lastrowid
    
    def delete(self, con: sqlite3.Connection):
        if ChatParticipants.existsByInternalID(self.internalID, con) == False :
            raise DBException("Critical: Chat does not exist")
        cur = con.cursor()
        cur.execute('''DELETE FROM ''' + tablenameChatParticipants + ''' WHERE (internalID == ''' + str(self.internalID) + ''')''')
        con.commit()
    
    def createTable(con: sqlite3.Connection):
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS ''' + tablenameChatParticipants + 
                    ''' (internalID INTEGER PRIMARY KEY AUTOINCREMENT, ChordID TEXT NOT NULL, ParticipantChordID TEXT NOT NULL)''')
        con.commit()

    @staticmethod
    def getChatParticipantsByChordID(ChordID: str, con: sqlite3.Connection) -> list[Chat]:
        cur = con.cursor()
        cur.execute(''' SELECT * FROM ''' + tablenameChatParticipants + ''' WHERE ChordID == \'''' + ChordID + '''\'''')
        rows = cur.fetchall()
        result = []

        for x in rows:
            result.append(ChatParticipants(x[1], x[2], x[0]))
        return result 

    @staticmethod
    def getAll(con: sqlite3.Connection) -> list[Chat]:
        cur = con.cursor()
        cur.execute(''' SELECT * FROM ''' + tablenameChatParticipants)
        rows = cur.fetchall()
        result = []

        for x in rows:
            result.append(ChatParticipants(x[1], x[2], x[0]))
        return result 

    @staticmethod        
    def existsByInternalID(internalKeyID: int, con: sqlite3.Connection) -> bool:
        cur = con.cursor()
        cur.execute(''' SELECT * FROM ''' + tablenameChatParticipants + ''' WHERE internalID == ''' + str(internalKeyID))
        rows = cur.fetchall()
        if len(rows) >= 1 :
            return True
        return False
