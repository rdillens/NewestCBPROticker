from datetime import datetime as dt
import time
from pathlib import Path


def ts():
    return dt.now().timestamp()


def fill_time(t, lim=1, msg=None):
    if msg == 'slept' and ts() - t < lim:
        print(msg, f'{t - ts() + lim:.6f}')
    elif msg is not None:
        print(msg)
    if ts() - t < lim:
        time.sleep(t - ts() + lim)
    return ts()


def iso(timestamp):
    return dt.utcfromtimestamp(timestamp).isoformat()


def utc(timestamp):
    return dt.utcfromtimestamp(timestamp)


def gen_f(name, *paths, ext=None, gen=False, base_path=None):
    if ext is None:
        ext = '.dat'
    if base_path is None:
        base_path = ''
    else:
        base_path = base_path + '/'
    for p in paths:
        base_path += str(p) + '/'
    d_folder = Path(base_path)
    f_name = name + ext
    if gen and not d_folder.exists():
        d_folder.mkdir()
    return d_folder / f_name


# def gen_f_dict(c, p, granularity):
#     f = {}
#     f_name = p + str(granularity)
#     f.setdefault('f_in', gen_f(f_name, p, ext='.csv', base_path='products'))
#     f.setdefault('f_out', gen_f(f_name, 'Crypto-Currencies', c['name'], p, ext='.csv', gen=True, base_path='Output'))
#     return f


def get_age_limit(g):
    if g == 900 or g == 300 or g == 60:
        return 3600 + g
    else:
        return g


def t_rem(v1, v2, g):
    return time.strftime('%H:%M:%S', time.gmtime(int(round((v1 - v2) / (300 * g), 0))))
