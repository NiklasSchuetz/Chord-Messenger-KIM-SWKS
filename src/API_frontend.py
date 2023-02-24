from flask import Flask, json, url_for, request
from flask_cors import CORS, cross_origin
from flask import jsonify

import logging
import asyncio
import grpc
import time
import hashlib


import os
from client import message

import grpc_messages_pb2
import grpc_messages_pb2_grpc


chordsdsad = str(hashlib.sha256(str("sdadsasdadsasd:sdadasdasd").encode()).hexdigest())
keychainds = str(hashlib.sha256(str("sdadsasdadsasd:sdassadsd_keys").encode()).hexdigest())
partners = str(hashlib.sha256(str("sdadsasdadsasd:sddsadadsadssasd_partners").encode()).hexdigest())

loop = asyncio.get_event_loop()
application = Flask(__name__)
api_cors_config = {
  "origins": ["http://localhost:4200", "http://localhost"],
  "methods": ["OPTIONS", "GET", "POST"],
  "allow_headers": ["Authorization", "Content-Type", "Access-Control-Allow-Origin"]
}
CORS(application, resources={"/api/*": api_cors_config}, supports_credentials=True)
application.config['CORS_HEADERS'] = 'Content-Type'

@application.route("/")
def index():
    return "Hello World!"

@application.route("/api")
async def api():
    return "api working"

@application.route("/api/post/login3", methods=['POST'])
@cross_origin()
def api_post_login3():
    userName = request.json['userName']
    password = request.json['password']
    
    n = request.json['n']
    e = request.json['e']
    d = request.json['d']
    chordId = str(hashlib.sha256(f'{userName}{password}'.encode()).hexdigest())
    keyId= str(hashlib.sha256(f'{userName}{password}-keys'.encode()).hexdigest())
    partnerId= str(hashlib.sha256(f'{userName}{password}-partner'.encode()).hexdigest())
    logging.info("###################S1")
    response = loop.run_until_complete(login(chordId, keyId, partnerId))
    logging.info("###################S2")
    logging.info(response)
    return jsonify("{ \"ChordID\": \""+ chordId + "\", \"IP\": \"" + str(response.port) + "\", \"Name\": \"" + chordId + "\", \"accessToken\": \"accessToken123\"}")


#region POST
@application.route("/api/post/login2", methods=['POST'])
@cross_origin()
def api_post_login2():
    if request.method == 'POST':
        userName = request.json['userName']
        password = request.json['password']
        
        n = request.json['n']
        e = request.json['e']
        d = request.json['d']

        logging.basicConfig()

        # for port in range(50001, 50010):
        #     asyncio.run(createPPKey(port))
        #     time.sleep(0.2)

        # for port in range(50002, 50010):
        #     asyncio.run(startJoin(port=port))
        #     time.sleep(0.2)

        # for port in range(50001, 50010):
        #     asyncio.run(getPreSuc(port=port))
        #     time.sleep(0.2)

        # ret = loginlocal()

        #TODO get user that fits the credentials from node
        # with grpc.insecure_channel(f'127.0.0.1:50001') as channel:
        #         stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        #         msg = grpc_messages_pb2.LogInToNewNodeRequest(chordId = "8f752e7f1a2af72f2ce3c11eaddc9a330399b5bc251206f8a80dcb1cb0a047c8", keyId = "1c7653f9939245b32c340c4ff28a535e9648eaf988470da6685a92c506e5e086", partnerId="f17322634ebe8626bd9e60a0e6632f025d1259b45d2e408256d12bdf23dc6935", n=187, e=56, d=323) 
        #         res = return stub.LoginNewNode(msg)
        #         print(res.ip)
        #         print(res.port)

        #return chordID -1 if credentials are false
        return jsonify("{ \"ChordID\": \"123\", \"IP\": \"" + "res.ip" + "." + "res.port" + "\", \"Name\": \"NameChordUser\", \"accessToken\": \"accessToken123\"}")

