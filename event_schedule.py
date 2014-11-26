#!/usr/bin/python3

import sseclient
import threading
import json
import queue
import datetime
import dateutil.parser
import pytz

def go(url, notification_requests, arena):
    events = queue.Queue()
    timers = []
    serverthread = threading.Thread(target=get_events, args=(url, notification_requests, arena, timers, events))
    serverthread.start()
    while True:
        print("Blocking on getting")
        yield events.get()
        print("Finished getting")


def wait_for_event(name, match_data, timers, events):
    timers.remove(threading.current_thread())
    print("Putting")
    events.put((name, match_data))
    print("Finished putting")
    

def get_events(url, notification_requests, arena, timers, events):
    messages = sseclient.SSEClient(url)
    print("Blocking on message")
    for msg in messages:
        print("Finished blocking")
        if msg.event == "match":
            for t in timers:
                t.cancel()
                timers.remove(t)
            match_data = json.loads(msg.data)
            try:
                arena, = filter(lambda x : x["arena"] == arena, match_data)
            except ValueError:
                continue
            for time, key in [
                    (arena["times"]["game"]["start"], "game-start"),
                    (arena["times"]["game"]["end"], "game-end"),
                    (arena["times"]["period"]["start"], "period-start"),
                    (arena["times"]["period"]["end"], "period-end")]:
                for delta, name in notification_requests.get(key, []):
                    print((time, key, delta, name))
                    notification_delta = (dateutil.parser.parse(time)+datetime.timedelta(seconds=delta)) - datetime.datetime.now(pytz.utc)
                    if notification_delta < datetime.timedelta():
                        continue
                    print("running thread")
                    t = threading.Timer(notification_delta.total_seconds(), wait_for_event, args=(name, match_data, timers, events))
                    timers.append(t)
                    t.start()
        print("Blocking on message")
