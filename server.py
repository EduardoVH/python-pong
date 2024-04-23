import asyncio
import websockets
import json
import random

server_ip = '192.168.1.179'
server_port = 9009
balls = []
global_state = {}
clients = set()
player_counter = 0
players_ready = 0
left_player_score = 0
right_player_score = 0
left_players = 0
right_players = 0
game_over = False

def check_all_ready():
    global all_ready
    all_ready = all(player['ready'] for player in global_state.values())

async def generate_balls():
    interval = 1

    while True:
        if clients and all_ready:
            if not balls:
                ball = {
                    'x': 425,
                    'y': 265,
                    'velocity_x': random.uniform(-6, -15),
                    'velocity_y': random.choice([-1, 1])
                }
                balls.append(ball)

        await asyncio.sleep(interval)

async def handle_client(websocket, path):
    global player_counter, left_players, right_players, game_over
    player_id = player_counter
    player_counter += 1

    if left_players <= right_players:
        global_state[player_id] = {'x': 100, 'y': 300, 'ready': False}
        left_players += 1
    else:
        global_state[player_id] = {'x': 700, 'y': 300, 'ready': False}
        right_players += 1

    await websocket.send(str(player_id))

    clients.add(websocket)
    print(f"Player {player_id} has joined the server.")

    try:
        while True:
            data = await websocket.recv()
            movement = json.loads(data)
            global_state[player_id] = movement

            if not movement['ready']:
                balls.clear()

    except websockets.ConnectionClosed:
        print(f"Connection with player {player_id} unexpectedly closed.")
    finally:
        clients.remove(websocket)
        if player_id in global_state:
            del global_state[player_id]
            print(f"Player {player_id} has been removed.")
            if player_id in global_state:
                if global_state[player_id]['x'] == 100:
                    left_players -= 1
                else:
                    right_players -= 1
        game_over = False

def check_collisions():
    global left_player_score, right_player_score, game_over
    for player_id, player in list(global_state.items()):
        if 'x' in player and 'y' in player:
            player_x = player['x']
            player_y = player['y']

            for ball in balls:
                ball_x = ball['x']
                ball_y = ball['y']

                if (player_x < ball_x + 20 and player_x + 87 > ball_x and
                        player_y < ball_y + 20 and player_y + 120 > ball_y):
                    ball['velocity_x'] *= -1
                    ball['velocity_y'] *= random.choice([-1, 1])

                if ball_x < 0:
                    game_over = True
                    global_state[player_id]['winner'] = False if player['x'] == 100 else True
                elif ball_x > 850:
                    game_over = True
                    global_state[player_id]['winner'] = True if player['x'] == 100 else False

                if ball_y < 10 or ball_y > 520:
                    ball['velocity_y'] *= -1

async def update_state():
    while True:
        check_all_ready()

        if all_ready:
            asyncio.create_task(generate_balls())

        if all_ready:
            check_collisions()

        for ball in balls:
            ball['x'] += ball['velocity_x']
            ball['y'] += ball['velocity_y']

        state = {
            'global_state': global_state,
            'balls': balls,
            'left_player_score': left_player_score,
            'right_player_score': right_player_score,
            'game_over': game_over
        }

        state_json = json.dumps(state)

        if clients:
            tasks = [asyncio.create_task(client.send(state_json)) for client in clients if client.open]
            if tasks:
                await asyncio.wait(tasks)

        await asyncio.sleep(0.1)

start_server = websockets.serve(handle_client, server_ip, server_port)

loop = asyncio.get_event_loop()
loop.run_until_complete(start_server)
loop.create_task(update_state())
loop.run_forever()
