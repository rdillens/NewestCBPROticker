import clients.ws_channel as ch
import history as h
import gui as gui
import queue
import concurrent.futures
import logging
import shelve
import tkinter as tk
import random
import threading
import time
import pprint


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
        self.hist_queue = queue.Queue()

        self.start_flag = False
        self.hist_flag = False
        self.running = 1
        self.thread1 = threading.Thread(target=self.worker_thread1)
        self.thread1.start()
        self.ws_channel = None

        self.gui = gui.TickerGui(
            self.master, self.msg_queue, self.hist_queue, self.shelf, self.start_channel)

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
            self.hist_flag = True
            # while not self.ws_channel.is_running:
            #     print(f"waiting")
            self.start_flag = False
        self.gui.process_msg()
        self.gui.process_hist_msg()
        if not self.running:
            self.ws_channel.close()
            import sys
            sys.exit()
        self.master.after(100, self.periodic_call)

    def worker_thread1(self):
        while self.running:
            if self.hist_flag:
                logging.debug(f"hist")
                self.hist_flag = False
                for prod in self.prod_list:
                    df = h.h_to_df(h.get_h(prod, h.gran[-1]))
                    self.hist_queue.put(df)

            # Sleep statement is required to release thread lock
            time.sleep(.001)
        pass

    def get_history(self):
        pass

    def start_channel(self, prod_list):
        self.prod_list = prod_list
        self.start_flag = True

    def end_program(self):
        self.running = 0


rand = random.Random()

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
    client.end_program()
