#! /home_rdlab/CLUSTER/soft/python-3.5.0/bin/python

# Implementation from scratch of the algorithms presented in the paper "Distribution-Based Synthetic Database Generation Techniques for Itemset Mining" by Ganesh Ramesh, Mohammed J. Zaki and William A. Maniatty
# Programmer: Christian Lezcano

from dbgenlibrary import *
import time

def main():

        # apriori parameter settings http://www.borgelt.net/doc/apriori/apriori.html
        # Format: apriori [options] infile [outfile]
        # Example: apriori.exe -f, -k, -s2 -tm groceries.csv -
        # input_item_delimeter = "-f,"
        input_item_delimeter = '-f" "'
        output_item_delimeter = "-k,"
        minimum_support_list = ["-s" + str(x).strip() for x in [2, 5, 7, 9]] # positive: percentage of transactions, negative: exact number of transactions
        targetype = "-tm"  # frequest (s) maximal (m) closed (c)
        output_format = '-v" "'  # empty support information for output result
        # inputfile = "dataset-1000.csv"
        # inputfile = "dataset-5000.csv"
        # inputfile = "dataset-20000.csv"
        # inputfile = "dataset-75000.csv"
        # inputfile = "dataset-88162.csv"
        # inputfile = "dataset-93371.csv"  # "groceries.csv"
        # inputfile = "dataset-100000.csv"
        inputfile = "dataset-112018.csv"
        # inputfile = "dataset-450624.csv"
        maximalout = "-"  # "-" for standard output

        var = DbGen(input_item_delimeter, output_item_delimeter, minimum_support_list, targetype, output_format, inputfile, maximalout)
        print("Input DB Number of elements : %d" % var.getNumElements())
        print("Input-Collections DB input lenght : ", var.getDBsize(DbGenType.Input))
        print("by DB : %d, %d, %d, %d," % (var.collection_list[0].size(DbGenType.Input), var.collection_list[1].size(DbGenType.Input), var.collection_list[2].size(DbGenType.Input), var.collection_list[3].size(DbGenType.Input)))

        startTime = time.time()
        var.dbGenBasic()
        elapsedTime = time.time() - startTime
        print("\nBasic running time : ", (elapsedTime * 1000))
        print("Output-Basic DB lenght : %d" % var.getDBsize(DbGenType.Basic))
        print("by DB : %d, %d, %d, %d," % (var.collection_list[0].size(DbGenType.Basic), var.collection_list[1].size(DbGenType.Basic), var.collection_list[2].size(DbGenType.Basic), var.collection_list[3].size(DbGenType.Basic)))
        print("Basic List of absolute minimum support levels : ", var.getAbsMinSupLev(DbGenType.Basic))
        print("Basic List of relative minimum support levels : ", var.getRelMinSupLev(DbGenType.Basic))
        print("Basic Satisfy the inverse mining property? : ", var.satisfyInverseMiningProp(DbGenType.Basic))

        startTime = time.time()
        var.dbGenBasicOptimized()
        elapsedTime = time.time() - startTime
        print("\nBasicOptimized running time : ", (elapsedTime * 1000))
        print("Output-BasicOptimized DB lenght : %d" % var.getDBsize(DbGenType.BasicOptimized))
        print("by DB : %d, %d, %d, %d," % (var.collection_list[0].size(DbGenType.BasicOptimized), var.collection_list[1].size(DbGenType.BasicOptimized), var.collection_list[2].size(DbGenType.BasicOptimized), var.collection_list[3].size(DbGenType.BasicOptimized)))
        print("BasicOptimized List of absolute minimum support levels : ", var.getAbsMinSupLev(DbGenType.BasicOptimized))
        print("BasicOptimized List of relative minimum support levels : ", var.getRelMinSupLev(DbGenType.BasicOptimized))
        print("BasicOptimized Satisfy the inverse mining property? : ", var.satisfyInverseMiningProp(DbGenType.BasicOptimized))

        startTime = time.time()
        var.dbGenGamma()
        elapsedTime = time.time() - startTime
        print("\nGamma running time : ", (elapsedTime * 1000))
        print("Output-Gamma DB lenght : %d" % var.getDBsize(DbGenType.Gamma))
        print("by DB : %d, %d, %d, %d," % (
            var.collection_list[0].size(DbGenType.Gamma),
            var.collection_list[1].size(DbGenType.Gamma),
            var.collection_list[2].size(DbGenType.Gamma),
            var.collection_list[3].size(DbGenType.Gamma)))
        print("Gamma List of absolute minimum support levels : ", var.getAbsMinSupLev(DbGenType.Gamma))
        print("Gamma List of relative minimum support levels : ", var.getRelMinSupLev(DbGenType.Gamma))
        print("Gamma Satisfy the inverse mining property? : ", var.satisfyInverseMiningProp(DbGenType.Gamma))

        startTime = time.time()
        var.dbGenGammaOptimized()
        elapsedTime = time.time() - startTime
        print("\nGammaOptimized running time : ", (elapsedTime * 1000))
        print("Output-GammaOptimized DB lenght : %d" % var.getDBsize(DbGenType.GammaOptimized))
        print("by DB : %d, %d, %d, %d," % (
        var.collection_list[0].size(DbGenType.GammaOptimized), var.collection_list[1].size(DbGenType.GammaOptimized),
        var.collection_list[2].size(DbGenType.GammaOptimized), var.collection_list[3].size(DbGenType.GammaOptimized)))
        print("GammaOptimized List of absolute minimum support levels : ", var.getAbsMinSupLev(DbGenType.GammaOptimized))
        print("GammaOptimized List of relative minimum support levels : ", var.getRelMinSupLev(DbGenType.GammaOptimized))
        print("GammaOptimized Satisfy the inverse mining property? : ", var.satisfyInverseMiningProp(DbGenType.GammaOptimized))

        startTime = time.time()
        var.dbGenHypergraph()
        elapsedTime = time.time() - startTime
        print("\nHypergraph running time : ", (elapsedTime * 1000))
        print("Output-Hypergraph DB lenght : %d" % var.getDBsize(DbGenType.Hypergraph))
        print("by DB : %d, %d, %d, %d," % (
            var.collection_list[0].size(DbGenType.Hypergraph),
            var.collection_list[1].size(DbGenType.Hypergraph),
            var.collection_list[2].size(DbGenType.Hypergraph),
            var.collection_list[3].size(DbGenType.Hypergraph)))
        print("Hypergraph List of absolute minimum support levels : ", var.getAbsMinSupLev(DbGenType.Hypergraph))
        print("Hypergraph List of relative minimum support levels : ", var.getRelMinSupLev(DbGenType.Hypergraph))
        print("Hypergraph Satisfy the inverse mining property? : ", var.satisfyInverseMiningProp(DbGenType.Hypergraph))



        # print("Optimized and Hypergraph are equal? : ", var.equalDB())

if __name__ == "__main__":
        main()
