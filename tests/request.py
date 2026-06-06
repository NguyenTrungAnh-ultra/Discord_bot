import requests

url = "https://www.vietcap.com.vn/api/cms-service/v2/page/analysis"


querystring = {"is-all":"false","page":"0","size":"100","direction":"DESC","sortBy":"date","page-ids":"144","language":"1"}

payload = ""
headers = {
    "cookie": "FECW=94818fa9b3004f16b7d0aeb545e4a4c7961e5f4190a6c062fa241f7e8a539697df1447bb97d175381fdb3b6a73c152d76750845c5f0c4b6386583127db1c0b1b1db65333a4242ef26428358e8c6fc0208e; FECWS=94818fa9b3004f16b7d0aeb545e4a4c7961e5f4190a6c062fa241f7e8a539697df1447bb97d175381fdb3b6a73c152d76750845c5f0c4b6386583127db1c0b1b1db65333a4242ef26428358e8c6fc0208e",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.8",
    "Connection": "keep-alive",
    "Origin": "https://trading.vietcap.com.vn",
    "Referer": "https://trading.vietcap.com.vn/",
    "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Brave";v="144"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Sec-GPC": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
}

response = requests.request("GET", url, data=payload, headers=headers, params=querystring)

print(response.text)