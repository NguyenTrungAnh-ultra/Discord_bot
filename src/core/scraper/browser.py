# Browser profiles and user agent utilities
import random

# === Browser Profiles ===

# Note: User agent strings are constantly evolving. These are set based on the latest available
# information as of early May 2025. They may need periodic updates to remain current.

DESKTOP_BROWSERS = {
    "chrome": {
        "windows": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        ),
        "macos": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) " # Using a common recent macOS version
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        ),
    },
    "firefox": {
        "windows": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) "
            "Gecko/20100101 Firefox/137.0"
        ),
        "macos": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:138.0) " # Using a common recent macOS version and latest Firefox
            "Gecko/20100101 Firefox/138.0"
        ),
    },
    "edge": {
        "windows": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.3240.50"
        ),
    },
    "opera": {
        "windows": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 OPR/117.0.0.0" # Based on Chromium 132 and Opera 117
        ),
        "macos": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) " # Using a common recent macOS version
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 OPR/118.0.0.0" # Based on Chromium 136 and Opera 118
        ),
    },
    "brave": {
        "windows": (
             "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Brave/1.77.101" # Using Chromium 136 and Brave 1.77
        ),
        "macos": (
             "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) " # Using a common recent macOS version
             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Brave/1.77.101" # Using Chromium 136 and Brave 1.77
        ),
    },
    "vivaldi": {
        "windows": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Vivaldi/7.2" # Using Chromium 136 and Vivaldi 7.2
        ),
    },
    "coccoc": {
        "windows": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 CocCoc/136.0.0.0" # Assuming Chromium 136 base for latest Coc Coc Windows
        ),
    },
    "safari": {
        "macos": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) " # Using a common recent macOS version
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15" # Using Safari 17.6
        ),
    },
}

MOBILE_BROWSERS = {
    "chrome": {
        "android": (
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) " # Keeping a common recent Android device
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.7103.60 Mobile Safari/537.36" # Using Chrome 136.0.7103.60
        ),
    },
    "safari": {
        "ios": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) " # Using a recent iOS version
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1" # Assuming Safari version aligns with iOS or latest found
        ),
    },
    "samsung": {
        "android": (
            "Mozilla/5.0 (Linux; Android 13; SAMSUNG SM-G991B) " # Keeping a common recent Samsung device
            "AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/21.0 Chrome/110.0.5481.154 Mobile Safari/537.36" # Using Samsung Browser 21 and Chrome 110 (based on search result)
        ),
    },
    "opera": {
        "android": (
            "Mozilla/5.0 (Linux; Android 13; M2102J20SG) " # Keeping a common recent Android device
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36 OPR/76.2.4027.73374" # Using Chromium 136 and Opera 76
        ),
    },
    "coccoc": {
        "android": (
            "Mozilla/5.0 (Linux; Android 13; Redmi Note 12) " # Keeping a common recent Android device
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36 CocCocBrowser/137.0.258" # Using Chrome 137 and CocCocBrowser 137.0.258
        ),
    },
    "firefox": {
        "android": "Mozilla/5.0 (Android 13; Mobile; rv:137.0) Gecko/137.0 Firefox/137.0", # Using Firefox 137
    },
}

# Combine all browser profiles
USER_AGENTS = {}

for browser_dict in [DESKTOP_BROWSERS, MOBILE_BROWSERS]:
    for browser, platforms in browser_dict.items():
        if browser not in USER_AGENTS:
            USER_AGENTS[browser] = {}
        USER_AGENTS[browser].update(platforms)


# === User Agent Functions ===

DEFAULT_HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9,vi-VN;q=0.8,vi;q=0.7',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'DNT': '1',
    'Pragma': 'no-cache',
    'sec-ch-ua-platform': '"Windows"',
    'sec-ch-ua-mobile': '?0',
}


HEADERS_MAPPING_SOURCE = {
    'SSI': {'Referer': 'https://iboard.ssi.com.vn', 'Origin': 'https://iboard.ssi.com.vn'},
    'VND': {'Referer': 'https://dchart.vndirect.com.vn', 'Origin': 'https://dchart.vndirect.com.vn'},
    'TCBS': {'Referer': 'https://tcinvest.tcbs.com.vn/', 'Origin': 'https://tcinvest.tcbs.com.vn/'},
    'VCI': {'Referer': 'https://trading.vietcap.com.vn/', 'Origin': 'https://trading.vietcap.com.vn/'},
    'MSN': {'Referer': 'https://www.msn.com/', 'Origin': 'https://www.msn.com/'},
    'FMARKET': {'Referer': 'https://fmarket.vn/', 'Origin': 'https://fmarket.vn/'},
    'SJC': {'Referer': 'https://sjc.com.vn/bieu-do-gia-vang', 'Origin': 'https://sjc.com.vn'},
}

def get_random_desktop_user_agent():
    """
    Trích xuất và trả về ngẫu nhiên một chuỗi User Agent từ DESKTOP_BROWSERS.
    """
    all_user_agents = []
    
    # Duyệt qua các trình duyệt (ví dụ: 'chrome', 'firefox')
    for browser in DESKTOP_BROWSERS.values():
        # Duyệt qua các hệ điều hành (ví dụ: 'windows', 'macos')
        for user_agent in browser.values():
            all_user_agents.append(user_agent)

    if not all_user_agents:
        # Trường hợp không tìm thấy User Agent nào, trả về mặc định
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    # Chọn ngẫu nhiên 1 User Agent
    return random.choice(all_user_agents)

def get_headers(
    data_source: str = 'SSI',
    random_agent: bool = True,
    browser: str = 'chrome',
    platform: str = 'windows'
) -> dict:
    """
    Generate browser-like headers with optional referer/origin and realistic User-Agent.

    Args:
        data_source (str): Predefined data source (e.g., 'SSI', 'VND').
        random_agent (bool): Whether to use a random browser/platform User-Agent.
        browser (str): Browser name to simulate if not random.
        platform (str): Platform name to simulate if not random.

    Returns:
        dict: HTTP headers with realistic settings.
    """
    ref_origin = HEADERS_MAPPING_SOURCE.get(data_source.upper(), {})
    referer = ref_origin.get("Referer", "")
    origin = ref_origin.get("Origin", "")

    # Determine browser/platform
    if random_agent:
        browser = random.choice(list(USER_AGENTS.keys()))
        platform = random.choice(list(USER_AGENTS[browser].keys()))

    ua = USER_AGENTS.get(browser.lower(), {}).get(platform.lower())

    if not ua:
        # Fallback to first available platform under chrome or first browser available
        ua = USER_AGENTS.get("chrome", {}).get("windows")
        if not ua:
            # As a last resort, pick any user agent
            for b in USER_AGENTS.values():
                if isinstance(b, dict):
                    ua = next(iter(b.values()))
                    break

    headers = DEFAULT_HEADERS.copy()
    headers["User-Agent"] = ua
    if referer:
        headers["Referer"] = referer
    if origin:
        headers["Origin"] = origin
    return headers


