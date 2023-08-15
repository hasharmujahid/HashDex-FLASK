import asyncio
import aiohttp
import requests
from stellar_sdk import Keypair
from datetime import datetime
from flask import Flask, render_template, request, jsonify , Markup
from flask import *
from flask import Flask, render_template, request
from stellar_sdk import Server, Keypair, Network, TransactionBuilder, Asset
import time
import argparse
import random
from stellar_sdk import Server, Keypair, Network, TransactionBuilder, Asset
from stellar_sdk.client.requests_client import RequestsClient
import datetime
import json
import argparse
import random
import os
import time
import threading

client = RequestsClient(num_retries=0, post_timeout=16)
class Bot():
    # ... Your existing Bot class definition ...
    def __init__(self):
        pub_secret_key = "SDWDCAW64U7JEEWTA2CMACADKLQUMC3OU4QQLOCU6FKXDB63YA2CXBVH"
        destination_account_id = ''
        self.BASE_FEE = 10000
        from_asset = Asset('8181','GBI3UEIFLFQ4TGH53DM3BQLHXHYTGTNZYEY2CLMQU64XUH5I5EQJW6DE')
        dest_asset = Asset('AQUA', 'GBNZILSTVQZ4R7IKQDGHYGY2QXL5QOFJYQMXPKWRRM5PAV7Y4M67AQUA')
        self.horizon_servers = ['https://horizon.stellar.org/', 'https://horizon.stellar.lobstr.co', 'https://h.fchain.io/','http://144.91.100.250:8000/','http://149.102.142.236:8000/']
        self.server_index = random.randint(0,3)
        self.server = Server(horizon_url=self.horizon_servers[self.server_index], client=client)
        self.passphrase = Network.PUBLIC_NETWORK_PASSPHRASE
        self.source_asset = from_asset
        self.destination_asset = dest_asset
        self.keypair = Keypair.from_secret(pub_secret_key)
        self.destination_account_id = destination_account_id
        self.name = "Bot"
      
    def get_optimal_path_receive(self, dest_amount):
        
        paths = self.server.strict_receive_paths(
            destination_asset=self.destination_asset,
            destination_amount=dest_amount,
            source=[self.source_asset],
        ).call()
        first_path = paths['_embedded']['records'][0]
        optimal_path = []
        for item in first_path['path']:
            if item['asset_type'] == 'native':
                optimal_path.append(Asset.native())
            else:
                optimal_path.append(Asset(item['asset_code'], item['asset_issuer']))
        return optimal_path

    def get_optimal_path(self, send_amount):
        
        paths = bot.server.strict_send_paths(
            source_asset=self.source_asset,
            source_amount=send_amount,
            destination=[self.destination_asset],
        ).call()
        first_path = paths['_embedded']['records'][0]
        optimal_path = []
        for item in first_path['path']:
            if item['asset_type'] == 'native':
                optimal_path.append(Asset.native())
            else:
                optimal_path.append(Asset(item['asset_code'], item['asset_issuer']))
        return optimal_path
        
    def path_payment_send_trade(self, send_amount, dest_min):
        optimal_path = self.get_optimal_path(send_amount)
        for i in optimal_path:
            print(i)
        account = self.server.load_account(account_id=self.keypair.public_key)
        transaction = (
            TransactionBuilder(
                source_account=account,
                network_passphrase=self.passphrase,
                base_fee=self.BASE_FEE,
            )
            .append_path_payment_strict_send_op(
                destination=self.destination_account_id,  # sending to ourselves
                send_asset=self.source_asset,
                send_amount=send_amount,
                dest_asset=self.destination_asset,
                dest_min=dest_min,
                path=optimal_path,
            )
            .set_timeout(80)
            .build()
        )

        # Sign and submit the transaction
        print('[X]: Submitting Using Path Payment Strict Send : ')
        transaction.sign(self.keypair)
        response = self.server.submit_transaction(transaction)
        return response
    
    def switch_to_next_server(self):
        new_server_index = random.randint(0,3)
        if self.server_index != new_server_index:
            print(f"[X] Switching server from {self.horizon_servers[self.server_index]} to {self.horizon_servers[new_server_index]}")
            self.server_index = new_server_index
            self.server = Server(horizon_url=self.horizon_servers[self.server_index], client=client)
        else:
            new_server_index = random.randint(0,3)
            print(f"[X] Switching server from {self.horizon_servers[self.server_index]} to {self.horizon_servers[new_server_index]}")
            self.server_index = new_server_index
            self.server = Server(horizon_url=self.horizon_servers[self.server_index], client=client)
            
    def trade_path_payment_strict_receive(self, dest_amount, send_max_amount):
        optimal_path = self.get_optimal_path_receive(dest_amount)

        for i in optimal_path:
            print(i)

        account = self.server.load_account(account_id=self.keypair.public_key)
        transaction = (
            TransactionBuilder(
                source_account=account,
                network_passphrase=self.passphrase,
                base_fee=self.BASE_FEE,
            )
            .append_path_payment_strict_receive_op(
                destination=self.destination_account_id,
                dest_asset=self.destination_asset,
                dest_amount=dest_amount,
                send_asset=self.source_asset,
                send_max=send_max_amount,  # Use the provided send_max_amount
                path=optimal_path,
            )
            .set_timeout(80)
            .build()
        )

        print('Submitting using Strict Recieve')
        transaction.sign(self.keypair)
        response = self.server.submit_transaction(transaction)
        return response
    
    def trade_path_payment_strict_receive_custom(self,custom_path, dest_amount, send_max_amount):
        optimal_path = custom_path

        account = self.server.load_account(account_id=self.keypair.public_key)
        transaction = (
            TransactionBuilder(
                source_account=account,
                network_passphrase=self.passphrase,
                base_fee=self.BASE_FEE,
            )
            .append_path_payment_strict_receive_op(
                destination=self.destination_account_id,
                dest_asset=self.destination_asset,
                dest_amount=dest_amount,
                send_asset=self.source_asset,
                send_max=send_max_amount,  # Use the provided send_max_amount
                path=optimal_path,
            )
            .set_timeout(80)
            .build()
        )

        print('Submitting using Custom Strict Recieve')
        transaction.sign(self.keypair)
        response = self.server.submit_transaction(transaction)
        print("Successfully Submitted")
        return response
    
    def path_payment_send_trade_custom(self, custom_path,send_amount, dest_min):
        optimal_path=custom_path
        account = self.server.load_account(account_id=self.keypair.public_key)
        transaction = (
            TransactionBuilder(
                source_account=account,
                network_passphrase=self.passphrase,
                base_fee=self.BASE_FEE,
            )
            .append_path_payment_strict_send_op(
                destination=self.destination_account_id,  # sending to ourselves
                send_asset=self.source_asset,
                send_amount=send_amount,
                dest_asset=self.destination_asset,
                dest_min=dest_min,
                path=optimal_path,
            )
            .set_timeout(80)
            .build()
        )

        # Sign and submit the transaction
        print('[X]: Submitting Using Custom Path Payment Strict Send : ')
        transaction.sign(self.keypair)
        response = self.server.submit_transaction(transaction)
        return response
# Create a bot instance
bot = Bot()
