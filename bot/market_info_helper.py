import json
import datetime
import pytz
import requests
import ast
from market.unpack_bytes import unpack
from market.unpack_bytes import unpack

def combine_dictionaries(dict_list):
    '''
    Converts a list of dictionaries into a single dictionary.
    '''
    combined_dict = {k: v for d in dict_list for k, v in d.items()}
    return combined_dict

def get_name_to_id():
    path = r"bot\key.json"
    with open(path, 'r') as file:
        data = json.load(file)
        combined_dict = combine_dictionaries(data)
    return combined_dict

def utc_to_est_formatted(timestamp):
    time = datetime.datetime.fromtimestamp(timestamp)
    return time.strftime("%Y-%m-%d %H:%M:%S")

def get_world_market_sub_list(id):
    sub_list_url = "https://na-trade.naeu.playblackdesert.com/Trademarket/GetWorldMarketSubList"
    headers = {
    "Content-Type": "application/json",
    "User-Agent": "BlackDesert"
    }
    payload = {
    "keyType": 0,
    "mainKey": id
    }
    response = requests.request('POST', sub_list_url, json=payload, headers=headers)
    data = ast.literal_eval(response.text) # Converts string which is formatted as a dicionary to be an actual disctionary object
    data = data['resultMsg']
    data = data.split("|")

    return data[:-1]

def get_bidding_info_list(id, sid):

    bidding_info_url = 'https://na-trade.naeu.playblackdesert.com/Trademarket/GetBiddingInfoList'
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "BlackDesert"
        }
    payload = {
    "keyType": 0,
    "mainKey": id,
    "subKey": sid
    }
    response = requests.request('POST', bidding_info_url, json=payload, headers=headers)
    data = unpack(response.content)
    data = data.split('|')
    
    return data[:-1]

def get_market_price_info(id, sid):
    url = 'https://na-trade.naeu.playblackdesert.com/Trademarket/GetMarketPriceInfo'
    headers = {
    "Content-Type": "application/json",
    "User-Agent": "BlackDesert"
    }
    payload = {
    "keyType": 0,
    "mainKey": id,
    "subKey": sid
    }
    response = requests.request('POST', url, json=payload, headers=headers)
    data = ast.literal_eval(response.text)
    data = data['resultMsg']
    data = data.split("-")
    data = [int(el) for el in data]
    return data

def get_highest_base_price(items):
    greatest_base_price = -1
    for item in items:
        if item.base_price > greatest_base_price:
            greatest_base_price = item.base_price
            greatest_base_price_item = item
    return greatest_base_price_item

if __name__ == "__main__":
    '''
    id = 10212
    print(get_world_market_sub_list(id))
    '''
    id = 10212
    data = get_market_price_info(id, 0)
    print(len(data))
    pass