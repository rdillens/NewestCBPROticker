import tkinter as tk
from tkinter import ttk
import queue
import logging
import clients.public as pub


class TickerGui:
    def __init__(self, master, msg_queue, shelf, start_ch):
        self.master = master
        self.msg_queue = msg_queue
        self.shelf = shelf
        self.start_ch = start_ch

        # Frames
        self.frm_quote = None
        self.frm_base = None
        self.frm_product = None

        self.frm_price = None
        self.frm_ohl = None
        self.frm_volume = None
        self.frm_last = None

        # Vars
        self.prod_selected = None

        self.qc_var = tk.IntVar()
        self.bc_var = tk.StringVar()

        # Dicts
        self.cur_dict = {}
        self.prod_dict = {}
        self.string_var_dict = {}
        self.lbl_dict = {}

        # Initialize
        self.init()

    def init(self):
        # Initialize main frames
        self.init_frm_quote()
        self.init_frm_base()
        self.init_frm_product()
        # Initialize currency and product dictionaries
        self.cur_dict = self.init_currency()
        self.prod_dict = self.init_products()
        self.init_string_vars()

        # Set qc and bc from shelf or create them
        self.set_sq()
        self.set_sb()

        self.prod_selected = self.get_selected_prod()

        self.gen_quote_frm()
        self.gen_base_frm()
        self.gen_prod_frm()
        self.start_ch([self.prod_selected])

    def set_sq(self):
        if 'quote_selected' not in self.shelf:
            self.shelf['quote_selected'] = 0
            self.shelf.sync()
        self.qc_var.set(self.shelf['quote_selected'])

    def set_sb(self):
        qs = self.sq_id()
        if qs not in self.shelf:
            self.shelf[qs] = self.base_list()[0]
            self.shelf.sync()
        self.bc_var.set(self.shelf[qs])
        self.bc_var.trace('w', self.update_base)

    def sq_id(self, selected_quote=None):
        if selected_quote is None:
            return self.quote_list()[self.qc_var.get()]
        else:
            return self.quote_list()[selected_quote]

    def sb_id(self, selected_base=None):
        if selected_base is None:
            return next(self.cur_dict[cur]['id'] for cur in self.cur_dict if
                        self.cur_dict[cur]['name'] == self.bc_var.get())
        else:
            return next(self.cur_dict[cur]['id'] for cur in self.cur_dict if
                        self.cur_dict[cur]['name'] == selected_base)

    def get_selected_prod(self):
        if 'prod_selected' not in self.shelf:
            self.prod_selected = 'BTC-USD'
            self.shelf['prod_selected'] = self.prod_selected
            self.shelf.sync()
        return self.shelf['prod_selected']

    # Process updates
    def update_quote(self, *args):
        qs = self.sq_id()
        logging.debug(f"Update quote {self.quote_list()[self.qc_var.get()]}{args}")
        self.shelf['quote_selected'] = self.qc_var.get()
        self.shelf.sync()
        if qs in self.shelf:
            self.bc_var.set(self.shelf[qs])
        else:
            logging.info(f"not in shelf")
            self.shelf[qs] = self.base_list()[0]
            self.shelf.sync()
            self.bc_var.set(self.shelf[qs])

        for widget in self.frm_base.winfo_children():
            widget.destroy()
        self.gen_base_frm()

    def update_base(self, *args):
        qs = self.sq_id()
        logging.debug(f"update base {self.bc_var.get()}{args}")
        self.shelf[qs] = self.bc_var.get()
        self.shelf.sync()
        self.update_product()

    def update_product(self):
        self.prod_selected = next(self.prod_dict[prod]['prod_info']['id'] for prod in self.prod_dict
                                  if self.prod_dict[prod]['quote_info']['id'] == self.sq_id()
                                  and self.prod_dict[prod]['base_info']['id'] == self.sb_id())
        self.shelf['prod_selected'] = self.prod_selected
        self.shelf.sync()
        logging.debug(f"Update product {self.shelf['prod_selected']}")
        self.start_ch([self.prod_selected])

        for widget in self.frm_price.winfo_children():
            widget.grid_forget()
        for widget in self.frm_ohl.winfo_children():
            widget.grid_forget()
        for widget in self.frm_volume.winfo_children():
            widget.grid_forget()
        for widget in self.frm_last.winfo_children():
            widget.grid_forget()
        self.gen_prod_frm()

    def process_msg(self):
        quotes = ['price', 'open_24h', 'low_24h', 'high_24h', 'best_bid', 'best_ask']
        bases = ['volume_24h', 'volume_30d', 'last_size']
        while self.msg_queue.qsize():
            try:
                msg = self.msg_queue.get(0)
                if 'type' in msg:
                    m_type = msg['type']
                    if m_type == 'subscriptions':
                        pass
                    if m_type == 'ticker':
                        m_pid = msg['product_id']
                        pd = self.prod_dict[m_pid]
                        sd = self.string_var_dict[m_pid]
                        pd[m_type] = msg
                        for quote in quotes:
                            if quote in pd[m_type]:
                                pd[m_type][quote] = self.set_quote_increment(msg, quote)
                        for base in bases:
                            if base in pd[m_type]:
                                pd[m_type][base] = self.set_base_increment(msg, base)
                        for item in msg:
                            sd[m_type][item].set(pd[m_type][item])

            except queue.Empty:
                pass
        else:
            self.shelf['prod_dict'] = self.prod_dict
            self.shelf.sync()

    def set_quote_increment(self, msg, item):
        pd = self.prod_dict[msg['product_id']]
        if pd['prod_info']['quote_increment'].find('1') == 0:
            qi_str = f",.0f"
        elif pd['prod_info']['quote_increment'].find('1') > 0:
            qi_str = f",.{pd['prod_info']['quote_increment'].find('1') - 1}f"
        else:
            logging.error("ERROR finding quote increment")
            return f"{pd['quote_info']['details']['symbol']}{float(pd[msg['type']][item])}"
        return f"{pd['quote_info']['details']['symbol']}{float(pd[msg['type']][item]):{qi_str}}"

    def set_base_increment(self, msg, item):
        pd = self.prod_dict[msg['product_id']]
        if pd['prod_info']['base_increment'].find('1') == 0:
            qi_str = f",.0f"
        elif pd['prod_info']['base_increment'].find('1') > 0:
            qi_str = f",.{pd['prod_info']['base_increment'].find('1') - 1}f"
        else:
            logging.error("ERROR finding base increment")
            return f"{float(pd[msg['type']][item])}"
        return f"{float(pd[msg['type']][item]):{qi_str}}"

    # Init dicts
    def quote_list(self):
        return sorted([*{*[self.prod_dict[prod]['prod_info']['quote_currency'] for prod in self.prod_dict]}],
                      key=lambda l:
                      next(self.cur_dict[cur]['details']['sort_order'] for cur in self.cur_dict
                           if self.cur_dict[cur]['id'] == l and self.cur_dict[cur]['status'] == 'online'))

    def base_list(self):
        base_list = [self.prod_dict[prod]['prod_info']['base_currency'] for prod in self.prod_dict
                     if self.prod_dict[prod]['prod_info']['quote_currency'] == self.sq_id()]
        return [self.cur_dict[cur]['name'] for cur in self.cur_dict
                if self.cur_dict[cur]['id'] in base_list]

    def init_currency(self):
        if 'cur_dict' not in self.shelf:
            cur_dict = {}
            logging.info(f"Creating currency dictionary from public client")
            for cur in pub.currencies:
                cur_dict[cur['id']] = cur
            self.shelf['cur_dict'] = cur_dict
            self.shelf.sync()
            logging.debug(f"currencies loaded: {cur_dict.keys()}")
            return cur_dict
        else:
            return self.shelf['cur_dict']

    def init_products(self):
        if 'prod_dict' not in self.shelf:
            prod_dict = {}
            logging.info(f"Creating product dictionary from public client")
            for prod in pub.products:
                prod_dict[prod['id']] = {
                    'prod_info': prod,
                    'quote_info': self.cur_dict[prod['quote_currency']],
                    'quote_details': self.cur_dict[prod['quote_currency']]['details'],
                    'base_info': self.cur_dict[prod['base_currency']],
                    'base_details': self.cur_dict[prod['base_currency']]['details'],
                    'heartbeat': {},
                    'ticker': {}
                }
            self.shelf['prod_dict'] = prod_dict
            self.shelf.sync()
            logging.debug(f"products loaded: {prod_dict.keys()}")
            return prod_dict
        else:
            return self.shelf['prod_dict']

    def init_string_vars(self):
        for prod in self.prod_dict:
            self.string_var_dict[prod] = {}
            self.lbl_dict[prod] = {}

            self.string_var_dict[prod]['ticker'] = {}
            self.lbl_dict[prod]['ticker'] = {}

            items_dict = {
                'price': {
                    'items': ['best_ask', 'price', 'best_bid'],
                    'frame': self.frm_price},
                'ohl': {
                    'items': ['open_24h', 'low_24h', 'high_24h'],
                    'frame': self.frm_ohl},
                'vol': {
                    'items': ['volume_24h', 'volume_30d'],
                    'frame': self.frm_volume},
                'last': {
                    'items': ['last_size', 'side'],
                    'frame': self.frm_last},
                'other': {
                    'items': ['type', 'trade_id', 'sequence', 'time', 'product_id'],
                    'frame': self.master}}

            for key in items_dict.keys():
                for item in items_dict[key]['items']:
                    self.string_var_dict[prod]['ticker'][item] = tk.StringVar()
                    self.lbl_dict[prod]['ticker'][item] = ttk.Label(
                        master=items_dict[key]['frame'], textvariable=self.string_var_dict[prod]['ticker'][item])

    # Init frames
    def init_frm_quote(self):
        self.frm_quote = ttk.Frame(self.master, relief=tk.RIDGE, borderwidth=5)
        self.frm_quote.columnconfigure(0, weight=1)
        self.frm_quote.rowconfigure(0, weight=1)
        self.frm_quote.grid(row=1, column=0, sticky='news')

    def init_frm_base(self):
        self.frm_base = ttk.Frame(self.master, relief=tk.RIDGE, borderwidth=5)
        self.frm_base.columnconfigure(0, weight=1)
        self.frm_base.rowconfigure(0, weight=1)
        self.frm_base.grid(row=0, column=0, sticky='news')

    def init_frm_product(self):
        self.frm_product = ttk.Frame(self.master, relief=tk.RIDGE, borderwidth=5)
        self.frm_product.columnconfigure(0, weight=1)
        self.frm_product.columnconfigure(1, weight=1)
        self.frm_product.rowconfigure(0, weight=1)
        self.frm_product.rowconfigure(1, weight=1)
        self.init_frm_price()
        self.init_frm_ohl()
        self.init_frm_volume()
        self.init_frm_last()
        self.frm_product.grid(row=0, column=1, rowspan=2, sticky='news')

    def init_frm_price(self):
        self.frm_price = ttk.Frame(self.frm_product, relief=tk.GROOVE, borderwidth=5)
        self.frm_price.columnconfigure(0, weight=1)
        self.frm_price.columnconfigure(1, weight=1)
        self.frm_price.rowconfigure(0, weight=1)
        self.frm_price.rowconfigure(1, weight=1)
        self.frm_price.rowconfigure(2, weight=1)
        self.frm_price.grid(row=0, column=0, sticky='news')

    def init_frm_ohl(self):
        self.frm_ohl = ttk.Frame(self.frm_product, relief=tk.GROOVE, borderwidth=5)
        self.frm_ohl.columnconfigure(0, weight=1)
        self.frm_ohl.columnconfigure(1, weight=1)
        self.frm_ohl.rowconfigure(0, weight=1)
        self.frm_ohl.rowconfigure(1, weight=1)
        self.frm_ohl.rowconfigure(2, weight=1)
        self.frm_ohl.grid(row=0, column=1, sticky='news')

    def init_frm_volume(self):
        self.frm_volume = ttk.Frame(self.frm_product, relief=tk.GROOVE, borderwidth=5)
        self.frm_volume.columnconfigure(0, weight=1)
        self.frm_volume.columnconfigure(1, weight=1)
        self.frm_volume.rowconfigure(0, weight=1)
        self.frm_volume.rowconfigure(1, weight=1)
        self.frm_volume.grid(row=1, column=1, sticky='news')

    def init_frm_last(self):
        self.frm_last = ttk.Frame(self.frm_product, relief=tk.GROOVE, borderwidth=5)
        self.frm_last.columnconfigure(0, weight=1)
        self.frm_last.columnconfigure(1, weight=1)
        self.frm_last.rowconfigure(0, weight=1)
        self.frm_last.rowconfigure(1, weight=1)
        self.frm_last.grid(row=1, column=0, sticky='news')

    # Gen frame content
    def gen_quote_frm(self):
        frm_rb = ttk.Frame(self.frm_quote)
        for i, qc in enumerate(self.quote_list()):
            rb = tk.Radiobutton(frm_rb, text=qc, indicatoron=0, variable=self.qc_var, value=i,
                                command=self.update_quote)
            rb.grid(row=0, column=i)
        frm_rb.grid(row=0, column=0)

    def gen_base_frm(self):
        bc_menu = tk.OptionMenu(self.frm_base, self.bc_var, *self.base_list())
        bc_menu.grid(row=0, column=0, sticky='ew')

    def gen_prod_frm(self):
        price_dict = {'best_ask': 'Ask',
                      'price': 'Price',
                      'best_bid': 'Bid'
                      }
        ohl_dict = {'open_24h': 'Open',
                    'low_24h': 'Low',
                    'high_24h': 'High'
                    }
        volume_dict = {'volume_24h': 'Volume (24h)',
                       'volume_30d': 'Volume (30d)'
                       }
        last_dict = {'last_size': 'Last Size',
                     'side': 'Side'
                     }
        self.populate_frame(price_dict, self.frm_price)
        self.populate_frame(ohl_dict, self.frm_ohl)
        self.populate_frame(volume_dict, self.frm_volume)
        self.populate_frame(last_dict, self.frm_last)

    def populate_frame(self, item_dict, frame):
        prod_dict = self.prod_dict[self.prod_selected]
        lbl_dict = self.lbl_dict[self.prod_selected]
        for i, item in enumerate(item_dict.keys()):
            if item in prod_dict['ticker'] and item in lbl_dict['ticker']:
                lbl_dict['ticker'][item].grid(row=i, column=1, sticky='e')
                lbl = ttk.Label(frame, text=item_dict[item])
                lbl.grid(row=i, column=0, sticky='w')
