import ssl
import json
import time
import uuid
import re
import asyncio
import threading
import subprocess
import tkinter as tk
from loguru import logger
from datetime import datetime
from tkinter import scrolledtext, messagebox
from fake_useragent import UserAgent
from websockets_proxy import Proxy, proxy_connect

nstProxyUrl = "https://app.nstproxy.com/register?i=wjgSmA"
telegramUrl = "https://t.me/web3airdropclub"
grassUrl = "https://app.getgrass.io/register/?referralCode=n2S8rhaFVHo0mjY"
nstProxyAppId = "F680F8381EB0D52B"


def get_datetime():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def insert_log(log_widget, content, tag):
    log_widget.insert(tk.END, content, tag)
    log_widget.see(tk.END)


async def connect_to_wss(user_id, socks5_proxy, log_widget):
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, f'{socks5_proxy}-{user_id}'))
    logger.info(device_id)
    insert_log(log_widget, f"{get_datetime()} user_id: {user_id} device_id: {device_id}\n", 'info')

    user_agent = UserAgent()
    random_user_agent = user_agent.random

    while True:
        try:
            await asyncio.sleep(1)
            custom_headers = {"User-Agent": random_user_agent}
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = "wss://proxy.wynd.network:4650/"
            server_hostname = "proxy.wynd.network"
            proxy = Proxy.from_url(socks5_proxy)
            async with proxy_connect(uri, proxy=proxy, ssl=ssl_context, server_hostname=server_hostname,
                                     extra_headers=custom_headers) as websocket:
                async def send_ping():
                    while True:
                        send_message = json.dumps(
                            {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                        try:
                            await websocket.send(send_message)
                            logger.debug(send_message)
                            insert_log(log_widget, f"{get_datetime()} send_message: {send_message}\n", 'info')
                        except Exception as e:
                            pass
                        await asyncio.sleep(2)

                asyncio.create_task(send_ping())
                while True:
                    response = await websocket.recv()
                    message = json.loads(response)
                    logger.info(message)
                    insert_log(log_widget, f"{get_datetime()} message: {message}\n", 'info')

                    if message.get("action") == "AUTH":
                        auth_response = {
                            "id": message["id"],
                            "origin_action": "AUTH",
                            "result": {
                                "browser_id": device_id,
                                "user_id": user_id,
                                "user_agent": custom_headers['User-Agent'],
                                "timestamp": int(time.time()),
                                "device_type": "extension",
                                "version": "3.3.2"
                            }
                        }
                        try:
                            await websocket.send(json.dumps(auth_response))
                            logger.debug(auth_response)
                            insert_log(log_widget, f"{get_datetime()} auth_response: {auth_response}\n", 'info')
                        except Exception as e:
                            pass

                    elif message.get("action") == "PONG":
                        pong_response = {"id": message["id"], "origin_action": "PONG"}
                        try:
                            await websocket.send(json.dumps(pong_response))
                            logger.debug(pong_response)
                            insert_log(log_widget, f"{get_datetime()} pong_response: {pong_response}\n", 'info')
                        except Exception as e:
                            pass

        except Exception as e:
            pass


def add_nstproxy_appid(proxy):
    if "nstproxy." in proxy:
        pattern = r"^(?:[^:]+)://([^:]+):[^@]+@"
        match = re.match(pattern, proxy)
        if match:
            username = match.group(1)
            if "appId" not in username:
                newusername = "{}-appid_{}".format(username, nstProxyAppId)
                proxy = proxy.replace(username, newusername)
                return proxy
    return proxy


def start_operation():
    user_id = user_id_entry.get()
    proxy = proxy_entry.get()
    proxy = add_nstproxy_appid(proxy)
    asyncio.run_coroutine_threadsafe(connect_to_wss(user_id, proxy, log_box), new_loop)


def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?\n"):
        root.destroy()


def run_asyncio_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def open_telegram(event):
    subprocess.Popen(['start', telegramUrl], shell=True)


if __name__ == '__main__':
    new_loop = asyncio.new_event_loop()
    root = tk.Tk()
    root.title("Grass")

    tk.Label(root, text="User ID:").pack()
    user_id_entry = tk.Entry(root, width=50)
    user_id_entry.pack()

    tk.Label(root, text="Socks5 Proxy:").pack()
    proxy_entry = tk.Entry(root, width=50)
    proxy_entry.pack()

    start_button = tk.Button(root, text="Start", command=start_operation)
    start_button.pack()

    log_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=15, width=130)
    log_box.pack(padx=10, pady=10)
    log_box.tag_configure('info', foreground='blue')
    log_box.tag_configure('warning', foreground='orange')
    log_box.tag_configure('error', foreground='red')

    labels_frame = tk.Frame(root)

    referral_label = tk.Label(labels_frame,
                              text="Join telegram: {}".format(telegramUrl),
                              fg="red")
    referral_label.pack(side=tk.LEFT)

    labels_frame.pack()
    log_box.insert(tk.END, 'Please enter the user_id.\n', 'info')
    log_box.insert(tk.END, 'The format for a SOCKS5 proxy is: socks5://username:password@ip:port\n', 'info')
    log_box.insert(tk.END, "Grass register: {}\n".format(grassUrl), 'info')
    log_box.insert(tk.END, "Join telegram: {}\n".format(telegramUrl), 'info')
    log_box.insert(tk.END, "Nstproxy register: {}\n".format(nstProxyUrl), 'info')

    asyncio_loop_thread = threading.Thread(target=run_asyncio_loop, args=(new_loop,), daemon=True)
    asyncio_loop_thread.start()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
