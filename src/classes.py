from dataclasses import dataclass
import methods
from collections import OrderedDict
import copy
import pandas as pd
import filter_codes

# Class that represents a list of characters [each character is a dictionary]
class CharacterList:
    
    # Method that is called when the class is initialized
    def __init__(self, char_list):
        self.char_list = copy.deepcopy(char_list) if char_list else []
        self.length = len(char_list) if char_list else 0
        self.features = list(char_list[0].keys()) if char_list else []
        self.current = 0
        
        # Set up dictionaries
        self.race_dict = {}
        self.prodigy_dict = {}
        self.inscription_dict = {}
        self.class_talents_dict = {}
        self.generic_talents_dict = {}
        self.appearing_dict = {}
        
        self.update_dicts()
    
    # Method that updates the dictionaries
    def update_dicts(self):
        # Reset dictionaries
        self.race_dict = {}
        self.prodigy_dict = {}
        self.inscription_dict = {}
        self.class_talents_dict = {}
        self.generic_talents_dict = {}
        
        # Loop over all characters and update the dictionaries
        for char in self.char_list:
            
            # Update the race dictionary
            if not char['race'] in list(self.race_dict.keys()):
                self.race_dict[char['race']] = 1
            else:
                self.race_dict[char['race']] += 1    
            
            # Update the prodigy dictionary
            for prodigy in char['prodigies']:
                if not prodigy in list(self.prodigy_dict.keys()):
                    self.prodigy_dict[prodigy] = 1
                else:
                    self.prodigy_dict[prodigy] += 1
            
            # Update the inscription dictionary        
            for inscription in char['inscriptions']:
                if not inscription in list(self.inscription_dict.keys()):
                    self.inscription_dict[inscription] = 1
                else:
                    self.inscription_dict[inscription] += 1

            # Update the class talents dictionary
            for tree, talents_dict in char['class talents'].items():
                if not tree in list(self.class_talents_dict.keys()):
                    self.class_talents_dict[tree] = list(talents_dict.keys())
                
            # Update the generic talents dictionary
            for tree, talents_dict in char['generic talents'].items():
                if not tree in list(self.generic_talents_dict.keys()):
                    self.generic_talents_dict[tree] = list(talents_dict.keys())
    
    # Method that cleans the charachter list
    def clean_characters(self):
        characters_cleaned = list()

        for char in self.char_list:
            if char['class talents'] == None:
                print(f"Threw {char['name']} away, not class talents")
                self.length -= 1
            elif not char['english']:
                print(f"Threw {char['name']} away, not english")
                self.length -= 1
            elif len(char['prodigies']) > 2:
                print(f"Threw {char['name']} away, too many prodigies")
                self.length -= 1
            else:
                characters_cleaned.append(char)
                
        self.char_list = characters_cleaned
        self.update_dicts()
    
    # Method that prints a summary of the character list
    def print_summary(self, num=5):
        
        races_ordered = sorted(self.race_dict, key=self.race_dict.get, reverse=True)
        races_percentages = [f'({round(100*self.race_dict[race]/self.length, 1)})%' for race in races_ordered]
        
        prodigies_ordered = sorted(self.prodigy_dict, key=self.prodigy_dict.get, reverse=True)
        prodigies_percentages = [f'({round(100*self.prodigy_dict[prodigy]/self.length, 1)})%' for prodigy in prodigies_ordered]
        
        inscriptions_ordered = sorted(self.inscription_dict, key=self.inscription_dict.get, reverse=True)
        inscriptions_percentages = [f'({round(100*self.inscription_dict[inscription]/self.length, 1)})%' for inscription in inscriptions_ordered]
        
        race_string = 'Races: \t'
        prodigy_string = 'Prodigies: \t'
        inscription_string = 'inscriptions: \t'
        for i in range(num):
            race_string += f'{races_ordered[i]} {races_percentages[i]}, '
            prodigy_string += f'{prodigies_ordered[i]} {prodigies_percentages[i]}, '
            inscription_string += f'{inscriptions_ordered[i]} {inscriptions_percentages[i]}, '
            
        print(race_string)
        print(prodigy_string)
        print(inscription_string)
    
    # Method that prints an econded pandas DataFrame for any feature except the talent trees
    def get_encoded_feature_df(self, feature):
        
        if not feature in self.features:
            raise Exception(f"Not a valid feature, choose from: {self.features}")
        
        if feature in ["class talents", "generic talents"]:
            df = methods.get_encoded_talents_df(self.char_list, type=feature)
        else:
            df = methods.get_encoded_feature_df(self.char_list, feature)
        
        self.appearing_dict[feature] = list(df.columns)
        
        # Rename generic talents that have the same name as a class
        if feature == 'generic talents':
            df = df.rename(columns={'Skeleton': 'Skeleton talent', "Ghoul": 'Ghoul talent'})
        
        return df
        
    def get_combined_encoded_df(self, features, weights = None):
        
        # Check if features is a list
        if not isinstance(features, list):
            # Wrap in list
            features = [features]
            
        # Set standard weights of 1
        if weights == None:
            weights = [1] * len(features)
        
        # Check if features and weights are the same length
        if len(features) != len(weights):
            raise Exception("The features and weights are different lengths")
        
        df = pd.DataFrame()
        
        # Loop over all features
        for index, feature in enumerate(features):
            
            # Check if feature is valid
            if not feature in features:
                raise Exception(f"{feature} is not a valid feature, choose from {self.features}")
            
            df = pd.concat([df, weights[index]*self.get_encoded_feature_df(feature)], axis = 1)
        
        return df
    
    # Method that prints a character in the character list
    def print_character(self, index):
        
        if 0 < index or index > self.length:
            raise Exception("Index must be between 0 and length")
        
        char = self.char_list[index]
        print(f"Name: \t{char['name']}")
        print(f"Race: \t{char['race']}")
        print(f"Sex: \t{char['sex']}")
        print(f"Diff.: \t{char['difficulty']}")
        print(f"PD: \t{char['permadeath']}")
    
    # Method that returns cluster model for (a) feature(s)
    def get_cluster_model(self, features, num_clusters, model=None, weights = None):
        
        df = self.get_combined_encoded_df(features, weights)
        
        # Return model
        return methods.get_cluster_model(df, num_clusters, model)
        
    # Method that prints a dendrogram for feature(s)
    def print_dendrogram(self, features, weights = None):
        
        df = self.get_combined_encoded_df(features, weights)
            
        # Print dendrogram
        methods.print_dendrogram(df)
    
    # Method that returns cluster centers and closest observation for (a) feature(s) and number of clusters
    def get_cluster_centers_and_closest_observations(self, features, num_clusters, weights = None, model=None):
        
        df = self.get_combined_encoded_df(features, weights)
        
        # Return
        return methods.get_cluster_centers_and_observations_closest(df=df, num_clusters = num_clusters, model=model)
    
    def __eq__(self, other):
        if isinstance(other, CharacterList):
            return self.char_list == other.char_list
        else:
            return False
        
    def __add__(self, other):
        if isinstance(other, CharacterList):
            return CharacterList(self.char_list + other.char_list)
        else:
            return False
        
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.current >= self.length:
            raise StopIteration
        
        self.current += 1
        return self.char_list[self.current - 1]
    
    def __str__(self):
        for char in self.char_list:
            print(char['name'])

