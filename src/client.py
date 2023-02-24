import logging
import asyncio
import grpc
import time
import hashlib

import grpc_messages_pb2
import grpc_messages_pb2_grpc


chordsdsad = str(hashlib.sha256(str("sdadsasdadsasd:sdadasdasd").encode()).hexdigest())
keychainds = str(hashlib.sha256(str("sdadsasdadsasd:sdassadsd_keys").encode()).hexdigest())
partners = str(hashlib.sha256(str("sdadsasdadsasd:sddsadadsadssasd_partners").encode()).hexdigest())

# GRPC calls
async def startChat(sender, to_chordId, content):
    async with grpc.aio.insecure_channel(f'127.0.0.1:{sender}') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        message= grpc_messages_pb2.SendMessageUI(to_chordId = to_chordId, content = content)
        await stub.SendMessage(message)

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

async def saveMessage(chordid, content, sender, receiver):
    async with grpc.aio.insecure_channel(f'127.0.0.1:50001') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        message= grpc_messages_pb2.Message(chordId=chordid, content=content,  sender=sender, receiver = receiver)
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



#####################################################################################

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

async def getChatpartner(port):    
    async with grpc.aio.insecure_channel(f'127.0.0.1:{port}') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        msg= grpc_messages_pb2.Empty()
        res = await stub.getChatpartner(msg)
        for i in res.chord_ids:
            print(i)

#####################################################################################


async def login():
    async with grpc.aio.insecure_channel(f'127.0.0.1:50001') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        msg = grpc_messages_pb2.LogInToNewNodeRequest(chordId = "8f752e7f1a2af72f2ce3c11eaddc9a330399b5bc251206f8a80dcb1cb0a047c8", keyId = "1c7653f9939245b32c340c4ff28a535e9648eaf988470da6685a92c506e5e086", partnerId="f17322634ebe8626bd9e60a0e6632f025d1259b45d2e408256d12bdf23dc6935", n=187, e=56, d=323) 
        res = await stub.LoginNewNode(msg)
        print(res.ip)
        print(res.port)

async def logout(port):
    async with grpc.aio.insecure_channel(f'127.0.0.1:{port}') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        await stub.Logout(grpc_messages_pb2.Empty())

async def createPPKey(port):
    async with grpc.aio.insecure_channel(f'127.0.0.1:{port}') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        msg=grpc_messages_pb2.PubPrivKey(n = 4, e = 5, d = 6)
        await stub.createAssymetricKeys(msg)

async def find_get_chatpartners(port):
    async with grpc.aio.insecure_channel(f'127.0.0.1:{port}') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        msg=grpc_messages_pb2.Empty()
        await stub.StartGetChatPartners(msg)

async def StartGetAllMessages(port):
    async with grpc.aio.insecure_channel(f'127.0.0.1:{port}') as channel:
        stub = grpc_messages_pb2_grpc.grpc_serviceStub(channel)
        msg=grpc_messages_pb2.Empty()
        await stub.StartGetAllMessages(msg)

def message():
    while True:
        sender = input("port wer?")
        to_chord = input("an wen (chordid)?")
        content = input("content: ")
        asyncio.run(startChat(sender=sender, to_chordId=to_chord, content=content))

# MAIN
if __name__ == '__main__':
    logging.basicConfig()

    print(chordsdsad)
    print(keychainds)
    print(partners)

    for port in range(50001, 50005):
        asyncio.run(createPPKey(port))
        time.sleep(0.1)

    for port in range(50002, 50005):
        asyncio.run(startJoin(port=port))
        time.sleep(0.1)

    for port in range(50001, 50005):
        asyncio.run(getPreSuc(port=port))
        time.sleep(0.2)


    # Store Chat Partner and retrieve
    # asyncio.run(AddChatpartner(partners, "c863f3dada8d2d53c35f274dfa61f25a2270baef5747da58e4e7ab084db3d3ed"))
    # asyncio.run(AddChatpartner(partners, "489b106d9c4954acf69dbc3d4f35755bfedc221a19b3e23412df6ed72e2a19b1"))

    # asyncio.run(find_get_chatpartners(port=50010))

    asyncio.run(startRegister(50005))
    asyncio.run(startRegister(50006))
    asyncio.run(startRegister(50007))
    asyncio.run(startRegister(50008))
    asyncio.run(startRegister(50009))
    asyncio.run(startRegister(50010))
    time.sleep(0.2)
    print("init done")

    # SEND MESSAGES
    # asyncio.run(startChat(sender=50010, to_chordId="772fdb33dd99cfaa898d85930d9228b40a8065cd17de4df1cf7fbf54f84cb982", content="1"))
    # asyncio.run(startChat(sender=50010, to_chordId="c863f3dada8d2d53c35f274dfa61f25a2270baef5747da58e4e7ab084db3d3ed", content="2"))
    # asyncio.run(startChat(sender=50010, to_chordId="c863f3dada8d2d53c35f274dfa61f25a2270baef5747da58e4e7ab084db3d3ed", content="3"))
    # asyncio.run(startChat(sender=50010, to_chordId="c863f3dada8d2d53c35f274dfa61f25a2270baef5747da58e4e7ab084db3d3ed", content="4"))
    # asyncio.run(startChat(sender=50005, to_chordId="8f752e7f1a2af72f2ce3c11eaddc9a330399b5bc251206f8a80dcb1cb0a047c8", content="5"))


    # GET MESSAGES BETWEEN node 5 and node 10
    #asyncio.run(getMessages(50010, "c863f3dada8d2d53c35f274dfa61f25a2270baef5747da58e4e7ab084db3d3ed"))

    # GET CHATPARTNER OF node 10
    #asyncio.run(getChatpartner(port=50010))

    # print(asyncio.run(FindMessagesFromChat("6d710592cd3c6451c52147dd718aeb6ac61c681dc2b644955de8f3fe6b98338e")))


