from asyncio.subprocess import PIPE


def aprioriexe():

        from subprocess import call, check_output, Popen

        algorithm = "apriori.exe"
        itemsepin = "-f,"  # input item separator
        itemsepout = "-k,"  # output item separator
        minsup = "-s2"  # minimun support, positive in percentage, negative in absolutes
        targetype = "-ts"  # frequest (s) maximal (m) closed (c)
        apriorifile = "groceries.csv"
        frequentout = "frequentout.csv"
        #maximalout = "maximalout.csv"
        maximalout = "-"


        cmd = algorithm + " " + itemsepin + " " + itemsepout + " " + minsup + " " + targetype + " " + apriorifile + " " + frequentout
        #print("command: ", cmd)
        #call(cmd, shell=True)

        targetype = "-tm"
        cmd = algorithm + " " + itemsepin + " " + itemsepout + " " + minsup + " " + targetype + " " + apriorifile + " " + maximalout
        print("command: ", cmd)
        list = check_output(cmd, shell=True).decode("utf-8").split("\n")
        for i,a in enumerate(list):
            print(i,":",a)
        print("output: ",len(list))

