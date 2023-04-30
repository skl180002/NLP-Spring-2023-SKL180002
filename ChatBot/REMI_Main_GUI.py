import os
import re
import sys
import glob
import pickle
from collections import OrderedDict
import copy

import spacy
import numpy as np
import pandas as pd
from nltk.corpus import wordnet2021 as wn
from nltk.tokenize import word_tokenize
from quantulum3 import parser

from RecipePreprocessor import Recipe
from RecipePreprocessor import isCookingVerb, parseTechniques, parsefromRecipes

class UserState():
    def __init__(self,
                 name = 'None_Provided',
                 ingredients = list(),
                 dingredients = list(),
                 pmethods = list(),
                 dmethods = list(),
                 recipes = OrderedDict(),
                 frecipies = list(),
                 nutrition = dict(),
                 rating = int,
                 time = int
                 ):
        self.userName = name #name of the current user
        self.userIngredients = ingredients #list of ingredients (potentially tuple of ingredient, quantity object)
        self.dislikedIngredients = dingredients #list of ingredients to avoid
        self.preferredMethods = pmethods #list of methods preferred (not used)
        self.dislikedMethods = dmethods #list of methods to avoid
        self.recipeCatalog = recipes #catalog of valid recipes according to user preferences
        self.foundRecipes = frecipies #keep track of all recipes explored so far
        self.nutritionPrefs = nutrition #dict of nutritional attr : value
        self.ratingThreshold = rating #cutoff for allowable rating
        self.maxCookTime = time #maximum time desired for recipe length

    def updateRecipeCatalog(self):
        numRemoved = 0
        update = copy.deepcopy(self.recipeCatalog)
        for dislikedingredient in self.dislikedIngredients:
            for keyval, recipe in self.recipeCatalog.items():
                searchString = str(recipe).lower()
                if searchString.find(dislikedingredient.lower()) != -1:
                    try:
                        update.pop(keyval)
                        numRemoved +=1
                    except (KeyError):
                        print(keyval, "Error")
                        continue
        for dislikedMethod in self.dislikedMethods:
            for keyval, recipe in self.recipeCatalog.items():
                searchString = str(recipe).lower()
                if searchString.find(dislikedMethod.lower()) != -1:
                    try:
                        update.pop(keyval)
                        numRemoved +=1
                    except (KeyError):
                        print(keyval, "Error")
                        continue

        self.recipeCatalog = copy.deepcopy(update)
        print("User", self.userName, "catalog updated, items removed: ", numRemoved)


    def updateMethods(self):
        count = 0
        update = list()
        for method in self.preferredMethods:
            doAppend = True
            for remMet in self.dislikedMethods:
                if method.find(remMet) != -1:
                    doAppend = False
                    count += 1
                    break
            if doAppend:
                update.append(method)
        self.preferredMethods = update
        print("User", self.userName, "Methods Updated:", count, "removed")

    def updateIngredients(self):
        count = 0
        update = list()
        for ingredient in self.userIngredients:
            doAppend = True
            for remIng in self.dislikedIngredients:
                if ingredient.find(remIng) != -1:
                    doAppend = False
                    count +=1
                    break
            if doAppend:
                update.append(ingredient)

        self.userIngredients = update
        print("User", self.userName, "Ingredients Updated:", count, "removed")
                
##SETUP:
    # load recipe 'database'
recipeData = pickle.load(open("recipeData.dat", 'rb'))
    # load list of ingredients and methods
ingredientData = pickle.load(open("ingredientData.dat", 'rb'))
methodData = pickle.load(open("methodData.dat", 'rb'))
    # load previous user states
try:
    userList = pickle.load(open("userStates.dat", 'rb'))
    loadFlag = True
except:
    userList = list()
    loadFlag = False
    # Import trained models
intentRegressor = pickle.load(open("intent_regressor.model", 'rb'))
intentBayes = pickle.load(open("intent_bayes.model", 'rb'))

    # set up default nutritional cases
healthyDiet = {
    'calories' : parser.parse('400 kcal'),
    'carbohydrateContent' : parser.parse('40 grams'),
    'cholesterolContent' : parser.parse('20 mg'),
    'fiberContent' : parser.parse('2 g'),
    'proteinContent' : parser.parse('15g'),
    'saturatedFatContent' : parser.parse('0 gram'),
    'sodiumContent' : parser.parse('500mg'),
    'sugarContent' : parser.parse('10 grams'),
    'fatContent' : parser.parse('15 grams'),
    'unsaturatedFatConent' : parser.parse('15 grams')
}

    

