import nltk
import sys
import re
import pickle

def main():
    isEasyInput = True
    if(isEasyInput):
        fileNames = ("C:\\Users\\benne\\Google Drive\\Laptop Sync\\UTD\\CS 4395\\Assignments\\Assignment 4- ngrams\\data\\data\\LangId.train.English",
                    "C:\\Users\\benne\\Google Drive\\Laptop Sync\\UTD\\CS 4395\\Assignments\\Assignment 4- ngrams\\data\\data\\LangId.train.French",
                    "C:\\Users\\benne\\Google Drive\\Laptop Sync\\UTD\\CS 4395\\Assignments\\Assignment 4- ngrams\\data\\data\\LangId.train.Italian")
    else:
        fileNames = (sys.argv[1], sys.argv[2], sys.argv[3])
    
    for file in fileNames:
        unigramDict, bigramDict = listGen(file)
        pickle.dump(unigramDict, open("u" + file[file.rfind('.'):] + ".p", "wb" ))
        pickle.dump(bigramDict, open("b" + file[file.rfind('.'):] + ".p", "wb" ))


def listGen(fName):
    
    #read in file input
    with open(fName, 'r', encoding='utf8') as inFile:
        rawText = inFile.read()
    
    #remove newlines and tokenize
    rawText = re.sub("\n", "", rawText)
    textTok = nltk.word_tokenize(rawText)

    #if needed/explore difference in outcome- token preprocessing
    '''
    textTok = [tok for tok in tokens if(tok.isalpha())]
    textTok = [tok.lower() for tok in tokens]
    '''    

    #construct unigram and bigram lists, unpack for dict construction
    unigram = textTok
    bigram = nltk.ngrams(textTok,2)
    
    bigram = [*bigram]

    #get unique entries for unigram/bigram
    uniqUnigram = list(set(unigram))
    uniqBigram = list(set(bigram))

    #construct unigram and bigram dictionaries
    unigram = {gram:unigram.count(gram) for gram in uniqUnigram}
    unigram = sorted(unigram.items(), key= lambda x: x[1], reverse=True)

    bigram = {gram:bigram.count(gram) for gram in uniqBigram}
    bigram = sorted(bigram.items(), key= lambda x: x[1], reverse=True)

    unigramD = dict()
    bigramD = dict()

    for gram in unigram:
        unigramD.update({gram[0]:gram[1]})
    
    for gram in bigram:
        bigramD.update({gram[0]:gram[1]})

    print("file processed")
    return unigramD, bigramD

#check for proper file system argument input
if __name__ == '__main__':
    if len(sys.argv) < 4 and not True:
        print('Please enter all filenames as a series of system arguments')
    else:
        main()   

