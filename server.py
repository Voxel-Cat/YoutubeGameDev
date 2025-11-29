import asyncio
import json
import websockets
import uuid
import traceback

HOST = "localhost"
PORT = 8765

connected_players = {}
player_names = {}
player_order = []
turn_index = 0


def make_player_info(pid):
    return {"id": pid, "name": player_names.get(pid, "Player")}


async def broadcast(packet, except_ws=None):
    """Send packet to all players except optional one."""
    message = json.dumps(packet)
    for pid, ws in list(connected_players.items()):
        if ws is not except_ws:
            try:
                await ws.send(message)
            except:
                pass


async def send_player_list():
    """Sync full player list + turn."""
    players = [make_player_info(pid) for pid in player_order]
    await broadcast({
        "type": "player_list",
        "players": players,
        "turn_index": turn_index
    })


async def handle_client(ws):
    global turn_index

    player_id = str(uuid.uuid4())
    connected_players[player_id] = ws
    player_names[player_id] = "Player"
    player_order.append(player_id)

    print(f"[JOIN] {player_id} connected")

    try:
        await ws.send(json.dumps({"type": "init", "id": player_id}))
    except:
        pass

    await broadcast({
        "type": "player_joined",
        "id": player_id,
        "name": player_names[player_id]
    }, except_ws=ws)

    await send_player_list()

    try:
        async for raw in ws:
            try:
                data = json.loads(raw)
            except:
                print("[ERROR] Invalid JSON:", raw)
                continue

            typ = data.get("type")

            if typ == "join":
                name = data.get("name", "Player")
                player_names[player_id] = name
                print(f"[NAME] {player_id} -> {name}")

                await broadcast({
                    "type": "player_joined",
                    "id": player_id,
                    "name": name
                })

                await send_player_list()

            elif typ == "action":
                action = data.get("action")

                if len(player_order) == 0:
                    continue

                current_pid = player_order[turn_index]

                if current_pid != player_id:
                    await ws.send(json.dumps({
                        "type": "action_rejected",
                        "reason": "not_your_turn",
                        "current_player": current_pid
                    }))
                    continue

                if action not in ("roll", "pass"):
                    await ws.send(json.dumps({
                        "type": "action_rejected",
                        "reason": "invalid_action"
                    }))
                    continue

                import random
                val = random.randint(0, 99)

                await broadcast({
                    "type": "action",
                    "player_id": player_id,
                    "action": action,
                    "value": val,
                    "player_name": player_names[player_id]
                })

                turn_index = (turn_index + 1) % len(player_order)
                await broadcast({
                    "type": "turn_update",
                    "turn_index": turn_index
                })

            elif typ == "move":
                x = data.get("x", 0)
                y = data.get("y", 0)
                await broadcast({
                    "type": "move",
                    "id": player_id,
                    "x": x,
                    "y": y
                }, except_ws=ws)

            else:
                print("[WARN] Unknown type:", typ)

    except websockets.ConnectionClosed:
        pass
    except Exception:
        traceback.print_exc()
    finally:
        print(f"[QUIT] {player_id} disconnected")

        if player_id in connected_players:
            del connected_players[player_id]
        name = player_names.pop(player_id, "Player")

        if player_id in player_order:
            idx = player_order.index(player_id)
            player_order.remove(player_id)

            if len(player_order) == 0:
                turn_index = 0
            else:
                if idx < turn_index:
                    turn_index -= 1
                elif idx == turn_index:
                    turn_index %= len(player_order)

        await broadcast({
            "type": "player_left",
            "id": player_id,
            "name": name
        })

        await send_player_list()


async def main():
    print(f"Starting server on ws://{HOST}:{PORT}")

    async with websockets.serve(handle_client, HOST, PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
