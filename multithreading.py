import clients.ws_channel as ch
import gui as gui
import queue
import concurrent.futures
import logging
import shelve
import tkinter as tk


class ThreadedClient:
    def __init__(self, master, shelf):
        """
        Start the GUI and the asynchronous threads. We are in the main
        (original) thread of the application, which will later be used by
        the GUI. We spawn a new thread for the worker.
        """
        self.master = master
        self.shelf = shelf
        self.prod_list = []
        self.msg_queue = queue.Queue()

        self.start_flag = False
        self.running = 1
        self.ws_channel = None

        self.gui = gui.TickerGui(
            self.master, self.msg_queue, self.shelf, self.start_channel)

        self.periodic_call()

    def start_ws_channel(self, products=None, channels=None):
        if products is None:
            products = ['BTC-USD']
        if channels is None:
            channels = ['status']
        self.ws_channel = ch.Channel(msg_queue=self.msg_queue, products=products, channels=channels)
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(self.ws_channel.start())

    def periodic_call(self):
        """
        Check every 100 ms if there is something new in the queue.
        """
        if self.start_flag:
            try:
                if self.ws_channel.is_running:
                    self.ws_channel.close()
                    # while self.ws_channel.is_running:
                    #     print(f"waiting")
            except AttributeError:
                pass
            self.start_ws_channel(products=self.prod_list, channels=['heartbeat', 'ticker'])
            # while not self.ws_channel.is_running:
            #     print(f"waiting")
            self.start_flag = False
        self.gui.process_msg()
        if not self.running:
            self.ws_channel.close()
            import sys
            sys.exit()
        self.master.after(100, self.periodic_call)

    def start_channel(self, prod_list):
        self.prod_list = prod_list
        self.start_flag = True


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    root = tk.Tk()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    root.columnconfigure(1, weight=1)
    root.rowconfigure(1, weight=1)

    with shelve.open('shelf') as sh:
        client = ThreadedClient(root, sh)
        root.mainloop()
    client.ws_channel.close()
