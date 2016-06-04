from subprocess import call
apriorifile = "groceries.csv"
cmd="apriori.exe " + apriorifile + " -"
call(cmd, shell=True)