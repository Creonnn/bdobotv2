from helper import substring_in_string_percentage, enhancement_levels,\
type_one, type_two, type_three, type_four, type_five


class Search:
    """
    Attempts to find the name of the actual item based on user input.
    Based on the item name of best match, get its ID and SID. 
    """
    def find_item(self, input: str, exact: bool, data: dict) -> dict:
        '''
        Takes in raw user input and extracts the intended search terms. 
        Then, finds the best partially matches or exact match of official item names.

        PARAMS:
        input: Raw user input
        exact: Specifies whether to use partial or exact match 
        '''
        item_search_term = self._get_item_search_term(input)
        search_result = self._get_id_and_name(item_search_term, data) if not exact else self._get_exact_id_and_name(item_search_term, data)

        return search_result
    
    def get_sid(self, response: list, enhancement_level: str) -> int:
        '''
        Returns the internal enhancement number based on the enhancement level. Returns None if enhancement level is not specified.
        '''
        if enhancement_level is None or len(response) == 1:
            enhancement_level = None # In case someone specifies an enhancement level for an item that doesn't have enhancement levels
            sid = 0

        elif enhancement_level in type_one.keys():
            sid = type_one[enhancement_level] if len(response) > 10 else type_two[enhancement_level]

        elif enhancement_level in type_three.keys():
            sid = type_three[enhancement_level]

        elif enhancement_level in type_four.keys() and len(response) > 10:
            sid = type_four[enhancement_level]

        else:
            sid = type_five[enhancement_level]
        
        return sid
    
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
    
    def _get_item_search_term(self, input):
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

    def _get_id_and_name(self, item_search_term: str, data: dict) -> dict:
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
    
    def _get_exact_id_and_name(self, item_search_term: str, data: dict) -> dict:
        '''
        Gets id and name of only exact matches based on item_search_term.
        item_search_term: The search term to be compared with official item names.
        data: Contains official item names to be used in the initialization stage.
        '''
        for name, id in data.items():
            if item_search_term.lower() == name.lower():
                return {id: name}
        return {}
    
    

if __name__ == '__main__':
    ...