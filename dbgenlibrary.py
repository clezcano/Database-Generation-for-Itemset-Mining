# Implementation of algorithms based on paper "Distribution-Based Synthetic Database Generation Techniques for Itemset Mining" by Ganesh Ramesh, Mohammed J. Zaki and William A. Maniatty

from subprocess import check_output
from collections import Counter
from enum import Enum
import csv

class DbGenType(Enum):
    Basic = 1
    Optimized = 2

class ItemSet:
    def __init__(self):
        self.itemset = set()
        self.basicCardinality = 1  # DbGenBasic algorithm updates this parameter
        self.optimizedCardinality = 1  # DbGenOptimized algorithm updates this parameter

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

    def size(self, algorithm):
        count = 0
        for itemset in self.getDataBase():
            if algorithm == DbGenType.Basic:
                count += itemset.basicCardinality
            elif algorithm == DbGenType.Optimized:
                count += itemset.optimizedCardinality
        return count

    def getUniverseSup(self):  # Maximum of the absolute support values of all the singleton items of DB
        self.itemUniverseSup.clear()
        for itemset in self.getDataBase():
            self.itemUniverseSup.update({}.fromkeys(itemset.getItemSet(), itemset.basicCardinality))
        return self.itemUniverseSup

class DbGen:
    # collection_list = [DataBase(), DataBase(),...]
    # colection_list[i] = [ItemSet(), ItemSet(),...]
    def __init__(self, input_item_delimiter, output_item_delimiter, minimum_support_list, targetype, output_format, inputfile, maximalout):
        self.input_item_delimiter = input_item_delimiter
        self.output_item_delimiter = output_item_delimiter
        self.minimum_support_list = minimum_support_list
        self.targetype = targetype
        self.output_format = output_format
        self.inputfile = inputfile
        self.maximalout = maximalout
        self.collection_list = list()  # list of maximal collections Ex: M1, M2, M3
        self.basicMinSupLevels = list()  # Minimum support levels of dbGenBasic algorithm
        self.optimizedMinSupLevels = list()  # Minimum support levels of dbGenOptimized algorithm
        self.loadCollections()
        if not self.satisfyContainmentProp():
            raise Exception("This DB does not satisfy the containment property.")

    def dbGenOptimized(self):
        pass


    def dbGenBasic(self):
        absoluteSupLevel = 1  # Absolute support level
        self.basicMinSupLevels.clear()
        self.basicMinSupLevels.append(absoluteSupLevel)
        numberCollections = self.getNumCollections()  # number of maximal collections
        for step in range(1, numberCollections):  # M1 saved at 0 zero, M2 at 1 one, ...
            absoluteSupLevel = self.getSupportLevel()
            self.basicMinSupLevels.append(absoluteSupLevel)
            self.genOperator(step, absoluteSupLevel, DbGenType.Basic)

    def getDBsize(self, algorithm):
        count = 0
        for db in self.getCollections():
            if algorithm == DbGenType.Basic:
                count += db.size(DbGenType.Basic)
            elif algorithm == DbGenType.Optimized:
                count += db.size(DbGenType.Optimized)
        return count

    def getSupportLevel(self, step):
        counter = Counter()
        for db in self.collection_list[0: step]:
            counter += db.getUniverseSup()
        return max(counter.values()) + 1

    def getRelMinSupLev(self, algorithm):  # Get relative minimum support levels
        if algorithm == DbGenType.Basic:
            BasicDBsize = self.getDBsize(DbGenType.Basic)
            return [minsup / BasicDBsize for minsup in self.basicMinSupLevels]
        elif algorithm == DbGenType.Optimized:
            OptimizedDBsize = self.getDBsize(DbGenType.Optimized)
            return [minsup / OptimizedDBsize for minsup in self.optimizedMinSupLevels]

    def getAbsMinSupLev(self, algorithm):  # Get absolute minimum support levels
        if algorithm == DbGenType.Basic:
            return self.basicMinSupLevels
        elif algorithm == DbGenType.Optimized:
            return self.optimizedMinSupLevels

    def genOperator(self, step, absoluteSupLevel, algorithm):
        for itemset in self.collection_list[step].getDataBase():
            if algorithm == DbGenType.Basic:
                itemset.basicCardinality = absoluteSupLevel
            elif algorithm == DbGenType.Optimized:
                itemset.optimizedCardinality = absoluteSupLevel

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

    def printDB(self, algorithm):
        if algorithm == DbGenType.Basic:
            [[[print(",".join(itemset.getItemSet())) for _ in range(itemset.basicCardinality)] for itemset in db.getDataBase()] for db in self.getCollections()]
        elif algorithm == DbGenType.Optimized:
            [[[print(",".join(itemset.getItemSet())) for _ in range(itemset.optimizedCardinality)] for itemset in db.getDataBase()] for db in self.getCollections()]

    def printDBtoFile(self, fileName, algorithm):
        csvFile = open(fileName, 'w', newline='')
        csvWriter = csv.writer(csvFile, delimiter=',', lineterminator='\n')
        if algorithm == DbGenType.Basic:
            [[[csvWriter.writerow(itemset.getItemSet()) for _ in range(itemset.basicCardinality)] for itemset in db.getDataBase()] for db in self.getCollections()]
        elif algorithm == DbGenType.Optimized:
            [[[csvWriter.writerow(itemset.getItemSet()) for _ in range(itemset.optimizedCardinality)] for itemset in db.getDataBase()] for db in self.getCollections()]
        csvFile.close()

    def compareDB(self, db):
        if len(db) != self.getNumCollections():
            print("Error in SatifyInverseMiningProp - collection lists' lenght not equal")
            return False

        for i in range(self.getNumCollections()):
            A = self.collection_list[i].getDataBase()
            B = db[i].getDataBase()
            if [x for x in A if x not in B] + [y for y in B if y not in A] != []:  # if (A-B) + (B-A) != []
                return False
        return True

    def satisfyInverseMiningProp(self, algorithm):
        file = "testoutput.csv"
        self.printDBtoFile(file, algorithm)
        input_item_delimeter = "-f,"
        output_item_delimeter = "-k,"
        if algorithm == DbGenType.Basic:
            minimum_support_list = [("-s-" + str(x).strip()) for x in self.getAbsMinSupLev(DbGenType.Basic)]  # positive: percentage of transactions, negative: exact number of transactions
        elif algorithm == DbGenType.Optimized:
            minimum_support_list = [("-s-" + str(x).strip()) for x in self.getAbsMinSupLev(DbGenType.Optimized)]  # positive: percentage of transactions, negative: exact number of transactions
        targetype = "-tm"  # frequest (s) maximal (m) closed (c)
        output_format = '-v" "'  # empty support information for output result
        inputfile = file
        maximalout = "-"  # "-" for standard output
        varInv = DbGen(input_item_delimeter, output_item_delimeter, minimum_support_list, targetype, output_format, inputfile, maximalout)
        return True if self.compareDB(varInv.getCollections()) else False
