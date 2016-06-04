from subprocess import call

algorithm = "apriori.exe"
minsup = "-s-15" # in percentage
itemsepin = "-f,"
itemsepout = "-k," # output item separator
maximal = "-tm"
apriorifile = "groceries.csv"
aprioriout = "output.csv"

cmd = algorithm + " " + itemsepin + " " + minsup + " " + itemsepout + " " + maximal + " " + apriorifile + " " + aprioriout
print("command: ", cmd)
call(cmd, shell=True)

maximal = "-ts"
cmd = algorithm + " " + itemsepin + " " + minsup + " " + itemsepout + " " + maximal + " " + apriorifile + " " + aprioriout
print("command: ", cmd)
call(cmd, shell=True)