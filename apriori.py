def aprioriexe():

        from subprocess import check_output

        algorithm = "apriori.exe"
        itemsepin = "-f,"  # input item separator
        itemsepout = "-k,"  # output item separator
        minsuplist = [0.5, 1, 1.5]
        minsup = "-s2"  # minimun support, positive in percentage, negative in absolutes

        targetype = "-tm"  # frequest (s) maximal (m) closed (c)
        apriorifile = "groceries.csv"
        maximalout = "-"

        for support in minsuplist:
                minsup = "-s" + str(support)
                cmd = algorithm + " " + itemsepin + " " + itemsepout + " " + minsup + " " + targetype + " " + apriorifile + " " + maximalout
                print("command for maximal: ", cmd)

                maximalist = check_output(cmd, shell=True).decode("utf-8").strip().split("\n")
                maximalinput = []
                for itemset in maximalist:
                    maximalinput.append(itemset.split("(")[0])
                [print(i, ": ", elem) for i, elem in enumerate(maximalinput, start=1)]
