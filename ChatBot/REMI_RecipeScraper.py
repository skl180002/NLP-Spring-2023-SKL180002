import os
import re
from urllib import request
from bs4 import BeautifulSoup
from torrequest import TorRequest

def main():
    prevurl = None
    url = "https://foodwishes.blogspot.com/"
    #url = "https://foodwishes.blogspot.com/2018/"
    #url = "https://foodwishes.blogspot.com/2020/"

    if not os.path.exists(os.getcwd() + "\\foodwishes"):
        os.mkdir(os.getcwd() + "\\foodwishes")
    if not os.path.exists(os.getcwd() + "\\allrecipes"):
        os.mkdir(os.getcwd() + "\\allrecipes")

    while(prevurl != url and url != "https://foodwishes.blogspot.com/2007/09/warning-chef-trying-to-do-something.html"):

        site = request.urlopen(url=url).read().decode('utf8')
        #print(site)
        soup = BeautifulSoup(site, features="lxml")
        for link in soup.find_all('a'):
            href = link.get('href')
            print(href)
            if(href):
                if(href.find("search?updated-max=") != -1):
                        prevurl = url
                        url = href
                elif(validateLink(href)):
                    foodWishScrape(href) if(href.find("allrecipe") == -1) else allRecipeScrape(href)

def foodWishScrape(link):
    grailText = "the-story-of-kismet-and-other-major"
    try:
        fwSite = request.urlopen(url= link).read().decode()
        if(fwSite.find(grailText) == -1 and (fwSite.find('ingredient') != -1 or fwSite.find('Ingredient') != -1)):
            fname = re.sub('[^0-9a-zA-Z]+', '_', link[link.find('com')+3:])

            recipeStart = fwSite.find("<iframe allow=\"autoplay; encrypted-media\" allowfullscreen=\"\" frameborder=\"0\" height=\"315\" src=\"https://www.youtube.com") + len("<iframe allow=\"autoplay; encrypted-media\" allowfullscreen=\"\" frameborder=\"0\" height=\"315\"")
            recipeEnd = fwSite.find("/* Font Definitions */")

            recipeEnd = recipeEnd if recipeEnd != -1 else fwSite.find("<a data-pin-do='buttonBookmark' href='//pinterest.com/pin/create/button/'>")

            fwSite = fwSite[recipeStart:recipeEnd]

            with open("foodwishes\\" + fname + ".txt", "w", encoding="utf8") as f:
                f.write(fwSite)
            return link
    except:
        print("Expired Link")
    return

def validateLink(link):
    if(not link):
        return False
    elif(link.find(".com") == -1):
        return False
    elif(link.find("foodwishes.blogspot.com/") != -1):
        if(link[-7:].find('.html') != -1):
            return True  
        else:
            return False
    elif(link.find("www.allrecipes.com") == -1):
        return False

    return True

def allRecipeScrape(link):
    with TorRequest(proxy_port=9050, ctrl_port=9051, password='16:872860B76453A77D60CA2BB8C1A7042072093276A3D701AD684053EC4C') as tr:
        tr.reset_identity()
    #sleep(1.7)
    print("allscrape: ", link)
    try:
        arSite = request.urlopen(url= link).read().decode()

        #extract the raw recipe from all the boilerplate and save to file
        recipeStart = arSite.find("]\n}\n,\"name\":")
        recipeEnd = arSite.find(",\"mainEntityOfPage\":")
        arSite = arSite[recipeStart+4:recipeEnd]
        fname = re.sub('[^0-9a-zA-Z]+', '', arSite[:arSite.find('\n')])
        with open("allrecipes\\"+fname+".txt", "w", encoding= "utf8") as f:
            f.write(arSite)
    except:
        print("Expired Link")

    return link


main()