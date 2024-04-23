import asyncio
import websockets
import pygame
from pygame.locals import *
import json

server_ip = '192.168.1.179'
server_port = 9009

# Initialize pygame
pygame.init()

# Screen configuration
screen = pygame.display.set_mode((850, 530))
pygame.display.set_caption("Ball Game")
clock = pygame.time.Clock()

# Load pixel font
font = pygame.font.Font("fonts/slkscrb.ttf", 25)

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Global variables for game state
global_state = {}
balls = []
game_over = False

# Function to update game state received from the server
async def update_state(websocket):
    global global_state, balls, game_over

    data = await websocket.recv()
    if data:
        state = json.loads(data)
        global_state = state['global_state']
        balls = state.get('balls', [])
        game_over = state.get('game_over', False)

# Function to send player movement to the server
async def send_movement(websocket, player_state):
    await websocket.send(json.dumps(player_state))
    await update_state(websocket)

# Main game function
async def main():
    async with websockets.connect(f"ws://{server_ip}:{server_port}") as websocket:
        player_id = await websocket.recv()
        running = True
        while running:
            if game_over:
                if global_state[player_id]['winner']:
                    message = font.render("You Won", True, WHITE)
                else:
                    message = font.render("You Lost", True, WHITE)
                screen.blit(message, ((screen.get_width() - message.get_width()) // 2, 90))
                pygame.display.update()
                pygame.time.wait(2000)
                running = False
                break

            # Event handling
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == KEYDOWN and event.key == K_SPACE:
                    global_state[player_id] = {
                        'x': global_state.get(player_id, {}).get('x', 100),
                        'y': global_state.get(player_id, {}).get('y', 300),
                        'ready': not global_state.get(player_id, {}).get('ready', False)
                    }
                    await send_movement(websocket, global_state[player_id])

            # Get pressed keys
            keys = pygame.key.get_pressed()

            if keys[K_UP] and global_state.get(player_id, {}).get('y', 300) > 0:
                global_state[player_id]['y'] -= 20
            if keys[K_DOWN] and global_state.get(player_id, {}).get('y', 300) < 410:
                global_state[player_id]['y'] += 20

            # Send movement to the server
            if player_id in global_state:
                await send_movement(websocket, global_state[player_id])
            else:
                global_state[player_id] = {'x': 100, 'y': 300, 'ready': False}
                await send_movement(websocket, global_state[player_id])

            # Draw black background
            screen.fill(BLACK)

            # Draw players and balls
            for _, pos in global_state.items():
                x = pos.get('x', 100)
                y = pos.get('y', 300)
                pygame.draw.rect(screen, WHITE, pygame.Rect(x, y, 20, 120))

            for ball_info in balls:
                ball_info['x'] -= 50
                pygame.draw.circle(screen, WHITE, (int(ball_info['x']), int(ball_info['y'])), 10)

            # Show start message
            message_text = font.render("Push SPACE to start", True, WHITE)
            screen.blit(message_text, ((screen.get_width() - message_text.get_width()) // 2, 10))

            # Update screen
            pygame.display.update()

            # Control frame rate
            clock.tick(60)

    pygame.quit()

# Run the main function
if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
