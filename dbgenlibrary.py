# Algorithms based on paper "Distribution-Based Synthetic Database Generation Techniques for Itemset Mining" by Ganesh Ramesh, Mohammed J. Zaki and William A. Maniatty

from subprocess import check_output
from collections import Counter

class ItemSet:

    def __init__(self):
        self.itemset = set()
        self.cardinality = 1
    def add(self, value):
        self.itemset.add(value)
    def size(self):
        return len(self.itemset)
    def getItemSet(self):
        return self.itemset

class DataBase:

    # Contains a list of itemsets
    def __init__(self):
        self.database = list()
        self.itemUniverseSup = Counter()

    def getDataBase(self):
        return self.database

    def append(self, value):
        self.database.append(value)

    def size(self):
        return len(self.database)

    def getMaxSup(self):  # Maximum of the absolute support values of all the singleton items of DB
        self.itemUniverseSup.clear()
        for itemset in self.getDataBase():
            self.itemUniverseSup.update(itemset.getItemSet())
        return max(self.itemUniverseSup.values())

    def appendDB(self, auxDB):
         for itemset in auxDB.getDataBase():
             self.getDataBase().append(itemset)

class DbGen:

    def __init__(self, input_item_delimiter, output_item_delimiter, minimum_support_list, targetype, output_format, inputfile, maximalout):
        self.input_item_delimiter = input_item_delimiter
        self.output_item_delimiter = output_item_delimiter
        self.minimum_support_list = minimum_support_list
        self.targetype = targetype
        self.output_format = output_format
        self.inputfile = inputfile
        self.maximalout = maximalout
        self.collection_list = [DataBase() for _ in self.minimum_support_list] # list of maximal collections Ex: M1, M2, M3
        self.minSupLevels = list()
        self.DB = DataBase()

    def dbGenBasic(self):
        self.loadCollections()
        if self.satisfyContainmentProp():
            self.runDbGenBasic()
        else:
            raise Exception("This DB does not satisfy the containment property.")

    def runDbGenBasic(self):
         collectionsSize = len(self.collection_list) # number of maximal collections
         step = 1 # current level
         absoluteSupLevel = 1 # Absolute support level
         self.minSupLevels.clear()
         self.minSupLevels.append(absoluteSupLevel)
         self.DB = self.genOperator(step, absoluteSupLevel)
         for step in range(2, collectionsSize + 1):
             absoluteSupLevel = self.getSupportLevel()
             self.minSupLevels.append(absoluteSupLevel)
             self.getDB().appendDB(self.genOperator(step, absoluteSupLevel))

    def getDB(self):  # Get final database
        return self.DB

    def getDBsize(self):
        return self.DB.size()

    def getSupportLevel(self):
        return self.getDB().getMaxSup() + 1

    def getRelMinSupLev(self): # Get relative minimum support levels
        return [minsup/self.getDBsize() for minsup in self.minSupLevels]

    def getAbsMinSupLev(self): # Get absolute minimum support levels
        return self.minSupLevels

    def genOperator(self, level, absoluteSupLevel):
        return DataBase()

    def loadCollections(self):
        self.collection_list.clear()
        for levelsupport in self.minimum_support_list:
            command = "apriori.exe" + " " + self.input_item_delimiter + " " + self.output_item_delimiter + " " + levelsupport + " " + self.targetype + " " + self.output_format + " " + self.inputfile + " " + self.maximalout
            temp_collection = check_output(command, shell=True).decode("utf-8").strip().split("\n")  # contains the maximal itemset list with useless space characters
            collection = [itemset.strip() for itemset in temp_collection]  # contains a maximal collection, ex: Mi
            mc = DataBase()
            for i in collection:
                itemset = ItemSet()
                for item in i.split(","):
                    itemset.add(item)
                mc.append(itemset)
            self.collection_list.append(mc)

    def getCollections(self):
        return self.collection_list

    def satisfyContainmentProp(self): # check if the maximal collections satisfy the containment property. Ex: Mk [ Mk-1 [ ... [ M2 [ M1
        i = 0
        while i < (len(self.collection_list) - 1):
           j = i + 1
           mc1 = self.collection_list[i].getDataBase() # returns a list of ItemSet
           mc2 = self.collection_list[j].getDataBase()
           for itemset2 in mc2:
               isSubset = False
               for itemset1 in mc1:
                    if set(itemset2).issubset(itemset1):
                        isSubset = True
                        break
               if not isSubset:
                   return False
           return True

