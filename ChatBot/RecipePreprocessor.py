import json
import os
import glob
import random
import pickle
from quantulum3 import parser
from collections import OrderedDict
import spacy
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet2021 as wn
from unidecode import unidecode

""""""

def main():
    nlp = spacy.load("en_core_web_trf")
    current_directory = os.getcwd()

    dirtyFiles = os.path.join(current_directory, r'allrecipes')
    recipeData = OrderedDict()
    keyint = -1
    for filename in glob.glob(os.path.join(dirtyFiles, '*.txt')):
        keyint += 1
        print(filename)
        with open(filename, 'r',  encoding="utf8") as file:
            ugly = file.read()
            ugly = ugly[1:]
            good = '{' + ugly + '}'
            recipe = parse_recipe(good, nlp)
            recipeData.update({recipe.name:recipe})
    entry_list = list(recipeData.items())
    random_entry = random.choice(entry_list)
    print(random_entry[1])
    dbfile = open('recipeData.dat', 'wb')
    pickle.dump(recipeData, dbfile )

    recipeData = pickle.load(open('recipeData.dat', 'rb'))

    ingredientData, methodData = parsefromRecipes(recipeData, nlp)

    pickle.dump(ingredientData, open("ingredientData.dat", "wb"))
    pickle.dump(methodData, open("methodData.dat", "wb"))
    
            

class Recipe:
    def __init__(self):
        self.name = '' #Contains the recipe name
        self.cuisine = '' #Contains what type of food the recipe is
        self.rating = 0 #Contains the average rating
        self.ratingCount = 0 #Contains the number of ratings
        self.prepTime = 0 #The ammount of preptime
        self.cookTime = 0 #the ammount of time needed to cook
        self.totalTime = 0
        self.nutrition = {} #Nutritional values, as a list of tuples.  Eg. ("calories", # of calories)
        self.servingCount = 0 #Number of servings made
        self.ingredients = {}# Contains a list of tuples, in the format (ingredient, ammount)
        self.howToSteps = {} #Contains a list of the steps in the recipe text
        self.techniques = [] #Contains a list of techniques used, like frying, baking, grilling, etc.
        self.reviews = {} #Contains a list of reviews people have written for the recipe

    def __str__(self):
        recipe_str = f"Name: {self.name}\n"
        recipe_str += f"Cuisine: {self.cuisine}\n"
        recipe_str += f"Rating: {self.rating}\n"
        recipe_str += f"Rating Count: {self.ratingCount}\n"
        recipe_str += f"Time: {self.totalTime}\n"
        recipe_str += f"prep Time: {self.prepTime}\n"
        recipe_str += f"cook Time: {self.cookTime}\n"
        recipe_str += f"Nutrition: {self.nutrition}\n"
        recipe_str += f"Serving Count: {self.servingCount}\n"
        recipe_str += "Ingredients:\n"
        for key, value in self.ingredients.items():
            vals = ''
            try:
                for v in value:
                    vals += v.surface
            except:
                #print(self.name)
                vals = value
            recipe_str += f"\t{key}: {vals}\n"
        recipe_str += "How-to Steps:\n"
        for key, value in self.howToSteps.items():
            recipe_str += f"\t{key}: {value}\n"
        """recipe_str += f"Techniques: {self.techniques}\n"
        recipe_str += "Reviews:\n"
        for key, value in self.reviews.items():
            recipe_str += f"\t{key}: {value}\n"""
        return recipe_str

