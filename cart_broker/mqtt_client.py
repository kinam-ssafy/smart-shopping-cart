import json
from datetime import datetime
import paho.mqtt.client as mqtt

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def mqtt_connect(host: str, port: int, user: str, pw: str):
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    c.username_pw_set(user, pw)
    c.connect(host, port, 60)
    c.loop_start()
    return c

def publish_uid_list(client, topic: str, active_uids: list[str]):
    payload = {"uids": active_uids, "time": now_str()}
    client.publish(topic, json.dumps(payload, ensure_ascii=False), qos=1, retain=True)
