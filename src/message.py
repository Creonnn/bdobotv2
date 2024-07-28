
from market_recipe import Item, Craftable
from market_recipe_helpers import cooking_mastery_dict, cooking_exceptions,alchemy_mastery_dict, alchemy_exceptions
from typing import Union

class Message:
    
    def deliverable():
        raise NotImplementedError
    
class Item(Message):

    def deliverable(self, item: Item) -> str:
        '''
        Returns market summary of item, to be sent as an embed to Discord.
        '''
        bidding_info = self._get_min_listed_and_max_bidder(item)

        name = self._name_text(item)
        listed = self._listed_text(bidding_info)
        bid = self._bid_text(bidding_info)
        

        s = f"Item: **{name}**\n"\
            f"Listed: **{item.current_stock:,}**\n"\
            f"Base Price: **{item.base_price:,}**\n"\
            f"Last sold time: **{item.last_sold_time} EDT**\n"\
            f"Last sold price: **{item.last_sold_price:,}**\n\n"\
            f"Min price available: **{listed}**\n"\
            f"Max price bidder(s): **{bid}**\n\n"\
        
        return s
    
    def _listed_text(self, info: dict) -> str:
        return f"{info['min_list_count']:,} listed @{info['min_list_price']:,}" if info['min_list_price'] is not None else "N/A"
    
    def _bid_text(self, info: dict) -> str:
        order = "order" if info['max_bid_count'] is not None and info['max_bid_count'] == 1 else "orders"
        return f"{info['max_bid_count']:,} {order} @{info['max_bid_price']:,}" if info['max_bid_price'] is not None else "N/A"
    
    def _name_text(self, item: Item) -> str:
        return f"{item.enhancement_level.upper()}: {item.name}" if item.enhancement_level is not None else item.name
    
    def _get_min_listed_and_max_bidder(self, item: Item) -> dict:
        '''
        Returns the minimum price that the item is listed at, and the quantity (if they exist).
        '''
        compare_price_listed = item.price_max # Price to compare to
        min_list_price = None # Lowest price in which the item is available, if it exists
        min_list_count = None # Quantity available at lowest price, if it exists

        compare_price_bid = item.price_min # Price to compare to
        max_bid_price = None # Greatest price in which there is a bidder for the item, if it exists
        max_bid_count = None # Number of bidders at the max bid price, if it exists

        for price_point in item.bidding_info:
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