@application.route("/api/post/login", methods=['POST'])
@cross_origin()
async def api_post_login():
    if request.method == 'POST':
        userName = request.json['userName']
        password = request.json['password']
        
        n = request.json['n']
        e = request.json['e']
        d = request.json['d']

        logging.basicConfig()

        # for port in range(50001, 50010):
        #     createPPKey(port)
        #     time.sleep(0.2)

        # for port in range(50002, 50010):
        #     startJoin(port=port)
        #     time.sleep(0.2)

        # for port in range(50001, 50010):
        #     getPreSuc(port=port)
        #     time.sleep(0.2)

        # startRegister(50010)
        #time.sleep(0.2)
        return await jsonify(login())
        #return chordID -1 if credentials are false
        #return jsonify("{ \"ChordID\": \"123\", \"IP\": \"" + res.ip + "." + res.port + "\", \"Name\": \"NameChordUser"+ res.ip + "." + res.port +"\", \"accessToken\": \"accessToken123\"}")
        #return jsonify(res)

@application.route("/api/post/message", methods=['POST'])
def api_post_message():
    if request.method == 'POST':
        senderID = request.json['senderID']
        receiverID = request.json['receiverID']
        messageContent = request.json['messageContent']
        accessToken = request.json['accessToken']
        #TODO get user that fits the credentials from node 
        logging.info("###################M1")
        logging.info(senderID)
        logging.info(receiverID)
        logging.info(messageContent)
        response = loop.run_until_complete(startChat(senderID, receiverID, messageContent))
        logging.info("###################M2")
        logging.info(response)
        return jsonify("{ \"status\": \"200\"}")
        # return "{ \"status\": \"404\" }"

#endregion

#region GET
@application.route("/api/get/chats", methods=['POST'])
@cross_origin()
def api_get_chats():
    userID = request.json['userID']
    accessToken = request.json['accessToken']
    #TODO load chats of user
    logging.info("###################C1")
    logging.info(userID)
    response = loop.run_until_complete(getChatpartner(userID))
    logging.info("###################C2")
    logging.info(response)
    jsonResponse = "{ \"chats\": ["
    
    counter = 0
    for chat in response:
        counter += 1
        logging.info(chat)
        jsonResponse += "{\"ChatID\": \"" + str(chat) + "\", \"Name\": \"" + str(chat) + "\"}"
        if counter < len(response):
            jsonResponse += ", "
    

    logging.info("###################C3")
    

    # content: "4"
    # receiver: "c863f3dada8d2d53c35f274dfa61f25a2270baef5747da58e4e7ab084db3d3ed"     
    # sender: "8f752e7f1a2af72f2ce3c11eaddc9a330399b5bc251206f8a80dcb1cb0a047c8"       
    # timestamp: 1631649803

    jsonResponse  += "] }"
    
    logging.info(jsonResponse)
    #return jsonify("{ \"chats\": [ { \"ChatID\": 1, \"Name\": \"Name\", \"Users\": [{ \"ChordID\": \"ChordID\", \"IP\": \"IP\", \"Name\": \"Name\"}, { \"ChordID\": \"ChordID\", \"IP\": \"IP\", \"Name\": \"Name\"}] }, { \"ChatID\": 2, \"Name\": \"Name\", \"Users\": [{ \"ChordID\": \"ChordID\", \"IP\": \"IP\", \"Name\": \"Name\"}, { \"ChordID\": \"ChordID\", \"IP\": \"IP\", \"Name\": \"Name\"}] } ] }")
    return jsonify(jsonResponse)

@application.route("/api/get/users", methods=['POST'])
def api_get_users():
    if request.method == 'POST':
        userID = request.json['userID']
        accessToken = request.json['accessToken']
        #TODO load users

        return jsonify("{ \"users\": [ { \"ChordID\": \"ChordID\", \"IP\": \"IP\", \"Name\": \"Name\"}, { \"ChordID\": \"ChordID\", \"IP\": \"IP\", \"Name\": \"Name\"}] }")

