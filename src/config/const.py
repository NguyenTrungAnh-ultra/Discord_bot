import pathlib
HOME_DIR = pathlib.Path.home()
PROJECT_DIR = HOME_DIR / ".vnstock"
ID_DIR = PROJECT_DIR / 'id'

TC_VAR = "ACCEPT_TC"
TC_VAL = "tôi đồng ý"

UA = {'Chrome' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
               'Opera' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0',
               'Edge' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0',
               'Firefox' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0'
               }

# Discord Embed Colors
HEX_COLOR_VANG = 0xFF9900
HEX_COLOR_DO = 0xEE0000
HEX_COLOR_XANH_LA = 0x00FF00

# Models
MODEL_MACRO = "gemma-4-26b-a4b-it"
MODEL_COMPANY = "gemma-4-31b-it"
MODEL_SUMMARY = "gemini-flash-latest"
MODEL_EMBEDDING = "gemini-embedding-2"