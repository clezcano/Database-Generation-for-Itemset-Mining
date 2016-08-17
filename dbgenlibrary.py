# Algorithms based on paper "Distribution-Based Synthetic Database Generation Techniques for Itemset Mining" by Ganesh Ramesh, Mohammed J. Zaki and William A. Maniatty

from subprocess import check_output

class DbGen:

    def __init__(self, input_item_delimiter, output_item_delimiter, minimum_support_list, targetype, output_format, inputfile, maximalout):

        self.input_item_delimiter = input_item_delimiter
        self.output_item_delimiter = output_item_delimiter
        self.minimum_support_list = minimum_support_list
        self.targetype = targetype
        self.output_format = output_format
        self.inputfile = inputfile
        self.maximalout = maximalout
        self.maximal_collection_list = [] # list of maximal collections Ex: M1, M2, M3
        self.item_universe = set()
        self.DB = []

    def dbGenBasic(self):

        self.loadMaximalCollections()
        if self.satisfyContainmentProp():
            self.runDbGenBasic()
        else:
            raise Exception("This DB does not satisfy the containment property.")

    def runDbGenBasic(self):

         maximalCollectionNumber = len(self.minimum_support_list) # number of maximal collections
         step = 1 # current level
         auxDB = []
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

        return []

    def loadMaximalCollections(self):

        self.maximal_collection_list = []
        for levelsupport in self.minimum_support_list:
            command = "apriori.exe" + " " + self.input_item_delimiter + " " + self.output_item_delimiter + " " + levelsupport + " " + self.targetype + " " + self.output_format + " " + self.inputfile + " " + self.maximalout
            # print("1. command for maximal: ", command)
            maximal_temp_collection = check_output(command, shell=True).decode("utf-8").strip().split("\n")  # contains the maximal itemset list with useless space characters
            # print("2. maximal temp list size: ", len(maximal_temp_collection))
            # print("3. maximal temp list: ", maximal_temp_collection)
            maximal_collection = [itemset.strip() for itemset in maximal_temp_collection]  # contains a maximal collection, ex: Mi
            # print("4. Maximal list size: ", len(maximal_collection))
            # print("5. Maximal list: ", maximal_collection)
            self.maximal_collection_list.append(maximal_collection)

    def getMaximalCollections(self):

        return self.maximal_collection_list

    def getItemUniverse(self):

        self.item_universe.clear()  # contains the list of all the single items.
        for maximal_collection in self.maximal_collection_list:
            [[self.item_universe.add(item.strip()) for item in itemset.split(",")] for itemset in maximal_collection]  # builds up the DB of singleton items
        print("6. Item universe size: ", len(self.item_universe), "\n7. item universe: ", self.item_universe)

    def getMaxSup(self): # Maximum of the absolute support values of all the singleton items of DB

    def satisfyContainmentProp(self): # check if the maximal collections satisfy the containment property. Ex: Mk [ Mk-1 [ ... [ M2 [ M1

