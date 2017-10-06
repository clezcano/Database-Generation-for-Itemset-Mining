import matplotlib.pyplot as plt
import networkx as nx
from itertools import chain, combinations
from subprocess import check_output, CalledProcessError
from hypergraph import *
from scipy.stats import entropy
import numpy as np

class InputFile:
    def __init__(self, filename, delimeter):
        self.filename = filename
        self.delimeter = delimeter

    def getFileNumElements(self):
        # print("escape: %s" % self.delimeter)
        with open(self.filename, 'r') as f:
            return len(set(chain.from_iterable([{i.strip() for i in line.strip().split(self.delimeter)} for line in f.readlines()])))

    def getFileElements(self):
        # print("escape: %s" % self.delimeter)
        with open(self.filename, 'r') as f:
            return set(chain.from_iterable([{i.strip() for i in line.strip().split(self.delimeter)} for line in f.readlines()]))

    def getFileSize(self):
        with open(self.filename, 'r') as f:
            return len(f.readlines())

    def number1(self):
        sum = 0
        with open(self.filename, 'r') as f:
            for line in f.readlines():
                sum += len(line.strip().split(self.delimeter))
        return sum

class ItemSet:
    def __init__(self):
        self.itemset = set()

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

    def getDataBase(self):
        return self.database

    def appendItemset(self, value):
        self.database.append(value)

    def size(self):
        return len(self.database)

    def readDB(self, filename, delimeter):
        self.database[:] = []
        with open(filename, 'r') as f:
            for line in f.readlines():
                itemset = ItemSet()
                for item in line.strip().split(delimeter):
                    itemset.add(item.strip())
                self.appendItemset(itemset)

    def getDBElements(self):
        return set(chain.from_iterable([itemset.getItemSet() for itemset in self.getDataBase()]))

    def getDBNumElements(self):
        return len(self.getDBElements())

    def getItemsetSup(self, xitemset):  # get the absolute support of an itemset in a database. Basic doest not use this method
            if isinstance(xitemset, ItemSet):
                return len(list(filter(lambda x: xitemset.getItemSet().issubset(x.getItemSet()), self.getDataBase())))
            elif isinstance(xitemset, set):
                return len(list(filter(lambda x: xitemset.issubset(x.getItemSet()), self.getDataBase())))
            else:
                exit("Method getItemsetSup() input an undefined parameter value")

