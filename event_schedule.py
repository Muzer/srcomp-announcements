#!/usr/bin/python3

import sseclient
import threading
import json
import queue
import datetime
import dateutil.parser
import pytz
import traceback

def go(url, notification_requests, arena):
    events = queue.Queue()
    timers = []
    serverthread = threading.Thread(target=get_events, args=(url, notification_requests, arena, timers, events))
    serverthread.start()
    while True:
        yield events.get()


def wait_for_event(name, match_data, timers, events):
    timers.remove(threading.current_thread())
    events.put((name, match_data))
    

def get_events(url, notification_requests, arena, timers, events):
    messages = sseclient.SSEClient(url)
    for msg in messages:
        if msg.event == "match":
            for t in timers:
                t.cancel()
                timers.remove(t)
            match_data = json.loads(msg.data)
            try:
                arena_data, = filter(lambda x : x["arena"] == arena, match_data)
            except ValueError as steve:
                continue
            for time, key in [
                    (arena_data["times"]["game"]["start"], "game-start"),
                    (arena_data["times"]["game"]["end"], "game-end"),
                    (arena_data["times"]["period"]["start"], "period-start"),
                    (arena_data["times"]["period"]["end"], "period-end")]:
                for delta, name in notification_requests.get(key, []):
                    notification_delta = (dateutil.parser.parse(time)+datetime.timedelta(seconds=delta)) - datetime.datetime.now(pytz.utc)
                    if notification_delta < datetime.timedelta():
                        continue
                    t = threading.Timer(notification_delta.total_seconds(), wait_for_event, args=(name, match_data, timers, events))
                    timers.append(t)
                    t.start()
