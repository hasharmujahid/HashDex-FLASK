import asyncio
import aiohttp
from stellar_sdk import Keypair
from datetime import datetime
from flask import Flask, render_template, request, jsonify , Markup
from flask import *
from flask import Flask, render_template, request
from stellar_sdk import Server, Keypair, Network, TransactionBuilder, Asset
import time
from stellar_sdk import Server, Keypair, Network, TransactionBuilder, Asset
from stellar_sdk.client.requests_client import RequestsClient
import datetime
import json
import time
import threading
from bot import *
from datetime import datetime





app = Flask(__name__)
global response_list
global bot_instances
global custom_paths
global global_error_string
global keep_running
keep_running = True
global_error_string = None
response_list = []
global horizon_url
horizon_url = 'https://horizon.stellar.org'
global account_data_list
account_data_list = []



def format_datetime(timestamp):
    dt = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
    return dt.strftime('%H:%M:%S, %d %b %Y')


async def get_account_data(session, secret_key):
    global horizon_url
    secret_key=str(secret_key)
    if secret_key.startswith('S') and len(secret_key) >= 56:
        keypair = Keypair.from_secret(secret_key)
        account_public_key = keypair.public_key
    else:
        return {
        'account_public_key': 'Wrong Secret Key',
        'account_secret_key': 'Wrong Secret Key',
        'payments': 'Wrong Secret Key',
        'balances': 'Wrong Secret Key',
        'claimable_balances': 'Wrong Secret Key'
    }
    async with session.get(f'{horizon_url}/accounts/{account_public_key}/payments?order=desc&limit=5') as response:
        payments = await response.json()
        payment_info = []
        embedded_records = payments.get('_embedded', {}).get('records', [])
        for payment in embedded_records:
            destination_asset_code = payment.get('asset_code', 'N/A')
            destination_asset_amount = payment.get('amount', 'N/A')
            source_asset_code = payment.get('source_asset_code', 'N/A')
            source_asset_amount = payment.get('source_amount', 'N/A')
            
            payment_data = {
                'id': payment.get('id', 'N/A'),
                'amount': destination_asset_amount,
                'source_asset_code': source_asset_code,
                'source_asset_amount': source_asset_amount,
                'destination_asset_code': destination_asset_code,
                'destination_asset_amount': destination_asset_amount,
                'created_at': format_datetime(payment.get('created_at', 'N/A'))
            }
            payment_info.append(payment_data)

    async with session.get(f'{horizon_url}/accounts/{account_public_key}') as response:
        account_details = await response.json()
        balance_info = []
        if 'balances' in account_details:
            balances = account_details['balances']
            for balance in balances:
                asset_code = balance.get('asset_code', 'N/A')
                balance_data = {
                    'asset': asset_code,
                    'balance': balance['balance']
                }
                balance_info.append(balance_data)
        else:
            balance_info.append({'asset': 'N/A', 'balance': 'N/A'})

    async with session.get(f'{horizon_url}/claimable_balances?claimant={account_public_key}&order=desc') as response:
        claimable_balances = await response.json()
        claimable_info = []
        for claimable_balance in claimable_balances['_embedded']['records']:
            asset = claimable_balance['asset']
            asset_code, issuer = asset.split(':')
            claimable_data = {
                'amount': claimable_balance['amount'],
                'asset_code': asset_code,
                'issuer': issuer
            }
            claimable_info.append(claimable_data)
    account_data_list.append({
        'account_public_key': keypair.public_key,
        'account_secret_key': secret_key,
        'payments': payment_info,
        'balances': balance_info,
        'claimable_balances': claimable_info
    })    

    return {
        'account_public_key': keypair.public_key,
        'account_secret_key': secret_key,
        'payments': payment_info,
        'balances': balance_info,
        'claimable_balances': claimable_info
    }

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/run_code', methods=['POST'])
async def run_code():
    if request.method == 'POST':
        secret_keys = request.form['secret_keys'].splitlines()
        async with aiohttp.ClientSession() as session:
            tasks = [get_account_data(session, key) for key in secret_keys]
            results = await asyncio.gather(*tasks)
            return render_template('results.html', results=results)


