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

class Item:
    '''
    An item on the market.
    '''

    type_one = {'pri': 6, 'duo': 7, 'tri': 8, 'tet': 9, 'pen': 10} # Regular armor and weapon
    type_two = {'pri': 1, 'duo': 2, 'tri': 3, 'tet': 4, 'pen': 5} # Accessories
    type_three = {'desperate': 1, 'distorted': 2, 'silent': 3, 'wailing': 4, 'obliterating': 5} # Fallen god
    type_four = {'+1': 0, '+2': 0, '+3': 0, '+4': 0, '+5': 0, '+6': 0, '+7': 0, '+8': 1, '+9': 1, '+10': 1, '+11': 2, '+12': 2, '+13': 3, '+14': 4, '+15': 5} # Regular armor and weapon
    type_five = {'+1': 1, '+2': 2, '+3': 3, '+4': 4, '+5': 5} # e.g. Silver embroidered

    def __init__(self, id, enhancement_level):
        
        sublist_response = get_world_market_sub_list(id)

        self.enhancement_level = enhancement_level.lower() if enhancement_level is not None else None
        self.sid = self._get_sid(sublist_response)

        item = sublist_response[self.sid]
        self.name = item['name'] if enhancement_level is None or len(sublist_response) == 1 else f"{self.enhancement_level.upper()}: {item['name']}"
        self.current_stock = item['currentStock']
        self.base_price = item['basePrice'] # Need this to set upper bound when getting bidding info
        self.price_max = item['priceMax']
        self.price_min = item['priceMin']
        self.last_sold_price = item['lastSoldPrice']
        self.last_sold_time = utc_to_est_formatted(item['lastSoldTime'])

        biddinginfo_response = get_bidding_info_list(id, self.sid)
        self.bidding_info = biddinginfo_response['orders']

    def _get_sid(self, response):
        '''
        Returns the internal enhancement number based on the enhancement level. Returns None if enhancement level is not specified.
        '''
        if self.enhancement_level is None or len(response) == 1:
            sid = 0

        elif self.enhancement_level in Item.type_one.keys():
            sid = Item.type_one[self.enhancement_level] if len(response) > 10 else Item.type_two[self.enhancement_level]

        elif self.enhancement_level in Item.type_three.keys():
            sid = Item.type_three[self.enhancement_level]

        elif self.enhancement_level in Item.type_four.keys() and len(response) > 10:
            sid = Item.type_four[self.enhancement_level]

        else:
            sid = Item.type_five[self.enhancement_level]
        
        return sid

    def get_min_listed_and_max_bidder(self):
        '''
        Returns the minimum price that the item is listed at, and the quantity (if they exist).
        '''
        compare_price_listed = self.price_max # Price to compare to
        min_list_price = None # Lowest price in which the item is available, if it exists
        min_list_count = None # Quantity available at lowest price, if it exists

        compare_price_bid = self.price_min # Price to compare to
        max_bid_price = None # Greatest price in which there is a bidder for the item, if it exists
        max_bid_count = None # Number of bidders at the max bid price, if it exists

        for price_point in self.bidding_info:
            if price_point['sellers'] != 0 and price_point['price'] <= compare_price_listed:
                compare_price_listed = price_point['price']
                min_list_price = price_point['price']
                min_list_count = price_point['sellers']

            if price_point['buyers'] != 0 and price_point['price'] >= compare_price_bid:
                compare_price_bid = price_point['price']
                max_bid_price = price_point['price']
                max_bid_count = price_point['buyers']
            

        return {'min_list_price': min_list_price, 'min_list_count': min_list_count, \
                'max_bid_price': max_bid_price, 'max_bid_count': max_bid_count}

    def message(self, warning):
        '''
        Returns market summary of item, to be sent as an embed to Discord.
        '''
        bidding_info = self.get_min_listed_and_max_bidder()
        listed = f"{bidding_info['min_list_count']:,} listed @{bidding_info['min_list_price']:,}" if bidding_info['min_list_price'] is not None else "N/A"
        bid = f"{bidding_info['max_bid_count']:,} orders @{bidding_info['max_bid_price']:,}" if bidding_info['max_bid_price'] is not None else "N/A"


        s = f"Item: **{self.name}**\n"\
            f"Listed: **{self.current_stock:,}**\n"\
            f"Base Price: **{self.base_price:,}**\n\n"\
            f"Min listed: **{listed}**\n"\
            f"Max bidder: **{bid}**\n\n"\
            f"{warning}"
        
        return s

class SearchTerm:
    '''
    Parse user's search terms and get relevant info.
    '''
    name_to_id = get_name_to_id()
    enhancement_levels = ['pri', 'duo', 'tri', 'tet', 'pen', 'desperate', 'distorted', 'silent', 'wailing', 'obliterating',\
                          '+1', '+2', '+3', '+4', '+5', '+6', '+7', '+8', '+9', '+10', '+11', '+12', '+13', '+14', '+15']

    def __init__(self, term):
        '''
        term: User's search term.
        '''
        term = term.strip()
        term = term.lower()

        self.term = term

    def _substrings_in_item_name(self, market_item):
        '''
        Returns True if all substrings in search term belongs in market item.
        Rreturns False otherwise.
        '''
        strings_list = self.item_name().split(" ")
        substrings_in_name = {substring: substring in market_item for substring in strings_list}
        all_substrings_in_name = all(substrings_in_name.values())
        return all_substrings_in_name

    def enhancement_level(self):
        '''
        Returns the enhancement level. If enhancement level is not specified by user, returns None.

        Example 1:
        >>>user_input = "tet blackstar vediant"
        >>>term = SearchTerm(user_input)
        >>>term.get_enhancement_level()
        >>>"tet"

        Example 2:
        >>>user_input = "corn"
        >>>term = SearchTerm(user_input)
        >>>term.get_enhancement_level()
        >>>None
        '''
        # Get the first substring in string
        check = self.term.split(" ")[0]

        # Check if the first substring is an enhancement level
        for enhancement_level in SearchTerm.enhancement_levels:
            if enhancement_level == check:
                return enhancement_level
        
        return None
    
    def item_name(self):
        '''
        Returns the base item name.
        Example:
        >>>user_input = "tet blackstar vediant"
        >>>term = SearchTerm(user_input)
        >>>term.get_item_name()
        >>>"blackstar vediant"
        '''

        # Remove enhancement level (if it was specified) from search term to get item name
        if self.enhancement_level() is not None:
            substrings = self.term.split(" ")
            item_name = " ".join(substrings[1:])

        else:
            item_name = self.term
        
        return item_name

    def get_ids(self):
        '''
        Gets ids of all partial matches based on search term. 
        '''
        exact_ids = []
        partial_ids = []

        for name, id in SearchTerm.name_to_id.items():
            name = name.lower()

            # Check for exact matches
            if self.item_name() == name:
                exact_ids.append(id)
            
            # Check for partial matches
            if self._substrings_in_item_name(name):
                partial_ids.append(id)

        return exact_ids, partial_ids


if __name__ == "__main__":
    user_input = "black stone"
    term = SearchTerm(user_input)
    exact, partial = term.get_ids()
    enhancement_level = term.enhancement_level()
    if len(exact) == 1:
        item = Item(exact[0], enhancement_level)
        print(item.message(""))
    else:
        for id in partial:
            item = Item(id, enhancement_level)
            print(item.message(""))