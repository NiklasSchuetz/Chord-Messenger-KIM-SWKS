"""
Class represents key storable in our SQL database
"""
from __future__ import annotations

import sqlite3

from .databaseObject import DatabaseObject, DBException


tablenameKey = "keys"

class Key(DatabaseObject):
    def __init__(self, identifierChordID, partnerChordID, Key, internalID = 0):
        self.internalID = internalID
        self.identifierChordID = identifierChordID
        self.partnerChordID = partnerChordID
        self.Key = Key
        
    def update(self, con: sqlite3.Connection):
        if Key.existsByInternalID(self.internalID, con) == False :
            raise DBException("Critical: Key does not exist")
        cur = con.cursor()
        cur.execute('''UPDATE ''' + tablenameKey + ''' SET identifierChordID = \'''' + self.identifierChordID + '''\', partnerChordID = \'''' + self.partnerChordID + '''\', Key = \'''' + 
                    self.Key + '''\' WHERE internalID == ''' + str(self.internalID))
        con.commit()
    
    def insert(self, con: sqlite3.Connection):
        if Key.existsByInternalID(self.internalID, con) == True :
            raise DBException("Critical: Key already exists")
        cur = con.cursor()
        cur.execute('''INSERT INTO ''' + tablenameKey + ''' (identifierChordID, partnerChordID, Key) VALUES ( \'''' +
                     self.identifierChordID + '''\', \'''' + self.partnerChordID + '''\', \'''' + self.Key + '''\' )''' )
        con.commit()
        self.internalID = cur.lastrowid
    
    def delete(self, con: sqlite3.Connection):
        if Key.existsByInternalID(self.internalID, con) == False :
            raise DBException("Critical: Key does not exist")
        cur = con.cursor()
        cur.execute('''DELETE FROM ''' + tablenameKey + ''' WHERE (internalID == ''' + str(self.internalID) + ''')''')
        con.commit()
    
    def createTable(con: sqlite3.Connection):
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS ''' + tablenameKey + 
                    ''' (internalID INTEGER PRIMARY KEY AUTOINCREMENT, identifierChordID STRING NOT NULL, partnerChordID STRING NOT NULL, Key TEXT NOT NULL)''')
        con.commit()

    @staticmethod
    def getKeyByIdentifierChordID(ChordID: str, con: sqlite3.Connection) -> Key:
        cur = con.cursor()
        cur.execute(''' SELECT * FROM ''' + tablenameKey + ''' WHERE identifierChordID == \'''' + ChordID + '''\'''')
        rows = cur.fetchall()
        if len(rows) != 1 :
            raise DBException("Critical: Key is not unique or not present!")
        return Key(rows[0][1], rows[0][2], rows[0][3], rows[0][0]) 

    @staticmethod
    def getAll(con: sqlite3.Connection) -> Key:
        cur = con.cursor()
        cur.execute(''' SELECT * FROM ''' + tablenameKey)
        rows = cur.fetchall()
        result = []

        for x in rows:
            result.append(Key(x[1], x[2], x[3],x[0]))
        return result 


    @staticmethod        
    def existsByInternalID(internalKeyID: int, con: sqlite3.Connection) -> bool:
        cur = con.cursor()
        cur.execute(''' SELECT * FROM ''' + tablenameKey + ''' WHERE internalID == ''' + str(internalKeyID))
        rows = cur.fetchall()
        if len(rows) >= 1 :
            return True
        return False
