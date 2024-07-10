from market_recipe_helpers import *
from typing import Union

class Item:

    def get_enhancement_level(self, input):
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
        check = input.split(" ")[0]

        # Check if the first substring is an enhancement level
        for enhancement_level in enhancement_levels:
            if enhancement_level == check:
                return enhancement_level
        
        return
    
    def get_item_search_term(self, input):
        '''
        Returns the intended search term.
        i.e. Removes additional specifications from input, mainly (really, only) the enhancement level.

        PARAMS:
        input: Raw user input

        Example:
        >>>user_input = "tet blackstar vediant"
        >>>term = SearchTerm(user_input)
        >>>term.get_item_name()
        >>>"blackstar vediant"
        '''

        # Remove enhancement level (if it was specified) from search term to get item name
        if self.get_enhancement_level(input):
            substrings = input.split()
            item_name = " ".join(substrings[1:])
            return item_name

        return input

    def get_id_and_name(self, item_search_term: str, data: dict) -> dict:
        '''
        Gets id and name based on the best partially matched item based on item_search_term.
        PARAMS:
        item_search_term: The search term to be compared with official item names.
        data: Contains official item names to be used in the initialization stage.
        '''
        match_percent = 0
        for name, id in data.items():
            percent = substring_in_string_percentage(item_search_term, name.lower())
            if percent >= match_percent:
                best_match_name = name
                best_match_ID = id
                match_percent = percent
        return {best_match_ID: best_match_name}
    
    def get_exact_id_and_name(self, item_search_term: str, data: dict) -> dict:
        '''
        Gets id and name of only exact matches based on item_search_term.
        item_search_term: The search term to be compared with official item names.
        data: Contains official item names to be used in the initialization stage.
        '''
        for name, id in data.items():
            if item_search_term.lower() == name.lower():
                return {id: name}
        return {}

    def deliverable(self):
        '''
        String to be included in the embed that will be sent as a Discord message.
        '''
        raise NotImplementedError

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

