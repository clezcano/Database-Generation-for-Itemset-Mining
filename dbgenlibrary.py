from subprocess import check_output

def dbgenbasic(input_item_delimeter, output_item_delimeter, minimum_support_list, targetype, output_format, inputfile, maximalout):

    maximal_collection_list = []
    item_universe = set() # contains the list of all the single items.

    for levelsupport in minimum_support_list:

           command = "apriori.exe" + " " + input_item_delimeter + " " + output_item_delimeter + " " + levelsupport + " " + targetype + " " + output_format + " " + inputfile + " " + maximalout
           #print("1. command for maximal: ", command)

           maximal_temp_collection = check_output(command, shell=True).decode("utf-8").strip().split("\n") # contains the maximal itemset list with useless space characters
           #print("2. maximal temp list size: ", len(maximal_temp_collection))
           #print("3. maximal temp list: ", maximal_temp_collection)

           maximal_collection = [itemset.strip() for itemset in maximal_temp_collection] # contains the list of maximal itemset
           #print("4. Maximal list size: ", len(maximal_collection))
           #print("5. Maximal list: ", maximal_collection)

           maximal_collection_list.append(maximal_collection) # matrix of maximal collections

           [[item_universe.add(item.strip()) for item in itemset.split(",")] for itemset in maximal_collection] # builds up the DB of singleton items

    print("6. Item universe size: ", len(item_universe), "\n7. item universe: ", item_universe)

