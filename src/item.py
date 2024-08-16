from helper import *
from search import *
from typing import Union

search = Search()

class Item:
    """
    An item that's in the market.
    """

    def __init__(self, user_input: Union[str, None], exact: bool=False, data: dict=all_name_to_id) -> None:

        if not user_input:
            self.name = None

        else:
            self.enhancement_level = search.get_enhancement_level(user_input)
            search_result = search.find_item(user_input, exact, data)
            print(search_result)

            self.id = list(search_result.keys())[0]
            self.name = list(search_result.values())[0]

            sublist_response = get_world_market_sub_list(self.id)
            self.sid = search.get_sid(sublist_response, self.enhancement_level)

            market_data = self._extract_market_data(sublist_response)
            self.current_stock = market_data['currentStock']
            self.base_price = market_data['basePrice']
            self.price_max = market_data['priceMax']
            self.price_min = market_data['priceMin']
            self.last_sold_price = market_data['lastSoldPrice']
            self.price = market_data['lastSoldPrice']
            self.last_sold_time = datetime_formatted(market_data['lastSoldTime'])
            self.bidding_info = self._extract_bidding_info()

    def get_min_listed_and_max_bidder(self) -> dict:
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

    def deliverable(self) -> str:
        '''
        Returns market summary of item, to be sent as an embed to Discord.
        '''
        bidding_info = self.get_min_listed_and_max_bidder()
        listed = f"{bidding_info['min_list_count']:,} listed @{bidding_info['min_list_price']:,}" if bidding_info['min_list_price'] is not None else "N/A"
        
        order = "order" if bidding_info['max_bid_count'] is not None and bidding_info['max_bid_count'] == 1 else "orders"
        bid = f"{bidding_info['max_bid_count']:,} {order} @{bidding_info['max_bid_price']:,}" if bidding_info['max_bid_price'] is not None else "N/A"
        
        name = f"{self.enhancement_level.upper()}: {self.name}" if self.enhancement_level is not None else self.name

        s = f"Item: **{name}**\n"\
            f"Listed: **{self.current_stock:,}**\n"\
            f"Base Price: **{self.base_price:,}**\n"\
            f"Last sold time: **{self.last_sold_time} EDT**\n"\
            f"Last sold price: **{self.last_sold_price:,}**\n\n"\
            f"Min price available: **{listed}**\n"\
            f"Max price bidder(s): **{bid}**\n\n"\
        
        return s

    def _extract_market_data(self, response: list) -> dict:
        '''
        Takes response and puts data into a dictionary.
        '''
        data = response[self.sid]
        components = data.split('-')
        item = {}
        for i, info in enumerate(components):
            item[response_data_structure[str(i)]] = int(info)
        return item

    def _extract_bidding_info(self) -> list:
        '''
        Performs API call and puts data into a list.
        '''
        bidding_info_response = get_bidding_info_list(self.id, self.sid)
        bidding_info = []
        for el in bidding_info_response:
            price_point = el.split('-')
            d = {'price': int(price_point[0]),
                'sellers': int(price_point[1]), 
                'buyers': int(price_point[2])}
            bidding_info.append(d)
        return bidding_info


