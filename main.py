#!/usr/bin/env python3

import event_schedule
import sys
import argparse

notification = {
    "game-start": [
        (-10, "countdown_10")
    ],
    "game-end": [
        (-5, "countdown_5")
    ]
}

parser = argparse.ArgumentParser(description='Announce things')
parser.add_argument('url', help='URL to connect to')

args = parser.parse_args()

for name, event in event_schedule.go(args.url, notification, "A"):
    print(name)
    print(event)
