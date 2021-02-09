import cbpro
import logging
import queue


class Channel(cbpro.WebsocketClient):
    def __init__(self, msg_queue=queue.Queue(), url="wss://ws-feed.pro.coinbase.com",
                 products=None, message_type="subscribe", mongo_collection=None, should_print=True, auth=False,
                 api_key="", api_secret="", api_passphrase="", channels=None):
        super().__init__(url, products, message_type, mongo_collection, should_print, auth, api_key, api_secret,
                         api_passphrase, channels)
        self.msg_queue = msg_queue
        self.products = products
        self.channels = channels
        self.is_running = False

    def on_open(self):
        self.is_running = True
        logging.info(f"Open {(', '.join(self.channels))} channels for {(', '.join(self.products))}")

    def on_close(self):
        self.is_running = False
        logging.info(f"Closed {(', '.join(self.channels))} channels for {(', '.join(self.products))}")

    def on_message(self, msg):
        # logging.debug(f"Produced {msg['type']} message")
        self.msg_queue.put(msg)


