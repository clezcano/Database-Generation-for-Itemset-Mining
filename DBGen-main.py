
if __name__ == "__main__":

        from subprocess import call
        algorithm = "apriori.exe"
        itemsepin = "-f," # input item separator
        itemsepout = "-k," # output item separator
        minsup = "-s25" # minimun support, positive in percentage, negative in absolutes
        targetype = "-ts" # frequest (s) maximal (m) closed (c)
        apriorifile = "groceries.csv"
        frequentout = "frequentout.csv"
        maximalout = "maximalout.csv"

        cmd = algorithm + " " + itemsepin + " " + itemsepout + " " + minsup + " " + targetype + " " + apriorifile + " " + frequentout
        print("command: ", cmd)
        call(cmd, shell=True)

        targetype = "-tm"
        cmd = algorithm + " " + itemsepin + " " + itemsepout + " " + minsup + " " + targetype + " " + apriorifile + " " + maximalout
        print("command: ", cmd)
        call(cmd, shell=True)