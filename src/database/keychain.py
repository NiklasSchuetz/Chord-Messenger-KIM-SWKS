"""
Class represents key references
"""
from __future__ import annotations

import sqlite3
from .databaseObject import DatabaseObject, DBException

tablenameKeychain = "keychains"

class Keychain(DatabaseObject):
    def __init__(self, identifierChordID, KeyChordID, internalID = 0):
        self.internalID = internalID
        self.identifierChordID = identifierChordID
        self.KeyChordID = KeyChordID 
        
    def update(self, con: sqlite3.Connection):
        if Keychain.existsByInternalID(self.internalID, con) == False :
            raise DBException("Critical: Keychain does not exist")
        cur = con.cursor()
        cur.execute('''UPDATE ''' + tablenameKeychain + ''' SET identifierChordID = \'''' + self.identifierChordID + '''\', KeyChordID = \'''' + 
                    self.KeyChordID + '''\' WHERE internalID == ''' + str(self.internalID))
        con.commit()
    
    def insert(self, con: sqlite3.Connection):
        if Keychain.existsByInternalID(self.internalID, con) == True :
            raise DBException("Critical: Keychain already exists")
        cur = con.cursor()
        cur.execute('''INSERT INTO ''' + tablenameKeychain + ''' (identifierChordID, KeyChordID) VALUES ( \'''' +
                     self.identifierChordID + '''\', \'''' + self.KeyChordID + '''\' )''' )
        con.commit()
        self.internalID = cur.lastrowid
    
    def delete(self, con: sqlite3.Connection):
        if Keychain.existsByInternalID(self.internalID, con) == False :
            raise DBException("Critical: Keychain does not exist")
        cur = con.cursor()
        cur.execute('''DELETE FROM ''' + tablenameKeychain + ''' WHERE (internalID == ''' + str(self.internalID) + ''')''')
        con.commit()
    
    def createTable(con: sqlite3.Connection):
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS ''' + tablenameKeychain + 
                    ''' (internalID INTEGER PRIMARY KEY AUTOINCREMENT, identifierChordID TEXT NOT NULL, KeyChordID TEXT NOT NULL)''')
        con.commit()

    @staticmethod
    def getKeyChordByChordID(ChordID: str, con: sqlite3.Connection) -> list[Keychain]:
        cur = con.cursor()
        cur.execute(''' SELECT * FROM ''' + tablenameKeychain + ''' WHERE identifierChordID == \'''' + ChordID + '''\'''')
        rows = cur.fetchall()
        if len(rows) != 1 :
            raise DBException("Critical: Keychain is not unique or not present!")
        return Keychain(rows[0][1], rows[0][2], rows[0][0]) 

    @staticmethod
    def getAll(con: sqlite3.Connection) -> list[Keychain]:
        cur = con.cursor()
        cur.execute(''' SELECT * FROM ''' + tablenameKeychain)
        rows = cur.fetchall()
        result = []

        for x in rows:
            result.append(Keychain(x[1], x[2], x[0]))
        return result 

    @staticmethod        
    def existsByInternalID(internalKeyID: int, con: sqlite3.Connection) -> bool:
        cur = con.cursor()
        cur.execute(''' SELECT * FROM ''' + tablenameKeychain + ''' WHERE internalID == ''' + str(internalKeyID))
        rows = cur.fetchall()
        if len(rows) >= 1 :
            return True
        return False
