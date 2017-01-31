# Implementation from scratch of the algorithms presented in the paper "Distribution-Based Synthetic Database Generation Techniques for Itemset Mining" by Ganesh Ramesh, Mohammed J. Zaki and William A. Maniatty
# Programmer: Christian Lezcano

from subprocess import check_output, CalledProcessError
from sys import platform
from collections import Counter
from enum import Enum
from itertools import chain, combinations
from hypergraph import *
import csv

class InputFile:
    def __init__(self, filename, delimeter):
        self.filename = filename
        self.delimeter = delimeter

    def getFileNumElements(self):
        print("escape: %s" % self.delimeter)
        with open(self.filename, 'r') as f:
            return len(set(chain.from_iterable([{i.strip() for i in line.strip().split(self.delimeter)} for line in f.readlines()])))

    def getFileMaxSup(self):
        with open(self.filename, 'r') as f:
            fileMaxSup = Counter()
            for itemset in [{i.strip() for i in line.strip().split(self.delimeter)} for line in f.readlines()]:
                fileMaxSup.update({}.fromkeys(itemset, 1))
        print(fileMaxSup)
        return max(fileMaxSup.values())

    def getFileSize(self):
        with open(self.filename, 'r') as f:
            return len(f.readlines())

class DbGenType(Enum):
    Input = 1
    Basic = 2
    BasicOptimized = 3
    Gamma = 4
    GammaOptimized = 5   # Our proposal
    Hypergraph = 6

