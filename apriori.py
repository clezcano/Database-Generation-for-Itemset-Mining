from subprocess import check_output

def aprioriexe(input_item_delimeter, output_item_delimeter, minimum_support_list, targetype, inputfile, maximalout):

    for levelsupport in minimum_support_list:

           current_minimun_support = "-s" + str(levelsupport).strip()
           command = "apriori.exe" + " " + input_item_delimeter + " " + output_item_delimeter + " " + current_minimun_support + " " + targetype + " " + inputfile + " " + maximalout
           print("command for maximal: ", command)

           maximal_input = []
           maximal_list = check_output(command, shell=True).decode("utf-8").strip().split("\n")
           print("maximal list: ")
           print(maximal_list)
           for itemset in maximal_list:
                   maximal_input.append(itemset.split("(")[0])
           [print(i, ": ", elem) for i, elem in enumerate(maximal_input, start=1)]
