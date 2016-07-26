from subprocess import check_output

def aprioriexe(input_item_delimeter, output_item_delimeter, minimum_support_list, targetype, output_format, inputfile, maximalout):

    for levelsupport in minimum_support_list:

           current_minimun_support = "-s" + str(levelsupport).strip()
           command = "apriori.exe" + " " + input_item_delimeter + " " + output_item_delimeter + " " + current_minimun_support + " " + targetype + " " + output_format + " " + inputfile + " " + maximalout
           print("1. command for maximal: ", command)

           maximal_list = check_output(command, shell=True).decode("utf-8").strip().split("\n") # get the maximal itemset list with format: itemset (support percentage)
           print("2. maximal list size: ", len(maximal_list))
           print("3. maximal list: ", maximal_list)

           [print(elem) for i, elem in enumerate(maximal_list, start=1)]

           item_universe = set()
           [[item_universe.add(item.strip()) for item in itemset.split(",")] for itemset in maximal_list]
           print("4. Item universe size: ", len(item_universe), "\nItem universe: ", item_universe)