def parse_recipe(inString, nlp):
    data = json.loads(inString)

    recipe = Recipe()

    try:
        recipe.name = data['name']
        recipe.name.replace('&#39;', '\'')
        recipe.name.replace('&#34;','')
    except KeyError:
        recipe.name = ''

    try:
        recipe.cuisine = data['recipeCategory']
    except KeyError:
        recipe.cuisine = ''

    try:
        recipe.rating = float(data['aggregateRating']['ratingValue'])
    except KeyError:
        recipe.rating = 0.0

    try:
        recipe.ratingCount = int(data['aggregateRating']['ratingCount'])
    except KeyError:
        recipe.ratingCount = 0

    try:
        recipe.prepTime = int(data['prepTime'][2:-1])
    except (KeyError, ValueError):
        recipe.prepTime = 0
    try:
        recipe.totalTime = int(data['totalTime'][2:-1])
    except (KeyError, ValueError):
        recipe.prepTime = 0
    try:
        recipe.cookTime = int(data['cookTime'][2:-1])
    except (KeyError, ValueError):
        recipe.cookTime = 0

    recipe.nutrition = {}
    nutrition_info = data.get('nutrition', {})
    for key, value in nutrition_info.items():
        if key != '@type':
            recipe.nutrition[key] = value

    try:
        recipe.servingCount = int(data['recipeYield'][0])
    except (KeyError, ValueError):
        recipe.servingCount = 0

    recipe.ingredients = OrderedDict()
    for ingredient in data.get('recipeIngredient', []):
        #try:
        ingredient.replace('(','').replace(')','')
        ingredient.replace(')','').replace('(','')
        amount = parser.parse(ingredient)
        if(amount == []):
            amount = "to taste"
            name = ingredient[:-len(amount)] if ingredient.find(amount) != -1 else ingredient
        else:
            name = ingredient[amount[-1].span[1]:]
        try:
            ingr, prep = name.rsplit(',', 1)
        except (ValueError):
            ingr = name
        recipe.ingredients[ingr.lower()] = amount

    recipe.howToSteps = {}
    for i, step in enumerate(data.get('recipeInstructions', [])):
        try:
            recipe.howToSteps[f"Step {i+1}"] = step['text']
        except (KeyError, TypeError):
            continue

    recipe.techniques = []
    
    for step in recipe.howToSteps.values():
        steptechs = parseTechniques(step, nlp)
        for t in steptechs:
            recipe.techniques.append(t)

    recipe.reviews = {}
    for review in data.get('review', []):
        try:
            author = review['author']['name']
            rating = int(review['reviewRating']['ratingValue'])
            body = review['reviewBody']
            recipe.reviews[author] = (rating, body)
        except (KeyError, TypeError, ValueError):
            continue

    return recipe
        
def get_recipe_instructions(recipe_string):
    import json
    recipe_dict = json.loads(recipe_string)
    recipe_instructions = [step['text'] for step in recipe_dict['recipeInstructions']]
    return recipe_instructions

def parseTechniques(sent, nlp):
    parsed = nlp(sent)
    ret = list()

    for tok in parsed:
        if tok.pos_ == "VERB":
            if isCookingVerb(unidecode(tok.text)):
                ret.append(tok.lemma_.lower())
    retset = set(ret)
    ret = list(retset)
    return ret

def isCookingVerb(verb):
    syn = wn.synsets(verb, pos=wn.VERB)
    for s in syn:
        cap = 0
        while s:
            cap += 1
            #print(s)
            if s == wn.synset('cook.v.03') or s == wn.synset('create_from_raw_material.v.01') or s == wn.synset('change.v.01'):
                return True
            if cap == 20:
                break
            if s.hypernyms():
                s = s.hypernyms()[0]
    return False

def parsefromRecipes(recipeData, nlp):
    rawingredientList = list()
    rawmethodList = list()
    for _, recipevalue in recipeData.items():
        for ingredientkey, _ in recipevalue.ingredients.items():
            rawingredientList.append(str(ingredientkey))
        for tech in recipevalue.techniques:
            rawmethodList.append(tech)

    ingredientList= list()
    methodList = list()

    #perform additional ingredient processing
    for ingr in rawingredientList:
        parse = nlp(ingr)
        ingrstr = ''
        for tok in parse:
            #print(tok.lemma_, tok.pos_, tok.dep_, tok.head.text)
            if(tok.dep_ == 'amod' or 
               tok.dep_ == 'ROOT' or
               tok.dep_ == 'compound' or
               tok.dep_ == 'dobj'):
                ingrstr += tok.text + " " 
        ingredientList.append(ingrstr)
    #remove verbs like 'sliced' or 'chopped'
    ilist = list()
    for ingr in ingredientList:
        parsed = nlp(ingr)
        outstr = ''
        for tok in parsed:
            if(tok.pos_ != 'VERB' and tok.pos_ != 'PUNCT'):
                outstr += tok.text + ' '
        ilist.append(outstr)

    ingredientList = list(set(ilist))
    methodList = list(set(rawmethodList))

    return ingredientList, methodList


if __name__ == "__main__":
    main()
