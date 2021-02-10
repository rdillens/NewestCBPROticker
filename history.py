import pandas as pd
import pandas.errors as pe
import helpful_methods as hm
import cbpro
import json.decoder


gran = [60, 300, 900, 3600, 21600, 86400]
df_index = ['Time', 'Low', 'High', 'Open', 'Close', 'Volume']
last_call = hm.ts()


def get_h(p, g, t=None):
    global last_call
    if t is None:
        try:
            hm.fill_time(last_call)
            return cbpro.PublicClient().get_product_historic_rates(p, granularity=g)
        except ConnectionError as e:
            print('\nSleeping for 30 secs', e)
            hm.fill_time(last_call, 30)
            return cbpro.PublicClient().get_product_historic_rates(p, granularity=g)
        except Exception as e:
            print('Exception')
            print(type(e), e)
            raise
        finally:
            last_call = hm.ts()
    else:
        try:
            hm.fill_time(last_call)
            return cbpro.PublicClient().get_product_historic_rates(p, hm.iso(t - (300 * g)), hm.iso(t), g)
        except ConnectionResetError:
            hm.fill_time(last_call, 30)
            return cbpro.PublicClient().get_product_historic_rates(p, hm.iso(t - (300 * g)), hm.iso(t), g)
        except ConnectionError as e:
            print('\nSleeping for 30 secs', e)
            hm.fill_time(last_call, 30)
            return cbpro.PublicClient().get_product_historic_rates(p, hm.iso(t - (300 * g)), hm.iso(t), g)
        except json.decoder.JSONDecodeError as e:
            print('\nSleeping for 30 secs', e)
            hm.fill_time(last_call, 30)
            return cbpro.PublicClient().get_product_historic_rates(p, hm.iso(t - (300 * g)), hm.iso(t), g)
        except Exception as e:
            print('\nUnhandled Exception')
            print(type(e), e)
            raise
        finally:
            last_call = hm.ts()


def h_to_df(h):
    index_list = []
    hist_list = []
    try:
        for i in h:
            index_list.append(i[0])
            hist_list.append(i[1:])
        df = pd.DataFrame(hist_list, index=index_list, columns=df_index[1:])
        df.index.name = df_index[0]
    except KeyError as e:
        print('Key Error.', e, h)
    except Exception as e:
        print(type(e), e, *h)
        raise
    else:
        return df
    return pd.DataFrame()


def csv_to_df(f, p, g):
    try:
        # FutureWarning occurs here
        # TODO: replace CSV file with SHELF file
        df = pd.read_csv(f, header=0, index_col=0)
        idx = df.index.drop_duplicates()
        if len(idx) != len(df):
            print(len(df) - len(idx))
        return df
    except pe.EmptyDataError as e:
        print(e)
        df = h_to_df(get_h(p, g))
        if not df.empty:
            df.to_csv(f, index=True)
        return df
    except Exception as e:
        print(type(e), e)
        raise


def update_to_present(f, df, p, g):
    # Determine if record needs update
    if hm.ts() - hm.get_age_limit(g) < df.index[0]:
        # Record is less than 1 hour old, no update needed
        return df
    else:
        # Record needs update, get new data
        df2 = h_to_df(get_h(p, g))
        # Determine if new data overlaps with old data
        if df.index[0] >= df2.index[-1] - g:
            # Data overlaps, append old data to new data
            df2 = df2.append(df[df.index < df2.index[-1]])
            print(f'{len(df2):8d} records, inserting {len(df2) - len(df)}', end=' ')
            df2.to_csv(f, index=True)
        else:
            # Data does not meet, continue getting data until old data overlaps
            new_time = df2.index[-1] - g
            while df.index[0] < new_time:
                df_new = h_to_df(get_h(p, g, new_time))
                if not df_new.empty:
                    df2 = df2.append(df_new)
                    new_time = df2.index[-1] - g
                else:
                    new_time -= (300 * g)
            else:
                # Append old data to new data and save
                df2 = df2.append(df[df.index < df2.index[-1]])
                print(f'{len(df2):8d} records, inserting {len(df2) - len(df)}', end=' ')
                df2.to_csv(f, index=True)
        return df2


def back_fill(f, df, p, g, p_string=None):
    oldest = hm.gen_f(p + str(gran[-1]), p, ext='.csv', base_path='products')
    oldest_df_index = df.index[-1]
    try:
        oldest_index = pd.read_csv(oldest, index_col=0).index[-1]
    except IndexError:
        oldest_index = df.index[-1] - g
    except Exception as e:
        print(e)
        raise
    finally:
        df2 = h_to_df(get_h(p, g, oldest_df_index - g))
    exit_flag = False
    while oldest_df_index > oldest_index + gran[-1] or not (df2.empty or exit_flag):
        t_rem = hm.t_rem(oldest_df_index, oldest_index, g)
        print(f'\r{p_string} {t_rem:10s} {len(df)}', end='')
        if not df2.empty and (df2.index[-1] != df.index[-1]):
            df2.to_csv(f, index=True, header=False, mode='a')
            df = df.append(df2)
            oldest_df_index = df.index[-1]
        else:
            oldest_df_index = oldest_df_index - (300 * g)
            exit_flag = True
        df2 = h_to_df(get_h(p, g, oldest_df_index - g))
    else:
        print(f'\r{p_string} Complete', end=' ')
    return df
