import networkx as nx
from itertools import chain
from collections import Counter

class InputFile:
    def __init__(self, filename, delimeter):
        self.filename = filename
        self.delimeter = delimeter

    def getFileNumElements(self):
        # print("escape: %s" % self.delimeter)
        with open(self.filename, 'r') as f:
            return len(set(chain.from_iterable([{i.strip() for i in line.strip().split(self.delimeter)} for line in f.readlines()])))

    def getFileSize(self):
        with open(self.filename, 'r') as f:
            return len(f.readlines())

    def getFileMaxSup(self):
        with open(self.filename, 'r') as f:
            fileMaxSup = Counter()
            for itemset in [{i.strip() for i in line.strip().split(self.delimeter)} for line in f.readlines()]:
                fileMaxSup.update({}.fromkeys(itemset, 1))
        print(fileMaxSup)
        return max(fileMaxSup.values())

class Graphmetrics:

    def __init__(self, filename, delimeter):
        self.G = nx.Graph()
        self.filename = filename
        self.delimeter = delimeter

    def nodeslist(self):
        return self.G.nodes()

    def edgeslist(self):
        return self.G.edges()

    def density(self):
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

def main():

    # inputfile = "dataset-246.csv"
    # inputfile = "dataset-377.csv"
    # inputfile = "dataset-1000.csv"
    # inputfile = "dataset-3196.csv"
    #inputfile = "dataset-4141.csv"
    # inputfile = "dataset-5000.csv"
    # inputfile = "dataset-8124.csv"
    # inputfile = "dataset-20000.csv"
    # inputfile = "dataset-49046v1.csv"
    # inputfile = "dataset-49046v2.csv"
    # inputfile = "dataset-59602.csv"
    # inputfile = "dataset-67557.csv"
    # inputfile = "dataset-75000.csv"
    # inputfile = "dataset-77512.csv"
    # inputfile = "dataset-88162.csv"
    # inputfile = "dataset-245057.csv"
    # inputfile = "dataset-340183.csv"
    inputfile = "dataset-541909.csv"
    # inputfile = "dataset-574913.csv"
    # inputfile = "dataset-990002.csv"  # "groceries.csv"
    # inputfile = "dataset-1000000v1.csv"
    # inputfile = "dataset-1000000v2.csv"
    # inputfile = "dataset-1000000v3.csv"
    # inputfile = "dataset-1040000.csv"
    # inputfile = "dataset-1112949.csv"
    # inputfile = "dataset-1692082.csv"
    # inputfile = "dataset-5000000.csv"
    #inputfile = "test1.tab"
    delimeter = " "
    #delimeter = ","
    dataset = InputFile(inputfile, delimeter)
    print("File name: %s DataFile size: %d Number of elements: %d " % (inputfile, dataset.getFileSize(), dataset.getFileNumElements()))
    Gmetric = Graphmetrics(inputfile, delimeter)
    print("Density %: ", Gmetric.density()*100)
    # G.add_edges_from([(1, 2), (1, 3)])
    # G.add_node(3)
    # G.add_node(4)
    # print(nx.density(G))
    print("nodes : ", Gmetric.nodeslist())
    print("number of nodes : ", len(Gmetric.nodeslist()))
    print("edgelist ", Gmetric.edgeslist())
    print("edgelist ", len(Gmetric.edgeslist()))


if __name__ == "__main__":
    main()
