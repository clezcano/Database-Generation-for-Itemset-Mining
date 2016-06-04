from subprocess import call

algorithm = "apriori.exe"
minsup = "-s10" # value in percentage
itemsepin = "-f," # input item separator
itemsepout = "-k," # output item separator
targetype = "-ts" # frequest (s) maximal (m) closed (c)
apriorifile = "groceries.csv"
frequentout = "frequentout.csv"
maximalout = "maximalout.csv"

cmd = algorithm + " " + itemsepin + " " + minsup + " " + itemsepout + " " + targetype + " " + apriorifile + " " + frequentout
print("command: ", cmd)
call(cmd, shell=True)

maximal = "-tm"
cmd = algorithm + " " + itemsepin + " " + minsup + " " + itemsepout + " " + targetype + " " + apriorifile + " " + maximalout
print("command: ", cmd)
call(cmd, shell=True)