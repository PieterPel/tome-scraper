import requests
import bs4 as BeautifulSoup
from collections import OrderedDict

# Method that gets the character urls from a page
def get_char_urls_from_page(page_url=None, soup=None):
    
    # Set up BeautifulSoup if isn't given
    if not soup:
        req = requests.get(page_url)
        soup = BeautifulSoup(req.text, 'html.parser')
    
    # Extract the html elements that contain the urls
    char_url_html_list = soup.find_all("tr", {"class": "even"}) + soup.find_all("tr", {"class": "odd"})
    
    # Loop over those elements to get the character page urls
    char_url_list = set()
    for url_html in char_url_html_list:
        char_url_list.add("https://te4.org/" + url_html.find_all("a")[1].get("href"))
        
    # Return set
    return char_url_list

def empty_page(page_url=None, soup=None):
    if not soup:
        req = requests.get(page_url)
        soup = BeautifulSoup(req.text, 'html.parser')
        
    check = soup.find("tr", {"class":"odd"})
    if check.text == 'No characters available. ':
        return True
    else:
        return False

# Method that returns all the character urls, up to a maximum
def get_all_character_urls(base_url, max_urls = 100):
    print('Extracting character urls...')
    
    # Set up
    character_urls = set()
    page_number = 0
    
    while len(character_urls) <= max_urls:
        
        print(f'Now at {len(character_urls)} characters. Extracting characters from page {page_number}...')
        
        # Make current page url, get soup
        page_url = f"{base_url}&page={page_number}"
        
        req = requests.get(page_url)
        soup = BeautifulSoup(req.text, "html.parser")
        
        # Break if the page is empty
        if empty_page(soup=soup):
            print(f"Page {page_number} is empty. Ending...")
            break
        
        # Get the character urls from the current page
        character_urls = character_urls | get_char_urls_from_page(soup=soup) # Take union of the two sets
        
        # Update the page number
        page_number += 1
        
    return character_urls

# Method that gets a dictionary containing the character table titles and their indices
def get_table_dict(tables):
    
    dict = {}
    
    dict['Prodigies'] = 17
    
    for index, table in enumerate(tables):
        try:
            name = table.find('h4').text
        
            if 'Inscriptions' in name.split(' '):
                name = 'Inscriptions'
        
            dict[name] = index
        except:
            pass
        
    return dict

# Method that extracts the information from the generic and class talent tables
def get_trees(table):
    
    try:
        lines_html = table.find_all("tr")
        
        talents = OrderedDict()
        line_num = 0
        extra = 0

        # Loop over all lines
        for line in lines_html:
            
            # Every fifth line stands for a tree
            if line_num % (5 + extra) == 0:
                line_num = 0
                elements = line.find_all('td')
                tree = elements[0].text

                tree_dict = OrderedDict()
                
                if tree == 'Technique / Combat training':
                    extra = 2 
                else: 
                    extra = 0
            
            # The other lines stand for skills in a tree
            else:
                line.find('div').decompose()
                talent = line.find('li').text
                level = line.find_all('td')[-1].text
                level_int = int(level[0])
                tree_dict[talent] = level_int
                talents[tree] = tree_dict

            line_num += 1
            
        return talents
    
    except Exception as e:
        print('Something went wrong extracting the skill tree (Probably a non-english character)')
        print(e)
        return OrderedDict()
    
# Method that puts the relevant data of a character in a dictionary
def get_character_dictionary(char_url):
    
    print(f'Beginning to extract {char_url}...')
    
    try:
    
        # Set up BeautifulSoup
        req = requests.get(char_url)
        soup = BeautifulSoup(req.text, 'html.parser')

        ### Name of the character (and the creator)
        full_name = soup.find("div", {"id": "title-container"}).text

        ### Info from tables at the top
        char_tables = soup.find_all("div", {"class": "charsheet"})
        
        tables_dict = get_table_dict(char_tables)

        ## Character table (Maybe change to dictionary later)
        character_index = tables_dict['Character']
        character_table = char_tables[character_index]
        character_table_entries = character_table.find_all("tr")

        # Game & Version
        game_line = character_table_entries[0]
        game_text = game_line.find_all("td")[1].text
        game_text_split = game_text.split(' ')

        version = list.pop(game_text_split)
        game = ' '.join(game_text_split)

        # Difficulty and permadeatch
        mode_line = character_table_entries[3]
        mode_text = mode_line.find_all("td")[1].text
        mode_text_split = mode_text.split(' ')
        difficulty = mode_text_split[0]
        permadeath = mode_text_split[1]

        # Sex
        sex_line = character_table_entries[4]
        sex = sex_line.find_all("td")[1].text

        # Race
        race_line = character_table_entries[5]
        race = race_line.find_all("td")[1].text

        # Class
        class_line = character_table_entries[6]
        class_ = class_line.find_all("td")[1].text

        # Level
        level_line = character_table_entries[7]
        level = level_line.find_all("td")[1].text
        
        # Size
        size_line = character_table_entries[8]
        size = size_line.find_all("td")[1].text
        
        # English
        if size in ['tiny', 'small', 'medium', 'big', 'huge', 'gargantuan']:
            english = True
        else: 
            english = False

        ## Stats
        stats_index = tables_dict['Primary Stats']
        stats_table = char_tables[stats_index]
        stats_table_entries = stats_table.find_all("tr")

        stats = {}
        for row in stats_table_entries:
            stat = row.find_all("td")[0].text
            value = row.find_all("td")[1].text
            stats[stat] = value
            
        ## Inscriptions
        inscriptions_index = tables_dict['Inscriptions']
        inscriptions_table = char_tables[inscriptions_index]
        inscriptions_html = inscriptions_table.find_all("td", {"class": "qtip-link"})

        inscriptions = list()
        for inscription in inscriptions_html:
            inscription.find('div').decompose()
            inscriptions.append(inscription.text)

        ## Class and Generic Talents
        
        class_talents_index = tables_dict["Class Talents"]
        generic_talents_index = tables_dict["Generic Talents"]
        
        class_talents_table = char_tables[class_talents_index]
        generic_talents_table = char_tables[generic_talents_index]
        
        class_talents = get_trees(class_talents_table)
        generic_talents = get_trees(generic_talents_table)

        ## Prodigies
        prodigies = list()
        
        prodigy_index = tables_dict['Prodigies']
        prodigy_table = char_tables[prodigy_index]
        
        if prodigy_table.find("h4").text == "Prodigies":
            
            entries = prodigy_table.find_all('tr')
            
            for line_html in entries:
                line_html.find('div').decompose()
                prodigies.append(line_html.find('li').text)
            
        char_dictionary = {'name': full_name,
                        'race': race,
                        'class': class_,
                        'sex': sex,
                        'level': level,
                        'size': size,
                        'english': english,
                        'stats': stats,
                        'inscriptions': inscriptions,
                        'class talents': class_talents,
                        'generic talents': generic_talents,
                        'prodigies': prodigies,
                        'game': game,
                        'version': version,
                        'difficulty': difficulty,
                        'permadeath': permadeath}
        
        return char_dictionary
    except Exception as e:
        print('Something went wrong with this character')
        print(e)
        return {'class talents': OrderedDict(), 'generic talents': OrderedDict()}