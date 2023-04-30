import pickle
import random
from DictBuilder import Recipe
def main():
    with open('recipeDictPickle', 'rb') as f:
        x = pickle.load(f)
        print(x.keys())
        while (True):
            y  = input("Type the name of the recipe from the list, or r for a random recipe")
            if y in x.keys():
                  print(x[y])
            else:
                capital = random.choice(list(x.values()))
                print(capital)

if __name__ == "__main__":
    main()
