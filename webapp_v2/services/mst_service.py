import httpx

async def lookup_mst(mst: str) -> dict:
    clean_mst = mst.strip().replace(' ', '')
    url = f"https://api.vietqr.io/v2/business/{clean_mst}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, headers=headers)
                data = resp.json()
                if data.get("code") == "00":
                    res = data.get("data", {})
                    # Normalize both Vietnamese and English keys for full compatibility
                    ten = res.get("name", "")
                    addr = res.get("address", "")
                    res["ten_cong_ty"] = ten
                    res["dia_chi"] = addr
                    res["ten_quoc_te"] = res.get("internationalName", "")
                    res["ten_viet_tat"] = res.get("shortName", "")
                    res["ma_so_thue"] = res.get("id", clean_mst)
                    return res
        except Exception as e:
            if attempt == 2:
                raise e
    return {}
