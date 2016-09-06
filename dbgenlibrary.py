# Implementation from scratch of the algorithms presented in the paper "Distribution-Based Synthetic Database Generation Techniques for Itemset Mining" by Ganesh Ramesh, Mohammed J. Zaki and William A. Maniatty
# Programmer: Christian Lezcano

from functools import reduce
from subprocess import check_output, CalledProcessError, STDOUT
from collections import Counter
from enum import Enum
from operator import add
from itertools import chain, combinations
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
        if algorithm == DbGenType.Basic:
            return reduce(add, [itemset.basicCardinality for itemset in self.getDataBase()])
        elif algorithm == DbGenType.Optimized:
            return reduce(add, [itemset.optimizedCardinality for itemset in self.getDataBase()])

    def getUniverseSup(self):  # Maximum of the absolute support values of all the singleton items of DB
        self.itemUniverseSup.clear()
        for itemset in self.getDataBase():
            self.itemUniverseSup.update({}.fromkeys(itemset.getItemSet(), itemset.basicCardinality))
        return self.itemUniverseSup

    def getItemsetSup(self, xitemset):  # get the absolute support of an itemset in a database
        if isinstance(xitemset, ItemSet):
            return reduce(add, map(lambda y: y.optimizedCardinality, filter(lambda x: xitemset.getItemSet().issubset(x.getItemSet()), self.getDataBase())))
        elif isinstance(xitemset, set):
            return reduce(add, map(lambda y: y.optimizedCardinality, filter(lambda x: xitemset.issubset(x.getItemSet()), self.getDataBase())))
        else:
            raise Exception("Method getItemsetSup() input an undefined parameter value")

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

    def dbGenBasic(self):
        absoluteSupLevel = 1  # Absolute support level
        self.basicMinSupLevels.clear()
        self.basicMinSupLevels.append(absoluteSupLevel)
        for step in range(1, self.getNumCollections()):  # M1 saved at 0 zero, M2 at 1 one, ...
            absoluteSupLevel = self.getSupportLevel(step, DbGenType.Basic) + 1
            self.basicMinSupLevels.append(absoluteSupLevel)
            self.genOperator(step, absoluteSupLevel, DbGenType.Basic)

    def dbGenOptimized(self):
        absoluteSupLevel = 1  # Absolute support level
        self.optimizedMinSupLevels.clear()
        self.optimizedMinSupLevels.append(absoluteSupLevel)
        for step in range(1, self.getNumCollections()):  # M1 saved at 0 zero, M2 at 1 one, ...
            absoluteSupLevel = self.getSupportLevel(step, DbGenType.Optimized) + 1
            self.optimizedMinSupLevels.append(absoluteSupLevel)
            self.genOperator(step, absoluteSupLevel, DbGenType.Optimized)

    def getItemsetSupport(self, itemset, step):  # get the absolute support of an itemset in the database DB
        return reduce(add, [db.getItemsetSup(itemset) for db in self.collection_list[0: step]])

    def getSupportLevel(self, step, algorithm):
        if algorithm == DbGenType.Basic:
            return self.supportLevelBasic(step)
        elif algorithm == DbGenType.Optimized:
            return self.supportLevelOptimized(step)

    def supportLevelBasic(self, step):
        counter = Counter()
        for db in self.collection_list[0: step]:
            counter += db.getUniverseSup()
        return max(counter.values())

    def supportLevelOptimized(self, step):
        maxTemp = max(self.optimizedMinSupLevels[step - 1], self.maxMinimal(step))
        m2sup = list({self.getItemsetSupport(itemset, step) for itemset in self.collection_list[step].getDataBase()})
        m2sup.sort()
        for i in m2sup:
            if i >= maxTemp:
                return i
        return maxTemp

    def maxMinimal(self, step):
        m1 = set(chain.from_iterable([self.powerset(itemset.getItemSet()) for itemset in self.collection_list[step - 1].getDataBase()]))
        m2 = set(chain.from_iterable([self.powerset(itemset.getItemSet()) for itemset in self.collection_list[step].getDataBase()]))
        diff = [set(i) for i in m1.difference(m2)]
        return self.getMaxSupAll(self.getMinimalItemsets(diff), step)

    def powerset(self, itemset):  # powerset(set)
        return set(chain.from_iterable(combinations(itemset, r) for r in range(1, len(itemset) + 1)))

    def getMinimalItemsets(self, dbList):
        minItemset = list()
        for itemset1 in dbList:
            isSuper = False
            for itemset2 in dbList:
                if itemset1 > itemset2:
                    isSuper = True
                    break
            if isSuper is False:
                minItemset.append(itemset1)
        return minItemset

    def getMaxSupAll(self, dbList, step):  # get the minimum support of all the itemset in a database DB
        return max([self.getItemsetSupport(itemset, step) for itemset in dbList])

    def genOperator(self, step, absoluteSupLevel, algorithm):
        if algorithm == DbGenType.Basic:
            for itemset in self.collection_list[step].getDataBase():
                itemset.basicCardinality = absoluteSupLevel
        elif algorithm == DbGenType.Optimized:
            for itemset in self.collection_list[step].getDataBase():
                itemsetsup = self.getItemsetSupport(itemset, step)
                itemset.optimizedCardinality = (absoluteSupLevel - itemsetsup) if itemsetsup < absoluteSupLevel else 0

    def getDBsize(self, algorithm):
        if algorithm == DbGenType.Basic:
            return reduce(add, [db.size(DbGenType.Basic) for db in self.getCollections()])
        elif algorithm == DbGenType.Optimized:
            return reduce(add, [db.size(DbGenType.Optimized) for db in self.getCollections()])

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

    def loadCollections(self):
        self.collection_list.clear()
        for levelsupport in self.minimum_support_list:
            command = "apriori.exe" + " " + self.input_item_delimiter + " " + self.output_item_delimiter + " " + levelsupport + " " + self.targetype + " " + self.output_format + " " + self.inputfile + " " + self.maximalout
            temp_collection = check_output(command).decode("utf-8").strip().split("\n")  # contains the maximal itemset list with useless space characters
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
        for i in range(numberCollections - 2):
            j = i + 1
            for itemset2 in self.collection_list[j].getDataBase():
                isSubset = False
                for itemset1 in self.collection_list[i].getDataBase():
                    if itemset2.getItemSet().issubset(itemset1.getItemSet()):
                        isSubset = True
                        break
                if not isSubset:
                    return False
        return True

    def printDB(self, algorithm):
        if algorithm == DbGenType.Basic:
            for db in self.getCollections():
                for itemset in db.getDataBase():
                    for _ in range(itemset.basicCardinality):
                        print(",".join(itemset.getItemSet()))
        elif algorithm == DbGenType.Optimized:
            for db in self.getCollections():
                for itemset in db.getDataBase():
                    for _ in range(itemset.optimizedCardinality):
                        print(",".join(itemset.getItemSet()))

    def printDBtoFile(self, fileName, algorithm):
        csvFile = open(fileName, 'w', newline='')
        csvWriter = csv.writer(csvFile, delimiter=',', lineterminator='\n')
        if algorithm == DbGenType.Basic:
            for db in self.getCollections():
                for itemset in db.getDataBase():
                    for _ in range(itemset.basicCardinality):
                        csvWriter.writerow(itemset.getItemSet())
        elif algorithm == DbGenType.Optimized:
            for db in self.getCollections():
                for itemset in db.getDataBase():
                    for _ in range(itemset.optimizedCardinality):
                        csvWriter.writerow(itemset.getItemSet())
        csvFile.close()

    def compareDB(self, db):
        if len(db) != self.getNumCollections():
            print("Error in SatifyInverseMiningProp - collection lists' lenght not equal")
            return False
        for i in range(self.getNumCollections()):
            A = [itemset.getItemSet() for itemset in self.collection_list[i].getDataBase()]
            B = [itemset.getItemSet() for itemset in db[i].getDataBase()]
            if [x for x in A if x not in B] + [y for y in B if y not in A] != []:  # if (A-B) + (B-A) != []
                return False
        return True

    def satisfyInverseMiningProp(self, algorithm):
        file = "testoutput.csv"
        self.printDBtoFile(file, algorithm)
        input_item_delimeter = "-f,"
        output_item_delimeter = "-k,"
        if algorithm == DbGenType.Basic:
            minimum_support_list = ["-s-" + str(x).strip() for x in self.getAbsMinSupLev(DbGenType.Basic)]  # positive: percentage of transactions, negative: exact number of transactions
        elif algorithm == DbGenType.Optimized:
            minimum_support_list = ["-s-" + str(x).strip() for x in self.getAbsMinSupLev(DbGenType.Optimized)]  # positive: percentage of transactions, negative: exact number of transactions
        targetype = "-tm"  # frequest (s) maximal (m) closed (c)
        output_format = '-v" "'  # empty support information for output result
        inputfile = file
        maximalout = "-"  # "-" for standard output
        varInv = DbGen(input_item_delimeter, output_item_delimeter, minimum_support_list, targetype, output_format, inputfile, maximalout)
        return True if self.compareDB(varInv.getCollections()) else False
