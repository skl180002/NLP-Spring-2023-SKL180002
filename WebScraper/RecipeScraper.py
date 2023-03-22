#Cole Bennett and Scott Lorance
# March 2023

import os
from urllib import request
from bs4 import BeautifulSoup

#IMPORTANT: Please ensure you have lxml for Beautiful Soup installed, if not remove the feature='lxml' speficiation in the function call

def main():
    #due to code body being fine tuned for this specific url, hard code starting url
    url = "https://foodwishes.blogspot.com/"

    #set up parameters for depth and breadth of crawl
    #websiteLinkDepth controls how many links are scraped from each website, totalLinkCap controls how many links to get total (if depth is limited, crawler will branch out further)
    websiteLinkDepth = max
    iterationTracker = 0
    totalLinkCap = 400
    blogLinks, nonBlogLinks = crawl(url, iterationTracker, websiteLinkDepth)

    #error handling: if bad links slipped through, catch them here
    blogLinks = cleanListofLinks(blogLinks)
    nonBlogLinks = cleanListofLinks(nonBlogLinks)

    #to ensure all links being sraped in the while loop are fresher, 
    prevBlogLinks = blogLinks
    prevNonBlogLinks = nonBlogLinks
     
    '''
        TODO for chatbot corpus:
            -def checkNovelLink: function that takes in a master list of all links scraped so far and returns true if the new link passed in is not found in the list
            -For chatbot, if site scraped matches foodwishes recipe format, don't bother scraping it for further links
            -modify how I'm cleaning the list of links to reduce outgoing requests in case I run into issues with timeouts for scraping

            -for debugging: additionally print out non-sanitized websites to examine link content

    '''

    #keep scraping while the total number of links is less than the cap
    while(len(blogLinks) + len(nonBlogLinks) < totalLinkCap):
        #for better organization of files and examination of behavior as crawler gets further out, store each iteration in separate folders denoted by iterationTracker
        iterationTracker += 1

        #initialize temporary link holders
        tempBL1 = tempBL2 = tempNBL1 = tempNBL2 = newBlogLinks = newNonBlogLinks = list()

        #for each link in the newly scraped section of the overall list of links, crawl and scrape them, then add results to correct list
        #first crawl the original domain and scrape links
        #for blogLink in blogLinks[newBlogTrack-1:]:
        for blogLink in prevBlogLinks:
            #in case the original url is found again, just skip over it
            if(blogLink != url):
                tempBL1, tempNBL1 = crawl(blogLink, iterationTracker, websiteLinkDepth)
                iterationTracker += 1
                newBlogLinks.append(tempBL1)
                newNonBlogLinks.append(tempNBL1)
                #allow crawler to stop at the soonest possible point
                if len(blogLinks) + len(nonBlogLinks) > totalLinkCap:
                    break
        
        #next crawl around non-domain links and scrape what can be scraped
        #for nblink in nonBlogLinks[newNonBlogTrack-1:]:
        for nblink in prevNonBlogLinks:
            #if somehow one non-domain site links back to the original url, skip over it
            if(blogLink != url):
                tempBL2, tempNBL2 = crawl(nblink, iterationTracker, websiteLinkDepth)
                iterationTracker += 1
                newBlogLinks.append(tempBL2)
                newNonBlogLinks.append(tempNBL2)
                #allow crawler to stop at the soonest possible point
                if len(blogLinks) + len(nonBlogLinks) > totalLinkCap:
                    break
        if len(blogLinks) + len(nonBlogLinks) > totalLinkCap:
                break

        #if any links slip through that might throw errors, catch them here before continuing
        newBlogLinks = cleanListofLinks(newBlogLinks)
        newNonBlogLinks = cleanListofLinks(newNonBlogLinks)

        prevBlogLinks = newBlogLinks
        prevNonBlogLinks = newNonBlogLinks

        blogLinks.append(newBlogLinks)
        nonBlogLinks.append(newNonBlogLinks)
        
        