class Craftable(Item):

    def __init__(self, user_input: str, mastery: int, verbose: bool) -> None:

        Item.__init__(self, user_input, data=craftable_name_to_id)

        query = {'name': self.name}
        data = items.find(query)[0]
        self.category = data['category']
        
        self.higher_grade = Item(data['higher_grade'], exact=True)

        recipes = data['all_recipes']
        self.recipes = {}
        self.substitutions = {}
        for recipe_number, recipe in recipes.items():
            recipe_object = Recipe(recipe)
            self.recipes[recipe_number] = recipe_object
            for ingredient, substitution in recipe_object.subsitutions.items():
                self.substitutions[ingredient] = substitution

        self.mastery = self._mastery_bracket(mastery)
        self.verbose = verbose

    def deliverable(self) -> str:
        '''
        Formats final recipe info string to be delivered as discord embed
        '''
        # Emotes
        item_value, cheapest_recipe, lowest_price = self._get_item_value_and_cheapest_recipe()
        profitability = item_value - lowest_price
        profit_emote = ':x:' if profitability < 0 else ':white_check_mark:'

        mastery_text = f"(per craft @{int(float(self.mastery))} mastery)" if 'Elixir' in self.category or 'Food' in self.category else ''

        all_ingredients = [ingredient.name for recipe_number in self.recipes for ingredient in self.recipes[recipe_number].recipe]
        longest_string = max(len(ingredient) for ingredient in all_ingredients)

        deliverable = f"Item: **{self.name} ({self.last_sold_price:,})**\n" if self.verbose else f"Item: **{self.name}**\n"
        deliverable += "Higher grade item: **N/A**\n" if not self.higher_grade.name else f"Higher grade item: **{self.higher_grade.name}**"
        deliverable += "\n" if not self.higher_grade.name or not self.verbose else f" **({self.higher_grade.price:,})**\n"
        deliverable += f"Profit margin: **{int(profitability):,}** {profit_emote} {mastery_text}\n\n"

        deliverable += "**Recipes**\n"

        for recipe_number, recipe in self.recipes.items():
            deliverable += f"```Recipe {recipe_number}*:\n" if int(recipe_number) == cheapest_recipe else f"```Recipe {recipe_number}:\n"

            for ingredient, quantity in recipe.recipe.items():
                deliverable += f"{ingredient.name.ljust(longest_string, '.')} x{quantity} ({ingredient.price:,})\n" if self.verbose else \
                                f"{ingredient.name.ljust(longest_string, '.')} x{quantity}\n"

            deliverable += "```\n"

        if self.substitutions:
            deliverable += "**Substitutions**\n"

        for ingredient_group, substitutes in self.substitutions.items():
            deliverable += f"```{ingredient_group}:\n"
            for substitute in substitutes:
                deliverable += f"    {substitute}\n"
            deliverable += "```\n"
        
        return deliverable

    def _mastery_bracket(self, mastery: int) -> str:
        '''
        Gets the mastery bracket based on a number.
        Mastery brackets range from 0 to 2000, at intervals of 50.
        Returns str instead of int/float because MongoDB only allows str as keys.
        '''
        floor = 0
        if mastery >= 2000:
            mastery = 2000
        elif mastery <= 0:
            mastery = 0
        else:
            floor = mastery % 50
        return str(float(mastery - floor))
    
    
class Vendor(Item):

    def __init__(self, input: str) -> None:
        self.name = input
        self.price = static_items[self.name]

    def deliverable(self) -> str:
        return f"Item: {self.name}\nVendor price: {self.price}"
    
class Drop(Item):

    def __init__(self, input: str) -> None:
        self.name = input
        self.price = 0

    def deliverable(self) -> str:
        return f"Item: {self.name}\nOnly obtained as loot."

class Recipe:
    
    def __init__(self, recipe: dict) -> None:
        self.recipe = {}
        self.subsitutions = {}
        for ingredient in recipe:
            quantity = recipe[ingredient]
            if ingredient in special:
                ingredient = special[ingredient]

            if ingredient in substitutions:
                self.subsitutions[ingredient] = substitutions[ingredient]
                ingredient = substitutions[ingredient][0]

            if ingredient in static_items:
                ingredient_item = Vendor(ingredient)
                self.recipe[ingredient_item] = quantity
                continue

            if ingredient.lower() not in [name.lower() for name in all_name_to_id]:
                ingredient_item = Drop(ingredient)
                self.recipe[ingredient_item] = quantity
                continue

            ingredient_item = Item(ingredient, exact=True)
            self.recipe[ingredient_item] = int(quantity)

    def __str__(self) -> str:
        result = ""
        for ingredient, quantity in self.recipe.items():
            result += f"{ingredient.name}: {quantity}\n"
        return result

if __name__ == "__main__":
    search = Search()
    input = "elixir death"
    exact = False
    data = all_name_to_id
    print(search.find_item(input, exact, data))

    
    