class metrics:

    def __init__(self, filename, delimeter):
        self.G = nx.Graph()
        self.filename = filename
        self.delimeter = delimeter

    def nodeslist(self):
        return self.G.nodes()

    def edgeslist(self):
        return self.G.edges()

    def fraction1(self):
        f = InputFile(self.filename, self.delimeter)
        return f.number1() / (f.getFileSize() * f.getFileNumElements())

    def graphDensity(self):
        self.G.clear()
        with open(self.filename, 'r') as f:
            for line in f.readlines():
                transaction = line.strip().split(self.delimeter)
                if len(transaction) == 1:
                    self.G.add_node(transaction[0])
                elif len(transaction) > 1:
                    for i in range(len(transaction) - 1):
                        for j in range(i + 1, len(transaction)):
                            self.G.add_edges_from([(transaction[i], transaction[j])])
                else:
                    return -1 # empty transaction found
        return nx.density(self.G)


    def getFreqSet(self, input_item_delimeter, output_item_delimiter, levelsupport, targetype, output_format, inputfile, maximalout):
        try:
            command = "eclat.exe" + " " + input_item_delimeter + " " + output_item_delimiter + " " + levelsupport + " " + targetype + " " + output_format + " " + inputfile + " " + maximalout
            # print("command eclat: ", command)
            temp_collection = check_output(command).decode("utf-8").strip().split("\n")  # contains the maximal itemset list with useless space characters
        except CalledProcessError as e:
            exit("Eclat has failed running with minimum support: %s Return code: %d Output: %s" % (levelsupport, e.returncode, e.output.decode("utf-8")))
        collection = [itemset.strip() for itemset in temp_collection]  # contains a maximal collection, ex: Mi
        return collection

    def numberOfFreqSets(self, input_item_delimeter, output_item_delimiter, levelsupport, targetype, output_format, inputfile, maximalout):  # Metric 6
        return len(self.getFreqSet(input_item_delimeter, output_item_delimiter, levelsupport, targetype, output_format, inputfile, maximalout))

    def freqAverageSupport(self, input_item_delimeter, output_item_delimiter, levelsupport, targetype, output_format, inputfile, maximalout): # Metric 7
        collection = self.getFreqSet(input_item_delimeter, output_item_delimiter, levelsupport, targetype, output_format, inputfile, maximalout)
        sum = 0
        for i in collection:
            sum = sum + float(i.split("(")[1].split(")")[0])
        return sum / len(collection)

    def avgFreqSize(self, input_item_delimeter, output_item_delimiter, levelsupport, targetype, output_format, inputfile, maximalout): # Metric 8
        collection = self.getFreqSet(input_item_delimeter, output_item_delimiter, levelsupport, targetype, output_format, inputfile, maximalout)
        sum = 0
        for i in collection:
            sum += len(i.split(","))
        return sum / len(collection)

    def freqMaxLenght(self, input_item_delimeter, output_item_delimiter, levelsupport, targetype, output_format, inputfile, maximalout): # Metric 9
        collection = self.getFreqSet(input_item_delimeter, output_item_delimiter, levelsupport, targetype, output_format, inputfile, maximalout)
        max = 0
        for i in collection:
            aux = len(i.split(","))
            if aux > max:
                max = aux
        return max

    def lengthDist_str(self, collection, numElem): # Metric 10
        dist = [0] * (numElem + 1)
        for i in collection:
            dist[len(i.split(","))] += 1
        aux = ""
        for _ in dist[1:]:
            aux += (str(_) + ", ")
        return aux

    def lengthDist_int(self, collection, numElem): # Metric 10
        dist = [0] * (numElem + 1)
        for i in collection:
            dist[len(i)] += 1
        aux = ""
        for _ in dist[1:]:
            aux += (str(_) + ", ")
        return aux

    def strToIn_itemset(self, itemset_str):
        aux = set()
        for i in itemset_str.split(","):
            aux.add(i.strip())
        return aux

    def freqLengthDist(self, input_item_delimeter, output_item_delimiter, levelsupport, targetype, output_format, inputfile, maximalout, numElem):
        collection = self.getFreqSet(input_item_delimeter, output_item_delimiter, levelsupport, targetype, output_format, inputfile, maximalout)
        return self.lengthDist_str(collection, numElem)

    def negativeBorderLengthDist(self, input_item_delimeter, output_item_delimiter, levelsupport, targetype, output_format, inputfile, maximalout, elements):
        numElem = len(elements)
        maximalFreq_string = self.getFreqSet(input_item_delimeter, output_item_delimiter, levelsupport, targetype, output_format, inputfile, maximalout)
        maximalFreq_int = [self.strToIn_itemset(itemset) for itemset in maximalFreq_string]
        h = hypergraph()
        for i in [elements.difference(itemset) for itemset in maximalFreq_int]:
            h.added(i)
        minTransv = h.transv().hyedges
        # print("minTransv : ", minTransv)
        return self.lengthDist_int(minTransv, numElem)

    def calculateEntropy(self, prob):
        return -sum((p * np.log2(p) for p in prob if p > 0))

    def entropy(self, filename, delimeter, itemsetSize, minsup, fun): # fun defines use of build-in entropy or my own
        db = DataBase()
        db.readDB(filename, delimeter)
        dbElem = db.getDBElements()
        dbSize = db.size()
        sumFreq = sum((float(db.getItemsetSup(set(itemset))) / dbSize for itemset in combinations(dbElem, itemsetSize)))
        kItemsetProb = ((float(db.getItemsetSup(set(itemset))) / dbSize) / sumFreq for itemset in combinations(dbElem, itemsetSize))
        if fun == 1:
            return entropy(kItemsetProb, base=2)
        elif fun == 2:
            return self.calculateEntropy(kItemsetProb)

