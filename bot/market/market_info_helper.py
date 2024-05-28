import json
import datetime
import pytz
import requests

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
    datetime_utc = datetime.datetime.fromtimestamp(timestamp / 1000)
    eastern_tz = pytz.timezone('US/Eastern')
    datetime_local = datetime_utc.replace(tzinfo=pytz.utc).astimezone(eastern_tz)
    return datetime_local.strftime("%Y-%m-%d %H:%M:%S %Z")

def get_world_market_sub_list(id):
    SubList_url = f"https://api.arsha.io/v2/na/GetWorldMarketSubList?id={id}&lang=en"
    response = requests.get(SubList_url)
    data = response.json()
    if not isinstance(data, list):
        data = [data]
    return data

def get_bidding_info_list(id, sid):
    BiddingInfo_url = f'https://api.arsha.io/v2/na/GetBiddingInfoList?id={id}&sid={sid}&lang=en'
    response = requests.get(BiddingInfo_url)
    data = response.json()
    
    return data

def get_highest_base_price(items):
    greatest_base_price = -1
    for item in items:
        if item.base_price > greatest_base_price:
            greatest_base_price = item.base_price
            greatest_base_price_item = item
    return greatest_base_price_item