class ItemSet:
    def __init__(self):
        self.itemset = set()
        self.basic_cardinality = 1  # DbGenBasic algorithm updates this parameter
        self.basicOptimized_cardinality = 1
        self.gamma_cardinality = 1  # DbGenOptimized algorithm updates this parameter
        self.gammaOptimized_cardinality = 1  # DbGenOptimized algorithm updates this parameter
        self.hypergraph_cardinality = 1

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
        if algorithm == DbGenType.Input:
            return len(self.database)
        elif algorithm == DbGenType.Basic:
            return sum([itemset.basic_cardinality for itemset in self.getDataBase()])
        elif algorithm == DbGenType.BasicOptimized:
            return sum([itemset.basicOptimized_cardinality for itemset in self.getDataBase()])
        elif algorithm == DbGenType.Gamma:
            return sum([itemset.gamma_cardinality for itemset in self.getDataBase()])
        elif algorithm == DbGenType.GammaOptimized:
            return sum([itemset.gammaOptimized_cardinality for itemset in self.getDataBase()])
        elif algorithm == DbGenType.Hypergraph:
            return sum([itemset.hypergraph_cardinality for itemset in self.getDataBase()])

    def getUniverseSup(self, algorithm):  # Maximum of the absolute support values of all the singleton items of DB
        self.itemUniverseSup.clear()
        if algorithm == DbGenType.Basic:
            for itemset in self.getDataBase():
                self.itemUniverseSup.update({}.fromkeys(itemset.getItemSet(), itemset.basic_cardinality))
        elif algorithm == DbGenType.BasicOptimized:
            for itemset in self.getDataBase():
                self.itemUniverseSup.update({}.fromkeys(itemset.getItemSet(), itemset.basicOptimized_cardinality))
        return dict(self.itemUniverseSup.most_common())

    def getDBElements(self, algorithm):
        if algorithm == DbGenType.Input:
            return set(chain.from_iterable([itemset.getItemSet() for itemset in self.getDataBase()]))
        elif algorithm == DbGenType.Basic:
            return set(chain.from_iterable([itemset.getItemSet() for itemset in self.getDataBase() if itemset.basic_cardinality > 0]))
        elif algorithm == DbGenType.BasicOptimized:
            return set(chain.from_iterable([itemset.getItemSet() for itemset in self.getDataBase() if itemset.basicOptimized_cardinality > 0]))
        elif algorithm == DbGenType.Gamma:
            return set(chain.from_iterable([itemset.getItemSet() for itemset in self.getDataBase() if itemset.gamma_cardinality > 0]))
        elif algorithm == DbGenType.GammaOptimized:
            return set(chain.from_iterable([itemset.getItemSet() for itemset in self.getDataBase() if itemset.gammaOptimized_cardinality > 0]))
        elif algorithm == DbGenType.Hypergraph:
            return set(chain.from_iterable([itemset.getItemSet() for itemset in self.getDataBase() if itemset.hypergraph_cardinality > 0]))

    def getDBNumElements(self, algorithm):
        return len(self.getDBElements(algorithm))

    def getItemsetSup(self, xitemset, algorithm):  # get the absolute support of an itemset in a database. Basic doest not use this method
        if algorithm == DbGenType.BasicOptimized:
            if isinstance(xitemset, ItemSet):
                return sum(map(lambda y: y.basicOptimized_cardinality, filter(lambda x: xitemset.getItemSet().issubset(x.getItemSet()), self.getDataBase())))
            elif isinstance(xitemset, set):
                return sum(map(lambda y: y.basicOptimized_cardinality, filter(lambda x: xitemset.issubset(x.getItemSet()), self.getDataBase())))
        elif algorithm == DbGenType.Gamma:
            if isinstance(xitemset, ItemSet):
                return sum(map(lambda y: y.gamma_cardinality, filter(lambda x: xitemset.getItemSet().issubset(x.getItemSet()), self.getDataBase())))
            elif isinstance(xitemset, set):
                return sum(map(lambda y: y.gamma_cardinality, filter(lambda x: xitemset.issubset(x.getItemSet()), self.getDataBase())))
        elif algorithm == DbGenType.GammaOptimized:
            if isinstance(xitemset, ItemSet):
                return sum(map(lambda y: y.gammaOptimized_cardinality, filter(lambda x: xitemset.getItemSet().issubset(x.getItemSet()), self.getDataBase())))
            elif isinstance(xitemset, set):
                return sum(map(lambda y: y.gammaOptimized_cardinality, filter(lambda x: xitemset.issubset(x.getItemSet()), self.getDataBase())))
        elif algorithm == DbGenType.Hypergraph:
            if isinstance(xitemset, ItemSet):
                return sum(map(lambda y: y.hypergraph_cardinality, filter(lambda x: xitemset.getItemSet().issubset(x.getItemSet()), self.getDataBase())))
            elif isinstance(xitemset, set):
                return sum(map(lambda y: y.hypergraph_cardinality, filter(lambda x: xitemset.issubset(x.getItemSet()), self.getDataBase())))
        else:
            exit("Method getItemsetSup() input an undefined parameter value")

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
        self.basic_MinSupLevels = list()  # Minimum support levels of dbGenBasic algorithm
        self.basicOpt_MinSupLevels = list()  # Minimum support levels of dbGenBasic algorithm
        self.gamma_MinSupLevels = list()  # Minimum support levels of dbGenOptimized algorithm
        self.gammaOpt_MinSupLevels = list()  # Minimum support levels of dbGenOptimized algorithm
        self.hypergraph_MinSupLevels = list()  # Minimum support levels of dbGenHypergraph algorithm
        self.loadCollections()
        # self.elements = self.getElements()  # Universe singleton elements
        if not self.satisfyContainmentProp():
            exit("This DB does not satisfy the containment property.")

    def loadCollections(self):
        self.collection_list.clear()
        for levelsupport in self.minimum_support_list:
            try:
                if platform == "win32":
                    command = "eclat.exe" + " " + self.input_item_delimiter + " " + self.output_item_delimiter + " " + levelsupport + " " + self.targetype + " " + self.output_format + " " + self.inputfile + " " + self.maximalout
                    print("command eclat: ", command)
                    temp_collection = check_output(command).decode("utf-8").strip().split("\n")  # contains the maximal itemset list with useless space characters
                elif platform == "linux" or platform == "linux2":
                    command = "./eclat" + " " + self.input_item_delimiter + " " + self.output_item_delimiter + " " + levelsupport + " " + self.targetype + " " + self.output_format + " " + self.inputfile + " " + self.maximalout
                    temp_collection = check_output(command, shell=True).decode("utf-8").strip().split("\n")  # contains the maximal itemset list with useless space characters
            except CalledProcessError as e:
                exit("Eclat has failed running with minimum support: %s Return code: %d Output: %s" % (levelsupport, e.returncode, e.output.decode("utf-8")))
            collection = [itemset.strip() for itemset in temp_collection]  # contains a maximal collection, ex: Mi
            mc = DataBase()
            for i in collection:
                itemset = ItemSet()
                for item in i.split(","):
                    itemset.add(item)
                mc.append(itemset)
            self.collection_list.append(mc)

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

    def dbGenBasic(self):
        absoluteSupLevel = 1  # Absolute support level
        self.basic_MinSupLevels.clear()
        self.basic_MinSupLevels.append(absoluteSupLevel)
        for step in range(1, self.getNumCollections()):  # M1 saved at 0 zero, M2 at 1 one, ...
            absoluteSupLevel = self.getSupportLevel(step, DbGenType.Basic) + 1
            self.genOperator(step, absoluteSupLevel, DbGenType.Basic)
            self.basic_MinSupLevels.append(absoluteSupLevel)

    def dbGenBasicOptimized(self):
        absoluteSupLevel = 1  # Absolute support level
        self.basicOpt_MinSupLevels.clear()
        self.basicOpt_MinSupLevels.append(absoluteSupLevel)
        for step in range(1, self.getNumCollections()):  # M1 saved at 0 zero, M2 at 1 one, ...
            absoluteSupLevel = self.getSupportLevel(step, DbGenType.BasicOptimized) + 1
            self.genOperator(step, absoluteSupLevel, DbGenType.BasicOptimized)
            self.basicOpt_MinSupLevels.append(absoluteSupLevel)

    def dbGenGamma(self):
        absoluteSupLevel = 1  # Absolute support level
        self.gamma_MinSupLevels.clear()
        self.gamma_MinSupLevels.append(absoluteSupLevel)
        for step in range(1, self.getNumCollections()):  # M1 saved at 0 zero, M2 at 1 one, ...
            absoluteSupLevel = self.getSupportLevel(step, DbGenType.Gamma) + 1
            self.genOperator(step, absoluteSupLevel, DbGenType.Gamma)
            self.gamma_MinSupLevels.append(absoluteSupLevel)

    def dbGenGammaOptimized(self):
        absoluteSupLevel = 1  # Absolute support level
        self.gammaOpt_MinSupLevels.clear()
        self.gammaOpt_MinSupLevels.append(absoluteSupLevel)
        for step in range(1, self.getNumCollections()):  # M1 saved at 0 zero, M2 at 1 one, ...
            absoluteSupLevel = self.getSupportLevel(step, DbGenType.GammaOptimized) + 1
            self.genOperator(step, absoluteSupLevel, DbGenType.GammaOptimized)
            self.gammaOpt_MinSupLevels.append(absoluteSupLevel)

    def dbGenHypergraph(self):
        absoluteSupLevel = 1  # Absolute support level
        self.hypergraph_MinSupLevels.clear()
        self.hypergraph_MinSupLevels.append(absoluteSupLevel)
        for step in range(1, self.getNumCollections()):  # M1 saved at 0 zero, M2 at 1 one, ...
            absoluteSupLevel = self.getSupportLevel(step, DbGenType.Hypergraph) + 1
            self.genOperator(step, absoluteSupLevel, DbGenType.Hypergraph)
            self.hypergraph_MinSupLevels.append(absoluteSupLevel)

    def getSupportLevel(self, step, algorithm):
        if algorithm == DbGenType.Basic:
            return self.supportLevelBasic(step, DbGenType.Basic)
        elif algorithm == DbGenType.BasicOptimized:  # BasicOptimized uses the same upper limit as Basic
            return self.supportLevelBasic(step, DbGenType.BasicOptimized)
        elif algorithm == DbGenType.Gamma:
            return self.supportLevelGamma(step)
        elif algorithm == DbGenType.GammaOptimized:
            return self.supportLevelGammaOptimized(step)
        elif algorithm == DbGenType.Hypergraph:
            return self.supportLevelHypergraph(step)

    def supportLevelBasic(self, step, algorithm):
        counter = Counter()
        for db in self.collection_list[0: step]:
            counter.update(db.getUniverseSup(algorithm))
        return max(counter.values())

    def supportLevelGamma(self, step):
        maxMin = self.getMaxMinimal(step, DbGenType.Gamma)
        if maxMin == -1:  # it means M_step-1 == M_step
            return self.gamma_MinSupLevels[step - 1] - 1
        maxTemp = max(self.gamma_MinSupLevels[step - 1], maxMin)
        m2sup = list({self.getItemsetSupport(itemset, step, DbGenType.Gamma) for itemset in self.collection_list[step].getDataBase()})
        m2sup.sort()
        for i in m2sup:
            if i >= maxTemp:
                return i
        return maxTemp

    def supportLevelGammaOptimized(self, step):
        maxMin = self.getMaxMinimal(step, DbGenType.GammaOptimized)
        if maxMin == -1: # it means M_step-1 == M_step
            return self.gammaOpt_MinSupLevels[step - 1] - 1
        return max(self.gammaOpt_MinSupLevels[step - 1], maxMin)

    def supportLevelHypergraph(self, step):
        maxMin = self.getMaxMinimal(step, DbGenType.Hypergraph)
        if maxMin == -1:
            return self.hypergraph_MinSupLevels[step - 1] - 1
        maxTemp = max(self.hypergraph_MinSupLevels[step - 1], maxMin)
        m2sup = list({self.getItemsetSupport(itemset, step, DbGenType.Hypergraph) for itemset in self.collection_list[step].getDataBase()})
        m2sup.sort()
        for i in m2sup:
            if i >= maxTemp:
                return i
        return maxTemp

    def getItemsetSupport(self, itemset, step, algorithm):  # get the absolute support of an itemset in the database DB
        return sum([db.getItemsetSup(itemset, algorithm) for db in self.collection_list[0: step]])

    def getMaxMinimal(self, step, algorithm):
        if algorithm == DbGenType.Gamma:
            return self.maxMinimalGamma(step)
        if algorithm == DbGenType.GammaOptimized:
            return self.maxMinimalGammaOptimized(step)
        elif algorithm == DbGenType.Hypergraph:
            return self.maxMinimalHypergraph(step)

    def maxMinimalGamma(self, step):
        m1powerset = [set(i) for i in set(chain.from_iterable([self.powerset(itemset.getItemSet()) for itemset in self.collection_list[step - 1].getDataBase()]))]
        m2powerset = [set(i) for i in set(chain.from_iterable([self.powerset(itemset.getItemSet()) for itemset in self.collection_list[step].getDataBase()]))]
        diff = [x for x in m1powerset if x not in m2powerset]
        if len(diff) > 0:
            return self.getMaxSupAll(self.getMinimalItemsets(diff), step, DbGenType.Gamma)
        else:
            return -1

    def maxMinimalGammaOptimized(self, step):
        m1powerset = [set(i) for i in set(chain.from_iterable([self.powerset(itemset.getItemSet()) for itemset in self.collection_list[step - 1].getDataBase()]))]
        m2powerset = [set(i) for i in set(chain.from_iterable([self.powerset(itemset.getItemSet()) for itemset in self.collection_list[step].getDataBase()]))]
        diff = [x for x in m1powerset if x not in m2powerset]
        if len(diff) > 0:
            return self.getMaxSupAll(self.getMinimalItemsets(diff), step, DbGenType.GammaOptimized)
        else:
            return -1

    def maxMinimalHypergraph(self, step):
        h = hypergraph()
        universeElements = self.getElements()
        for i in [universeElements.difference(itemset.getItemSet()) for itemset in self.collection_list[step].getDataBase()]:
            h.added(i)
        minTransv = h.transv().hyedges
        previousDB = [itemset.getItemSet() for itemset in self.collection_list[step - 1].getDataBase()]
        minimals = [x for x in minTransv for y in previousDB if x.issubset(y)]
        if len(minimals) > 0:
            return self.getMaxSupAll(minimals, step, DbGenType.Hypergraph)
        else:
            return -1

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

    def getMaxSupAll(self, dbList, step, algorithm):  # get the minimum support of all the itemset in a database DB
        if algorithm == DbGenType.Gamma:
            return max([self.getItemsetSupport(itemset, step, DbGenType.Gamma) for itemset in dbList])
        if algorithm == DbGenType.GammaOptimized:
            return max([self.getItemsetSupport(itemset, step, DbGenType.GammaOptimized) for itemset in dbList])
        if algorithm == DbGenType.Hypergraph:
            return max([self.getItemsetSupport(itemset, step, DbGenType.Hypergraph) for itemset in dbList])

    def getElements(self, algorithm):
        return set(chain.from_iterable([db.getDBElements(algorithm) for db in self.collection_list]))

    def getNumElements(self, algorithm):
        return len(self.getElements(algorithm))

    def genOperator(self, step, absoluteSupLevel, algorithm):
        if algorithm == DbGenType.Basic:
            for itemset in self.collection_list[step].getDataBase():
                itemset.basic_cardinality = absoluteSupLevel
        elif algorithm == DbGenType.BasicOptimized:
            for itemset in self.collection_list[step].getDataBase():
                itemsetsup = self.getItemsetSupport(itemset, step, DbGenType.BasicOptimized)
                itemset.basicOptimized_cardinality = (absoluteSupLevel - itemsetsup) if itemsetsup < absoluteSupLevel else 0
        elif algorithm == DbGenType.Gamma:
            for itemset in self.collection_list[step].getDataBase():
                itemsetsup = self.getItemsetSupport(itemset, step, DbGenType.Gamma)
                itemset.gamma_cardinality = (absoluteSupLevel - itemsetsup) if itemsetsup < absoluteSupLevel else 0
        elif algorithm == DbGenType.GammaOptimized:
            for itemset in self.collection_list[step].getDataBase():
                itemsetsup = self.getItemsetSupport(itemset, step, DbGenType.GammaOptimized)
                itemset.gammaOptimized_cardinality = (absoluteSupLevel - itemsetsup) if itemsetsup < absoluteSupLevel else 0
        elif algorithm == DbGenType.Hypergraph:
            for itemset in self.collection_list[step].getDataBase():
                itemsetsup = self.getItemsetSupport(itemset, step, DbGenType.Hypergraph)
                itemset.hypergraph_cardinality = (absoluteSupLevel - itemsetsup) if itemsetsup < absoluteSupLevel else 0

    def getDBsize(self, algorithm):
        if algorithm == DbGenType.Input:
            return sum([db.size(DbGenType.Input) for db in self.getCollections()])
        elif algorithm == DbGenType.Basic:
            return sum([db.size(DbGenType.Basic) for db in self.getCollections()])
        elif algorithm == DbGenType.BasicOptimized:
            return sum([db.size(DbGenType.BasicOptimized) for db in self.getCollections()])
        elif algorithm == DbGenType.Gamma:
            return sum([db.size(DbGenType.Gamma) for db in self.getCollections()])
        elif algorithm == DbGenType.GammaOptimized:
            return sum([db.size(DbGenType.GammaOptimized) for db in self.getCollections()])
        elif algorithm == DbGenType.Hypergraph:
            return sum([db.size(DbGenType.Hypergraph) for db in self.getCollections()])

    def getRelMinSupLev(self, algorithm):  # Get relative minimum support levels
        if algorithm == DbGenType.Basic:
            DBsize = self.getDBsize(DbGenType.Basic)
            return [(minsup / DBsize) * 100 for minsup in self.basic_MinSupLevels]
        if algorithm == DbGenType.BasicOptimized:
            DBsize = self.getDBsize(DbGenType.BasicOptimized)
            return [(minsup / DBsize) * 100 for minsup in self.basicOpt_MinSupLevels]
        elif algorithm == DbGenType.Gamma:
            DBsize = self.getDBsize(DbGenType.Gamma)
            return [(minsup / DBsize) * 100 for minsup in self.gamma_MinSupLevels]
        elif algorithm == DbGenType.GammaOptimized:
            DBsize = self.getDBsize(DbGenType.GammaOptimized)
            return [(minsup / DBsize) * 100 for minsup in self.gammaOpt_MinSupLevels]
        elif algorithm == DbGenType.Hypergraph:
            DBsize = self.getDBsize(DbGenType.Hypergraph)
            return [(minsup / DBsize) * 100 for minsup in self.hypergraph_MinSupLevels]

    def getAbsMinSupLev(self, algorithm):  # Get absolute minimum support levels
        if algorithm == DbGenType.Basic:
            return self.basic_MinSupLevels
        elif algorithm == DbGenType.BasicOptimized:
            return self.basicOpt_MinSupLevels
        elif algorithm == DbGenType.Gamma:
            return self.gamma_MinSupLevels
        elif algorithm == DbGenType.GammaOptimized:
            return self.gammaOpt_MinSupLevels
        elif algorithm == DbGenType.Hypergraph:
            return self.hypergraph_MinSupLevels

    def getCollections(self):
        return self.collection_list

    def getNumCollections(self):
        return len(self.collection_list)

    def printDB(self, algorithm):
        if algorithm == DbGenType.Input:
            for db in self.getCollections():
                for itemset in db.getDataBase():
                    print(",".join(itemset.getItemSet()))
        elif algorithm == DbGenType.Basic:
            for db in self.getCollections():
                for itemset in db.getDataBase():
                    for _ in range(itemset.basic_cardinality):
                        print(",".join(itemset.getItemSet()))
        elif algorithm == DbGenType.BasicOptimized:
            for db in self.getCollections():
                for itemset in db.getDataBase():
                    for _ in range(itemset.basicOptimized_cardinality):
                        print(",".join(itemset.getItemSet()))
        elif algorithm == DbGenType.Gamma:
            for db in self.getCollections():
                for itemset in db.getDataBase():
                    for _ in range(itemset.gamma_cardinality):
                        print(",".join(itemset.getItemSet()))
        elif algorithm == DbGenType.GammaOptimized:
            for db in self.getCollections():
                for itemset in db.getDataBase():
                    for _ in range(itemset.gammaOptimized_cardinality):
                        print(",".join(itemset.getItemSet()))
        elif algorithm == DbGenType.Hypergraph:
            for db in self.getCollections():
                for itemset in db.getDataBase():
                    for _ in range(itemset.hypergraph_cardinality):
                        print(",".join(itemset.getItemSet()))

    def printDBtoFile(self, fileName, algorithm):
        csvFile = open(fileName, 'w', newline='')
        csvWriter = csv.writer(csvFile, delimiter=',', lineterminator='\n')
        if algorithm == DbGenType.Basic:
            for db in self.getCollections():
                for itemset in db.getDataBase():
                    for _ in range(itemset.basic_cardinality):
                        csvWriter.writerow(itemset.getItemSet())
        elif algorithm == DbGenType.BasicOptimized:
            for db in self.getCollections():
                for itemset in db.getDataBase():
                    for _ in range(itemset.basicOptimized_cardinality):
                        csvWriter.writerow(itemset.getItemSet())
        elif algorithm == DbGenType.Gamma:
            for db in self.getCollections():
                for itemset in db.getDataBase():
                    for _ in range(itemset.gamma_cardinality):
                        csvWriter.writerow(itemset.getItemSet())
        elif algorithm == DbGenType.GammaOptimized:
            for db in self.getCollections():
                for itemset in db.getDataBase():
                    for _ in range(itemset.gammaOptimized_cardinality):
                        csvWriter.writerow(itemset.getItemSet())
        elif algorithm == DbGenType.Hypergraph:
            for db in self.getCollections():
                for itemset in db.getDataBase():
                    for _ in range(itemset.hypergraph_cardinality):
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
        file = "dbOutput.csv"
        self.printDBtoFile(file, algorithm)
        input_item_delimeter = "-f,"
        output_item_delimeter = "-k,"
        if algorithm == DbGenType.Basic:
            minimum_support_list = ["-s-" + str(x).strip() for x in self.getAbsMinSupLev(DbGenType.Basic)]  # positive: percentage of transactions, negative: exact number of transactions
        elif algorithm == DbGenType.BasicOptimized:
            minimum_support_list = ["-s-" + str(x).strip() for x in self.getAbsMinSupLev(DbGenType.BasicOptimized)]  # positive: percentage of transactions, negative: exact number of transactions
        elif algorithm == DbGenType.Gamma:
            minimum_support_list = ["-s-" + str(x).strip() for x in self.getAbsMinSupLev(DbGenType.Gamma)]  # positive: percentage of transactions, negative: exact number of transactions
        elif algorithm == DbGenType.GammaOptimized:
            minimum_support_list = ["-s-" + str(x).strip() for x in self.getAbsMinSupLev(DbGenType.GammaOptimized)]  # positive: percentage of transactions, negative: exact number of transactions
        elif algorithm == DbGenType.Hypergraph:
            minimum_support_list = ["-s-" + str(x).strip() for x in self.getAbsMinSupLev(DbGenType.Hypergraph)]  # positive: percentage of transactions, negative: exact number of transactions
        targetype = "-tm"  # frequest (s) maximal (m) closed (c)
        output_format = '-v" "'  # empty support information for output result
        inputfile = file
        maximalout = "-"  # "-" for standard output
        varInv = DbGen(input_item_delimeter, output_item_delimeter, minimum_support_list, targetype, output_format, inputfile, maximalout)
        return self.compareDB(varInv.getCollections())

    def equalDB(self):
        for db in self.getCollections():
            db1 = [itemset.gamma_cardinality for itemset in db.getDataBase()]
            db2 = [itemset.hypergraph_cardinality for itemset in db.getDataBase()]
            if db1 != db2:
                return False
        return True


