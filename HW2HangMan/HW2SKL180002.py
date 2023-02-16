#Scott Lorance
# Feb 2023
import sys
import os
import re
import nltk
import string
import random
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk import pos_tag

def main():
    """Takes in an input file as a command line argument, reads the text from
    the file and plays a game of hangman with it.
    """
    if len(sys.argv) < 2:
        print('Please enter a filename as a system arg')
    else:
        fp = sys.argv[1]
        with open(os.path.join(os.getcwd(), fp), 'r') as f: #Opens the file
            text_in = f.read()
            tokens = word_tokenize(text_in)
            print("Initial token count, including punctuation and short words:", len(tokens))
            #print("Total of all tokens:", len(tokens))
            print("(2) Lexical diversity pre filtering: {:0.2f}%\n".format(lexicalDiversity(tokens))) #2 decimal print of lexical diversity
            nltk.download("punkt")
            nltk.download("stopwords") #I do as the console output demands
            nltk.download('wordnet')
            nltk.download('averaged_perceptron_tagger')
            frequencyDictionary = freqDict(preProcess(text_in)[1])
            first50pairs = {k: frequencyDictionary[k] for k in list(frequencyDictionary)[:50]}
            print("The 50 most common nouns: ")
            print(first50pairs)
            hangMan(first50pairs)
            

def preProcess(text_in):
    """this function takes the raw text, and turns it into a list of tokens longer than 5 letters that aren't stop words.
    it also returns a list of lemmatized nouns"""
    text_in = text_in.lower() #Make it all  lowercase
    text_in = re.sub("[^a-zA-Z\s]+", "", text_in) #remove non letters

    tokens = word_tokenize(text_in) #Tokenize
    filteredTokens = filterTokens(tokens) #Removes stopwords and short words
    
    lemmatizedSet, lemmatized = lemmatizeTokens(filteredTokens) #turns into lemmas.
    
    tokens_tagged = pos_tag(lemmatizedSet) #Tags only unique words, saves computation at cost of some accuracy
    nounsOnly = []
    for taggedToken in tokens_tagged: 
        if taggedToken[1] == 'NN' :
            nounsOnly.append(taggedToken[0]) #Only keep the nouns
    firstTwenty = nounsOnly[:20]
    print('Number of unique noun lemmas:', len(nounsOnly))
    print('(3.c) First 20 unique nouns tagged (its a set, order varies run to run):' )
    print(firstTwenty)
    print("(3.e) Total tokens after removing numbers, stopwords and punctuation:" , len(filteredTokens))
    culledList = []
    for lemmaToken in lemmatized:
        if lemmaToken in nounsOnly:
            culledList.append(lemmaToken)
    print("(3.e) Number of nouns after lemmatizing and filtering (Includes repeats):" , len(culledList))
    return(filteredTokens, culledList)
    
    
    #print("Total non-stopwords with length > 5:", len(tokens))
    #print("Lexical diversity after filtering:", lexicalDiversity(tokens))

def filterTokens(inTokens):
    """Removes short words and stop words from a list of tokens"""
    stop_words = set(stopwords.words('english'))
    filteredTokens = [w for w in inTokens if ((not w in stop_words) and (len(w)> 5))]
    return filteredTokens


def lexicalDiversity(inTokens):
    """Calculates lexical diversity as a percentage given a list of tokens"""
    return (len(set(inTokens))/len(inTokens))*100


def lemmatizeTokens(inTokens):
    lemmatized = []
    lemmatizer = WordNetLemmatizer()
    for token in inTokens:
        lemmatized.append(lemmatizer.lemmatize(token))
    lemmatizedSet = set(lemmatized)
    return (lemmatizedSet, lemmatized)

def freqDict(wordList):
    """For any given list of words, make a sorted dictionary in order from most common to least."""
    frequencyDict = dict()
    for word in wordList:
        if word in frequencyDict:
            frequencyDict[word] += 1
        else:
            frequencyDict[word] = 1
    frequencyDict = dict(sorted(frequencyDict.items(), key=lambda item: item[1], reverse = True))
    return frequencyDict

def hangMan(wordBank):
    score = 5
    guess = ""
    userInput = ""
    print("Now Playing hangman.")
    while (score > 0 and userInput != "!"):
        targetWord = random.choice(list(wordBank.keys()))
        displayText = ""
        alreadyGuessed = []
        for charachter in targetWord:
            displayText = displayText +"_"
        while (score > 0 and displayText != targetWord and userInput != "!"):
            print ("Score =", score)
            print("Fill in the blanks")
            print(displayText)
            print ("Guess a letter")
            guess = input()
            guess = guess.lower()
            if guess not in 'abcdefghijklmnopqrstuvwxyz!':
                continue
            if guess in alreadyGuessed:
                print("You already guessed that letter")
                continue
            alreadyGuessed.append(guess)
            counter = 0
            flag = False
            stringToList = list(displayText)
            for blank in displayText:
                if guess == targetWord[counter]:
                    stringToList[counter] = guess
                    flag = True
                counter += 1
            if flag:
                print("Right!")
                score += 1
            else:
                print("Guess again.")
                score -=1
            displayText = ""
            for letter in stringToList:
                displayText += letter
            userInput = guess
        print("The word was", targetWord)
    print("Thanks for playing, goodbye.")

            
        
    

if __name__ == "__main__":
    main()