# Set up spaCy Model
global nlp 
nlp = spacy.load("en_core_web_trf")
global inputState
inputState = 3 #We initialize the input state to 3 to get the procedural stuff done. 3 Is the welcome state. 2 is the no name state, 1 is how can I help, 0 is I dont understand/handle error.
global currentUserId
currentUserId = 0 #Current user needs to be a global variable, so it is remembered between function calls.
global workingRecipe
workingRecipe = Recipe()

def firstTimeThing():
    global currentUserId
    global inputState
    global nlp
    print("currentUserID: ", currentUserId)
    sampleUser = UserState(recipes=recipeData)
    sampleUser.userName = "Demo N. Stration"
    sampleUser.userIngredients = ("potato", "rice", "beef", "cabbage")
    sampleUser.preferredMethods = ("saute", "roast", "deep fry")
    sampleUser.nutritionPrefs = healthyDiet
        # display welcome/first prompt explaining what REMI can do
            #sub-idea: give sample conversation as demo
                #sample user state for demo????

        # working db- whole db filtered by constraints set in user models
    outString = ''
    outString += "Welcome to REMI_V1! \n"
    outString += "I’m REMI, the Recipe Exploration and Modification Intelligence!\n"
    outString += "To start, please tell me your name!"
    inputState = 2 #transition to the get user name state
    print("Current Input State:", inputState)
    currentUserID = 0
    return outString

def getUserName(UserInput):
    global currentUserId
    global inputState
    global nlp
    print("Current User ID:", currentUserId)
    #Parse name from userIn
    nameParse = nlp(UserInput)
    isLoadName = False
    ind = 0
    if(len(nameParse) == 1):
        if(loadFlag):
            for user in userList:
                if user.userName == nameParse[0].text.capitalize():
                    currentUserId = ind
                    isLoadName = True
                    break
                ind +=1
        if not isLoadName:
            userList.append(UserState(name= nameParse[0].text.capitalize(), recipes=recipeData, ingredients=ingredientData, pmethods=methodData))
        foundName = True
        currentUserId = ind
    else:
        for tok in nameParse:
            if tok.pos_ == 'PROPN' and tok.text.lower().find('remi') == -1 and not tok.is_stop:
                if(loadFlag):
                    for user in userList:
                        if user.userName == tok.text.capitalize():
                            currentUserId = ind
                            isLoadName = True
                            break
                        ind +=1
                foundName = True
                currentUserId = ind
                if not isLoadName:
                    userList.append(UserState(name=tok.text.capitalize(), recipes=recipeData, ingredients=ingredientData, pmethods=methodData))
                break
    if isLoadName:
        inputState = 1
        return ("Welcome back " + getattr(userList[currentUserId], 'userName') + "!\n How can I help you today?")
    if foundName:
        inputState = 1
        return ("Nice to meet you " + getattr(userList[currentUserId], 'userName') + "!\n What can I help you with today?")
        
    else:
        inputState = 2
        return ("I didn't quite catch your name there, can you tell me again?")
        
    
def handleError():
    global currentUserId
    global inputState
    global nlp
    inputState = 1
    
    return("I'm not quite sure what you meant, can you phrase that a little differently?")