def crawl(url, count, cap):
    try:
        #scrape the url and generate the initial soup object
        isNotFoodwishesFlag = False if url.find("foodwishes") == -1 else True
        site = request.urlopen(url= url).read().decode('utf8')
        soup = BeautifulSoup(site, features="lxml")

        #create separate lists for links within the same website domain and for links outside the domain
        foodWishLinkList = list()
        nonFoodWishLinkList = list()
        foodWishCount = 0
        nonFoodWishCount = 0

        #generate a file of links for each page
        with open("linkdocs\\links{0}.txt".format(count), 'w', encoding='utf8') as file:
            #if the subfolder to store crawled/scraped data does not exist, create it
            if not os.path.exists(os.getcwd() + "\\foodwishesContent{0}".format(count)):
                os.mkdir(os.getcwd() + "\\foodwishesContent{0}".format(count))
            if not os.path.exists(os.getcwd() + "\\nonfoodwishesContent{0}".format(count)):
                os.mkdir(os.getcwd() + "\\nonfoodwishesContent{0}".format(count))

            for link in soup.find_all('a'):
                #create string for each link in the soup and a formatted version to allow it to become a unique filename
                linkString = str(link.get('href'))
                fileNameString = linkString[linkString.find("//") + 2:]
                fileNameString = "".join(c for c in fileNameString if c.isalnum())
                
                #if the link is a recipe from the original domain and the parent url is from the original domain, scrape until n=count valid links are scraped, or the list is exhausted
                if(linkString.find("foodwishes.blogspot.com") != -1 and linkString != "https://foodwishes.blogspot.com/" and linkString.find("search/label") == -1 and linkString.find("netvibes.com") == -1 and linkString.find("yahoo.com") == -1 and foodWishCount < cap and isNotFoodwishesFlag):
                    with open(("foodwishesContent{0}\\".format(count) + fileNameString + ".txt"), "w", encoding='utf8') as textFile:
                        try:
                            textFile.write(scrape(linkString))
                            file.write(linkString + '\n')
                            foodWishLinkList.append(linkString)
                            foodWishCount += 1
                            print(link.get('href'), "recipe", foodWishCount)
                        except:
                            print("Bad Link")

                #if the link is not from the original domain and valid, scrape until n=count links are scraped, or the list is exhausted
                elif(nonFoodWishCount < cap and linkString.find("foodwishes") == -1 and linkString.find("javascript: void") == -1 and linkString.find('#') == -1 and linkString.find("javascript:void") == -1 and linkString.find(".") != -1 and linkString.find("youtube") == -1 and linkString.find("blogger.com") == -1 and linkString.find("pinterest") == -1 and linkString.find("yahoo") == -1 and linkString.find("magazine.com") == -1):
                    with open(("nonfoodwishesContent{0}\\".format(count) + fileNameString + ".txt"), "w", encoding= 'utf8') as textFile:
                        try:
                            textFile.write(scrape(linkString))
                            file.write(linkString + '\n')
                            nonFoodWishLinkList.append(linkString)
                            nonFoodWishCount += 1
                            print(link.get('href'), "nonrecipe", nonFoodWishCount)
                        except:
                            print("Bad Link")
        #return a list of links within the domain and outside to allow finer control over the direction of the crawl if desired
        return foodWishLinkList, nonFoodWishLinkList
    #if a bad website is somehow passed in to this function, return nothing
    except:
        print("uhoh")
        return list(), list()
    

def scrape(link):
    #generate a soup object for the link found on the website currently being scraped
    soup = BeautifulSoup(request.urlopen(link).read().decode('utf8'), features="lxml")

    #remove script/style garbage and return the main content of the site
    for script in soup(["script", "style"]):
        script.extract()
    
    return soup.get_text()

#function to remove any links that throw errors when requested
def cleanListofLinks(llist):
    retlist = list()
    for link in llist:
        try:
            request.urlopen(url= link).read().decode('utf8')
            retlist.append(link)
        except:
            print("Bad Link Slipped Through: ", link)

    return retlist

main()