class Craftable(Message):
    
    def deliverable(self, item: Craftable):
        '''
        Formats final recipe info string to be delivered as discord embed
        '''
        # Emotes
        item_value, cheapest_recipe, lowest_price = self._get_item_value_and_cheapest_recipe(item)
        profitability = item_value - lowest_price
        profit_emote = self._profit_emote(profitability)

        mastery_text = self._mastery_text(item)

        longest_string = self._longest_string(item)

        deliverable = self._name_text(item)
        deliverable += self._higher_grade_text(item)
        deliverable += self._higher_grade_text(item)
        deliverable += self._profit_margin_text(profitability, profit_emote, mastery_text)
        deliverable += "**Recipes**\n"
        deliverable += self._recipe_text(item, longest_string, cheapest_recipe)

        if item.substitutions:
            deliverable += "**Substitutions**\n"
            deliverable += self._substitution_text(item)
        
        return deliverable
    
    def _profit_emote(self, profit: int) -> str:
        return ':x:' if profit < 0 else ':white_check_mark:'
    
    def _mastery_text(self, item: Item) -> str:
        return f"(per craft @{int(float(item.mastery))} mastery)" if 'Elixir' in item.category or 'Food' in item.category else ''
    
    def _name_text(self, item: Item) -> str:
        return f"Item: **{item.name} ({item.last_sold_price:,})**\n" if item.verbose else f"Item: **{item.name}**\n"
    
    def _higher_grade_text(self, item: Item) -> str:
        s = "Higher grade item: **N/A**\n" if not item.higher_grade.name else f"Higher grade item: **{item.higher_grade.name}**"
        s += "\n" if not item.higher_grade.name or not item.verbose else f" **({item.higher_grade.price:,})**\n"
        return s
    
    def _profit_margin_text(self, profitability: Union[int, float], profit_emote: str, mastery_text: str) -> str:
        return f"Profit margin: **{int(profitability):,}** {profit_emote} {mastery_text}\n\n"
    
    def _recipe_text(self, item: Item, longest_string: int, cheapest_recipe: int) -> str:
        s = ""
        for recipe_number, recipe in item.recipes.items():
            s += f"```Recipe {recipe_number}*:\n" if int(recipe_number) == cheapest_recipe else f"```Recipe {recipe_number}:\n"

            for ingredient, quantity in recipe.recipe.items():
                s += f"{ingredient.name.ljust(longest_string, '.')} x{quantity} ({ingredient.price:,})\n" if item.verbose else \
                                f"{ingredient.name.ljust(longest_string, '.')} x{quantity}\n"

            s += "```\n"

        return s
    
    def _substitution_text(self, item: Item) -> str:
        s = ""
        for ingredient_group, substitutes in item.substitutions.items():
            s += f"```{ingredient_group}:\n"
            for substitute in substitutes:
                s += f"    {substitute}\n"
            s += "```\n"

        return s

    def _longest_string(self, item: Item) -> int:
        all_ingredients = [ingredient.name for recipe_number in item.recipes for ingredient in item.recipes[recipe_number].recipe]
        return max(len(ingredient) for ingredient in all_ingredients)

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
    
    def _cooking_mastery(self, item: Item) -> tuple[dict, dict]:
        '''
        Returns average cooking rates based on cooking mastery.
        '''
        name = item.name.lower()
        mastery_mult = cooking_mastery_dict[item.mastery]

        # For items with proc exceptions
        if name in cooking_exceptions.keys():
            return cooking_exceptions[name], mastery_mult
        
        return {'reg_base': 2.5, 'reg_mult': 1.5, 'rare_base': 1.5, 'rare_mult': 0.5, 'rare_proc_base_chance': 0.2}, mastery_mult

    def _alchemy_mastery(self, item: Item) -> tuple[dict, dict]:
        '''
        Returns average alchemy rates based on alchemy mastery.
        '''
        name = item.name.lower()
        mastery_mult = alchemy_mastery_dict[item.mastery]

        # For items with different proc rates than the norm
        if name in alchemy_exceptions.keys():
            return alchemy_exceptions[name], mastery_mult

        # For items that can only proc once per craft
        elif 'perfume' in name or 'draught' in name or 'deep sea' in name or\
            'indignation' in name or 'khalk' in name or 'sturdy whale tendon elixir' == name or\
            'sturdy whale tendon potion' == name or 'elixir of regeneration' == name or\
            ("party" in name and "harmony" in name):
            return {'reg_base': 1, 'reg_mult': 0, 'rare_base': 0, 'rare_mult': 0}, mastery_mult
        
        return {'reg_base': 2.5, 'reg_mult': 1.5, 'rare_base': 0.3, 'rare_mult': 0}, mastery_mult
    
    def _get_cooking_item_value(self, item: Item) -> Union[int, float]:
        '''
        Returns the item value as a result from one cooking proc.
        '''
        rates, mastery_multiplers = item._cooking_mastery()

        reg_price = item.last_sold_price
        rare_price = 0 if item.higher_grade.name is None else item.higher_grade.last_sold_price

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
    
    def _get_alchemy_item_value(self, item: Item) -> Union[int, float]:
        '''
        Returns the item value as a result from one alchemy proc.
        '''
        rates, mastery_multiplers = item._alchemy_mastery()

        reg_price = item.last_sold_price
        rare_price = 0 if item.higher_grade.name is None else item.higher_grade.last_sold_price

        reg_base_proc = rates['reg_base']
        reg_max_proc_multiplier = rates['reg_mult']
        reg_max_proc_chance_multiplier = mastery_multiplers["Max Proc Chance"]

        rare_base_proc = rates['rare_base']


        item_value = reg_price * (reg_base_proc + reg_max_proc_multiplier * reg_max_proc_chance_multiplier) +\
                    rare_price * (rare_base_proc)

        return item_value
    
    def _get_cheapest_recipe(self, item: Item) -> tuple[str, Union[int, float]]:
        '''
        Returns the cheapest recipe and the cost of the recipe, given a list of different recipes that crafts the same item.
        '''
        cheapest_recipe = None
        lowest_price = None
        compare_price = 0

        for recipe_number in item.recipes:

            for ingredient, quantity in item.recipes[recipe_number].recipe.items():
                compare_price += quantity * ingredient.price

            if lowest_price is None:
                cheapest_recipe = recipe_number
                lowest_price = compare_price

            elif compare_price < lowest_price:
                cheapest_recipe = recipe_number
                lowest_price = compare_price
            compare_price = 0

        return cheapest_recipe, lowest_price
    
    def _get_item_value_and_cheapest_recipe(self, item: Item) -> tuple[Union[int, float], Union[int, float], Union[int, float]]:
        '''
        Gets price of item, the cheapest recipe to craft the item (if there are multiple recipes), and the cost of using cheapest recipe.
        '''
        cheapest_recipe, lowest_price = self._get_cheapest_recipe(item)
        if item.category == 'Food':
            item_value = self._get_cooking_item_value(item)
                
        elif 'elixir' in item.category.lower():
            item_value = self._get_alchemy_item_value(item)

        elif item.category == 'Material':
            item_value = 0 if not item.name else item.last_sold_price * 2.5

        else:
            item_value = 0 if not item.name else item.last_sold_price

        return item_value, cheapest_recipe, lowest_price
    

if __name__ == "__main__":
    ...