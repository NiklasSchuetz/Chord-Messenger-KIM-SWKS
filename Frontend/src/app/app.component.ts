import { Component, ModuleWithComponentFactories, OnInit } from '@angular/core';
import { HttpService } from './http.service';
import {Observable,of, from } from 'rxjs';


@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})

export class AppComponent implements OnInit{
  authenticated = false;
  userName = "";
  password = "";
  accessToken = "";
  loading = false;
  currentUser = {} as User;
  chats = new Array<Chat>();
  contacts = new Array<User>();
  selectedChat = {} as Chat;
  messageToSend: any;
  newChatChordID = "";

  n  = 43;
  e  = 26;
  d  = 18;

  sub:any;

  constructor(private http: HttpService){}
  
  //dummy
  dummyusers = new Array<User>();
  dummymessages = new Array<Message>();
  dummymessages2 = new Array<Message>();

  
  ngOnInit(){
    //Put in chordID + Rnd Key
    //await IP+Port of own node
    //get Users/Chats from node
    
    //https://github.com/htw-saar/SWKS-SoSe2021_Gruppe1/blob/feature/grcp_node/src/protos/grpc_messages.proto #21
    

    //#region fill with dummy data
    // this.currentUser = new User("ChordID2", "192.168.0.2", "User2");

    // this.dummyusers.push(new User("ChordID1", "192.168.0.1", "User1"));
    // this.dummyusers.push(new User("ChordID2", "192.168.0.2", "User2"));
    // this.dummyusers.push(new User("ChordID3", "192.168.0.3", "User3"));
    // this.dummyusers.push(new User("ChordID4", "192.168.0.4", "User4"));
    // this.dummyusers.push(new User("ChordID5", "192.168.0.5", "User5"));
    // this.dummyusers.push(new User("ChordID6", "192.168.0.6", "User6"));


    // this.dummymessages.push(new Message( "chord10101010", new Date().toLocaleDateString(), "messagecontent", "ChordID3","ChordID1"));
    

    // this.chats.push(new Chat(1,"Chatname1", "today 13:23", this.dummyusers, this.dummymessages));
    // this.chats.push(new Chat(2,"Chatname2", "today 13:21", this.dummyusers, this.dummymessages2));
    // this.chats.push(new Chat(3,"Chatname3", "today 12:23", this.dummyusers, this.dummymessages2));
    // this.chats.push(new Chat(4,"Chatname4", "today 10:53", this.dummyusers, this.dummymessages));
    //#endregion

  }

  initUserData(){
    console.log("initUserData");
    //Get all data for currentUser per httpcalls
    this.http.getUsers(this.currentUser.IP, this.currentUser.ChordID, this.accessToken).subscribe( data=>{
      var resp = JSON.parse(data);
      if(resp != null && resp.users != null){
        this.contacts.push.apply(this.contacts, resp.users);
      }
    })
    this.http.getChats(this.currentUser.IP, this.currentUser.ChordID, this.accessToken).subscribe( data=>{
      var resp = JSON.parse(data);
      if(resp != null && resp.chats != null){
        this.chats.push.apply(this.chats, resp.chats);
        this.swapChat(this.chats[0].ChatID);
      }
      console.log(this.chats);
      //start the auto chat refresh
      //setInterval(()=> { this.swapChat(this.selectedChat.ChatID) }, 5 * 1000);
    })
  }

  logIn(){
    console.log("logIn");
    this.currentUser = new User("1", "50201", "empty");
    //send Username and password to Server and set currentUser
    //this.http.postLogin(this.userName, this.password).subscribe( data=>{
    try{
      this.http.postLogin(this.currentUser.IP, this.userName, this.password, this.n, this.e ,this.d).subscribe( data=>{
        console.log(data);
        var newUser = JSON.parse(data);
        //if login ok
        if(newUser.ChordID != "-1"){
          this.currentUser = newUser;
          var backupNumber: number = +this.currentUser.IP + 200;
          this.currentUser.IP = backupNumber.toString();
          this.accessToken = newUser.accessToken;
          this.userName = "";
          this.password = "";
          this.authenticated = true;
          //this.initUserData();
        }
        else{
          //else show error
          alert("Login not viable");
        }
      }); 
    }
    catch(e){
      alert("no free nodes. Sorry");
    }
  }

