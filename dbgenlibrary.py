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

    def getUniverseSup(self):  # Maximum of the absolute support values of all the singleton items of DB
        self.itemUniverseSup.clear()
        for itemset in self.getDataBase():
            self.itemUniverseSup.update({}.fromkeys(itemset.getItemSet(), itemset.cardinality))
        return self.itemUniverseSup

class DbGen:
    def __init__(self, input_item_delimiter, output_item_delimiter, minimum_support_list, targetype, output_format, inputfile, maximalout):
        self.input_item_delimiter = input_item_delimiter
        self.output_item_delimiter = output_item_delimiter
        self.minimum_support_list = minimum_support_list
        self.targetype = targetype
        self.output_format = output_format
        self.inputfile = inputfile
        self.maximalout = maximalout
        self.collection_list = list()  # list of maximal collections Ex: M1, M2, M3
        self.minSupLevels = list()

    # collection_list = [DataBase(), DataBase(),...]
    # colection_list[i] = [ItemSet(), ItemSet(),...]
    def dbGenBasic(self):
        self.loadCollections()
        if self.satisfyContainmentProp():
            self.runDbGenBasic()
        else:
            raise Exception("This DB does not satisfy the containment property.")

    def runDbGenBasic(self):
        absoluteSupLevel = 1  # Absolute support level
        self.minSupLevels.clear()
        self.minSupLevels.append(absoluteSupLevel)
        numberCollections = self.getNumCollections()  # number of maximal collections
        for step in range(1, numberCollections):  # M1 saved at 0 zero, M2 at 1 one, ...
            absoluteSupLevel = self.getSupportLevel()
            self.minSupLevels.append(absoluteSupLevel)
            self.genOperator(step, absoluteSupLevel)

    def getDBsize(self):
        count = 0
        for db in self.getCollections():
            count += db.size()
        return count

    def getSupportLevel(self, step):
        counter = Counter()
        for db in self.collection_list[0: step]:
            counter += db.getUniverseSup()
        return max(counter.values()) + 1

    def getRelMinSupLev(self):  # Get relative minimum support levels
        return [minsup / self.getDBsize() for minsup in self.minSupLevels]

    def getAbsMinSupLev(self):  # Get absolute minimum support levels
        return self.minSupLevels

    def genOperator(self, step, absoluteSupLevel):
        for itemset in self.collection_list[step].getDataBase():
            itemset.cardinality = absoluteSupLevel

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

    def getNumCollections(self):
        return len(self.collection_list)

    def satisfyContainmentProp(self):  # check if the maximal collections satisfy the containment property. Ex: Mk [ Mk-1 [ ... [ M2 [ M1
        numberCollections = self.getNumCollections()
        if numberCollections == 1:
            return True
        i = 0
        while i < (numberCollections - 1):
            j = i + 1
            mc1 = self.collection_list[i].getDataBase()  # returns a list of ItemSet
            mc2 = self.collection_list[j].getDataBase()
            for itemset2 in mc2:
                isSubset = False
                set2 = itemset2.getItemSet()
                for itemset1 in mc1:
                    if set2.issubset(itemset1.getItemSet()):
                        isSubset = True
                        break
                if not isSubset:
                    return False
            i += 1
        return True

    def printDB(self):
        [[print(",".join(itemset.getItemSet())) for itemset in db.getDataBase()] for db in self.getCollections()]

    def satisfyInverseMiningProp(self):
        pass
