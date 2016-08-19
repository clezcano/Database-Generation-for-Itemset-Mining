# Algorithms based on paper "Distribution-Based Synthetic Database Generation Techniques for Itemset Mining" by Ganesh Ramesh, Mohammed J. Zaki and William A. Maniatty

from subprocess import check_output

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

class MaximalCollection:
    # Contains a list of itemsets
    def __init__(self):
        self.maximalCollection = list()
    def getMaximalCollection(self):
        return self.maximalCollection
    def append(self, value):
        self.maximalCollection.append(value)
    def size(self):
        return len(self.maximalCollection)

class DbGen:

    def __init__(self, input_item_delimiter, output_item_delimiter, minimum_support_list, targetype, output_format, inputfile, maximalout):

        self.input_item_delimiter = input_item_delimiter
        self.output_item_delimiter = output_item_delimiter
        self.minimum_support_list = minimum_support_list
        self.targetype = targetype
        self.output_format = output_format
        self.inputfile = inputfile
        self.maximalout = maximalout
        self.maximal_collection_list = [MaximalCollection() for i in self.minimum_support_list] # list of maximal collections Ex: M1, M2, M3
        self.item_universe = set()
        self.DB = list()

    def dbGenBasic(self):

        self.loadMaximalCollections()
        if self.satisfyContainmentProp():
            self.runDbGenBasic()
        else:
            raise Exception("This DB does not satisfy the containment property.")

    def runDbGenBasic(self):

         maximalCollectionNumber = len(self.maximal_collection_list) # number of maximal collections
         step = 1 # current level
         auxDB = list()
         absoluteSupLevel = 1 # Absolute support level
         auxDB = self.generationOperator(step, absoluteSupLevel)
         self.DB = auxDB
         for step in range(2, maximalCollectionNumber + 1):
             absoluteSupLevel = self.getMaxSup() + 1
             auxDB = self.generationOperator(step, absoluteSupLevel)
             self.appendDB(auxDB)

    def getDB(self): # Get final database

        return self.DB

    def getRelMinSupLev(self): # Get relative minimum support levels

    def getAbsMinSupLev(self): # Get absolute minimum support levels

    def appendDB(self, auxDB):

    def generationOperator(level, absoluteSupLevel):

        return list()

    def loadMaximalCollections(self):

        self.maximal_collection_list.clear()
        for levelsupport in self.minimum_support_list:
            command = "apriori.exe" + " " + self.input_item_delimiter + " " + self.output_item_delimiter + " " + levelsupport + " " + self.targetype + " " + self.output_format + " " + self.inputfile + " " + self.maximalout
            # print("1. command for maximal: ", command)
            maximal_temp_collection = check_output(command, shell=True).decode("utf-8").strip().split("\n")  # contains the maximal itemset list with useless space characters
            # print("2. maximal temp list size: ", len(maximal_temp_collection))
            # print("3. maximal temp list: ", maximal_temp_collection)
            maximal_collection = [itemset.strip() for itemset in maximal_temp_collection]  # contains a maximal collection, ex: Mi
            # print("4. Maximal list size: ", len(maximal_collection))
            # print("5. Maximal list: ", maximal_collection)
            mc = MaximalCollection()
            for i in maximal_collection:
                itemset = ItemSet()
                for item in i.split(","):
                    itemset.add(item)
                mc.append(itemset)
            self.maximal_collection_list.append(mc)

    def getMaximalCollections(self):

        return self.maximal_collection_list

    def getItemUniverse(self):
        # builds up the DB of singleton items
        self.item_universe.clear()  # contains the list of all the single items.
        for maximal_collection in self.maximal_collection_list:
            [[self.item_universe.add(item.strip()) for item in itemset.split(",")] for itemset in maximal_collection]  # builds up the DB of singleton items
        print("6. Item universe size: ", len(self.item_universe), "\n7. item universe: ", self.item_universe)

    def getMaxSup(self): # Maximum of the absolute support values of all the singleton items of DB


    def satisfyContainmentProp(self): # check if the maximal collections satisfy the containment property. Ex: Mk [ Mk-1 [ ... [ M2 [ M1

        i = 0
        while i < (len(self.maximal_collection_list) - 1):
           j = i + 1
           mc1 = self.maximal_collection_list[i].getMaximalCollection() # returns a list of ItemSet
           mc2 = self.maximal_collection_list[j].getMaximalCollection()
           for itemset2 in mc2:
               isSubset = False
               for itemset1 in mc1:
                    if set(itemset2).issubset(itemset1):
                        isSubset = True
                        break
               if not isSubset:
                   return False
           return True

