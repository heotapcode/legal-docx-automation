import httpx

async def lookup_mst(mst: str) -> dict:
    url = f"https://api.vietqr.io/v2/business/{mst.strip().replace(' ', '')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, headers=headers)
                data = resp.json()
                if data.get("code") == "00":
                    return data.get("data", {})
        except Exception as e:
            if attempt == 2:
                raise e
    return {}