class Market(Item):

    def __init__(self, user_input: str, exact: bool=False, data: dict=all_name_to_id) -> None:

        if user_input is None:
            self.name = None

        else:
            self.enhancement_level = Item.get_enhancement_level(self, user_input)
            search_result = self._find_item(user_input, exact, data)
            self.id = list(search_result.keys())[0]
            self.name = list(search_result.values())[0]

            sublist_response = get_world_market_sub_list(self.id)
            self.sid = self._get_sid(sublist_response)

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

    def _find_item(self, input: str, exact: bool, data: dict) -> dict:
        '''
        Takes in raw user input and extracts the intended search terms. 
        Then, finds the best partially matches or exact match of official item names.

        PARAMS:
        input: Raw user input
        exact: Specifies whether to use partial or exact match 
        '''
        item_search_term = Item.get_item_search_term(self, input)
        search_result = Item.get_id_and_name(self, item_search_term, data) if not exact else Item.get_exact_id_and_name(self, item_search_term, data)

        return search_result

    def _extract_market_data(self, response: list) -> dict:
        '''
        Takes API response and puts data into a dictionary.
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

    def _get_sid(self, response: list) -> int:
        '''
        Returns the internal enhancement number based on the enhancement level. Returns None if enhancement level is not specified.
        '''
        if self.enhancement_level is None or len(response) == 1:
            sid = 0

        elif self.enhancement_level in type_one.keys():
            sid = type_one[self.enhancement_level] if len(response) > 10 else type_two[self.enhancement_level]

        elif self.enhancement_level in type_three.keys():
            sid = type_three[self.enhancement_level]

        elif self.enhancement_level in type_four.keys() and len(response) > 10:
            sid = type_four[self.enhancement_level]

        else:
            sid = type_five[self.enhancement_level]
        
        return sid
    
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

            ingredient_item = Market(ingredient)
            self.recipe[ingredient_item] = int(quantity)

    def __str__(self) -> str:
        result = ""
        for ingredient, quantity in self.recipe.items():
            result += f"{ingredient.name}: {quantity}\n"
        return result

class Craftable(Market):

    def __init__(self, user_input: str, mastery: int, verbose: bool) -> None:
        Market.__init__(self, user_input, data=craftable_name_to_id)

        query = {'name': self.name}
        data = items.find(query)[0]
        self.category = data['category']
        
        self.higher_grade = Market(data['higher_grade'], exact=True)

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
        item_value, cheapest_recipe, lowest_price = self.get_item_value_and_cheapest_recipe()
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
    
    def _cooking_mastery(self) -> tuple[dict, dict]:
        '''
        Returns average cooking rates based on cooking mastery.
        '''
        name = self.name.lower()
        mastery_mult = cooking_mastery_dict[self.mastery]

        # For items with proc exceptions
        if name in cooking_exceptions.keys():
            return cooking_exceptions[name], mastery_mult
        
        return {'reg_base': 2.5, 'reg_mult': 1.5, 'rare_base': 1.5, 'rare_mult': 0.5, 'rare_proc_base_chance': 0.2}, mastery_mult

    def _alchemy_mastery(self) -> tuple[dict, dict]:
        '''
        Returns average alchemy rates based on alchemy mastery.
        '''
        name = self.name.lower()
        mastery_mult = alchemy_mastery_dict[self.mastery]

        # For items that can only proc once per craft
        if 'perfume' in name or 'draught' in name or 'deep sea' in name or\
            'indignation' in name or 'khalk' in name or 'sturdy whale tendon elixir' == name or\
            'sturdy whale tendon potion' == name or 'elixir of regeneration' == name:
            return {'reg_base': 1, 'reg_mult': 0, 'rare_base': 0, 'rare_mult': 0}, mastery_mult
        
        # For items with different proc rates than the norm
        elif name in alchemy_exceptions.keys():
            return alchemy_exceptions[name], mastery_mult
    
        return {'reg_base': 2.5, 'reg_mult': 1.5, 'rare_base': 0.3, 'rare_mult': 0}, mastery_mult
    
    def get_cooking_item_value(self) -> Union[int, float]:
        '''
        Returns the item value as a result from one cooking proc.
        '''
        rates, mastery_multiplers = self._cooking_mastery()

        reg_price = self.last_sold_price
        rare_price = 0 if self.higher_grade.name is None else self.higher_grade.last_sold_price

        reg_base_proc = rates['reg_base']
        reg_additional_proc = rates['reg_mult']
        reg_additional_proc_chance = mastery_multiplers["Regular Max Proc Chance"]

        rare_base_proc = rates['rare_base']
        rare_additional_proc = rates['rare_mult']
        rare_additional_proc_chance = mastery_multiplers["Regular Max Proc Chance"]
        rare_proc_base_chance = rates['rare_proc_base_chance']
        rare_proc_additional_chance = mastery_multiplers['Rare Add. Chance']

        item_value = reg_price * (reg_base_proc + reg_additional_proc * reg_additional_proc_chance) + \
        rare_price * (rare_base_proc + rare_additional_proc * rare_additional_proc_chance) * (rare_proc_base_chance + rare_proc_additional_chance)
        
        return item_value
    
    def get_alchemy_item_value(self) -> Union[int, float]:
        '''
        Returns the item value as a result from one alchemy proc.
        '''
        rates, mastery_multiplers = self._alchemy_mastery()

        reg_price = self.last_sold_price
        rare_price = 0 if self.higher_grade.name is None else self.higher_grade.last_sold_price

        reg_base_proc = rates['reg_base']
        reg_max_proc_multiplier = rates['reg_mult']
        reg_max_proc_chance_multiplier = mastery_multiplers["Max Proc Chance"]

        rare_base_proc = rates['rare_base']


        item_value = reg_price * (reg_base_proc + reg_max_proc_multiplier * reg_max_proc_chance_multiplier) +\
                    rare_price * (rare_base_proc)

        return item_value
    
    def get_cheapest_recipe(self) -> tuple[str, Union[int, float]]:
        '''
        Returns the cheapest recipe and the cost of the recipe, given a list of different recipes that crafts the same item.
        '''
        cheapest_recipe = None
        lowest_price = None
        compare_price = 0

        for recipe_number in self.recipes:

            for ingredient, quantity in self.recipes[recipe_number].recipe.items():
                compare_price += quantity * ingredient.price

            if lowest_price is None:
                cheapest_recipe = recipe_number
                lowest_price = compare_price

            elif compare_price < lowest_price:
                cheapest_recipe = recipe_number
                lowest_price = compare_price
            compare_price = 0

        return cheapest_recipe, lowest_price
    
    def get_item_value_and_cheapest_recipe(self) -> tuple[Union[int, float], Union[int, float], Union[int, float]]:
        '''
        Gets price of item, the cheapest recipe to craft the item (if there are multiple recipes), and the cost of using cheapest recipe.
        '''
        cheapest_recipe, lowest_price = self.get_cheapest_recipe()
        if self.category == 'Food':
            item_value = self.get_cooking_item_value()
                
        elif 'elixir' in self.category.lower():
            item_value = self.get_alchemy_item_value()

        elif self.category == 'Material':
            item_value = 0 if self.name is None else self.last_sold_price * 2.5

        else:
            item_value = 0 if self.name is None else self.last_sold_price

        return item_value, cheapest_recipe, lowest_price

if __name__ == "__main__":

    input = "elixir death"
    item = Craftable(input, 1000, True)

    print(item.deliverable())

    
    