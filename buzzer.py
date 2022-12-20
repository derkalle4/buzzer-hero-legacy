#!/usr/bin/python
from buzz import BuzzController
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO
from threading import Thread
from time import sleep
import hid
import os

# create buzzer list
buzzers = []
for interface in hid.enumerate(0x54c, 0x1000):
    device = hid.device()
    print('open controller #{}'.format(interface['path']))
    device.open_path(interface['path'])
    buzzers.append(BuzzController(device, ))

# variables
game_state = {
    'status': 0,
    'buzzer_pressed': {},
    'buzzer_ids': [],
    'controller_count': len(buzzers),
    'player_names': {},
    'quit': False,
}

def game_worker(key, buzzer):
    print('start worker for {}'.format(key))
    # unlimited loop
    while game_state['quit'] is not True:
        try:
            # get pressed button
            ControllerPressed = buzzer.controller_get_first_pressed('red')
            print('{} pressed {}'.format(key, ControllerPressed))
            if ControllerPressed != None:
                ControllerIndex = '{}_{}'.format(key,ControllerPressed)
                if game_state['status'] is 0: # pregame
                    # check if someone has pressed the big red button to join the game
                        if ControllerIndex not in game_state['buzzer_ids']:
                            game_state['buzzer_ids'].append(ControllerIndex)
                            buzzer.light_set(ControllerPressed, True)
                            print('added controller {} to the game'.format(ControllerIndex))
                            # send to clients
                            socketio.emit('game.status', game_state)
                            socketio.sleep(.3)
                            buzzer.light_set(ControllerPressed, False)
                elif game_state['status'] is 1:
                    # only proceed when nobody has pressed a button
                    if len(game_state['buzzer_pressed']) == 0:
                        # check who has pressed the button and highlight this
                        if ControllerIndex in game_state['buzzer_ids'] and ControllerIndex not in game_state['buzzer_pressed']:
                            buzzer.light_set(ControllerPressed, True)
                            game_state['buzzer_pressed'][ControllerIndex] = 'red'
                            print('controller {} pressed the button {}'.format(ControllerIndex, 'red'))
                            socketio.emit('game.status', game_state)
        except:
            print('Unknown error. Lets go on regardless of everything!')
    print('stopped worker for {}'.format(key))

##################
##################
##################

app = Flask(__name__)
app.websocket_enabled=True
app.config['SECRET_KEY'] = 'psstDoNotUse'
socketio = SocketIO(app, debug=True)

def thread_socketio():
    print('started socketIO thread')
    socketio.run(app, host="0.0.0.0", port=int("8000"))
    while game_state['quit'] is not True:
        socketio.sleep(1)
    print('stopped socketIO thread')

def main():
    print('started main thread')
    tmp_socketio = Thread(target=thread_socketio, args=())
    tmp_socketio.start()
    while game_state['quit'] is not True:
        sleep(1)
    print('stopped main thread')

def set_lights(buzzer, status):
    for i in range(-2,6):
        buzzer.light_set(i, status)

## app routings

@app.route('/assets/<path:path>')
def send_js(path):
    return send_from_directory('assets', path)
@app.route('/')
def index():
    return render_template('index.html')
# send status to clients
@socketio.on('get.status')
def get_status():
    count = 0
    for buzzer in buzzers:
        count+=1
        socketio.start_background_task(target=game_worker, key=count, buzzer=buzzer)
        # we only need to start one worker because unfortunately all workers will get all information
    socketio.emit('game.status', game_state)

# change gamestate depending on current gamestate
@socketio.on('set.gamestate')
def set_gamestate():
    for buzzer in buzzers:
        set_lights(buzzer, False)
    if game_state['status'] == 0 and len(game_state['buzzer_ids']) >= 2:
        game_state['status'] = 1
    else:
        game_state['status'] = 0
        game_state['buzzer_ids'] = []
        game_state['buzzer_pressed'] = {}
        
    socketio.emit('game.status', game_state)

# reset pressed buttons
@socketio.on('set.reset')
def set_reset():
    for buzzer in buzzers:
        set_lights(buzzer, False)
    game_state['buzzer_pressed'] = {}
    socketio.emit('game.status', game_state)

# set player name
@socketio.on('set.playername')
def set_playername(data):
    if len(data[1]) > 0:
        game_state['player_names'][data[0]] = data[1]
    else:
        if data[0] in game_state['player_names']:
            del game_state['player_names'][data[0]]
    socketio.emit('game.status', game_state)

# quit software
@socketio.on('do_quit')
def do_quit():
    print('end program')
    game_state['quit'] = True
    for i in range(10):
        os.kill(os.getpid(), 9)

if __name__ == '__main__':
    main()
