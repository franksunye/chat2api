import base64
import hashlib
import json
import random
import time
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser

answers = {}
cores = [8, 12, 16, 24, 32]
screens = [3000, 4000, 6000]
timeLayout = "%a %b %d %Y %H:%M:%S"

cached_scripts = []
cached_dpl = ""
cached_time = 0


class ScriptSrcParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        global cached_scripts, cached_dpl, cached_time
        if tag == "script":
            attrs_dict = dict(attrs)
            if "src" in attrs_dict:
                src = attrs_dict["src"]
                cached_scripts.append(src)
                if not cached_dpl and "dpl" in src:
                    cached_dpl = src[src.index("dpl"):]
                    cached_time = int(time.time())


async def get_dpl(service):
    if int(time.time()) - cached_time < 60 * 60:
        return True

    headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/json',
        'Oai-Device-Id': service.oai_device_id,
        'Oai-Language': 'en-US',
        'Origin': 'https://chatgpt.com',
        'Referer': 'https://chatgpt.com/',
        'User-Agent': service.user_agent
    }
    try:
        r = await service.s.get(service.host_url, headers=headers)
        r.raise_for_status()
        parser = ScriptSrcParser()
        parser.feed(r.text)
        return len(cached_scripts) != 0
    except Exception:
        return False


def get_parse_time():
    now = datetime.now(timezone(timedelta(hours=-8)))
    return now.strftime(timeLayout) + " GMT-0800 (Pacific Time)"


def get_config(user_agent):
    random.seed(int(time.time() * 1e9))
    core = random.choice(cores)
    screen = random.choice(screens)
    config = [
        core + screen,
        get_parse_time(),
        4294705152,
        0,
        user_agent,
        random.choice(cached_scripts) if cached_scripts else "",
        cached_dpl,
        "en-US",
        "en-US,en"
    ]
    return config


def calc_proof_token(seed, diff, config):
    diff_len = len(diff) // 2
    for i in range(50000):
        config[3] = i
        json_data = json.dumps(config, separators=(',', ':'), ensure_ascii=False)
        base = base64.b64encode(json_data.encode()).decode()
        hasher = hashlib.sha3_512()
        hasher.update((seed + base).encode())
        hash_value = hasher.digest()

        if hash_value[:diff_len].hex() <= diff:
            result = "gAAAAAB" + base
            return result

    return "gAAAAABwQ8Lk5FbGpA2NcR9dShT6gYjU7VxZ4D" + base64.b64encode(f'"{seed}"'.encode()).decode()


def calc_config_token(config):
    json_data = json.dumps(config).encode()
    base = base64.b64encode(json_data).decode()
    return 'gAAAAAC' + base