  logOut(){
    console.log("logOut");
    //wipe local data and show login mask
    this.currentUser = new User("", "", "No User");
    this.chats = new Array<Chat>();
    this.contacts = new Array<User>();
    this.authenticated = false;
  }

  refreshChat(){
    this.swapChat(this.selectedChat.ChatID)
  }

  refreshUser(){
    this.http.getChats(this.currentUser.IP, this.currentUser.ChordID, this.accessToken).subscribe( data=>{
      console.log(data);
      var resp = JSON.parse(data);
      if(resp != null && resp.chats != null){
        console.log(resp);
        this.chats = Array<Chat>()
        this.chats = resp.chats;
        this.swapChat(this.chats[0].ChatID);
      }
      console.log(this.chats);
    })
  }

  swapChat(chatID: string){
    if(chatID != "" && chatID != undefined){
      console.log("swapping chat");
      //find chat in local list and load the messages for this chat per http call
      this.selectedChat = <Chat>this.chats.find(x => x.ChatID == chatID);
      if(this.selectedChat!= null){
        this.http.getMessages(this.currentUser.IP, chatID, this.accessToken).subscribe( data=>{
          console.log(data);
          var resp = JSON.parse(data);
          if(resp != null && resp.messages != null){
            console.log(resp);
            this.selectedChat.Messages = Array<Message>();
            this.selectedChat.Messages = resp.messages;
          }
        })
      }
    }
    else{
      console.log("Please log in!");
    }
  }

  sendMessage(){
    console.log("sending message");
    var targetID = this.selectedChat.ChatID;
    //send message to node
    var newMessage = new Message("-1", new Date().toLocaleDateString(), this.messageToSend, this.currentUser.ChordID, targetID.toString());
    
    this.http.postMessage(this.currentUser.IP, newMessage.Content, Number(this.currentUser.IP), newMessage.ReceiverID, this.accessToken).subscribe( data=>{
      console.log(data);
      debugger;
      var resp = JSON.parse(data);
      if(resp != null && resp.status != null){
        console.log(resp);
        if(resp.status == "200"){
          this.selectedChat.Messages.push(newMessage);
          this.messageToSend = "";
        }
        else{
          alert("Could not send message, please try again!");
        }
      }
    })
  }

  createNewChat(){
    this.chats.push(new Chat(this.newChatChordID, this.newChatChordID, new Array<Message>()));
    this.swapChat(this.newChatChordID);
    this.newChatChordID = "";
  }

}

export class Message{
  ChordID!: string;
  Timestamp!: string;
  Content!: string;
  SenderID!: string;
  ReceiverID!: string;

  constructor( ChordID: string, Timestamp: string, Content: string, SenderID: string, ReceiverID: string) {
    this.ChordID = ChordID;
    this.Timestamp = Timestamp;
    this.Content = Content;
    this.SenderID = SenderID;
    this.ReceiverID = ReceiverID;
  }
}

export class User{
  ChordID!: string;
  IP!: string;
  Name!: string;
  accessToken!: string;

  constructor(ChordID: string, IP: string, Name: string){
    this.ChordID = ChordID,
    this.IP = IP,
    this.Name = Name
  }
}

export class Chat{
  ChatID!: string;
  Name!: string;
  TimestampLastMessage!: string;
  Users!: Array<User>;
  Messages!: Array<Message>;
  
  constructor(ChatID: string, Name: string, Messages: Array<Message>){
    this.ChatID = ChatID,
    this.Name = Name,
    this.Messages = Messages
  }

  // addMessage(Message: Message){
  //   this.Messages.push(Message);
  // }

  // addUser(User: User){
  //   this.Users.push(User);
  // }
}
