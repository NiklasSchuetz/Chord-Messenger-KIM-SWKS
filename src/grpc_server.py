import logging
import asyncio
from sqlite3.dbapi2 import DatabaseError
from typing import Optional
import grpc
import hashlib
import sqlite3

import os
import sys
import time

from dataclasses import dataclass

from database.chatParticipant import ChatParticipants
from database.create_db import create_db
from database.databaseObject import DBException
from database.message import Message
from database.chat import Chat
from database.key import Key
from database.keychain import Keychain

# use import to compile
import grpc_messages_pb2_grpc, grpc_messages_pb2
# use from . import during development for correct linting
# from . import grpc_messages_pb2_grpc, grpc_messages_pb2


@dataclass
class other_node:
    """data class to store information of other chord nodes"""
    chord_id: str
    ip: str
    port: int
    public_key: Optional[str] = None
    name: Optional[str] = None

class ServerNode(grpc_messages_pb2_grpc.grpc_serviceServicer):

    def __init__(self, ip: str, port: int, db_name: str):
        """Constructor method
        """
        self.chord_id: str = self.compute_chord_id(f'ip:{ip} port:{port}')
        self.chat_partner_chord_id: str = self.compute_chord_id(f'ip:{ip} port:{port}-partner')
        self.keychain_chord_id: str = self.compute_chord_id(f'ip:{ip} port:{port}-keychain')
        self.message_ids: list[str] = []
        self.chat_partners: list[str] = []
        self.predecessor: other_node = None
        self.successor: other_node = None
        self.fingertable: dict[str, other_node] = {}
        self.db_conn = sqlite3.connect(db_name)
        self.port: int = port
        self.ip: str = ip
        self.standby_nodes: list[other_node] = []

        self.symmetric_keys: dict[str, str] = None # key:chord_id of chat_partner, value: symmetric key
        self.private_key: str = None
        self.public_key: str = None

    def compute_chord_id(self, to_hash):
        """computes the sha256 hash for a given object

        :param to_hash: object which gets hashed
        :return: the hash in hexadezimal
        :rtype: string
        """
        return str(hashlib.sha256(str(to_hash).encode()).hexdigest())

    def set_my_chord_ids(self, node_id, keychain_id, partner_id):
        """ set new chord IDs
        :param node_id: new chord id for identifying node
        :param keychain_id: new chord id to get key chord ids trough FindKeyChain-Method
        :param partner_id: new chord id to get all chat partners trough FindChatPartners-Method
        """
        self.chord_id = node_id
        self.keychain_chord_id = keychain_id
        self.chat_partner_chord_id = partner_id


    def change_predecessor(self, node: other_node):
        """ set new predecessor
        :param node: new node of type other_node
        """
        self.predecessor = node
        self.add_to_fingertable(node=node)

    def change_successor(self, node: other_node):
        """ add new node to successors list
        :param node: new node of type other_node
        """
        self.successor = node
        self.add_to_fingertable(node)

    def add_to_fingertable(self, node: other_node):
        """ adds note to fingertable
        :param node: new node of type other_node
        """
        self.fingertable[node.chord_id] = node

    def remove_from_fingertable(self, chord_id):
        """ removes note to fingertable
        :param node: new node of type other_node
        """
        self.fingertable.pop(chord_id)

    def check_responsible(self, searched_chord_id:str):
        """ check if node is responsible for given chord_id

        :param searched_chord_id: chord_id you want to check
        :return: True if responsible; False if not responsible
        :rtype: bool
        """
        # Check for most common case (between me and predecessor)
        # logging.info(f"pre:{self.predecessor.chord_id}, search:{searched_chord_id}, self:{self.chord_id}")
        if int(self.predecessor.chord_id, 16) < int(searched_chord_id, 16) < int(self.chord_id, 16):
            return True
        
        # check if node is responsible when range wraps around 0 - eg. pre is 90, node is 10 -> responsible for range 91-9
        elif int(self.predecessor.chord_id, 16) > int(self.chord_id, 16):
            if int(searched_chord_id, 16) < int(self.chord_id, 16) or int(self.predecessor.chord_id, 16) < int(searched_chord_id, 16):
                return True
            else:
                return False
        else:
            return False

    def get_next_smaller_successor(self, searched_chord_id: str) -> other_node:
        """get one of successors with the smallest distance to searched chord id
        :param searched_chord_id: chord_id (str) you search for

        :return: object of node
        :rtype: other_node()
        """
        max = self.successor
        for ft_node_chordId in self.fingertable:
            if int(max.chord_id, 16) < int(ft_node_chordId, 16) < int(searched_chord_id, 16):
                max = self.fingertable[ft_node_chordId]

        return max

    def register_new_standby_node(self, node:other_node):
        """ adds node to list of standbynodes

        :param node: node which gets added
        """
        self.standby_nodes.append(node)

    def get_standby_node(self) -> other_node:
        """ adds node to list of standbynodes
        :return: node
        :rtype: other_node()
        """
        try:
            return self.standby_nodes.pop(0)
        except KeyError:
            return other_node(None, None, None)

    # # # # #
    # gRPC  #
    # # # # #

    async def Join(
        self, request: grpc_messages_pb2.JoinRequest,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.JoinReply:
        """gRPC to let other nodes join the Chord network.

        :param request: JoinRequest
        :return: JoinReply
        """
        # check if neighbors exist
        if self.predecessor is None:
                new_node = other_node(chord_id=request.RequesterChordId, ip=request.RequesterIp, port=request.RequesterPort, public_key=request.publicKey)
                self.change_predecessor(new_node)
                self.change_successor(new_node)
                return grpc_messages_pb2.JoinReply(successful=True, suc_chordId=self.chord_id, suc_ip=self.ip, suc_port=self.port, suc_pk=self.public_key, pre_chordId=self.chord_id, pre_ip=self.ip, pre_port=self.port, pre_pk = self.public_key)

        if self.check_responsible(request.RequesterChordId):  # check if responsible -> new node is my pre 
            # set Predecessors successors to joining node
            async with grpc.aio.insecure_channel(f'{self.predecessor.ip}:{self.predecessor.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                message= grpc_messages_pb2.SetSuccessorRequest(chordId=request.RequesterChordId, ip=request.RequesterIp, port=request.RequesterPort)
                await stub.SetSuccessor(message)
            
            old_pre = self.predecessor
            new_pre = other_node(chord_id=request.RequesterChordId, ip=request.RequesterIp, port=request.RequesterPort, public_key=request.publicKey)
            self.change_predecessor(new_pre)
            return grpc_messages_pb2.JoinReply(successful=True, suc_chordId=self.chord_id, suc_ip=self.ip, suc_port=self.port, suc_pk=self.public_key, pre_chordId=old_pre.chord_id, pre_ip=old_pre.ip, pre_port=old_pre.port, pre_pk=old_pre.public_key)
        
        else:  # Send to next smaller successor
            next_node = self.get_next_smaller_successor(request.RequesterChordId)
            async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                return await stub.Join(request)

    async def SetPredecessor(
        self, request: grpc_messages_pb2.SetPredecessorRequest,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.Reply:
        """gRPC to set predecessor
        :param request: SetPredecessorRequest
        :return: Reply
        """
        node = other_node(request.chordId, request.ip, request.port, request.publickey)
        self.change_predecessor(node)

        return grpc_messages_pb2.Reply(successful=True)

    async def SetSuccessor(
        self, request: grpc_messages_pb2.SetSuccessorRequest,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.Reply:
        """gRPC to set sucessor
        :param request: SetSuccessorRequest
        :return: Reply
        """
        self.change_successor(other_node(chord_id=request.chordId, ip=request.ip, port=request.port, public_key=request.publickey))
        return grpc_messages_pb2.Reply(successful=True)

    async def Chat(
        self, request: grpc_messages_pb2.ChatMsg,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.Reply:
        """ gRPC to call if one wants to send this node a message
        :param request: ChatMsg
        :return: Reply
        """

        # check if known
        if request.sender not in self.chat_partners:
            # Add to chat partners; local and chord
            self.chat_partners.append(request.sender)
            
            # add chat_partner in chord
            next_node = self.get_next_smaller_successor(self.chat_partner_chord_id)
            async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                message= grpc_messages_pb2.AddChatPartner(chordId=self.chat_partner_chord_id, partnerChordId=request.sender)
                await stub.AddChatpartner(message)

            # get information for new chat partner
            next_node = self.get_next_smaller_successor(request.sender)
            async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                msg = grpc_messages_pb2.FindRequest(chordId = request.sender)
                user = await stub.FindUser(msg)

            node = other_node(chord_id=user.chordId, ip=user.ip, port=user.port, public_key=user.publicKey, name=user.name)
            self.add_to_fingertable(node)
            self.chat_partners.append(node.chord_id)

        logging.info(f'Nachricht an {self.chord_id}')

        # STORE LOCALLY
        Message(ChordID=" ", Timestamp=int(time.time()), Content=request.content, SenderID=request.sender, ReceiverID = [self.chord_id]).insert(self.db_conn)

        # SAVE MESSAGE in DB
        msg_chord_id = self.compute_chord_id(f'{self.chord_id}->{request.sender}:{request.content}')
        chat_chord_id = self.compute_chord_id(f'{self.chord_id}:{request.sender}')
        # logging.info(f'msg_chord_id: {msg_chord_id}\nchat_chord_id={chat_chord_id}')

        if self.check_responsible(msg_chord_id):
            Message(ChordID=msg_chord_id, Timestamp=int(time.time()), Content=request.content, SenderID=request.sender, ReceiverID = [self.chord_id]).insert(self.db_conn)
        else:
            next_node = self.get_next_smaller_successor(msg_chord_id)
            async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                msg = grpc_messages_pb2.Message(chordId=msg_chord_id, content=request.content, sender=self.chord_id, receiver=self.chord_id, timestamp= int(time.time()))
                await stub.SaveMessage(msg)

        # add message chord id to chat
        if self.check_responsible(chat_chord_id): 
            Chat(ChatChordID=chat_chord_id, MessageChordID=msg_chord_id).insert(self.db_conn)
        else:
            next_node = self.get_next_smaller_successor(chat_chord_id)
            async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                message= grpc_messages_pb2.AddMessage(chatChordId=chat_chord_id, messageChordId=msg_chord_id)
                await stub.AddMessageToChat(message)


        return grpc_messages_pb2.Reply(successful = True)
   
    async def SetChordIds(
        self, request: grpc_messages_pb2.NewChordIDs,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.Reply:
        """ gRPC to set the 3 chord ids.
        :param request: NewChordIDs
        :return: Reply
        """
        self.set_my_chord_ids(node_id=request.chordId, keychain_id=request.keyId, partner_id=request.partnerId)
        logging.info(f'chordId: {self.chord_id}\npartner_chordId: {self.chat_partner_chord_id}\nkeys_chord_Id: {self.keychain_chord_id}')
        return grpc_messages_pb2.Reply(successful=True)

    # # # # # #
    # Storage #
    # # # # # #

    # User
    async def FindUser( 
        self, request: grpc_messages_pb2.FindRequest,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.User:
        """gRPC to find and retrieve other nodes by its chord id.
        :param request: FindRequest
        :return: User
        """
        try:
            found_node = self.fingertable[request.chordId]
            return grpc_messages_pb2.User(
                successful=True, chordId=found_node.chord_id, ip=found_node.ip, 
                port=found_node.port, publicKey=found_node.public_key, name=found_node.name)
        except KeyError:
                next_node = self.get_next_smaller_successor(request.chordId)
                async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                    stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                    return await stub.FindUser(request)

    # Message
    async def FindMessage( 
        self, request: grpc_messages_pb2.FindRequest,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.Message:
        """gRPC to find and retrieve messages by their chord id.
        :param request: FindRequest
        :return: Message
        """

        if self.check_responsible(request.chordId): # if responsible: retrieve
            dbmessage = Message.getMessageByChordID(con = self.db_conn, ChordID=request.chordId)
            if len(dbmessage)==1:
                dbmessage = dbmessage[0]
                return grpc_messages_pb2.Message(successful=True, chordId=dbmessage.ChordID, content=dbmessage.Content, sender=dbmessage.SenderID, receiver=dbmessage.ReceiverID)
            else:
                return grpc_messages_pb2.Message(successful=False)

        else: # else: send to next
            next_node = self.get_next_smaller_successor(request.chordId)
            async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                return await stub.FindMessage(request)

    async def SaveMessage(
        self, request: grpc_messages_pb2.Message,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.Reply:
        """ gRPC for saving a message
        :param request: Message defined in /proto/grpc_messages.proto
        :return: Reply defined in /proto/grpc_messages.proto
        """

        if self.check_responsible(request.chordId):
            Message(ChordID=request.chordId, Timestamp=int(time.time()), Content=request.content, SenderID=request.sender, ReceiverID = request.receiver).insert(self.db_conn)
            return grpc_messages_pb2.Reply(successful=True)

        else:
            next_node = self.get_next_smaller_successor(request.chordId)
            async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                return await stub.SaveMessage(request)

    # Chat
    async def AddMessageToChat(
        self, request: grpc_messages_pb2.AddMessage,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.Reply:
        """gRPC to store the message chord id for a chat
        :param request: AddMessage defined in /proto/grpc_messages.proto
        :return: Reply defined in /proto/grpc_messages.proto
        """
        
        if self.check_responsible(request.chatChordId): # if responsible: write into db
            Chat(ChatChordID=request.chatChordId, MessageChordID=request.messageChordId).insert(self.db_conn)
            return grpc_messages_pb2.Reply(successful=True)

        else: # if not: send to neighbor
            next_node = self.get_next_smaller_successor(request.chatChordId)
            async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                return await stub.AddMessageToChat(request)

    async def FindMessagesFromChat( 
        self, request: grpc_messages_pb2.FindRequest,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.FindReply:
        """gRPC to find and retrieve messages by their chats chord id.
        :param request: FindRequest defined in /proto/grpc_messages.proto
        :return: FindReply defined in /proto/grpc_messages.proto
        """

        if self.check_responsible(request.chordId):
            try:
                message_chord_ids = Chat.getChatByChordID(con = self.db_conn, ChordID=request.chordId)
                message_chord_ids = [o.MessageChordID for o in message_chord_ids]

                msg = grpc_messages_pb2.FindReply(successful=True)
                msg.foundChordId[:] = message_chord_ids
                return msg

            except DBException:
                return grpc_messages_pb2.FindReply(successful=False)

        else:
            next_node = self.get_next_smaller_successor(request.chordId)
            async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                return await stub.FindMessagesFromChat(request)

    # chatParticipant
    async def AddChatpartner(
        self, request: grpc_messages_pb2.AddChatPartner,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.Reply:
        """gRPC to add ChatPartner, so it can be retrieved from chord
        :param request: AddChatPartner defined in /proto/grpc_messages.proto
        :return: Reply defined in /proto/grpc_messages.proto
        """
        if self.check_responsible(request.chordId): # if responsible: write into db
            ChatParticipants(ChordID = request.chordId, ParticipantChordID = request.partnerChordId).insert(self.db_conn)
            return grpc_messages_pb2.Reply(successful=True)

        else: # if not: send to neighbor
            next_node = self.get_next_smaller_successor(request.chordId)
            async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                return await stub.AddChatpartner(request)

    async def FindChatPartners( 
        self, request: grpc_messages_pb2.FindRequest,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.FindReply:
        """gRPC to find and retrieve chat partners with nodes chord id.
        :param request: FindRequest defined in /proto/grpc_messages.proto
        :return: FindReply defined in /proto/grpc_messages.proto
        """

        if self.check_responsible(request.chordId):
            try:
                partner = ChatParticipants.getChatParticipantsByChordID(con = self.db_conn, ChordID=request.chordId)                
                partner = [o.ParticipantChordID for o in partner]

                logging.info(partner)

                message = grpc_messages_pb2.FindReply(successful=True)
                message.foundChordId[:] = partner
                return message

            except DBException:
                return grpc_messages_pb2.FindReply(successful=False)

        else:
            next_node = self.get_next_smaller_successor(request.chordId)
            async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                return await stub.FindChatPartners(request)

    # Key
    async def FindKey( 
        self, request: grpc_messages_pb2.FindRequest,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.Key:
        """gRPC to find and retrieve keys by their chord id.
        :param request: FindRequest defined in /proto/grpc_messages.proto
        :return: Key defined in /proto/grpc_messages.proto
        """

        if self.check_responsible(request.chordId): # if responsible: retrieve
            try:
                key = Key.getKeyByIdentifierChordID(con = self.db_conn, ChordID=request.chordId)
                return grpc_messages_pb2.Message(successful=True, chordId=key.identifierChordID, partnerId=key.partnerChordID , key=key.Key) 
            except DBException:
                return grpc_messages_pb2.Message(successful=False)

        else: # else: send to next
            next_node = self.get_next_smaller_successor(request.chordId)
            async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                return await stub.FindKey(request)

    async def SaveKey(
        self, request: grpc_messages_pb2.Key,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.Reply:
        """ gRPC to save keys.
        :param request: Key defined in /proto/grpc_messages.proto
        :return: Reply defined in /proto/grpc_messages.proto
        """
        if self.check_responsible(request.chordId):
            Key(identifierChordID=request.chordId, Key=request.Key, partnerChordID=request.partnerId).insert(self.db_conn)
            return grpc_messages_pb2.Reply(successful=True)

        else:
            next_node = self.get_next_smaller_successor(request.chordId)
            async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                return await stub.SaveKey(request)

    # Keychain
    async def addToKeyChain(
        self, request: grpc_messages_pb2.AddKeyChain,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.Reply:
        """gRPC to add key to keychain so it can be retrieved next login
        :param request: AddKeyChain defined in /proto/grpc_messages.proto
        :return: Reply defined in /proto/grpc_messages.proto
        """
        
        if self.check_responsible(request.chordId): # if responsible: write into db
            Keychain(identifierChordID=request.chordId, KeyChordID=request.keyChordId).insert(self.db_conn)
            return grpc_messages_pb2.Reply(successful=True)

        else: # if not: send to neighbor
            next_node = self.get_next_smaller_successor(request.chordId)
            async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                return await stub.addToKeyChain(request)
    
    async def FindKeyChain( 
        self, request: grpc_messages_pb2.FindRequest,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.FindReply:
        """gRPC to find and retrieve key chor_ids with nodes key chord id.
        :param request: AddKeyChain defined in /proto/grpc_messages.proto
        :return: FindReply defined in /proto/grpc_messages.proto
        """

        if self.check_responsible(request.chordId):
            try:
                keys = Keychain.getKeyChordByChordID(con = self.db_conn, ChordID=request.chordId)                
                keys = [o.KeyChordID for o in keys]

                message = grpc_messages_pb2.FindReply(successful=True)
                message.foundChordId[:] = keys
                return message

            except DBException:
                return grpc_messages_pb2.FindReply(successful=False)

        else:
            next_node = self.get_next_smaller_successor(request.chordId)
            async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                return await stub.FindKeyChain(request)

    # # # # # # # # # #
    # gRPC for Client #
    # # # # # # # # # #

    async def StartJoin(
        self, request: grpc_messages_pb2.Empty,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.Reply:
        """gRPC for UI to start the join process at node address given by env variable
        :param request: Empty defined in /proto/grpc_messages.proto (suprise: its empty)
        :return: Reply defined in /proto/grpc_messages.proto
        """
        if os.getenv("my_ip") != "node1":
            async with grpc.aio.insecure_channel(os.getenv("entry_node_address")) as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                message = grpc_messages_pb2.JoinRequest(
                    RequesterChordId=self.chord_id,
                    RequesterIp=self.ip, RequesterPort=self.port, publicKey= self.public_key)
                response = await stub.Join(message)

                if response.suc_chordId:
                    self.change_successor(other_node(
                        chord_id=response.suc_chordId, ip=response.suc_ip,
                        port=response.suc_port, public_key=response.suc_pk))
                if response.pre_chordId:
                    self.change_predecessor(other_node(
                        chord_id=response.pre_chordId, ip=response.pre_ip,
                        port=response.pre_port, public_key=response.pre_pk))

        return grpc_messages_pb2.Reply(successful=True)

    async def SendMessage(
        self, request: grpc_messages_pb2.SendMessageUI,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.SendMessageUIReply:
        """ gRPC for ui to instruct node to send a chat message
        :param request: SendMessageUI defined in /proto/grpc_messages.proto
        :return: Reply defined in /proto/grpc_messages.proto
        """

        logging.info("send message called")

        try:  # check if target is known
            node: other_node = self.fingertable[request.to_chordId]

            if node.chord_id not in self.chat_partners:
                self.chat_partners.append(node.chord_id)

        except KeyError:  # if not known -> search for user
            next_node: other_node = self.get_next_smaller_successor(searched_chord_id=request.to_chordId)

            async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                user = await stub.FindUser(grpc_messages_pb2.FindRequest(chordId=request.to_chordId))

            if user.successful is False:  # return False if user not found
                return grpc_messages_pb2.SendMessageUIReply(successful=False)

            node = other_node(chord_id=user.chordId, ip=user.ip, port=user.port, public_key=user.publicKey, name=user.name)
            self.add_to_fingertable(node=node)
            self.chat_partners.append(node.chord_id)

            # add to chatPartner
            next_node = self.get_next_smaller_successor(self.chat_partner_chord_id)
            async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                message= grpc_messages_pb2.AddChatPartner(chordId=self.chat_partner_chord_id, partnerChordId=node.chord_id)
                res = await stub.AddChatpartner(message)


        logging.info(f'Sending Message to:{node.ip}:{node.port}')
        async with grpc.aio.insecure_channel(f'{node.ip}:{node.port}') as channel:
            stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
            await stub.Chat(grpc_messages_pb2.ChatMsg(content=request.content, sender=self.chord_id, receiver=node.chord_id))

        # STORE LOCALLY
        Message(ChordID=" ", Timestamp=int(time.time()), Content=request.content, SenderID=self.chord_id, ReceiverID = [request.to_chordId]).insert(self.db_conn)

        # SAVE MESSAGE in DB
        msg_chord_id = self.compute_chord_id(f'{self.chord_id}->{request.to_chordId}:{request.content}')
        chat_chord_id = self.compute_chord_id(f'{self.chord_id}:{request.to_chordId}')
        logging.info(f'msg_chord_id: {msg_chord_id}\nchat_chord_id={chat_chord_id}')

        if self.check_responsible(msg_chord_id):
            Message(ChordID=msg_chord_id, Timestamp=int(time.time()), Content=request.content, SenderID=self.chord_id, ReceiverID = [request.to_chordId]).insert(self.db_conn)
        else:
            next_node = self.get_next_smaller_successor(msg_chord_id)
            async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                msg = grpc_messages_pb2.Message(chordId=msg_chord_id, content=request.content, sender=self.chord_id, receiver=request.to_chordId, timestamp= int(time.time()))
                await stub.SaveMessage(msg)

        # add message chord id to chat
        if self.check_responsible(chat_chord_id): 
            Chat(ChatChordID=chat_chord_id, MessageChordID=msg_chord_id).insert(self.db_conn)
        else:
            next_node = self.get_next_smaller_successor(chat_chord_id)
            async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                message= grpc_messages_pb2.AddMessage(chatChordId=chat_chord_id, messageChordId=msg_chord_id)
                await stub.AddMessageToChat(message)

        return grpc_messages_pb2.SendMessageUIReply(successful=True)

    async def Fingertable(
        self, request: grpc_messages_pb2.Empty,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.Empty:
        """ Funktion to create or refresh Fingertable
        :param request: Empty defined in /proto/grpc_messages.proto
        :return: Empty defined in /proto/grpc_messages.proto
        """

        fingernr = 3
        my_chord_id = int(self.predecessor.chord_id, 16)

        for i in range(1, fingernr-1):
            new_node_chord_id = ((my_chord_id + 2**(i-1)) % 2**256)

            next_node = self.get_next_smaller_successor(new_node_chord_id)
            async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                user = await stub.FindUser(chordId = new_node_chord_id)
                new_finger = other_node(user.chordId, user.ip, user.port)
                self.add_to_fingertable(new_finger)


        return grpc_messages_pb2.Empty()

    async def StartGetChatPartners(
        self, request: grpc_messages_pb2.Empty,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.Reply:
        """gRPC to tell the node to fetch users it has already chatted with
        :param request: Empty defined in /proto/grpc_messages.proto
        :return: Reply defined in /proto/grpc_messages.proto
        """
        # get all chord ids of nodes i have chatted with
        next_node = self.get_next_smaller_successor(self.chat_partner_chord_id)
        async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
            stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
            msg = grpc_messages_pb2.FindRequest(chordId=self.chat_partner_chord_id)
            partner_ids = await stub.FindChatPartners(msg)

            partner_ids = partner_ids.foundChordId

        # loop over chord ids of partners, get their info (ip, port, etc) and save in chat_partners dict
        for id in partner_ids:
            next_node = self.get_next_smaller_successor(id)
            async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                msg = grpc_messages_pb2.FindRequest(chordId=id)
                user = await stub.FindUser(msg)

            new_node = other_node(chord_id=user.chordId, ip=user.ip, port=user.port, public_key=user.publicKey, name=user.name)
            self.add_to_fingertable(new_node)

            self.chat_partners.append(user.chordId)

        return grpc_messages_pb2.Reply(successful = True)

    async def StartGetAllMessages(
        self, request: grpc_messages_pb2.Empty,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.Reply:
        """gRPC to tell the node to fetch all messages it has send or received
        :param request: Empty defined in /proto/grpc_messages.proto
        :return: Reply defined in /proto/grpc_messages.proto
        """

        logging.info(f'StartGetAllMessages called')

        for partner in self.chat_partners:
            # create chat key
            chat_id = self.compute_chord_id(f'{self.chord_id}:{partner}')

            # get message chord ids
            next_node = self.get_next_smaller_successor(chat_id)
            async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                msg = grpc_messages_pb2.FindRequest(chordId=chat_id)
                message_ids = await stub.FindMessagesFromChat(msg)

                message_ids = message_ids.foundChordId

                logging.info(f'received message ids: {message_ids}')

                # iterate over message chord ids and search for message
                for message_id in message_ids:
                    next_node = self.get_next_smaller_successor(chat_id)
                    async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                        message= grpc_messages_pb2.FindRequest(chordId=message_id)
                        res = await stub.FindMessage(message)

                        # get and save message
                        logging.info(f' content: {res.content}')
                        Message(ChordID=" ", Timestamp=res.timestamp, Content=res.content, SenderID=res.sender, ReceiverID = [res.receiver]).insert(self.db_conn)

        return grpc_messages_pb2.Reply(successful = True)

    async def PreSuc(
        self, request: grpc_messages_pb2.PSreq,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.PSres:
        """ gRPC to log successor and predecessor
        :param request: PSreq defined in /proto/grpc_messages.proto
        :return: PSres defined in /proto/grpc_messages.proto
        """

        suc = self.successor
        pre = self.predecessor
        logging.info(f'successors: {suc}')
        logging.info(f'predecessor: {pre}')

        return grpc_messages_pb2.PSres(a ="dsa")

    async def getMessages(
        self, request: grpc_messages_pb2.User,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.MessagesWrapper:
        """ gRPC to get all (locally) stored messages
        :param request: User defined in /proto/grpc_messages.proto
        :return: MessagesWrapper defined in /proto/grpc_messages.proto
        """
        dbmessages = Message.getMessageByChordID(con = self.db_conn, ChordID=" ")
        
        # filtering messages
        filtered_messages = []
        for  message in dbmessages:
            if message.SenderID == request.chordId or message.ReceiverID[0] == request.chordId:
                filtered_messages.append(message)

        wrapper = grpc_messages_pb2.MessagesWrapper()
        for o in filtered_messages:
            msg = grpc_messages_pb2.Message(content=o.Content, sender=o.SenderID, receiver=o.ReceiverID, timestamp=o.Timestamp)
            wrapper.Messages.append(msg)

        return wrapper

    async def getChatpartner(
        self, request: grpc_messages_pb2.Empty,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.UserChordIdList:
        """ rpc for flask api to get a list of all chat partner chord ids
        :param request: Empty defined in /proto/grpc_messages.proto
        :return: UserChordIdList defined in /proto/grpc_messages.proto
        """

        response = grpc_messages_pb2.UserChordIdList()

        logging.info(f'{self.chat_partners}')
        
        for i in self.chat_partners:
            response.chord_ids.append(i)

        return response


    # BOOTSTRAP

    async def LoginNewNode(
        self, request: grpc_messages_pb2.LogInToNewNodeRequest,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.Empty:
        """ gRPC to call to get a standbynode to prepare and join the chord network
        :param request: LogInToNewNodeRequest defined in /proto/grpc_messages.proto
        :return: Empty defined in /proto/grpc_messages.proto
        """

        # get standby node
        node = self.get_standby_node()

        # send them chord_ids
        async with grpc.aio.insecure_channel(f'{node.ip}:{node.port}') as channel:
            stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
            message = grpc_messages_pb2.NewChordIDs(chordId=request.chordId, keyId=request.keyId, partnerId=request.partnerId)
            await stub.SetChordIds(message)

        # tell them to join
        async with grpc.aio.insecure_channel(f'{node.ip}:{node.port}') as channel:
            stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
            await stub.StartJoin(grpc_messages_pb2.Empty())

        # create public and private key
        async with grpc.aio.insecure_channel(f'{node.ip}:{node.port}') as channel:
            stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
            msg = grpc_messages_pb2.PubPrivKey(n=1, e=2, d=3)
            await stub.createAssymetricKeys(msg)

        # get all chat messages related to node from chord network
        async with grpc.aio.insecure_channel(f'{node.ip}:{node.port}') as channel:
            stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
            await stub.StartGetChatPartners(grpc_messages_pb2.Empty())

        # get all chat messages related to node from chord network
        async with grpc.aio.insecure_channel(f'{node.ip}:{node.port}') as channel:
            stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
            await stub.StartGetAllMessages(grpc_messages_pb2.Empty())

        # return chord_id, ip, port, name?
        message = grpc_messages_pb2.User(successful=True, ip=node.ip, port=node.port)
        return message

    async def Logout(self, request: grpc_messages_pb2.Empty,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.Empty:
        """ to call to logout the node from chord network
        :param request: Empty defined in /proto/grpc_messages.proto
        :return: Empty defined in /proto/grpc_messages.proto
        """
        #set successor
        async with grpc.aio.insecure_channel(f'{self.predecessor.ip}:{self.predecessor.port}') as channel:
            stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
            message= grpc_messages_pb2.SetSuccessorRequest(chordId=self.successor.chord_id, ip=self.successor.ip, port=self.successor.port)
            await stub.SetSuccessor(message)
        #set predecessor
        async with grpc.aio.insecure_channel(f'{self.successor.ip}:{self.successor.port}') as channel:
            stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
            message= grpc_messages_pb2.SetPredecessorRequest(chordId=self.predecessor.chord_id, ip=self.predecessor.ip, port=self.predecessor.port)
            await stub.SetPredecessor(message)
        #get all sendable db objects
        chats = Chat.getAll(self.db_conn)
        chatParticipants = ChatParticipants.getAll(self.db_conn)
        keys = Key.getAll(self.db_conn)
        keychains = Keychain.getAll(self.db_conn)
        messages = Message.getAllWithID(self.db_conn) 
        #send db objects

        for c in chatParticipants:
            async with grpc.aio.insecure_channel(f'{self.successor.ip}:{self.successor.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                message= grpc_messages_pb2.AddChatPartner(chordId=c.ChordID, partnerChordId=c.ParticipantChordID)
                await stub.AddChatPartner(message)  

        for c in chats:
            async with grpc.aio.insecure_channel(f'{self.successor.ip}:{self.successor.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                message= grpc_messages_pb2.AddMessage(chatChordId=c.ChatChordID, messageChordID=c.MessageChordID)
                await stub.AddMessageToChat(message)

        for k in keys:
            async with grpc.aio.insecure_channel(f'{self.successor.ip}:{self.successor.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                message= grpc_messages_pb2.Key(chordId=k.identifierChordID, partnerId=k.partnerChordID, key=k.Key)
                await stub.SaveKey(message)

        for k in keychains:
            async with grpc.aio.insecure_channel(f'{self.successor.ip}:{self.successor.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                message= grpc_messages_pb2.AddKeyChain(chordId=k.identifierChordID, keyChordId=k.keyChordID)
                await stub.addToKeyChain(message)

        for m in messages:
            async with grpc.aio.insecure_channel(f'{self.successor.ip}:{self.successor.port}') as channel:
                stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                message= grpc_messages_pb2.Message(chordId=m.ChordID, content=m.Content, timestamp=m.Timestamp, sender=m.SenderID, receiver=m.ReceiverID[0]) 
                await stub.SaveMessage(message)
        return  grpc_messages_pb2.Empty

    async def Register(
        self, request: grpc_messages_pb2.RegisterNode,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.Reply:
        """ gRPC to register as standby node; ready to get assigned a chord_id
        :param request: RegisterNode defined in /proto/grpc_messages.proto
        :return: Reply defined in /proto/grpc_messages.proto
        """
        
        node = other_node(chord_id=None, ip=request.ip, port=request.port)
        self.register_new_standby_node(node)

        return grpc_messages_pb2.Reply(successful=True)

    async def StartRegister(
        self, request: grpc_messages_pb2.Empty,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.Reply:
        """ gRPC to tell a node to send Register() to bootstrap node set by docker compose as environment variable
        :param request: Empty defined in /proto/grpc_messages.proto
        :return: Reply defined in /proto/grpc_messages.proto
        """
        my_ip=os.getenv("my_ip")
        my_port=int(os.getenv("my_port"))
        async with grpc.aio.insecure_channel(os.getenv("entry_node_address")) as channel:
            stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
            msg = grpc_messages_pb2.RegisterNode(ip=my_ip , port=my_port)
            await stub.Register(msg)

        return grpc_messages_pb2.Reply(successful=True)

    async def RetrieveKeys(
        self, request: grpc_messages_pb2.Empty,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.Reply:
        """ gRPC to tell the node to retrieve all keys stored in chord network
        :param request: Empty defined in /proto/grpc_messages.proto
        :return: Reply defined in /proto/grpc_messages.proto
        """
        # Get all key chord ids from keychain
        next_node = self.get_next_smaller_successor(self.keychain_chord_id)
        async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
            stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
            msg = grpc_messages_pb2.FindRequest(chordId=self.keychain_chord_id)
            response = await stub.FindKeyChain(msg)

        if len(response.foundChordId) > 0:
            for key_chord_id in response.foundChordId:

                next_node = self.get_next_smaller_successor(key_chord_id)
                async with grpc.aio.insecure_channel(f'{next_node.ip}:{next_node.port}') as channel:
                    stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
                    msg = grpc_messages_pb2.FindRequest(chordId=key_chord_id)
                    response = await stub.FindKeyChain(msg)

                #TODO response.key mit eigenem private key entschlüsseln
                
                self.symmetric_keys[response.partnerId] = response.key

        return grpc_messages_pb2.Reply(successful=True)

    # ENCRYPTION

    async def createAssymetricKeys(
        self, request: grpc_messages_pb2.PubPrivKey,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.Reply:
        """ rpc call to create public and private key in node
        :param request: PubPrivKey defined in /proto/grpc_messages.proto
        :return: Reply defined in /proto/grpc_messages.proto
        """
        n = request.n
        e = request.e
        d = request.d

        #TODO public und private key generieren

        self.private_key = f'{n}'
        self.public_key = f'{e}'

        return grpc_messages_pb2.Reply(successful=True)

    async def shareSymmetricKey(
        self, request: grpc_messages_pb2.SymmetricKey,
        context: grpc.aio.ServicerContext) -> grpc_messages_pb2.Reply:
        """ rpc call to share a symmetric key with partner
        :param request: SymmetricKey defined in /proto/grpc_messages.proto
        :return: Reply defined in /proto/grpc_messages.proto
        """
        
        self.symmetric_keys[request.partnerChordId] = request.key

        return grpc_messages_pb2.Reply(successfull=True)

async def serve(node: ServerNode) -> None:
        server = grpc.aio.server()
        grpc_messages_pb2_grpc.add_grpc_serviceServicer_to_server(node, server)
        listen_addr = f'[::]:{node.port}'
        server.add_insecure_port(listen_addr)
        logging.info("Starting server on %s", listen_addr)
        await server.start()
        await server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    if os.environ.get('https_proxy'):
        del os.environ['https_proxy']
    if os.environ.get('http_proxy'):
        del os.environ['http_proxy']

    create_db()

    ip = os.getenv("my_ip")
    port = int(os.getenv("my_port"))
    node = ServerNode(ip, port, db_name="database.db")

    asyncio.run(serve(node=node))