@app.route('/search', methods=['POST', 'GET'])
def search():
    search_query = request.args.get('query', '').lower()
    if len(search_query) == 0:
        return render_template('results.html')
    else:
        search_results = []

        # Search for the query in the account data list
        for account_data in account_data_list:
            if (
                search_query in account_data['account_public_key'].lower()
                or search_query in account_data['account_secret_key'].lower()
                or any(
                    search_query in payment_data['source_asset_code'].lower() or
                    search_query in payment_data['destination_asset_code'].lower() or
                    search_query in balance_data['asset'].lower() or
                    search_query in claimable_data['asset_code'].lower()
                    for payment_data in account_data['payments']
                    for balance_data in account_data['balances']
                    for claimable_data in account_data['claimable_balances']
                )
            ):
                search_results.append(account_data)

    # Highlight the search text in the search results
        for result in search_results:
            for key, value in result.items():
                if isinstance(value, str) and search_query in value.lower():
                    # Highlight the search text in the value
                    result[key] = Markup(value.replace(search_query, f'<span class="highlight">{search_query}</span>'))

        # Render the 'results.html' template with the search results
        return render_template('results.html', results=search_results)
    
@app.route('/run_bot', methods=['GET', 'POST'])
def run_bot():
    global global_error_string 
    global kill
    global keep_running
    keep_running = True

    if request.method == 'POST':
        print(request.data)
        mode = request.form.get('mode')
        amount1 = str(request.form.get('amount1'))
        amount2 = str(request.form.get('amount2'))
        delay = float(request.form.get('delay'))
        server_index = int(request.form.get('server_index'))
        pub_secret_key = request.form.get('pub_secret_key').strip()
        source_code = request.form.get('source_code').strip()
        source_issuer = request.form.get('source_issuer').strip()
        dest_code = request.form.get('dest_code').strip()
        dest_issuer = request.form.get('dest_issuer').strip()
        usedest = request.form.get('dest_account')
        global enable_custom_path
        enable_custom_path = request.form.get('enable_custom_path')
        print(amount1)
        # Update bot instance with provided values

        if enable_custom_path == "true":
            global custom_paths
            custom_paths = []  # Clear the list for each run
            for i in range(1, 6):  # Check up to 5 paths
                path_code = request.form.get(f'path{i}_code')
                path_issuer = request.form.get(f'path{i}_issuer')


                print('loading paths')
                if path_code and path_issuer !=None:
                    path_issuer = path_issuer.strip()
                    path_code = path_code.strip()    
                    if path_code and path_issuer:
                        if path_code.lower() == 'xlm' or path_issuer.lower() == 'n':
                            custom_paths.append(Asset.native())
                        else:
                            custom_paths.append(Asset(path_code, path_issuer))
        else:
            enable_custom_path='false'
        
        new_bot=Bot()

        if source_code.lower() == 'xlm':
            new_bot.source_asset=Asset.native()
        elif dest_code.lower  == 'xlm':
            new_bot.destination_asset=Asset.native() 
        else:            
            new_bot.source_asset = Asset(source_code, source_issuer)
            new_bot.destination_asset = Asset(dest_code, dest_issuer)
        
        new_bot.keypair = Keypair.from_secret(pub_secret_key)
        new_bot.server_index = server_index
        new_bot.server = Server(horizon_url=bot.horizon_servers[server_index], client=client)
        
        
        if usedest == 'true':
            new_bot.destination_account_id='GCEVTSXRYPVZHH2Q3Y63JPS6UZXHKTOIN2QOSRDV3WI35ACQNUYO3LHD'
        else:
            new_bot.destination_account_id=new_bot.keypair.public_key
        global response_list
        response_list = []

        def trade_thread():
            global response_list
            global global_error_string
            global keep_running
            while keep_running == True:
                try:
                    if mode == "strict-receive":
                        dest_amount = amount1
                        send_max_amount = amount2
                        try:
                            response = new_bot.trade_path_payment_strict_receive(dest_amount=dest_amount, send_max_amount=send_max_amount)
                            error_string = None
                        except Exception as e:
                            global_error_string = ""
                            error_string = str(e)
                            if 'read timeout' in error_string:
                                error_string = 'Timed out'
                            print("Trade thread error:", error_string)
                            global_error_string = error_string
                            response = None
                    elif mode == "strict-send":
                        send_amount = amount1
                        dest_min = amount2
                        try:
                            response = new_bot.path_payment_send_trade(send_amount=send_amount, dest_min=dest_min)
                            error_string = None
                        except Exception as e:
                            global_error_string = ""
                            error_string = str(e)
                            if 'read timeout' in error_string:
                                error_string = 'Timed out'
                            print("Trade thread error:", error_string)
                            global_error_string = error_string
                            response = None
                    response_list.append(response)
                    time.sleep(delay)
                except Exception as e:
                    global_error_string = ""
                    print("Trade thread error:", str(e))
                    error_string = str(e)
                    global_error_string = error_string

        
        def custom_path_trade():
            global response_list
            global custom_paths
            global global_error_string
            global keep_running 
            keep_running = True
            while keep_running == True:
                try:
                    if mode == "strict-receive":
                        dest_amount = amount1
                        send_max_amount = amount2
                        try:
                            response = new_bot.trade_path_payment_strict_receive_custom(custom_path=custom_paths, dest_amount=dest_amount, send_max_amount=send_max_amount)
                            error_string = None
                        except Exception as e:
                            global_error_string = ""
                            error_string = str(e)
                            if 'read timeout' in error_string:
                                error_string = 'Timed out'
                            print("Custom path trade thread error:", error_string)
                            global_error_string = error_string
                            response = None
                    elif mode == "strict-send":
                        send_amount = amount1
                        dest_min = amount2
                        try:
                            response = new_bot.path_payment_send_trade_custom(custom_path=custom_paths, send_amount=send_amount, dest_min=dest_min)
                            error_string = None
                        except Exception as e:
                            global_error_string = ""
                            error_string = str(e)
                            if 'read timeout' in error_string:
                                error_string = 'Timed out'
                            print("Trade thread error:", error_string)
                            global_error_string = error_string
                            response = None
                    response_list.append(response)
                    time.sleep(delay)
                except Exception as e:
                    global_error_string = ""
                    print("Trade thread error:", str(e))
                    error_string = str(e)
                    global_error_string = error_string

        if enable_custom_path == "true":
            thread = threading.Thread(target=custom_path_trade)
            thread.start()
        else:
            thread = threading.Thread(target=trade_thread)
            thread.start()
    return render_template('runbot.html')

@app.route('/get_responses', methods=['GET'])
def get_responses():
    global response_list
    global global_error_string
    
    logs_data = []
    errors = []
    
    for response in response_list:
        if response is not None:
            message = response.get('hash', '')
            status = response.get('successful', '')  # Assuming 'status' is a field in your response
            logs_data.append({'hash': message, 'successful': status})
    
    if global_error_string:
        try:
            error_data = json.loads(global_error_string)
            result_codes = error_data.get('extras', {}).get('result_codes', {})
            operations = result_codes.get('operations', [])
            errors.extend(operations)  # Store the errors in the 'errors' list
        except json.decoder.JSONDecodeError:
            errors.append(global_error_string)
    
    combined_data = {"logs": logs_data, "errors": errors}
    
    return jsonify(combined_data)


@app.route('/stop_bot', methods=['GET'])
def stop_bot():
    global keep_running
    keep_running = False
    global response_list
    response_list = []
    global global_error_string
    global_error_string = ""
    return render_template('runbot.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=9812)
