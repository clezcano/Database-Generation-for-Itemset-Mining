from subprocess import check_output

def aprioriexe(input_item_delimeter, output_item_delimeter, minimum_support_list, targetype, inputfile, maximalout):

    for levelsupport in minimum_support_list:

           current_minimun_support = "-s" + str(levelsupport).strip()
           command = "apriori.exe" + " " + input_item_delimeter + " " + output_item_delimeter + " " + current_minimun_support + " " + targetype + " " + inputfile + " " + maximalout
           print("command for maximal: ", command)

           maximal_list = []
           maximal_temp_list = check_output(command, shell=True).decode("utf-8").strip().split("\n") # get the maximal itemset list with format: itemset (support percentage)
           for itemset in maximal_temp_list:
                   maximal_list.append(itemset.split("(")[0].strip()) # removes every itemset support percentage

           print("maximal size: ", len(maximal_list))
           [print(elem) for i, elem in enumerate(maximal_list, start=1)]

           aux = set()
           [[aux.add(i) for i in elem.split(",")] for elem in maximal_list]
           print("set size: ", len(aux), "\nset: ", aux)