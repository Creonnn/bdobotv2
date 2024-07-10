from pymongo import MongoClient
from pymongo.collection import Collection
from dotenv import load_dotenv
import urllib, os, json, requests, ast, datetime
from unpack_bytes import unpack
from typing import Union


def load_json(path: str) -> dict:
    '''
    Read and load a JSON file.
    Returns data as Python Dictionary.
    '''
    with open(path, 'r') as file:
        data = json.load(file)
    return data

def get_mongo_collection(cluster_name: str, collection_name: str) -> Collection:
    '''
    Returns PyMongo collection given the cluster name and collection name.
    '''
    load_dotenv()
    password = urllib.parse.quote(os.getenv('PASSWORD'))
    uri = f"mongodb+srv://Creonnn:{password}@cluster0.3ataaai.mongodb.net/"
    cluster = MongoClient(uri)
    db = cluster[cluster_name]
    items = db[collection_name]
    return items

def get_world_market_sub_list(id: int) -> list:
    '''
    Gets the BDO world market sublist of item based on item id.
    The following data are provided from response:
        0 - Item ID
        1 - Enhancement range - min
        2 - Enhancement range - max
        3 - Base price
        4 - Current stock
        5 - Total trades
        6 - Price hard cap - min
        7 - Price hard cap - max
        8 - Last sale price
        9 - Last sale time
    Each attribute of the item is seperated by a hyphen (-). Each item is seperated by a pipe (|). 
    '''
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
    
    data = ast.literal_eval(response.text) # Converts string which is formatted as a dicionary to be an actual dictionary object
    data = data['resultMsg']
    data = data.split("|")

    return data[:-1]

def get_bidding_info_list(id: int, sid: int) -> list:
    '''
    Gets the BDO bidding info list on the item based on the id and sid of the item. sid usually represents
    the enhancement level of the item. If the item does not have enhancement levels, then sid=0.
    The following data are provided from response:
        0 - Price
        1 - Amount of sell orders
        2 - Amount of buy orders
    '''
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

def datetime_formatted(timestamp: int) -> datetime:
    '''
    Takes UNIX Epoche timestamp and turns it into human-readable time.
    '''
    time = datetime.datetime.fromtimestamp(timestamp)
    return time.strftime("%Y-%m-%d %H:%M:%S")

def substring_in_string_percentage(s1, s2):
    '''
    Ranks how s1 partially matches with s2.
    Rank of 0 means that none of the sub-strings of s1 is contained within s2. This is also the case if len(s1) > len(s2).
    Rank of 1 means that all of the sub-strings of s1 is contained within s2. 
    '''
    if len(s1) > len(s2):
        return 0
    strings_list = s1.lower().split(" ")
    substring_matches = 0

    for string in strings_list:
        if string in s2:
            substring_matches += 1

    return (substring_matches / len(s2.split(" "))) * 0.5 + (substring_matches / len(strings_list)) * 0.5

def query_misc_data(collection: Collection, name: str) -> Union[dict, list]:
    '''
    Gets misc data based on the "name" field.
    '''
    query = {'name': name}
    result = collection.find_one(query)
    data = result['data']
    return data

# Load static
misc_data = get_mongo_collection('bdobotv2', 'misc')
enhancement_levels = query_misc_data(misc_data, 'enhancement_levels')
response_data_structure = query_misc_data(misc_data, 'response_data_structure')
type_one = query_misc_data(misc_data, 'type_one')
type_two = query_misc_data(misc_data, 'type_two')
type_three = query_misc_data(misc_data, 'type_three')
type_four = query_misc_data(misc_data, 'type_four')
type_five = query_misc_data(misc_data, 'type_five')
cooking_mastery_dict = query_misc_data(misc_data, 'cooking_mastery')
alchemy_mastery_dict = query_misc_data(misc_data, 'alchemy_mastery')
substitutions = query_misc_data(misc_data, 'substitutions')
all_name_to_id = query_misc_data(misc_data, 'key')
special = query_misc_data(misc_data, 'special')
static_items = query_misc_data(misc_data, 'static_items')
cooking_exceptions = query_misc_data(misc_data, 'cooking_exceptions')
alchemy_exceptions = query_misc_data(misc_data, 'alchemy_exceptions')
items = get_mongo_collection('bdobotv2', 'craftable_items')
craftable_name_to_id = query_misc_data(misc_data, 'craftable_name_to_id')

if __name__ == '__main__':
    path = 'bot\cooking_mastery.json'
    print(load_json(path))