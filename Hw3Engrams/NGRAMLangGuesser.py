#Scott Lorance
# Feb 2023
import sys
import os
import re
import nltk
import string
import pickle
from nltk.tokenize import word_tokenize
from nltk.util import ngrams

def main():
    """Takes in a test set and a labels file as command line arguments.
    The pickled dictionaries are hard coded. Outputs a prediction for the language
    of each line in the test, and an accuracy score.
    """
    if len(sys.argv) < 3:
        print('Please enter a filename for the test set AND label set as a system argument. The pickles are hard coded.')
    else:
        fp1 = sys.argv[1]
        with open(os.path.join(os.getcwd(), fp1), 'r') as f1: #Opens the test file
            text_in = f1.read()
            lines = text_in.splitlines() #We split input into lines
            
            fp2 = sys.argv[2]
            with open(os.path.join(os.getcwd(), fp2), 'r') as f2: #Opens the label file
                labelsBlock = f2.read()
                labels = labelsBlock.splitlines() # We split target into lines
                EnglishBigrams = pickle.load(open('b.English.p', 'rb'))
                EnglishUnigrams = pickle.load(open('u.English.p', 'rb'))
                #print('type:', EnglishUnigrams['the'])
                EnglishProbs = langProb(lines, EnglishBigrams, EnglishUnigrams) #Generates a list of probabilities that each line is english
                FrenchBigrams = pickle.load(open('b.French.p', 'rb'))
                FrenchUnigrams = pickle.load(open('u.French.p', 'rb'))
                FrenchProbs = langProb(lines, FrenchBigrams, FrenchUnigrams)
                ItalianBigrams = pickle.load(open('b.Italian.p', 'rb'))
                ItalianUnigrams = pickle.load(open('u.Italian.p', 'rb'))
                ItalianProbs = langProb(lines, ItalianBigrams, ItalianUnigrams)
                guesser(EnglishProbs, FrenchProbs, ItalianProbs, labels)

def langProb(testLines, Bigrams, Unigrams):
    """Takes in a set of lines, and two dictionaries of frequencies.
        finds the probability of it being the language of the dictionaries.
        returns a list of probabilities
    """
    probs = []
    bigN = sum(Unigrams.values())
    bigV = len(Unigrams)
    for Line in testLines:
        lineUni = word_tokenize(Line)
        lineBi = list(ngrams(lineUni,2))
        
        #Good-Turing smoothing looked easier, so we're gonna use that.
        #Ignore above, reread the rubric :(
        #Also, apparently the function is in the slides. EZ mode.
        prob = 1
        for bigram in lineBi:
            n = Bigrams[bigram] if bigram in Bigrams else 0
            d = Unigrams[bigram[0]] if bigram[0] in Unigrams else 0
            prob = prob * ((n+1)/(d+bigV))
            """ if d == 0:
                prob = prob*(1/bigN)
            else:
                prob = prob * (n / d)
            """
        probs.append(prob)
    return probs

def guesser(engProbs, frProbs, itProbs, answerKey):
    f = open("guesses.txt", "w")
    score = 0
    for prob in range(len(engProbs)):
        guess = str(prob+1)
        if engProbs[prob] >= frProbs[prob] and engProbs[prob] >= itProbs[prob]:
            guess = guess + " English"
        elif frProbs[prob] >= engProbs[prob] and frProbs[prob] >= itProbs[prob]:
            guess = guess + " French"
        elif itProbs[prob] >= engProbs[prob] and itProbs[prob] >= frProbs[prob]:
            guess = guess + " Italian"
        if guess == answerKey[prob]:
            score = score + 1
        else:
            print("Wrong guess on line", prob + 1)
        f.write(guess)
        maxProb = max(engProbs[prob], frProbs[prob], itProbs[prob])
        #print (maxProb)
        f.write(' ' + str(maxProb))
        f.write('\n')
        #Stuff
    print("Guess Accuracy:", score/len(answerKey))
    f.close()       


if __name__ == "__main__":
    main()
