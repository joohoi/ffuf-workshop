#!/usr/bin/env python3
import sys

import requests

WEBHOOK_URL = "https://ffuf-workshop.cloud.mattermost.com/hooks/t66crf68sff7md5agconww1cah"
CHANNEL = "town-square"

data = []
for line in sys.stdin:
    data.append(line.strip())
requests.post(WEBHOOK_URL, json={"channel": CHANNEL, "text": "\n".join(data)})
