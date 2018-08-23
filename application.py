import os
import requests
import datetime

from flask import Flask, render_template, request, session
# from flask_session import Session
from flask_socketio import SocketIO, emit, send, join_room, leave_room

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)


class Room:
    def __init__(self, name):
        self.name = name
        self.messages = []

    def PostMessage(self, user, message):
        if len(self.messages) > 100:  # limit amount of message in the room
            self.messages.pop(0)
        timenow = datetime.datetime.now().strftime('%d %b %Y %H:%M')
        message = f"[{timenow}] {user}:> {message}"
        self.messages.append(message)


# setup initial set of chat rooms
rooms = []
Home = Room(name="Home")
Home.PostMessage(user="Masterbot", message="Hello my dears!")
Home.PostMessage(user="Masterbot", message="How are you all doing today?")
Help = Room(name="Help")
CS50WebDev = Room(name="CS50 Web dev")
rooms.append(Home)
rooms.append(Help)
rooms.append(CS50WebDev)


def getRoomByName(roomname):
    for room in rooms:
        if room.name == roomname:
            return room


@app.route("/")
def index():
    return render_template("index.html", rooms=rooms)


@app.route("/main", methods=["POST"])
def main():
    if request.method == "GET":
        render_template("index.html", rooms=rooms)
    username = request.form.get("username")
    roomname = request.form.get("room")
    room = getRoomByName(roomname=roomname)
    return render_template("chat.html", username=username, room=room)


@socketio.on('message')
def handle_message(message):
    msg = message["message"]
    username = message["username"]
    room = message["room"]
    r = getRoomByName(roomname=room)
    r.PostMessage(user=username, message=msg)
    timenow = datetime.datetime.now().strftime('%d %b %Y %H:%M')
    m = f"[{timenow}] {username}:> {msg}"
    emit('message', {"message": m}, room=room)


@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    m = f"{username} has entered the room"
    r = getRoomByName(roomname=room)
    r.PostMessage(user="Masterbot", message=m)
    timenow = datetime.datetime.now().strftime('%d %b %Y %H:%M')
    m = f"[{timenow}] Masterbot:> {m}"
    emit('join', {"message": m}, room=room)


@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    m = f"{username} has left the room"
    r = getRoomByName(roomname=room)
    r.PostMessage(user="Masterbot", message=m)
    timenow = datetime.datetime.now().strftime('%d %b %Y %H:%M')
    m = f"[{timenow}] Masterbot:> {m}"
    emit('leave', {"message": m}, room=room)


@socketio.on('getrooms')
def on_getrooms(data):
    roomslist = []
    for r in rooms:
        roomslist.append(r.name)
    emit('list of rooms', {"rooms": roomslist}, room=request.sid)


@socketio.on('getmessages')
def on_getmessages(data):
    room = getRoomByName(roomname=data['room'])
    messages = []
    emit('messages', {'messages': room.messages}, room=request.sid)


@socketio.on('addroom')
def on_addroom(data):
    room = Room(name=data['room'])
    roomslist = []
    rooms.append(room)
    for r in rooms:
        roomslist.append(r.name)
    emit('list of rooms', {"rooms": roomslist}, broadcast=True)
