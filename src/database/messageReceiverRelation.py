"""
Connects messages and receiver internal ID
used to fully build objects like Message
WARNING: Do not use manually. Intended to be used by message object only
"""

from __future__ import annotations

import sqlite3
from .databaseObject import DatabaseObject, DBException

tablenameMessageToReceiver = "messagesToReceivers"
tablenameMessage = "messages"

class MessageReceiverRelation(DatabaseObject):
    def __init__(self, internalMessageID, userChordID):
        self.internalID = 0
        self.internalMessageID = internalMessageID
        self.userChordID = userChordID
    
    def update(self, con: sqlite3.Connection):
        if MessageReceiverRelation.existsByInternalID(self.internalID, con) == False :
            raise DBException("Critical: Relation does not exist")
        cur = con.cursor()
        cur.execute('''UPDATE ''' + tablenameMessageToReceiver + ''' SET internalMessageID = \'''' + self.internalMessageID + 
                    '''\', userChordID = \'''' + self.userChordID + '''\' WHERE internalID == ''' + str(self.internalID) )
        con.commit()
        
    def insert(self, con: sqlite3.Connection):
        # WARNING: Does not commit due to failsafe mechanism. Only commit in message object when new receivers could be written for a message
        if MessageReceiverRelation.existsByInternalID(self.internalID, con) == True :
            raise DBException("Critical: Relation already exists")
        cur = con.cursor()
        cur.execute('''INSERT INTO ''' + tablenameMessageToReceiver + ''' (internalMessageID, userChordID) VALUES ( ''' +
                    str(self.internalMessageID) + ''', \'''' + self.userChordID + '''\' )''' )
        self.internalID = cur.lastrowid
    
    def delete(self, con: sqlite3.Connection):
        if MessageReceiverRelation.existsByInternalID(self.internalID, con) == False :
            raise DBException("Critical: Relation does not exist")
        cur = con.cursor()
        cur.execute('''DELETE FROM ''' + tablenameMessageToReceiver + ''' WHERE internalID == ''' + str(self.internalID))
        con.commit()
    
    def createTable(con: sqlite3.Connection):
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS ''' + tablenameMessageToReceiver + 
                    ''' (internalID INTEGER PRIMARY KEY AUTOINCREMENT, internalMessageID INTEGER NOT NULL, userChordID TEXT NOT NULL)''')
        con.commit()
    
    @staticmethod
    def deleteAllReceiverForMessage(internalMessageID: int, con: sqlite3.Connection) :
        # WARNING: Does not commit due to failsafe mechanism. Only commit in message object when new receivers could be written for a message
        cur = con.cursor()
        cur.execute(''' DELETE FROM ''' + tablenameMessageToReceiver + ''' WHERE (internalMessageID == ''' + str(internalMessageID) + ''')''')
    
    @staticmethod
    def getReceiverChordIDsByMessageID(internalMessageID: int, con: sqlite3.Connection) -> list[str]:
        cur = con.cursor()
        cur.execute(''' SELECT userChordID FROM ''' + tablenameMessageToReceiver + ''' WHERE (internalMessageID == \'''' + str(internalMessageID) + '''\')''')
        rows = cur.fetchall()
        if len(rows) <= 0 :
            raise DBException("Critical: Message has no receivers")
        result = []
        for x in rows:
            result.append(x[0])
        return result
    
    @staticmethod        
    def existsByInternalID(internalRelationID: int, con: sqlite3.Connection) -> bool:
        cur = con.cursor()
        cur.execute(''' SELECT * FROM ''' + tablenameMessageToReceiver + ''' WHERE (internalID == ''' + str(internalRelationID) + ''')''')
        rows = cur.fetchall()
        if len(rows) >= 1 :
            return True
        return False
