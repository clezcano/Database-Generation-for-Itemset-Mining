# Implementation from scratch of the algorithms presented in the paper "Distribution-Based Synthetic Database Generation Techniques for Itemset Mining" by Ganesh Ramesh, Mohammed J. Zaki and William A. Maniatty
# Programmer: Christian Lezcano

from dbgenlibrary import *
import time

def main():

        # apriori parameter settings http://www.borgelt.net/doc/apriori/apriori.html
        # Format: apriori [options] infile [outfile]
        # Example: apriori.exe -f, -k, -s2 -tm groceries.csv -
        input_item_delimeter = "-f,"
        output_item_delimeter = "-k,"
        minimum_support_list = ["-s" + str(x).strip() for x in [-1, -20, -70, -100]]  # positive: percentage of transactions, negative: exact number of transactions
        targetype = "-tm"  # frequest (s) maximal (m) closed (c)
        output_format = '-v" "'  # empty support information for output result
        inputfile = "dataset-75000.csv"  # "groceries.csv"
        maximalout = "-"  # "-" for standard output

        var = DbGen(input_item_delimeter, output_item_delimeter, minimum_support_list, targetype, output_format, inputfile, maximalout)
        print("Collections DB input lenght : ", var.getDBsize(DbGenType.Input))
        # var.printDB(DbGenType.Input)
        startTime = time.time()
        var.dbGenBasic()
        elapsedTime = time.time() - startTime
        print("Basic running time : ", (elapsedTime * 1000))
        print("Basic DB lenght : %d" % var.getDBsize(DbGenType.Basic))
        print("Basic List of absolute minimum support levels : ", var.getAbsMinSupLev(DbGenType.Basic))
        print("Basic List of relative minimum support levels : ", var.getRelMinSupLev(DbGenType.Basic))
        print("Basic Satisfy the inverse mining property? : ", var.satisfyInverseMiningProp(DbGenType.Basic))
        # print("DBGenBasic database : \n", var.printDB(DbGenType.Basic))
        print("dbGenOptimized")
        startTime = time.time()
        var.dbGenOptimized()
        elapsedTime = time.time() - startTime
        print("Optimized running time : ", (elapsedTime * 1000))
        print("Optimized DB lenght : ", var.getDBsize(DbGenType.Optimized))
        print("Optimized Collections DB input lenght : ", var.getDBsize(DbGenType.Input))
        print("Optimized Satisfy the inverse mining property? :", var.satisfyInverseMiningProp(DbGenType.Optimized))
        print("Optimized List of absolute minimum support levels : ", var.getAbsMinSupLev(DbGenType.Optimized))
        print("Optimized List of relative minimum support levels : ", var.getRelMinSupLev(DbGenType.Optimized))
        # print("DBGenOptimized database :")
        # var.printDB(DbGenType.Optimized)

if __name__ == "__main__":
        main()
