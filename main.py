import roblox
from roblox import Roblox
import random
import asyncio

async def main():
    while True:
        try:
            with open('cookies.txt') as f:
                cookie = random.choice(f.read().splitlines())
            api = Roblox()
            csrf_token = await api.get_csrf_token(cookie)
            universe = await api.create_universe(cookie, csrf_token)
            universe_id, root_place_id = universe["universeId"], universe["rootPlaceId"]
            await api.activate_universe(universe_id, csrf_token, cookie)
            await api.configure_universe("Skibidi Tower Defense 🚽", universe_id, csrf_token, cookie)
            with open('game.rbxl', 'rb') as f:
                await api.upload_game(universe_id, root_place_id, f.read(), csrf_token, cookie)
            print(f"\nMonitoring condo: https://roblox.com/games/{root_place_id}...")
            while True:
                status = await api.get_playability_status(universe_id, cookie)
                print(f"Status: {status}", end='\r')
                if status == "GameUnapproved":
                    print(f"\nThe condo was deleted, reuploading...")
                    break
                await asyncio.sleep(0.5)
        except FileNotFoundError:
            break
        except Exception as e:
            await asyncio.sleep(5)
if __name__ == "__main__":
    asyncio.run(main())