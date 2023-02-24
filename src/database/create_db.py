import sqlite3
from .chat import Chat
from .chatParticipant import ChatParticipants
from .key import Key
from .keychain import Keychain
from .message import Message
from .messageReceiverRelation import MessageReceiverRelation

def create_db():
    con = sqlite3.connect("database.db")

    Chat.createTable(con)
    ChatParticipants.createTable(con)
    Key.createTable(con)
    Keychain.createTable(con)
    Message.createTable(con)
    MessageReceiverRelation.createTable(con)

    con.commit()