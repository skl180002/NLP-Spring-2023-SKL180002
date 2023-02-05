# Scott Lorance
# Feb 2023

import sys
import os
import re
import pickle

def main():
    """Cleans up a messy CSV input of employee data.
    Input file must be specified in the sys arg.
    """
    if len(sys.argv) < 2:
        print('Please enter a filename as a system arg')
    else:
        fp = sys.argv[1]
        with open(os.path.join(os.getcwd(), fp), 'r') as f:
            text_in = f.read()
            dictionaryToPickle = fileParser(text_in)
            #print(dictionaryToPickle)
            pickle.dump(dictionaryToPickle, open('SKL180002HW1Pickle.p', 'wb'))
            openedPickle = pickle.load(open('SKL180002HW1Pickle.p', 'rb'))
            print("Employee list:")
            print("")
            for key in openedPickle:
                openedPickle[key].display()
        
            

def fileParser(inputText):
    """Takes in the text from the file, returns a dictionary of employees.
    ARGS: Input string from opened file
    """
    tokenList = re.split(',|\n', inputText)
    tokenList = tokenList[5:]
    print(tokenList)
    employeeList = dict()
    for employee in chunker(tokenList, 5):
        employee[0] = employee[0].capitalize()
        employee[1] = employee[1].capitalize()
        if not employee[2]:
           # print("Debug: was blank")
            employee[2] = "X"
        else:
            #print("Debug, was", employee[2])
            employee[2] = employee[2].capitalize()[0]
        while not re.match(r"[A-Za-z][A-Za-z]\d\d\d\d", employee[3]):
            print("ID invalid:", employee[3])
            print("ID format is two letters followed by four didgits")
            employee[3] = input("Please enter a valid id:")
        while not re.match(r"\d\d\d-\d\d\d-\d\d\d\d", employee[4]):
            print("Phone invalid:", employee[4])
            print("Phone format is 123-456-7890")
            employee[4] = input("Please enter a valid phone number:")
        if employee[3] in employeeList:
            print("Employee ID already in list, duplicate skipped.")
        else:
            employeeList.update({employee[3]: Person(employee[0], employee[1], employee[2], employee[3], employee[4])})
    return employeeList

        
def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))
    #Chunking utility from stack exchange user nosklo. Turns a list into sub lists of size 'size'.

class Person:
    """Contains employ info.
    """
    def __init__(self, lastName, firstName, midInit, empId, phone):
        self.lastName = lastName
        self.firstName = firstName
        self.midInit = midInit
        self.empId = empId
        self.phone = phone
    def __str__(self):
        return (self.lastName +" "+ self.firstName +" "+ self.midInit +" "+ self.empId +" "+ self.phone)
    def display(self):
        print("Employee id:", self.empId)
        print("\t", self.firstName, self.midInit, self.lastName)
        print("\t", self.phone)
      

if __name__ == "__main__":
    main()
