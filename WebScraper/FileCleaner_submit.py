#Scott Lorance and Cole Bennett
# March 2023
import sys
import os
import re
import nltk
import string
import pickle
import urllib
import os
import sys
from nltk.corpus import stopwords
from collections import OrderedDict

#import requests
from urllib import request
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize
import glob
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd

def main():
    """Takes in a URL and a keyword and does a limited depth web crawl to find relevant terms.
    """
    nltk.download("punkt")
    nltk.download("stopwords")
    current_directory = os.getcwd()
    dirtyFiles = os.path.join(current_directory, r'dirtyTxts')
    final_directory = os.path.join(current_directory, r'cleanTxts')
    if not os.path.exists(final_directory):
       os.makedirs(final_directory)
    #print(directory)
    dictionaries = cleanFiles(dirtyFiles)
    print (list(dictionaryMerger(dictionaries).items())[0:50])

    #implement tf-idf to find better terms

    #gather a list of the file names for the creation of the KB
    fileList = list()
    for filename in glob.glob(os.path.join(final_directory, '*.txt')):
        fileList.append(filename)

    #calculate tf-idf and format output for printing
    vectorizer = TfidfVectorizer(input= 'filename', decode_error='ignore')
    tfIdf = vectorizer.fit_transform(fileList)
    df = pd.DataFrame(tfIdf[0].T.todense(), index=vectorizer.get_feature_names_out(), columns=["TF-IDF"])
    df = df.sort_values('TF-IDF', ascending=False)

    print("Top 100 Terms via tf-idf:\n")
    print (df[:50])
    print(df[50:100])

    #selected top 10 words from above
    top10words = [
        "cuisine",
        "cup",
        "food",
        "rice",
        "tablespoons",
        "pinch",
        "making",
        "butter",
        "sugar",
        "chocolate"
                ]
    
    print("10 Words Selected via Domain Knowledge:\n", top10words)
    
    #generate a list of all cleaned sentences
    sentences = list()
    for files in glob.glob(os.path.join(dirtyFiles, '*.txt')):
        with open(filename, 'r',  encoding="utf8") as f:
            rawText = f.read()
            rawText = re.sub("\n", " ", rawText)
            rawText = re.sub(r'\W+', ' ', rawText)
            rawText = re.sub(r'[0-9]', ' ', rawText)
            rawTexts = re.split("[^A-Za-z0-9 ]|[ ]{3,}", rawText)
            for rt in rawTexts:
                senttok = nltk.sent_tokenize(rt)
                sentences.append(senttok)
            #sentences.append(rawText)

    #iterate through all sentences, if they contain a top 10 word, key them with the nth occurance of the word and store in the KB dictionary
    dictCountTracker = [0,0,0,0,0,0,0,0,0,0]
    knowledgebase = dict()
    print(len(sentences[0]))
    for sentlist in sentences:
        for sent in sentlist:
            count = 0
            for word in top10words:
                if(sent.find(word) != -1):
                    #sentCheck = sent
                    #if(len(sentCheck.split(" ")) > 2):
                    keystr = str(top10words[count]) + str(dictCountTracker[count])
                    dictCountTracker[count] += 1
                    knowledgebase[keystr] = sent
                    break
                count += 1
    
    #print 20 entries from the knowledge base
    print(str(OrderedDict(list(knowledgebase.items())[80:])))

    pickle.dump(knowledgebase, open("knowledge_base.p", "wb"))

def dictionaryMerger(dictList):
    bigDict = dict()
    for smallDict in dictList:
        for word, count in smallDict.items():
            if word in bigDict:
                bigDict[word] += smallDict[word]
            else:
                bigDict[word] = smallDict[word]
    bigDict = dict(sorted(bigDict.items(), key=lambda item: item[1], reverse = True))
    return bigDict
    
        
    

def cleanFiles(websitesFolder):
    #print(websitesFolder)
    counter = 0
    docTerms = []
    for filename in glob.glob(os.path.join(websitesFolder, '*.txt')):
        counter = counter + 1 
        with open(filename, 'r',  encoding="utf8") as f:
            text = f.read()
            print (filename)
            print (len(text))
            text = text.split()
            text = ' '.join(text)
            sentences = sent_tokenize(text)
            newFileName = 'cleaned' + str(counter) + '.txt'
            current_directory = os.getcwd()
            final_directory = os.path.join(current_directory, r'cleanTxts')
            print(newFileName)
            with open(os.path.join(final_directory, newFileName), 'w', encoding="utf-8") as f2:
                for sent in sentences:
                    #print(sent)
                    f2.write(sent.lower())
                    f2.write('\n')
            docTerms.append(listGen(os.path.join(final_directory, newFileName)))
    return docTerms
        
def listGen(fName):
    
    #read in file input
    with open(fName, 'r', encoding='utf8') as inFile:
        rawText = inFile.read()
    
    #remove newlines and tokenize
    rawText = re.sub("\n", "", rawText)
    rawText = re.sub(r'\W+', ' ', rawText)
    rawText = re.sub(r'[0-9]', ' ', rawText)
    
    textTok = nltk.word_tokenize(rawText)
    textTok = filterTokens(textTok)

    #if needed/explore difference in outcome- token preprocessing
    '''
    textTok = [tok for tok in tokens if(tok.isalpha())]
    textTok = [tok.lower() for tok in tokens]
    '''    

    #construct unigram and bigram lists, unpack for dict construction
    unigram = textTok

    #get unique entries for unigram/bigram
    uniqUnigram = list(set(unigram))

    #construct unigram and bigram dictionaries
    unigram = {gram:unigram.count(gram) for gram in uniqUnigram}
    unigram = sorted(unigram.items(), key= lambda x: x[1], reverse=True)

    unigramD = dict()

    for gram in unigram:
        unigramD.update({gram[0]:gram[1]})

    print("file processed")
    return unigramD     

def filterTokens(inTokens):
    """Removes stop words from a list of tokens"""
    stop_words = set(stopwords.words('english'))
    otherBadWords = {'save', 'view', 'ratings', 'share', 'like', 'follow', 'subscribe', 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'}
    stop_words = stop_words.union(set(otherBadWords))
    filteredTokens = [w for w in inTokens if ((not w in stop_words))]
    return filteredTokens

if __name__ == "__main__":
    main()