@application.route("/api/get/messages", methods=['POST'])
def api_get_messages():
    if request.method == 'POST':
        chatID = request.json['chatID']
        port = request.json['port']
        accessToken = request.json['accessToken']
        #TODO load messages of chat
        logging.info("###################GM1")
        logging.info(chatID)
        logging.info(port)
        response = loop.run_until_complete(getMessages(port, chatID))
        logging.info("###################GM2")
        logging.info(response)
        jsonResponse = "{ \"messages\": ["
        #if response != []:
        counter = 0
        for msg in response:
            counter += 1
            logging.info(msg)
            jsonResponse += "{ \"ChordID\": \"ChordID\", \"Timestamp\": \"" 
            jsonResponse += str(msg.timestamp) 
            jsonResponse += "\", \"Content\": \"" 
            jsonResponse += str(msg.content) + "\", \"SenderID\": \"" 
            jsonResponse += str(msg.sender)
            jsonResponse += "\", \"ReceiverID\": \"" 
            jsonResponse += str(msg.receiver)
            jsonResponse += "\" }"
            if counter < len(response):
                jsonResponse += ", "
        

        logging.info("###################GM3")
        
    
        # content: "4"
        # receiver: "c863f3dada8d2d53c35f274dfa61f25a2270baef5747da58e4e7ab084db3d3ed"     
        # sender: "8f752e7f1a2af72f2ce3c11eaddc9a330399b5bc251206f8a80dcb1cb0a047c8"       
        # timestamp: 1631649803

        jsonResponse  += "] }"
        
        logging.info(jsonResponse)
        #return jsonify("{ \"messages\": [ { \"ChordID\": \"ChordID\", \"Timestamp\": \"Timestamp\", \"Content\": \"Content\", \"SenderID\": \"SenderID\", \"ReceiverID\": \"ReceiverID\" }, { \"ChordID\": \"ChordID\", \"Timestamp\": \"Timestamp\", \"Content\": \"Content\", \"SenderID\": \"SenderID\", \"ReceiverID\": \"ReceiverID\" }] }")
        return jsonify(jsonResponse)
  
#endregion

#region GRPC NODE FUNC ASYNC
async def startChat(sender, to_chordId, content):
    async with grpc.aio.insecure_channel(f'127.0.0.1:{sender}') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        message= grpc_messages_pb2.SendMessageUI(to_chordId = to_chordId, content = content)
        res = await stub.SendMessage(message)
        return res

async def startJoin(port):
    async with grpc.aio.insecure_channel(f'127.0.0.1:{port}') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        message= grpc_messages_pb2.Empty()
        await stub.StartJoin(message)

async def getPreSuc(port):
    async with grpc.aio.insecure_channel(f'127.0.0.1:{port}') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        message= grpc_messages_pb2.PSreq(a="dsadasd")
        await stub.PreSuc(message)

async def saveMessage():
    async with grpc.aio.insecure_channel(f'127.0.0.1:50001') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        message= grpc_messages_pb2.Message(chordId="14c4f561fc71748ffbd9a6adf249806dd3226cb3d01773226cb3d01779855d8eb2df67166700", content="das ist eine nachricht",  sender="12346516546")
        message.receiver = "187ads"
        await stub.SaveMessage(message)

async def getMessage(chordid):
    async with grpc.aio.insecure_channel(f'127.0.0.1:50001') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        message= grpc_messages_pb2.FindRequest(chordId=chordid)
        res = await stub.FindMessage(message)
        if res.successful:
            print(res.content)
        else:
            print(res.successful)

async def addMessageToChat(chatChord, msgChord):
    async with grpc.aio.insecure_channel(f'127.0.0.1:50001') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        message= grpc_messages_pb2.AddMessage(chatChordId=chatChord, messageChordId=msgChord)
        await stub.AddMessageToChat(message)

