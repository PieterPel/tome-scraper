import requests
from  bs4 import BeautifulSoup
from collections import OrderedDict
import pandas as pd
import copy

from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import pairwise_distances_argmin_min
from matplotlib import pyplot as plt
from scipy.cluster.hierarchy import dendrogram
import numpy as np

################################################################################3
### Extraction

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
                        'permadeath': permadeath,
                        'url': char_url}
        
        return char_dictionary
    except Exception as e:
        print('Something went wrong with this character')
        print(e)
        return {'class talents': OrderedDict(), 'generic talents': OrderedDict()}
    
##########################################################################################
### Analysis

def plot_dendrogram(model, **kwargs):
    # Create linkage matrix and then plot the dendrogram

    # create the counts of samples under each node
    counts = np.zeros(model.children_.shape[0])
    n_samples = len(model.labels_)
    for i, merge in enumerate(model.children_):
        current_count = 0
        for child_idx in merge:
            if child_idx < n_samples:
                current_count += 1  # leaf node
            else:
                current_count += counts[child_idx - n_samples]
        counts[i] = current_count

    linkage_matrix = np.column_stack(
        [model.children_, model.distances_, counts]
    ).astype(float)

    # Plot the corresponding dendrogram
    dendrogram(linkage_matrix, **kwargs)
    
    
# Method that returns an encoded dataframe with regards to the prodigies
def get_encoded_prodigy_df(char_list):
    
    # Get unique prodigies
    unique_prodigies = set()
    for char in char_list:
        prodigies = char['prodigies']
        for prodigy in prodigies:
            unique_prodigies.add(prodigy)
    
    unique_prodigies = list(unique_prodigies)
    
    # Create basic dataframe
    data = []
    for char in char_list:
        dict = {"Prodigies": char['prodigies']}
        data.append(dict)
        
    df = pd.DataFrame(data)

    # Create binary variables for each prodigy
    for prodigy in unique_prodigies:
        df[prodigy] = df['Prodigies'].apply(lambda x: int(prodigy in x))
    
    # Drop first column
    df = df.iloc[: , 1:]
    
    return df

# Method that returns an encoded dataframe with regards to a single feature except the talents
def get_encoded_feature_df(char_list, feature):
    
    # Get unique features
    unique_features = set()
    for char in char_list:
        features = char[feature]
        
        # Check if features is a list
        if not isinstance(features, list):
            # Wrap it in a list
            features = [features]
        
        # Loop over the features
        for instance in features:
            unique_features.add(instance)

    unique_features = list(unique_features)
    
    # Create basic dataframe
    data = []
    for char in char_list:
        dict = {"features": char[feature]}
        data.append(dict)
        
    df = pd.DataFrame(data)

    # Create binary variables for each prodigy
    for feature in unique_features:
        df[feature] = df['features'].apply(lambda x: int(feature in x))
    
    # Drop first column
    df = df.iloc[: , 1:]
    
    return df

# Input list of characters, output dendogram, uses plot_dendrogram method from previous block
def print_dendrogram(encoded_df):

    # setting distance_threshold=0 ensures we compute the full tree.
    model = AgglomerativeClustering(distance_threshold=0, n_clusters=None)

    model = model.fit(encoded_df.to_numpy())
    plt.title("Hierarchical Clustering Dendrogram")
    # plot the top three levels of the dendrogram
    plot_dendrogram(model, truncate_mode="level", p=3)
    plt.xlabel("Number of points in node (or index of point if no parenthesis).")
    plt.show()
    
# Method that output the cluster model of the characters with regards to the prodigies
def get_cluster_model(encoded_df, num_clusters, model = None):
    
    if model == None:
        model = AgglomerativeClustering(n_clusters=num_clusters, compute_distances=True)

    model = model.fit(encoded_df.to_numpy())
    
    return model

# Method that returns encoded dataframe of class or generic talents
def get_encoded_talents_df(char_list, type='class talents'):
    
    if not type in ['class talents', 'generic talents']:
        print('Use \'class talents\' or \'generic talents\' for type') 
        return None
    
    # First get unique trees and talents
    unique_trees = set()
    unique_talents = set()

    for char in char_list:
        
        # Update unique trees
        trees = set(char[type].keys())
        unique_trees = unique_trees | trees # Take union
        
        # Update  unique talents
        talents = list()
        for tree in list(char[type].values()):
            talents.extend(tree.keys())
            
        unique_talents = unique_talents | set(talents) # Take union
    
    # Create initial dataframe
    column_names = list(unique_trees) + list(unique_talents)
    start_data = np.zeros((len(char_list), len(column_names)))
    df = pd.DataFrame(start_data,columns=column_names)
    
    # Update dataframe
    for index, char in enumerate(char_list):
        for tree_name, tree_dict in list(char[type].items()):
            
            df.at[index, tree_name] = 1
            
            for talent_name, talent_level in tree_dict.items():
                df.at[index, talent_name] = talent_level
    
    return df

def get_cluster_centers_and_observations_closest(df, model=None, num_clusters=2):

    if model == None:
        model = AgglomerativeClustering(n_clusters=num_clusters)

    cluster_labels = model.fit_predict(df)

    # Calculate the cluster centers (means)
    cluster_centers = [np.mean(df[cluster_labels == i], axis=0) for i in range(num_clusters)]

    # Find the closest data point to each cluster center
    closest_points = []
    for cluster_center in cluster_centers:
        closest_point_idx = pairwise_distances_argmin_min([cluster_center], df)[0][0]
        closest_points.append(df.iloc[closest_point_idx])

    return cluster_centers, closest_points

