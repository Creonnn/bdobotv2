from bot.market import market_info

# Items with static price

static_items = {"Salt": 20, "Sugar": 20, "Leavening Agent": 20, "Cooking Oil": 20, "Olive Oil": 40, "Deep Frying Oil": 40,\
                "Cooking Wine": 40, "Base Sauce": 40, "Mineral Water": 30}

def format_recipes_dictionary(recipes):
    new_recipes_dictionary = {}
    for recipe_number, recipe in recipes.items():
        recipe_number = int(recipe_number)
        new_recipes_dictionary[recipe_number] = {}
        for ingredient, quantity in recipe.items():
            if ingredient not in static_items.keys():
                ingredient_search = market_info.SearchTerm(ingredient)
                ingredient_search_result = ingredient_search.get_ids()
                ingredient_id = list(ingredient_search_result.keys())[0]
                ingredient_name = list(ingredient_search_result.values())[0]
                ingredient_item = market_info.Item(ingredient_id, ingredient_name, None)
                new_recipes_dictionary[recipe_number][ingredient_item] = quantity
            else: 
                new_recipes_dictionary[recipe_number][ingredient] = quantity
    return new_recipes_dictionary

def crafted_item_revenue():
    pass

def ingredient_revenue():
    pass

def cooking_mastery():
    pass

def alchemy_mastery():
    "Item is alchemy if reagent, elixir, perfume, or draught is in name"
    pass

if __name__ == "__main__":
    import pandas as pd
    df = pd.read_excel('mastery.xlsx', sheet_name='Sheet1')
    print(df.head())
    pass