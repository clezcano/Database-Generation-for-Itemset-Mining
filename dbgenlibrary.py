# Algoritms based on paper "Distribution-Based Synthetic Database Generation Techniques for Itemset Mining" by Ganesh Ramesh, Mohammed J. Zaki and William A. Maniatty

from subprocess import check_output

class DbGen:


    def __init__(self, input_item_delimeter, output_item_delimeter, minimum_support_list, targetype, output_format, inputfile, maximalout):


        
    def dbgenbasic(input_item_delimeter, output_item_delimeter, minimum_support_list, targetype, output_format, inputfile, maximalout):

        maximal_collection_list = loadmaximalcollections()

        if satisfycontainmentprop(): # check if the maximal collections satisfy the containment property. Ex: Mk [ Mk-1 [ ... [ M2 [ M1
            dbgenbasic(maximal_collection_list)
        else:
            print("This DB does not satisfy the containment property. Execution stop")



    def dbgenbasic(maximal_collection_list):

    def getmaxsup():

    def satisfycontainmentprop():

    def loadmaximalcollections():

        maximal_collection_list = []  # list of maximal collections Ex: M1, M2, M3
        item_universe = set()  # contains the list of all the single items.

        for levelsupport in minimum_support_list:
            command = "apriori.exe" + " " + input_item_delimeter + " " + output_item_delimeter + " " + levelsupport + " " + targetype + " " + output_format + " " + inputfile + " " + maximalout
            # print("1. command for maximal: ", command)

            maximal_temp_collection = check_output(command, shell=True).decode("utf-8").strip().split("\n")  # contains the maximal itemset list with useless space characters
            # print("2. maximal temp list size: ", len(maximal_temp_collection))
            # print("3. maximal temp list: ", maximal_temp_collection)

            maximal_collection = [itemset.strip() for itemset in maximal_temp_collection]  # contains a maximal collection, ex: Mi
            # print("4. Maximal list size: ", len(maximal_collection))
            # print("5. Maximal list: ", maximal_collection)

            maximal_collection_list.append(maximal_collection)  # list of maximal collections Ex: M1, M2, M3

            [[item_universe.add(item.strip()) for item in itemset.split(",")] for itemset in maximal_collection]  # builds up the DB of singleton items

        print("6. Item universe size: ", len(item_universe), "\n7. item universe: ", item_universe)