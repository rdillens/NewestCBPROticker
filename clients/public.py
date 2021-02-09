import cbpro
from time import sleep, time

start_time = time()
try:
    public_client = cbpro.PublicClient()
    currencies = sorted(public_client.get_currencies(), key=lambda i: i['details']['sort_order'])
    products = public_client.get_products()

except Exception as inst:
    print(f'Error type: {type(inst)}\n{inst} \nError connecting public client')
    raise
finally:
    process_time = time() - start_time
    if process_time < 1:
        sleep(1-process_time)


def reset_pub_client():
    try:
        pub_client = cbpro.PublicClient()
    except Exception:
        print(Exception)
        raise
    return pub_client