def getResponse(userInput):
    global currentUserId
    global inputState
    global nlp
    global workingRecipe
    try:
        print("Current Input State:", inputState)
        if inputState == 3:
            return firstTimeThing()
        if inputState == 2:
            return getUserName(userInput)
        if inputState == 0:
            return handleError()
        outString = ''
        userIn = userInput
        #query for intent
        intent = '\0'
        intent = getUserIntent(userIn)
        #else:
        # print("\tSorry, I don't quite know what you want.\n")
        #intent = 'u'
        """
            Definition Intent:
                This area provides the mechanism by which REMI provides definitions
                for ingredients or cooking methods.
                The user's statement is passed in and parsed using spaCy's english language
                transformer to tag part-of-speech information. All ingredients are nouns,
                so a list of noun words found in the sentence is constructed, and from there 
                WordNet is used to check if a form of these nouns are categorized as an ingredient.
        """
        if intent == 'd':
            print("Intent: Define Reached")

            ingredientDefs, methodDefs = parseforcooking(userIn)

            defs = ingredientDefs + methodDefs
            print("Defs: " , defs)
            try:
                outstr = "Sure thing, here's a definition for " + defs[0][0]
                if len(defs) > 1:
                    if len(defs) > 2:
                        outstr += ','
                        for i in range(1,len(defs)-1):
                            outstr += " " + defs[i][0] + ','
                    outstr += " and " + defs[-1][0]
                outString += outstr + '\n'
                for definition in defs:
                    outString += definition[0].capitalize() + " : " + definition[1].definition() + "\n"
                print("Intent D: Definitions-\n", defs)
                print("Ouput String for Chatbot: \n", outString)
            except (IndexError):
                outString += "Hmm... sorry, doesn't seem like I know what that means. \n"
                outString += handleError()
                print("Intent D: Definitions-\n", defs)
            return outString
                
                
        """
            Exploration Intent:
                This is REMI's core functionality: based on what it knows about the user
                and the incoming request, it will attempt to find a recipe that best matches
                the user's desire.

                The main focus is to filter recipe by ingredients
        """
        if intent == 'e':
            print("Intent: Explore Reached")
            ingredientsearch, methodsearch = parseforcooking(userIn)
            search = ingredientsearch + methodsearch
            cols = list()
            for term in search:
                if term[0].find("ingredient") == -1: 
                    cols.append(term[0]) 
            defaultdata = np.zeros(len(cols))
            print("Search Terms:", cols)
            try:
                #create dataframe of search results, 1 if term is found, 0 else
                searchResults = pd.DataFrame(data=[defaultdata],index=["N/A"],columns=cols)
                for recipekey, recipevalue in userList[currentUserId].recipeCatalog.items():
                    result = pd.DataFrame(data = [defaultdata],index=[recipekey], columns=cols)
                    for term in cols:
                        if (str(recipevalue.ingredients) + str(recipevalue.techniques)).lower().find(term) != -1:
                            result[[term]] = 1
                        else:
                            result[[term]] = 0
                    searchResults = pd.concat([searchResults, result])
                
                maxSearchVal = 0
                for index, result in searchResults.iterrows():
                    sumval = 0
                    for term in cols:
                        sumval += result[term]
                    if sumval > maxSearchVal:
                        maxSearchVal = sumval
                print("Degree of Match", len(cols), maxSearchVal, maxSearchVal/len(cols))
                filteredSearch = pd.DataFrame(data = [defaultdata], columns=cols)
                filteredNames = list()
                for index, result in searchResults.iterrows():
                    sumval = 0
                    for term in cols:
                        sumval += result[term]
                    if sumval == maxSearchVal:
                        print(index)
                        filteredNames.append(index)
                        filteredSearch = pd.concat([filteredSearch, result])

                if not filteredSearch.empty:
                    outString += "Here's what I was able to find for you:\n\n"
                    for index in filteredNames:
                        outString += str(userList[currentUserId].recipeCatalog[index]) + '\n\n'
                else:
                    outString += "Sorry, I couldn't find anything close to a match :("
                return outString
            except:
                return "Sorry, I couldn't find any matches for you."


        """
            Modification Intent:
                Using the loaded ingredient or method lists, the user's request will be parsed
                for either a method or ingredient and the next closest term will be given.
                Closeness will be determined by wu-palmer similarity, and if that fails then
                the first lemma that is not an alternate definition of the word will be selected.

                To make REMI better help each user, any modification requests will be saved to 
                the userState, and the searchable dictionary will be filtered down to exclude those
                techniques or ingredients.
        """
        if intent == 'm': 
            print("Intent: Modify Reached")
            
            #retrieve synsets for all methods
            ingrSyns = list()
            methodSyns = list()
            ingrs, methods = parseforcooking(userIn)

            print("Ingredients Found:", ingrs)
            print("Methods Found:", methods)
            for ingr in ingrs:
                if str(ingr).find('ingredient') == -1:
                    ingrSyns.append(ingr[1])
            for method in methods:
                methodSyns.append(method[1])
            
            print("\nIngredient Synsets:", ingrSyns)
            print("Method Synsets:", methodSyns)
            similarIngredients = list()
            similarMethods = list()

            #find term from relevant master list with highest wup-similarity
            if not methods:
                ilemmaflag = True
                for ibaseSyn in ingrSyns:
                    imostSimilar = (None, 0)
                    isimTok = ''
                    for ingredient in userList[currentUserId].userIngredients:
                        tokens = word_tokenize(ingredient)
                        for tok in tokens:
                            try:
                                isimilarSyns = wn.synsets(tok, pos= wn.NOUN)
                                for isyn in isimilarSyns:
                                    iwup = wn.wup_similarity(ibaseSyn, isyn)
                                    if iwup > imostSimilar[1] and iwup != 1.0:
                                        imostSimilar = (isyn, iwup)
                                        isimTok = tok
                            except:
                                continue
                    similarIngredients.append((ibaseSyn, imostSimilar))
                    synName = ibaseSyn.name()[0:ibaseSyn.name().find('.')]
                    if(imostSimilar[1] > 0.5):
                        ilemmaflag = False
                        percentFormat = '{:.1f}%'.format(imostSimilar[1]*100)
                        outString += f"{synName.capitalize()} can be substituted with {isimTok} (Similarity: {percentFormat})\n"
                    elif ibaseSyn.lemmas() and ilemmaflag:
                        synName = ibaseSyn.name()[0:ibaseSyn.name().find('.')]
                        ilemmas = ibaseSyn.lemmas()
                        for lem in ilemmas:
                            if imostSimilar[0].name().find(lem.name()) == -1:
                                similarMethods.append((ibaseSyn, (lem, 0.9)))
                                outString += f"{synName} can be substituted with {lem.name()} (Lemma)\n"
                
            mlemmaflag = True
            for mbaseSyn in methodSyns:
                mmostSimilar = (None, 0)
                msimTok = ''
                for met in userList[currentUserId].preferredMethods:
                    tokens = word_tokenize(met)
                    for tok in tokens:
                        try:
                            msimilarSyns = wn.synsets(tok, pos= wn.VERB)
                            for msyn in msimilarSyns:
                                mwup = wn.wup_similarity(mbaseSyn, msyn)
                                if mwup > mmostSimilar[1] and mwup != 1.0:
                                    mmostSimilar = (msyn, mwup)
                                    msimTok = tok
                        except:
                            continue
                similarMethods.append((mbaseSyn, mmostSimilar))
                synName = mbaseSyn.name()[0:mbaseSyn.name().find('.')]
                if(mmostSimilar[1] > 0.5):
                    mlemmaflag = False
                    percentFormat = '{:.1f}%'.format(mmostSimilar[1]*100)
                    outString += f"{synName} can be substituted with {msimTok} (Similarity: {percentFormat})\n"
                    outString += f"Here's what it means to {msimTok}:\n{mmostSimilar[0].definition()}\n"
                elif mbaseSyn.lemmas() and mlemmaflag:
                    mlemmas = mbaseSyn.lemmas()
                    for lem in mlemmas:
                        if synName != lem.name():
                            similarMethods.append((mbaseSyn, (lem, 0.9)))
                            outString += f"{synName} can be substituted with {lem.name()} (Lemma)\n"
                            outString += f"Here's what it means to {lem.name()}:\n{mbaseSyn.definition()}\n"

            modificationOut = similarIngredients + similarMethods
            print("\nAll Substitutions Found:\n", modificationOut)
            """if len(modificationOut) > 1:
                outString += "\nREMI:\tIt appears you wanted me to find some different things for you.\n"
                outString += "\nREMI:\tDid you want me to avoid recipes containing the following going forward?\n"
            elif len(modificationOut == 1):
                outString += "\nREMI:\tIt appears you wanted me to find something different for you.\n"
                outString += "\nREMI:\tDid you want me to avoid recipes containing it going forward?\n"
            else:
                outString += "Sorry, looks like I couldn't find any substitutions."""
            
            if not outString:
                outString = "Sorry, looks like I couldn't find any substitutions."

            for uingr in ingrs:
                userList[currentUserId].dislikedIngredients.append(uingr[0])
            #userList[currentUserId].dislikedIngredients += ingrs
            for umethod in methods:
                userList[currentUserId].dislikedMethods.append(umethod[0])
            #userList[currentUserId].dislikedMethods += methods
            userList[currentUserId].updateRecipeCatalog()
            userList[currentUserId].updateMethods()
            userList[currentUserId].updateIngredients()
            #sentiment analysis to determine if ingredients should be appended to user avoid state
            

            return outString    
                

            
        if intent == 'u':                            #Im not using this, currently is switches to handle error state for this.
            ##PRIMARY USE: UNCERTAINTY RESOLUTION
            if(userIn.lower().find("exit") != -1):
                print("Program Execution Complete.")
                pickle.dump(userList, open("userStates.dat", 'wb'))
                return "Thanks for using REMI! Have a good day!"
            print('Intent Classification: Uncertainty Detected')

            return handleError()
            #new user detection
                #proper noun?

            #refer to something in current recipe
                #if there's a number
                #word: step, else ingredient

            #conversion
                #using quantulum3, if multiple units are detected in a string, 
                #figure out how to use pint for conversions
            #genuine uncertainty- reprompt
            intent = 'icd'
        elif intent == 'icd':
            print("Input corrective domain")
            print(intent)
            return("")
            
            #parse/display something specifically in the recipe
            #if ingredient
                #quantulum3 parser to handle quantities
            #if method/step
                #also leverage quantulum3????
                #go check recipe class for viability
    #    pickle.dump(userList, open("userStates.dat", 'wb'))
    except:
        return "Ouch, I lost my train of thought. Ask me something else. (error occurred)"








