from dataclasses import dataclass
import methods
from collections import OrderedDict

# Class that contains the filter for the vault and has a method to extrac the characters
@dataclass(frozen=False)
class charFilter:
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
        import filter_codes
        
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
                
        return characters