# Class that contains the filter for the vault and has a method to extrac the characters
@dataclass(frozen=False)
class CharFilter:
    name: str = ''
    minlevel: str = ''
    maxlevel: str = ''
    dead: bool = False
    winner: bool = False
    permadeath: str = ''
    difficulty: str = ''
    race: str = ''
    char_class: str = ''
    campaign: str = ''
    version: str = ''
    only_official_addons: bool = False
    max_urls: int = 100
    
    # Method that creates the filtered base url
    def create_url(self) -> str:
        
        tags = list()
        
        if self.name != '':
            tags.append(f'tag_name={self.name}')
        
        if self.minlevel != '':
            tags.append(f'tag_level_min={self.minlevel}')
            
        if self.maxlevel != '':
            tags.append(f'tag_level_max={self.maxlevel}')
        
        if self.dead:
            tags.append('tag_dead=dead')
            
        if self.winner:
            tags.append('tag_winner=winner')
            
        if self.permadeath != '':
            permadeath_code = filter_codes.permadeath_codes[self.permadeath]
            tags.append(f'tag_permadeath%5B%5D={permadeath_code}')
            
        if self.difficulty != '':
            difficulty_code = filter_codes.difficulty_codes[self.difficulty]
            tags.append(f'tag_difficulty%5B%5D={difficulty_code}')
            
        if self.race != '':
            race_code = filter_codes.race_codes[self.race]
            tags.append(f'tag_race%5B%5D={race_code}')
            
        if self.char_class != '':
            class_code = filter_codes.class_codes[self.char_class]
            tags.append(f'tag_class%5B%5D={class_code}')
            
        if self.campaign != '':
            campagin_code = filter_codes.campaign_codes[self.campaign]
            tags.append(f'tag_campagin%5B%5D={campagin_code}')
            
        if self.version != '':
            version_code = filter_codes.version_codes[self.version]
            tags.append(f'tag_game%5B%5D={version_code}')
            
        if self.only_official_addons:
            tags.append('tag_official_addons=1')
            
        base_url = 'https://te4.org/characters-vault?'
        filter_tags = '&'.join(tags)
        url = base_url + filter_tags
        
        return url
    
    # Method that extracts the filtered characters
    def get_characters(self):
        
        # Get url
        filtered_url = self.create_url()
        
        # Get charachter links
        char_urls = methods.get_all_character_urls(base_url = filtered_url, max_urls = self.max_urls)
        
        # Extract characters
        characters = list()
        for url in char_urls:
    
            char = methods.get_character_dictionary(url)
    
            # Filter out non-english characters
            if not char['class talents'] == OrderedDict() and not char['generic talents'] == OrderedDict():
                characters.append(char)
                
        return CharacterList(characters)
    
        
    

        
        
    
    
        