async def FindMessagesFromChat(chatChord):
    async with grpc.aio.insecure_channel(f'127.0.0.1:50001') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        message = grpc_messages_pb2.FindRequest(chordId = chatChord)
        res = await stub.FindMessagesFromChat(message)
        for i in res.foundChordId:
            print(i)
        return res.foundChordId

async def SetChordId():
    async with grpc.aio.insecure_channel(f'127.0.0.1:50001') as channel:
       stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
       message = grpc_messages_pb2.NewChordIDs(chordId="1", keyId="2", partnerId="3")
       await stub.SetChordIds(message)

async def AddChatpartner(chatpartners, partner):
    async with grpc.aio.insecure_channel(f'127.0.0.1:50001') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        message = grpc_messages_pb2.AddChatPartner(chordId=chatpartners, partnerChordId = partner)
        await stub.AddChatpartner(message)
  
async def FindChatPartners(chatChord):
    async with grpc.aio.insecure_channel(f'127.0.0.1:50001') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        message = grpc_messages_pb2.FindRequest(chordId = chatChord)
        res = await stub.FindChatPartners(message)
        for i in res.foundChordId:
            print(i)

async def Fingertable():
    async with grpc.aio.insecure_channel(f'127.0.0.1:50001') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        message = grpc_messages_pb2.Empty()
        await stub.Fingertable(message)

async def findKey():
    async with grpc.aio.insecure_channel(f'127.0.0.1:50001') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        message = grpc_messages_pb2.Empty()
        await stub.Fingertable(message)

async def startRegister(port):
    async with grpc.aio.insecure_channel(f'127.0.0.1:{port}') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        await stub.StartRegister(grpc_messages_pb2.Empty())

async def getMessages(port):
    async with grpc.aio.insecure_channel(f'127.0.0.1:{port}') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        await stub.getMessages(grpc_messages_pb2.Empty())

async def login(_chordId, _keyId, _partnerId):
    async with grpc.aio.insecure_channel(f'127.0.0.1:50001') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        msg = grpc_messages_pb2.LogInToNewNodeRequest(chordId = _chordId, keyId = _keyId, partnerId=_partnerId, n=187, e=56, d=323) 
        res = await stub.LoginNewNode(msg)
        return res

async def getMessages(port, id):
    async with grpc.aio.insecure_channel(f'127.0.0.1:{port}') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        res = await stub.getMessages(grpc_messages_pb2.User(chordId=id))
        for msg in res.Messages:
            print(msg)
            # msg ist vom typ Message (proto): 
            # beispielantwort:
            # content: "4"
            # receiver: "c863f3dada8d2d53c35f274dfa61f25a2270baef5747da58e4e7ab084db3d3ed"     
            # sender: "8f752e7f1a2af72f2ce3c11eaddc9a330399b5bc251206f8a80dcb1cb0a047c8"       
            # timestamp: 1631649803
        return res.Messages

async def getChatpartner(port):    
    async with grpc.aio.insecure_channel(f'127.0.0.1:{port}') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        msg= grpc_messages_pb2.Empty()
        res = await stub.getChatpartner(msg)
        for i in res.chord_ids:
            print(i)
        return res.chord_ids

async def createPPKey(port):
    async with grpc.aio.insecure_channel(f'127.0.0.1:{port}') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        msg=grpc_messages_pb2.PubPrivKey(n = 4, e = 5, d = 6)
        await stub.createAssymetricKeys(msg)

# def message():
    while True:
        sender = input("port wer?")
        to_chord = input("an wen (chordid)?")
        content = input("content: ")
        asyncio.run(startChat(sender=sender, to_chordId=to_chord, content=content))
#endregion



if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    application.run(host='0.0.0.0', port = int(os.getenv("flask_port")), debug=True)
    #application.run(port = 1337, debug=True)