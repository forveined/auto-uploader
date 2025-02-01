import aiohttp
import json
import asyncio
from typing import Optional, Dict, Tuple

class Roblox:
    def __init__(self):
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        self.studio_useragent = "RobloxStudio/WinInet RobloxApp/0.651.0.6510833 (GlobalDist; RobloxDirectDownload)"
    async def get_csrf_token(self, cookie: str) -> Optional[str]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://auth.roblox.com/v2/logout",
                    headers={
                        "Cookie": f".ROBLOSECURITY={cookie}",
                        "User-Agent": self.user_agent
                    }
                ) as response:
                    return response.headers.get('x-csrf-token')
        except Exception as e:
            print(f"Error getting CSRF token: {e}")
            return None

    async def create_universe(self, cookie: str, csrf_token: str) -> Optional[Dict[str, str]]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://apis.roblox.com/universes/v1/universes/create",
                    headers={
                        "Content-Type": "application/json",
                        "Cookie": f".ROBLOSECURITY={cookie}",
                        "User-Agent": self.studio_useragent,
                        "x-csrf-token": csrf_token
                    },
                    json={"templatePlaceId": 95206881}
                ) as response:
                    data = await response.json()
                    
                    if "universeId" in data and "rootPlaceId" in data:
                        return {
                            "universeId": str(data["universeId"]),
                            "rootPlaceId": str(data["rootPlaceId"])
                        }
                    print(f"Failed to create universe: {data}")
                    return None
        except Exception as e:
            print(f"Error creating universe: {e}")
            return None

    async def activate_universe(self, universe_id: str, csrf_token: str, cookie: str) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"https://develop.roblox.com/v1/universes/{universe_id}/activate",
                    headers={
                        "accept": "*/*",
                        "Cookie": f".ROBLOSECURITY={cookie}",
                        "User-Agent": self.studio_useragent,
                        "x-csrf-token": csrf_token
                    }
                ) as response:
                    return response.status == 200
        except Exception as e:
            print(f"Error activating universe: {e}")
            return False

    async def upload_game(self, universe_id: str, place_id: str, file_data: bytes, csrf_token: str, cookie: str) -> Optional[dict]:
        try:
            form = aiohttp.FormData()
            request_json = {
                "assetType": "Place",
                "assetId": int(place_id),
                "published": True,
                "creationContext": {}
            }
            
            # Convert request_json to string before adding to form
            form.add_field('request', json.dumps(request_json), content_type='application/json')
            form.add_field('fileContent', file_data, filename='contentToUpload')

            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"https://apis.roblox.com/assets/user-auth/v1/assets/{place_id}",
                    headers={
                        'Accept': '*/*',
                        'Cookie': f".ROBLOSECURITY={cookie}",
                        'Accept-Encoding': 'gzip, deflate',
                        'Cache-Control': 'no-cache',
                        'Connection': 'keep-alive',
                        'User-Agent': self.studio_useragent,
                        'Roblox-Place-Id': place_id,
                        'Roblox-Universe-Id': universe_id,
                        'Requester': 'Client',
                        'PlayerCount': '0',
                        'X-CSRF-TOKEN': csrf_token
                    },
                    data=form
                ) as response:
                    if not response.ok:
                        error_text = await response.text()
                        raise Exception(f"Upload failed with status {response.status}: {error_text}")
                    
                    result = await response.text()
                    try:
                        return json.loads(result) if result else {"status": "success"}
                    except json.JSONDecodeError as e:
                        return {"message": result, "error": str(e)}
        except Exception as e:
            print(f"Error uploading game: {e}")
            return None

    async def configure_universe(self, name: str, universe_id: str, csrf_token: str, cookie: str) -> Optional[dict]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"https://develop.roblox.com/v2/universes/{universe_id}/configuration",
                    headers={
                        "Content-Type": "application/json",
                        "Cookie": f".ROBLOSECURITY={cookie}",
                        "User-Agent": self.studio_useragent,
                        "x-csrf-token": csrf_token
                    },
                    json={
                        "name": name,
                        "description": "Testing",
                        "universeAvatarType": "MorphToR6",
                        "allowPrivateServers": True,
                        "privateServerPrice": 0
                    }
                ) as response:
                    if response.ok:
                        return await response.json()
                    print(f"Failed to configure universe: {response.status}")
                    return None
        except Exception as e:
            print(f"Error configuring universe: {e}")
            return None

    async def get_playability_status(self, universe_id: str, cookie: str) -> Optional[str]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://games.roblox.com/v1/games/multiget-playability-status?universeIds={universe_id}",
                    headers={
                        "cookie": f".ROBLOSECURITY={cookie}",
                        "User-Agent": self.user_agent
                    }
                ) as response:
                    if not response.ok:
                        return None
                    
                    data = await response.json()
                    
                    if isinstance(data, list) and len(data) > 0:
                        status = data[0].get('playabilityStatus')
                        
                        if status == "UnderReview":
                            return "UnderReview"
                        elif status == "GameUnapproved":
                            return "GameUnapproved" 
                        elif status == "Playable" or "PlaceHasNoPublishedVersion":
                            return "Playable"
                        else:
                            return status
                    else:
                        print("Unexpected response structure:", data)
                        return None
                        
        except Exception as e:
            print(f"Error fetching playability status: {e}")
            return None