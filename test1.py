import networkx as nx
from itertools import chain
from collections import Counter
from subprocess import check_output, CalledProcessError

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

    def number1(self):
        sum = 0
        with open(self.filename, 'r') as f:
            for line in f.readlines():
                sum = sum + len(line.strip().split(self.delimeter))
        return sum

class metrics:

    def __init__(self, filename, delimeter):
        self.G = nx.Graph()
        self.filename = filename
        self.delimeter = delimeter

    def nodeslist(self):
        return self.G.nodes()

    def edgeslist(self):
        return self.G.edges()

    def fraction1(self):  # Metric 2
        f = InputFile(self.filename, self.delimeter)
        return f.number1() / (f.getFileSize() * f.getFileNumElements())

    def graphDensity(self):  # Metric 1
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

    def numberOfFreqSets(self, input_item_delimiter, output_item_delimiter, levelsupport, targetype, output_format, inputfile, maximalout):
        try:
            command = "eclat.exe" + " " + input_item_delimiter + " " + output_item_delimiter + " " + levelsupport + " " + targetype + " " + output_format + " " + inputfile + " " + maximalout
            print("command eclat: ", command)
            temp_collection = check_output(command).decode("utf-8").strip().split("\n")  # contains the maximal itemset list with useless space characters
        except CalledProcessError as e:
            exit("Eclat has failed running with minimum support: %s Return code: %d Output: %s" % (levelsupport, e.returncode, e.output.decode("utf-8")))
        return len(temp_collection)

    def averageSupport(self, input_item_delimeter, output_item_delimiter, levelsupport, targetype, output_format, inputfile, maximalout):
        try:
            command = "eclat.exe" + " " + input_item_delimeter + " " + output_item_delimiter + " " + levelsupport + " " + targetype + " " + output_format + " " + inputfile + " " + maximalout
            print("command eclat: ", command)
            temp_collection = check_output(command).decode("utf-8").strip().split("\n")  # contains the maximal itemset list with useless space characters
        except CalledProcessError as e:
            exit("Eclat has failed running with minimum support: %s Return code: %d Output: %s" % (levelsupport, e.returncode, e.output.decode("utf-8")))
        collection = [itemset.strip() for itemset in temp_collection]  # contains a maximal collection, ex: Mi
        sum = 0
        for i in collection:
            sum = sum + float(i.split("(")[1].split(")")[0])
        return sum / len(collection)

    def averageTransSize(self, input_item_delimeter, output_item_delimiter, levelsupport, targetype, output_format, inputfile, maximalout):
        try:
            command = "eclat.exe" + " " + input_item_delimeter + " " + output_item_delimiter + " " + levelsupport + " " + targetype + " " + output_format + " " + inputfile + " " + maximalout
            print("command eclat: ", command)
            temp_collection = check_output(command).decode("utf-8").strip().split("\n")  # contains the maximal itemset list with useless space characters
        except CalledProcessError as e:
            exit("Eclat has failed running with minimum support: %s Return code: %d Output: %s" % (levelsupport, e.returncode, e.output.decode("utf-8")))
        collection = [itemset.strip() for itemset in temp_collection]  # contains a maximal collection, ex: Mi
        sum = 0
        for i in collection:
            sum = sum + len(i.split(","))
        return sum / len(collection)

def main():
    delimeter = " "
    # delimeter = ","
    input_item_delimeter = '-f"' + delimeter + '"'
    output_item_delimeter = "-k,"
    minimum_support = "-s50" # positive: percentage of transactions, negative: exact number of transactions
    targetype = "-ts"  # frequest (s) maximal (m) closed (c)
    # output_format = '-v" "'  # empty support information for output result
    output_format = ''  # empty support information for output result
    maximalout = "-"  # "-" for standard output
    inputfile = "dataset-246.csv"
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
    # inputfile = "dataset-541909.csv"
    # inputfile = "dataset-574913.csv"
    # inputfile = "dataset-990002.csv"  # "groceries.csv"
    # inputfile = "dataset-1000000v1.csv"
    # inputfile = "dataset-1000000v2.csv"
    # inputfile = "dataset-1000000v3.csv"
    # inputfile = "dataset-1040000.csv"
    # inputfile = "dataset-1112949.csv"
    # inputfile = "dataset-1692082.csv"
    # inputfile = "dataset-5000000.csv"
    # inputfile = "test1.tab"

    dataset = InputFile(inputfile, delimeter)
    print("File name: %s \nDataFile size: %d \nNumber of elements: %d " % (inputfile, dataset.getFileSize(), dataset.getFileNumElements()))
    Gmetric = metrics(inputfile, delimeter)
    print("Graph density %: ", Gmetric.graphDensity()*100)
    # G.add_edges_from([(1, 2), (1, 3)])
    # G.add_node(3)
    # G.add_node(4)
    # print(nx.density(G))
    print("nodes : ", Gmetric.nodeslist())
    print("number of nodes : ", len(Gmetric.nodeslist()))
    print("edgelist :", Gmetric.edgeslist())
    print("edgelist :", len(Gmetric.edgeslist()))
    print("fraction of 1s %: ", Gmetric.fraction1() * 100)
    print("Number of frequent itemsets : ", Gmetric.numberOfFreqSets(input_item_delimeter, output_item_delimeter, minimum_support, targetype, output_format, inputfile, maximalout))
    print("Average support %: ", Gmetric.averageSupport(input_item_delimeter, output_item_delimeter, minimum_support, targetype, output_format, inputfile, maximalout))
    print("Average transaction size : ", Gmetric.averageTransSize(input_item_delimeter, output_item_delimeter, minimum_support, targetype, output_format, inputfile, maximalout) )

if __name__ == "__main__":
    main()