def getUserIntent(userstring):
    global workingRecipe
    intent = ''
    reg = intentRegressor.predict([userstring]), intentRegressor.predict_proba([userstring])
    bayes = intentBayes.predict([userstring]), intentBayes.predict_proba([userstring])

    if bayes[0][0] == reg[0][0]:
        intent = bayes[0][0]
    else:
        if(reg[1].max() > 0.8 and (np.std(bayes[1]) > 0.18)) or reg[1].max() > 0.985:
            print('reg override', reg[1].max(), np.std(bayes[1]))
            intent = reg[0][0]
        elif(bayes[1].max() > 0.7 and (np.std(reg[1]) > 0.25)):
            print('bayes override', bayes[1].max(), np.std(reg[1]))
            intent = bayes[0][0]
        else:
            print("Probabilities:", reg[1], bayes[1])
            print("STDdevs:", np.std(reg[1]), np.std(bayes[1]))
            intent = 'u'

    return intent    


"""
    Parse For Cooking:
        This function takes in a sentence parsed by spaCy and outputs a list
        of ingredients (i.e. food nouns) and methods (i.e. cooking related verbs)
"""
def parseforcooking(inputFromUser):
    global nlp
    definitionParse = nlp(inputFromUser)
    ingredientList = list()
    methodList = parseTechniques(inputFromUser, nlp=nlp)

    defineIngList = list()
    defineMethodList = list()
    
    if len(definitionParse) < 4:
        for tok in definitionParse:
            ingredientList.append(tok.text)
    else:
        for tok in definitionParse:
            if tok.pos_ == 'NOUN':
                ingredientList.append(tok.text)


    #if ingredients found,  
    listind = 0
    for ingr in ingredientList:
        #check to see if this is actually an ingredient
        try:
            syn = wn.synsets(ingr, pos=wn.NOUN)
            ingrIndex = -1
            for s in syn:
                isIngredientHyponym = False
                ingrIndex +=1
                try:
                    hyp = s.hypernyms()[0]
                    entity = wn.synset('entity.n.01')
                    ingredient = wn.synset('ingredient.n.03')
                    herb = wn.synset('herb.n.01')
                    food = wn.synset('food.n.02')
                    while hyp:
                        #print(bechHyp)
                        if hyp == ingredient or hyp == herb or hyp == food:
                            isIngredientHyponym = True
                            break
                        if hyp == entity:
                            break
                        if hyp.hypernyms():
                            hyp = hyp.hypernyms()[0]
                    if isIngredientHyponym:
                        break
                except (IndexError):
                    #print(s, s.definition())
                    continue
            if ingrIndex != -1 and isIngredientHyponym:
                #append word and definition to list
                defineIngList.append((ingredientList[listind], syn[ingrIndex]))
        except:
            continue
        listind +=1

    listind = 0
    for method in methodList:
        try:
            syn = wn.synsets(method, pos=wn.VERB)
            mIndex = -1
            for s in syn:
                isMethodHyponym = False
                mIndex +=1
                try:
                    hyp = s.hypernyms()[0]
                    cap = 0
                    while hyp:
                        cap +=1
                        raw = wn.synset('create_from_raw_material.v.01')
                        cut = wn.synset('cut.v.01')
                        cook = wn.synset('cook.v.03')
                        heat = wn.synset('heat.v.01')
                        if hyp == cook or hyp == raw or hyp == cut or hyp == heat:
                            isMethodHyponym = True
                            break
                        if cap > 10:
                            break
                        if hyp.hypernyms():
                            hyp = hyp.hypernyms()[0]
                    if isMethodHyponym:
                        break
                except (IndexError):
                    print(s, s.definition())
                    continue
            if mIndex != -1 and isMethodHyponym:
                #append word and definition to list
                defineMethodList.append((methodList[listind], syn[mIndex]))
        except:
            continue
        listind += 1

    return defineIngList, defineMethodList