# Get dicionary that has all the trees and the corresponding skills, must be doable by looping over every character
def get_tree_dictionary(char_list, type='class talents'):

    trees_already_seen = set()

    trees_dictionary = OrderedDict()

    for char in char_list:
        
        for tree_name, talent_dict in char[type].items():
            
            if not tree_name in trees_already_seen:
                talent_names = list(talent_dict.keys())
                trees_dictionary[tree_name] = talent_names
                trees_already_seen.add(tree_name)
            
    return trees_dictionary

# Method that prints a character tree of a character
def print_character_tree(char, tree_dict, type='class talents'):
    
    char_trees = char[type].keys()
    
    for tree in tree_dict.keys():
        
        if tree in char_trees:
            print(tree)
            
            for talent, level in char[type][tree].items():
                print(f'\t {talent}: {level}')
                
# Method that prints the talent trees of a pd.Series
def print_talent_series(series, tree_dict):
    
    for tree, talents_list in tree_dict.items():   
        
        if series[tree] != 0:
            print(tree)
            
            for talent in talents_list:
                print(f'\t {talent}: {series[talent]}')

# Method that can print a closest observation
def print_closest_observation(charList, char_series):
    
    ## Race
    races_in_list = charList.race_dict.keys()
    races_in_series = [x for x in races_in_list if x in char_series.index]
    
    for race in races_in_series:
        try:
            if char_series[race] != 0:
                print(f"Race: {race}")
        except Exception as e:
            print(e)
            
    
    ## Prodigies
    prodigies_in_list = charList.prodigy_dict.keys()
    prodigies_in_series = [x for x in prodigies_in_list if x in char_series.index]

    prodigies = []
    for prod in prodigies_in_series:
        if char_series[prod] != 0:
            prodigies.append(prod)
    
    print("Prodigies:")
    for prodigy in prodigies:
        print(f"\t{prodigy}")
    
    ## Class talents
    print("Class talents:")
    for tree, talents_list in charList.class_talents_dict.items():
        if char_series[tree] != 0:
            print(f"\t{tree}")
            for talent in talents_list:
                print(f"\t \t {talent:<30}: \t {char_series[talent]}")
    
    
    ## Generic talents # Need to remove redundant class trees
    print("Generic talents:")
    for tree, talents_list in charList.generic_talents_dict.items():
        if char_series[tree] != 0:
            print(f"\t{tree}")
            for talent in talents_list:
                print(f"\t \t {talent:<30}: \t {char_series[talent]}")

# Method that converts a mean to  a build          
def get_converted_mean(charList, series):
    
    # Make a deep copy of the series
    char_series = copy.deepcopy(series)
    
    ## Convert Race
    races_in_list = charList.race_dict.keys()
    races_in_series = [x for x in races_in_list if x in char_series.index]
    races_sorted = sorted(races_in_series, key=lambda race: char_series[race], reverse=True)
    races_sorted.extend(['Whitehooves', 'Yeti'])
    
    # Set tree value to 0 for all but the most important race
    for race in races_in_series:
        if race == races_sorted[0]:
            char_series[race] = 1
        else:
            char_series[race] = 0
    
    # Set race talents to zero for all but the most important race     
    for index in char_series.index:
        if '/' in index and any(race in index for race in races_sorted[1:]):
            char_series[index] = 0
            for talent in charList.generic_talents_dict[index]:
                char_series[talent] = 0
    
    ## Convert Prodigies
    
    prodigies_in_list = charList.prodigy_dict.keys()
    prodigies_in_series = [x for x in prodigies_in_list if x in char_series.index]
    prodigies_sorted = sorted(prodigies_in_series, key=lambda prod: char_series[prod], reverse=True)
    
    # Loop over the prodigies in the series
    for prod in prodigies_in_series:
        if prod in prodigies_sorted[:2]:
            char_series[prod] = 1
        else:
            char_series[prod] = 0
    
    ## Convert class and generic talents
    type_dict = {'class talents': charList.class_talents_dict.values(),
            'generic talents': charList.generic_talents_dict.values()}
    
    for type in ['class talents', 'generic talents']:
    
        type_talents_total = list()
        for talents in type_dict[type]:
            type_talents_total.extend(talents)
        
        type_talents = [x for x in type_talents_total if x in char_series.index]
        
        # Back-up series
        rounded_down = 0
        rounded_down_dict = {}
        
        # Round talents down
        for talent in type_talents:
            
            after_decimal = char_series[talent] % 1
            char_series[talent] = np.floor(char_series[talent])
            
            rounded_down += after_decimal
            rounded_down_dict[talent] = after_decimal
        
        # Sort class talents by how much has been rounded
        type_talents_ordered = sorted(rounded_down_dict, key=rounded_down_dict.get, reverse=True)
        
        # Redistribute
        for talent in type_talents_ordered:
            
            char_series[talent] += 1
            
            rounded_down -= rounded_down_dict[talent]
            
            if rounded_down < 1:
                break
        
    return char_series
