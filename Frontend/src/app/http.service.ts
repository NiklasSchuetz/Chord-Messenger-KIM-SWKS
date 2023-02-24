import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Chat, Message, User } from './app.component';
import { EmptyError, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class HttpService {

  constructor(private http:HttpClient) { }
  ip = "http://127.0.0.1:"

  //#region GET
  getStuff(){
    return "stuff";
  }

  getUsers(_port:string, _currentUserID:string, _accessToken:string){
    console.log("getUsers");
    const headers = { 'content-type': 'application/json'};
    return this.http.post<string>(this.ip + _port + "/api/get/users", { userID: _currentUserID, accessToken: _accessToken},{'headers':headers});
  }

  getChats(_port:string, _currentUserID:string, _accessToken:string){
    console.log("getChats");
    const headers = { 'content-type': 'application/json'};
    var backupNumber: number = +_port - 200;
    return this.http.post<string>(this.ip + _port + "/api/get/chats", { userID: backupNumber.toString(), accessToken: _accessToken},{'headers':headers});
  }

  getMessages(_port:string, _chatID: string, _accessToken:string){
    console.log("getMessages " + _chatID);
    const headers = { 'content-type': 'application/json'};
    var backupNumber: number = +_port - 200;
    return this.http.post<string>(this.ip + _port + "/api/get/messages", { chatID: _chatID, port: backupNumber.toString(), accessToken: _accessToken},{'headers':headers});
  }
  //#endregion

  //#region POST
  postLogin(_port:string, _userName: string, _password: string, _n: number, _e: number, _d: number){
    try{
      console.log("Login");
      const headers = { 'content-type': 'application/json'};
      return this.http.post<string>(this.ip + _port + "/api/post/login3", { userName: _userName, password: _password, n: _n, e: _e, d: _d },{'headers':headers});
    }
    catch(e){
      alert("No free Nodes");
      return this.http.get<string>(this.ip + _port + "/api");
    }
  }

  // getLogin(_userName: string, _password: string, _n: number, _e: number, _d: number){
  //   console.log("Login");
  //   // const headers = { 'content-type': 'application/json'};

  //   let headers = new Headers();
  //   headers.append('Content-Type', 'application/json');
  //   // headers.append('projectid', this.id);

  //   return this.http.get<string>(this.ip + "/api/post/login2", {headers: headers});
  // }

  postMessage(_port:string, _message: string, _senderID: number, _receiverID: string, _accessToken: string){
    console.log("SendMessage");
    const headers = { 'content-type': 'application/json'};
    return this.http.post<string>(this.ip + _port + "/api/post/message", { messageContent: _message, senderID: _senderID-200, receiverID: _receiverID, accessToken: _accessToken},{'headers':headers});
  }
  //#endregion
}
