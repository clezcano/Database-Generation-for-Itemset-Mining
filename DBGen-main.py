# Implementation from scratch of the algorithms presented in the paper "Distribution-Based Synthetic Database Generation Techniques for Itemset Mining" by Ganesh Ramesh, Mohammed J. Zaki and William A. Maniatty
# Programmer: Christian Lezcano

from dbgenlibrary import *
import timeit

def main():

        # apriori parameter settings http://www.borgelt.net/doc/apriori/apriori.html
        # Format: apriori [options] infile [outfile]
        # Example: apriori.exe -f, -k, -s2 -tm groceries.csv -
        input_item_delimeter = "-f,"
        output_item_delimeter = "-k,"
        # minimum_support_list = ["-s" + str(x).strip() for x in [-0, -3, -7.5]]  # positive: percentage of transactions, negative: exact number of transactions
        minimum_support_list = ["-s" + str(x).strip() for x in [-50]]  # positive: percentage of transactions, negative: exact number of transactions
        targetype = "-tm"  # frequest (s) maximal (m) closed (c)
        output_format = '-v" "'  # empty support information for output result
        inputfile = "dataset-1000.csv"  # "groceries.csv"
        maximalout = "-"  # "-" for standard output

        var = DbGen(input_item_delimeter, output_item_delimeter, minimum_support_list, targetype, output_format, inputfile, maximalout)
        print("DB input lenght : ", var.getDBsize(DbGenType.Input))
        var.printDB(DbGenType.Input)
        timeit.timeit(var.dbGenBasic())
        # print("Execution of dbGenBasic algorithm")
        # print("List of absolute minimum support levels : ", var.getAbsMinSupLev(DbGenType.Basic))
        # print("List of relative minimum support levels : ", var.getRelMinSupLev(DbGenType.Basic))
        # print("Satisfy the inverse mining property? : ", var.satisfyInverseMiningProp(DbGenType.Basic))
        # print("DBGenBasic database : \n", var.printDB(DbGenType.Basic))
        # var.dbGenOptimized()
        # print("dbGenOptimized")
        # print("Satisfy the inverse mining property? :", var.satisfyInverseMiningProp(DbGenType.Optimized))
        # print("List of absolute minimum support levels : ", var.getAbsMinSupLev(DbGenType.Optimized))
        # print("List of relative minimum support levels : ", var.getRelMinSupLev(DbGenType.Optimized))
        # print("DB lenght : ", var.getDBsize(DbGenType.Optimized))
        # print("DBGenOptimized database :")
        # var.printDB(DbGenType.Optimized)

if __name__ == "__main__":
        main()
