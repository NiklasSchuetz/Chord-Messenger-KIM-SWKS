"""
Class represents single message storable in our SQL database
"""
from __future__ import annotations

import sqlite3

from .databaseObject import DatabaseObject
from .databaseObject import DBException
from .messageReceiverRelation import MessageReceiverRelation


tablenameMessage = "messages"

class Message(DatabaseObject):
    
    def __init__(self, ChordID, Timestamp, Content, SenderID, ReceiverID: list[str], internalID = 0):
        self.internalID = internalID
        self.ChordID = ChordID
        self.Timestamp = Timestamp
        self.Content = Content
        self.SenderID = SenderID
        self.ReceiverID = ReceiverID
        
    def update(self, con: sqlite3.Connection):
        if Message.existsByInternalID(self.internalID, con) == False :
            raise DBException("Critical: Message does not exist")
        cur = con.cursor()
        #update message table entry
        cur.execute('''UPDATE ''' + tablenameMessage + ''' SET ChordID = \'''' + self.ChordID + '''\', Timestamp = \'''' + 
                    str(self.Timestamp) + '''\', Content = \'''' + self.Content + '''\', SenderID = \'''' + self.SenderID + 
                    '''\' WHERE internalID == ''' + str(self.internalID) )
        #remove all connections between message and receivers
        MessageReceiverRelation.deleteAllReceiverForMessage(self.internalID, con)
        #then add updated receivers
        msgRecv = list[MessageReceiverRelation]
        for x in self.ReceiverID :
            msgRecv = MessageReceiverRelation(self.internalID, x)
            msgRecv.insert(con)
        con.commit()
        return
    
    def insert(self, con: sqlite3.Connection):
        if Message.existsByInternalID(self.internalID, con) == True :
            raise DBException("Critical: Message already exists")
        cur = con.cursor()
        #create message table entry
        cur.execute('''INSERT INTO ''' + tablenameMessage + ''' (ChordID, Timestamp, Content, SenderID) VALUES ( \'''' +
                    self.ChordID + '''\', ''' + str(self.Timestamp) + ''', \'''' + self.Content +'''\', \'''' + self.SenderID + '''\' )''' )
        con.commit()
        self.internalID = cur.lastrowid
        # set receivers for message
        msgRecv = list[MessageReceiverRelation]
        for x in self.ReceiverID :
            msgRecv = MessageReceiverRelation(self.internalID, x)
            msgRecv.insert(con)
        con.commit()
    
    def delete(self, con: sqlite3.Connection):
        if Message.existsByInternalID(self.internalID, con) == False :
            raise DBException("Critical: Message does not exist")
        cur = con.cursor()
        cur.execute('''DELETE FROM ''' + tablenameMessage + ''' WHERE (internalID == ''' + str(self.internalID) + ''')''')
        con.commit()
        #MessageReceiverRelation will be deleted due to ON DELETE CASCADE
    
    def createTable(con: sqlite3.Connection):
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS ''' + tablenameMessage + 
                    ''' (internalID INTEGER PRIMARY KEY AUTOINCREMENT, ChordID TEXT , Timestamp INTEGER NOT NULL, Content TEXT NOT NULL, SenderID TEXT NOT NULL)''')
        con.commit()
    
    @staticmethod
    def getMessageByInternalID(internalMessageID: int, con: sqlite3.Connection) -> Message:
        cur = con.cursor()
        cur.execute(''' SELECT * FROM ''' + tablenameMessage + ''' WHERE (internalID == ''' + str(internalMessageID) + ''')''')
        rows = cur.fetchall()
        result = []
        for x in rows:
            result.append(Message(x[1], x[2], x[3], x[4], MessageReceiverRelation.getReceiverChordIDsByMessageID(x[0], con), x[0]))
        return result

    @staticmethod
    def getMessageByChordID(ChordID: str, con: sqlite3.Connection) -> Message:
        cur = con.cursor()
        cur.execute(''' SELECT * FROM ''' + tablenameMessage + ''' WHERE (ChordID == \'''' + ChordID + '''\')''')
        rows = cur.fetchall()
        result = []
        for x in rows:
            result.append(Message(x[1], x[2], x[3], x[4], MessageReceiverRelation.getReceiverChordIDsByMessageID(x[0], con), x[0]))
        return result
    

    @staticmethod
    def getAllWithID(con: sqlite3.Connection) -> Message:
        cur = con.cursor()
        cur.execute(''' SELECT * FROM ''' + tablenameMessage + ''' WHERE (ChordID <> \' \')''')
        rows = cur.fetchall()
        result = []
        for x in rows:
            result.append(Message(x[1], x[2], x[3], x[4], MessageReceiverRelation.getReceiverChordIDsByMessageID(x[0], con), x[0]))
        return result

    @staticmethod        
    def existsByInternalID(internalUserID: int, con: sqlite3.Connection) -> bool:
        cur = con.cursor()
        cur.execute(''' SELECT * FROM ''' + tablenameMessage + ''' WHERE (internalID == ''' + str(internalUserID) + ''')''')
        rows = cur.fetchall()
        if len(rows) >= 1 :
            return True
        return False