def main():
    delimeter = " "
    # delimeter = ","
    input_item_delimeter = '-f"' + delimeter + '"'
    output_item_delimeter = "-k,"
    suppValue = "5" # positive: percentage of transactions, negative: exact number of transactions
    minimum_support = "-s" + suppValue   # Ex: "-s50" or "-s-50"
    targetype = "-ts"  # frequest (s) maximal (m) closed (c)
    output_format = ''  # empty support information for output result # output_format = '-v" "'  # empty support information for output result
    entropyItemsetSize = 2
    entropyFunction = 1  # 1 scify.stats.entropy, 2 my own
    maximalout = "-"  # "-" for standard output
    # inputfile = "dataset-246.csv"
    # inputfile = "dataset-377.csv"
    # inputfile = "dataset-1000.csv"
    # inputfile = "dataset-3196.csv"
    # inputfile = "dataset-4141.csv" # " "
    # inputfile = "dataset-5000.csv"
    # inputfile = "dataset-8124.csv"
    # inputfile = "dataset-20000.csv"
    # inputfile = "dataset-49046v1.csv"  # " "
    # inputfile = "dataset-49046v2.csv"  # " "
    # inputfile = "dataset-59602.csv"   # " "
    # inputfile = "dataset-67557.csv"
    # inputfile = "dataset-75000.csv"     # ","
    # inputfile = "dataset-77512.csv"
    # inputfile = "dataset-88162.csv"     # " "
    # inputfile = "dataset-245057.csv"
    # inputfile = "dataset-340183.csv"   # " "
    inputfile = "dataset-541909.csv"   # " "
    # inputfile = "dataset-574913.csv"    # " "
    # inputfile = "dataset-990002.csv"  # "groceries.csv"
    # inputfile = "dataset-1000000v1.csv"  # " "
    # inputfile = "dataset-1000000v2.csv"
    # inputfile = "dataset-1000000v3.csv"   # " "
    # inputfile = "dataset-1040000.csv"   # " "
    # inputfile = "dataset-1112949.csv"
    # inputfile = "dataset-1692082.csv"
    # inputfile = "dataset-5000000.csv"
    # inputfile = "test1.tab"

    # G.add_edges_from([(1, 2), (1, 3)])
    # G.add_node(3)
    # G.add_node(4)
    # print(nx.density(G))
    # print("nodes : ", Gmetric.nodeslist())
    # print("number of nodes : ", len(Gmetric.nodeslist()))
    # print("edgelist :", Gmetric.edgeslist())
    # print("edgelist :", len(Gmetric.edgeslist()))

    dataset = InputFile(inputfile, delimeter)
    numElem = dataset.getFileNumElements()
    elements = dataset.getFileElements()
    Gmetric = metrics(inputfile, delimeter)
    print("File name: %s " % (inputfile))
    # print("1/ Data file size: %d " % (dataset.getFileSize()))
    # print("2/ Data file number of elements: %d " % numElem)
    # print("3/ Data file fraction of 1s %: ", Gmetric.fraction1() * 100)
    # print("4/ Data file graph density %: ", Gmetric.graphDensity() * 100)
    # print("5.1/ Entropy (scipy.stats): ", Gmetric.entropy(inputfile, delimeter, entropyItemsetSize, float(suppValue) / 100, entropyFunction))
    print("5.2/ Entropy (my own): ", Gmetric.entropy(inputfile, delimeter, entropyItemsetSize, float(suppValue) / 100, 2))
    # print("6/ Number of frequent itemsets : ", Gmetric.numberOfFreqSets(input_item_delimeter, output_item_delimeter, minimum_support, targetype, output_format, inputfile, maximalout))
    # print("7/ Frequent itemset average support %: ", Gmetric.freqAverageSupport(input_item_delimeter, output_item_delimeter, minimum_support, targetype, output_format, inputfile, maximalout))
    # print("8/ Frequent itemset average length : ", Gmetric.avgFreqSize(input_item_delimeter, output_item_delimeter, minimum_support, targetype, output_format, inputfile, maximalout))
    # print("9/ Frequent itemset maximum length : ", Gmetric.freqMaxLenght(input_item_delimeter, output_item_delimeter, minimum_support, targetype, output_format, inputfile, maximalout))
    # print("10/ Frequent itemset length distribution : [", Gmetric.freqLengthDist(input_item_delimeter, output_item_delimeter, minimum_support, targetype, output_format, inputfile, maximalout, numElem), "]")
    # print("11/ Positive border length distribution : [", Gmetric.freqLengthDist(input_item_delimeter, output_item_delimeter, minimum_support, "-tm", output_format, inputfile, maximalout, numElem), "]")
    # print("12/ Negative border length distribution : [", Gmetric.negativeBorderLengthDist(input_item_delimeter, output_item_delimeter, minimum_support, "-tm", '-v" "', inputfile, maximalout, elements), "]")



if __name__ == "__main__":
    main()