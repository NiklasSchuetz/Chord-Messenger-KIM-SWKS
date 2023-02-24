import unittest
from key import Key
from message import Message
from messageReceiverRelation import MessageReceiverRelation
from chat import Chat
from chatParticipant import ChatParticipants
from keychain import Keychain
import sqlite3

class TestMessages(unittest.TestCase):
    def setUp(self):
        con = sqlite3.connect('example.db')
        Message.createTable(con)
        MessageReceiverRelation.createTable(con)

    def tearDown(self):
        con = sqlite3.connect('example.db')
        cur  = con.cursor()
        cur.execute("DELETE FROM messagesToReceivers")
        cur.execute("DELETE FROM messages")
        con.commit()
    
    def testinsertMessages(self):
        con = sqlite3.connect('example.db')
        m1 = Message("M123", 1000, "I am Test Message", "ABC", ["EFG", "XYZ"])
        m1.insert(con)
        m2 = Message.getMessageByChordID("M123", con)  
        self.assertEqual(m1.ChordID, m2[0].ChordID)

    def testupdateMessages(self):
        con = sqlite3.connect('example.db')
        m1 = Message("M123", 1000, "I am Test Message", "ABC", ["EFG", "XYZ"])
        m1.insert(con)
        m1.Content = " I am new content"
        m1.update(con)
        m2 = Message.getMessageByChordID("M123", con)  
        self.assertEqual(m1.Content, m2[0].Content)

    def testdeleteMessages(self):
        con = sqlite3.connect('example.db')
        m1 = Message("M123", 1000, "I am Test Message", "ABC", ["EFG", "XYZ"])
        m1.insert(con)
        m2 = Message.getMessageByChordID("M123", con)  
        m2[0].delete(con)
        try:
            m2 = Message.getMessageByChordID("M123", con)  
            self.assertTrue(False)
        except:
            self.assertTrue(True)

class TestKey(unittest.TestCase):
    def setUp(self):
        con = sqlite3.connect('example.db')
        Key.createTable(con)
    def tearDown(self):
        con = sqlite3.connect('example.db')
        cur  = con.cursor()
        cur.execute("DELETE FROM keys")
        con.commit()
    
    def testinsertKey(self):
        con = sqlite3.connect('example.db')
        k1 = Key("ABC", "VXY", "iamkey")
        k1.insert(con)
        k2 = Key.getKeyByIdentifierChordID("ABC", con)  
        self.assertEqual(k1.identifierChordID, k2.identifierChordID)
    
    def testupdateKey(self):
        con = sqlite3.connect('example.db')
        k1 = Key("ABC", "VXY", "iamkey")
        k1.insert(con)
        k1.Key = "newkey"
        k1.update(con)
        k2 = Key.getKeyByIdentifierChordID("ABC", con)  
        self.assertEqual(k1.Key, k2.Key)

    def testdeleteKey(self):
        con = sqlite3.connect('example.db')
        k1 = Key("ABC", "VXY", "iamkey")
        k1.insert(con)
        k2 = Key.getKeyByIdentifierChordID("ABC", con)  
        k2.delete(con)
        try:
            k2 = Key.getKeyByIdentifierChordID("ABC", con)  
            self.assertTrue(False)
        except:
            self.assertTrue(True)

class TestKeychain(unittest.TestCase):
    def setUp(self):
        con = sqlite3.connect('example.db')
        Keychain.createTable(con)

    def tearDown(self):
        con = sqlite3.connect('example.db')
        cur  = con.cursor()
        cur.execute("DELETE FROM keychains")
        con.commit()
    
    def testinsertKeychain(self):
        con = sqlite3.connect('example.db')
        k1 = Keychain("ABC", "XYZ")
        k1.insert(con)
        k2 = Keychain.getKeyChordByChordID("ABC",con)
        self.assertEqual(k1.KeyChordID, k2.KeyChordID)

    def testupdateKeychain(self):
        con = sqlite3.connect('example.db')
        k1 = Keychain("ABC", "XYZ")
        k1.insert(con)
        k1.KeyChordID = "ABD"
        k1.update(con)
        k2 = Keychain.getKeyChordByChordID("ABC",con)
        self.assertEqual(k1.KeyChordID, k2.KeyChordID)
    
    def testdeleteKeychain(self):
        con = sqlite3.connect('example.db')
        k1 = Keychain("ABC", "XYZ")
        k1.insert(con)
        k2 = Keychain.getKeyChordByChordID("ABC",con)
        k2.delete(con) 
        try:
            k2 = Keychain.getKeyChordByChordID("ABC", con)  
            self.assertTrue(False)
        except:
            self.assertTrue(True)

class TestChats(unittest.TestCase):
    def setUp(self):
        con = sqlite3.connect('example.db')
        Chat.createTable(con)

    def tearDown(self):
        con = sqlite3.connect('example.db')
        cur  = con.cursor()
        cur.execute("DELETE FROM chats")
        con.commit()
    
    def testinsertChat(self):
        con = sqlite3.connect('example.db')
        c1 = Chat("ABC", "XYZ")
        c1.insert(con)
        c2 = Chat.getChatByChordID("ABC",con)
        self.assertEqual(c1.ChatChordID, c2[0].ChatChordID)

    def testupdateChat(self):
        con = sqlite3.connect('example.db')
        c1 = Chat("ABC", "XYZ")
        c1.insert(con)
        c1.ParticipantChordID = "ABD"
        c1.update(con)
        c2 = Chat.getChatByChordID("ABC",con)
        self.assertEqual(c1.MessageChordID, c2[0].MessageChordID)
    
    def testdeleteChat(self):
        con = sqlite3.connect('example.db')
        c1 = Chat("ABC", "XYZ")
        c1.insert(con)
        c2 = Chat.getChatByChordID("ABC",con)
        c2[0].delete(con)        
        try:
            c2 = Chat.getChatByChordID("ABC", con)  
            self.assertTrue(False)
        except:
            self.assertTrue(True)

class TestChatParticipants(unittest.TestCase):
    def setUp(self):
        con = sqlite3.connect('example.db')
        ChatParticipants.createTable(con)

    def tearDown(self):
        con = sqlite3.connect('example.db')
        cur  = con.cursor()
        cur.execute("DELETE FROM chatparticipants")
        con.commit()
    
    def testinsertChatParticipants(self):
        con = sqlite3.connect('example.db')
        c1 = ChatParticipants("ABC", "XYZ")
        c1.insert(con)
        c2 = ChatParticipants.getChatParticipantsByChordID("ABC",con)
        self.assertEqual(c1.ChordID, c2[0].ChordID)

    def testupdateChatParticipants(self):
        con = sqlite3.connect('example.db')
        c1 = ChatParticipants("ABC", "XYZ")
        c1.insert(con)
        c1.ParticipantChordID = "ABD"
        c1.update(con)
        c2 = ChatParticipants.getChatParticipantsByChordID("ABC",con)
        self.assertEqual(c1.ParticipantChordID, c2[0].ParticipantChordID)
    
    def testdeleteChatParticipants(self):
        con = sqlite3.connect('example.db')
        c1 = ChatParticipants("ABC", "XYZ")
        c1.insert(con)
        c2 = ChatParticipants.getChatParticipantsByChordID("ABC",con)
        c2[0].delete(con)        
        try:
            c2 = ChatParticipants.getChatParticipantsByChordID("ABC", con)  
            self.assertTrue(False)
        except:
            self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
