#! /home_rdlab/CLUSTER/soft/python-3.5.0/bin/python

# Implementation from scratch of the algorithms presented in the paper "Distribution-Based Synthetic Database Generation Techniques for Itemset Mining" by Ganesh Ramesh, Mohammed J. Zaki and William A. Maniatty
# Programmer: Christian Lezcano

from dbgenlibrary import *
import time

def main():

        # apriori parameter settings http://www.borgelt.net/doc/apriori/apriori.html
        # Format: apriori [options] infile [outfile]
        # Example: apriori.exe -f, -k, -s2 -tm groceries.csv -
        delimeter = " "
        # delimeter = ","
        input_item_delimeter = '-f"' + delimeter + '"'
        output_item_delimeter = "-k,"
        minimum_support_list = ["-s" + str(x).strip() for x in [55, 65, 75]] # positive: percentage of transactions, negative: exact number of transactions
        # minimum_support_list = ["-s" + str(x).strip() for x in [45, 55, 65, 75]]  # positive: percentage of transactions, negative: exact number of transactions
        targetype = "-tm"  # frequest (s) maximal (m) closed (c)
        output_format = '-v" "'  # empty support information for output result
        maximalout = "-"  # "-" for standard output
        # inputfile = "dataset-246.csv"
        # inputfile = "dataset-377.csv"
        # inputfile = "dataset-1000.csv"
        # inputfile = "dataset-3196.csv"
        # inputfile = "dataset-4141.csv"
        # inputfile = "dataset-5000.csv"
        # inputfile = "dataset-8124.csv"
        # inputfile = "dataset-20000.csv"
        # inputfile = "dataset-49046v1.csv"
        # inputfile = "dataset-49046v2.csv"
        # inputfile = "dataset-59602.csv"
        # inputfile = "dataset-67557.csv"
        # inputfile = "dataset-75000.csv"
        # inputfile = "dataset-77512.csv"
        # inputfile = "dataset-88162.csv"
        # inputfile = "dataset-245057.csv"
        # inputfile = "dataset-340183.csv"
        # inputfile = "dataset-541909.csv"
        # inputfile = "dataset-574913.csv"
        # inputfile = "dataset-990002.csv"  # "groceries.csv"
        # inputfile = "dataset-1000000v1.csv"
        # inputfile = "dataset-1000000v2.csv"
        # inputfile = "dataset-1000000v3.csv"
        # inputfile = "dataset-1040000.csv"
        # inputfile = "dataset-1112949.csv"
        inputfile = "dataset-1692082.csv"
        # inputfile = "dataset-5000000.csv"

        print("Dataset analysis-------------------------------------------------------------------------------------------------")
        dataset = InputFile(inputfile, delimeter)
        print("File name: %s DataFile size: %d Number of elements: %d maximun support:  %d maximun support percentage: %.15f " % (inputfile, dataset.getFileSize(), dataset.getFileNumElements(), dataset.getFileMaxSup(), (dataset.getFileMaxSup()/dataset.getFileSize()) * 100))
        # print("File name: %s DataFile size: %d Number of elements: %d " % (inputfile, dataset.getFileSize(), dataset.getFileNumElements()))
        # print("File name: %s Number of elements: %d " % (inputfile, dataset.getFileNumElements()))
        #
        print(
            "Input analysis-------------------------------------------------------------------------------------------------")
        var = DbGen(input_item_delimeter, output_item_delimeter, minimum_support_list, targetype, output_format, inputfile, maximalout)
        # print("Input DB Number of elements : %d" % var.getNumElements())
        print("\nM1 size: %d M2 size: %d M3 size: %d " % (var.collection_list[0].size(DbGenType.Input), var.collection_list[1].size(DbGenType.Input), var.collection_list[2].size(DbGenType.Input)))
        print("Input DB size : ", var.getDBsize(DbGenType.Input))
        print("\nM1 # elements: %d M2 # elements: %d M3 # elements: %d" % (
        var.collection_list[0].getDBNumElements(DbGenType.Input), var.collection_list[1].getDBNumElements(DbGenType.Input),
        var.collection_list[2].getDBNumElements(DbGenType.Input)))
        print("Input DB # elements : ", var.getNumElements(DbGenType.Input))
        #
        # print("Basic-------------------------------------------------------------------------------------------------")
        # startTime = time.time()
        # var.dbGenBasic()
        # elapsedTime = time.time() - startTime
        # print("\nPartial DB # elements First stage: %d Partial DB # elements Second stage: %d Partial DB # elements Third stage: %d" %
        #       (var.collection_list[0].getDBNumElements(DbGenType.Basic),
        #       var.collection_list[1].getDBNumElements(DbGenType.Basic),
        #       var.collection_list[2].getDBNumElements(DbGenType.Basic)))
        # print("Final DB # elements : ", var.getNumElements(DbGenType.Basic))
        # print("\nBasic running time : ", (elapsedTime * 1000))
        #
        # print("\nPartial DB size First stage: %d Partial DB size Second stage: %d Partial DB size Third stage: %d" %
        #       (var.collection_list[0].size(DbGenType.Basic),
        #        var.collection_list[1].size(DbGenType.Basic),
        #        var.collection_list[2].size(DbGenType.Basic)))
        # print("Final DB size : %d" % var.getDBsize(DbGenType.Basic))
        # print("Basic List of absolute minimum support levels : ", var.getAbsMinSupLev(DbGenType.Basic))
        # print("Basic List of relative minimum support levels : ", var.getRelMinSupLev(DbGenType.Basic))
        # print("Basic Satisfy the inverse mining property? : ", var.satisfyInverseMiningProp(DbGenType.Basic))
        #
        # print(
        #     "BasicOptimized-------------------------------------------------------------------------------------------------")
        # startTime = time.time()
        # var.dbGenBasicOptimized()
        # elapsedTime = time.time() - startTime
        # print("\nPartial DB # elements First stage: %d Partial DB # elements Second stage: %d Partial DB # elements Third stage: %d" %
        #      (var.collection_list[0].getDBNumElements(DbGenType.BasicOptimized),
        #      var.collection_list[1].getDBNumElements(DbGenType.BasicOptimized),
        #      var.collection_list[2].getDBNumElements(DbGenType.BasicOptimized)))
        #
        # print("Final DB # elements : ", var.getNumElements(DbGenType.BasicOptimized))
        # print("\0BasicOptimized running time : ", (elapsedTime * 1000))
        #
        # print("\nPartial DB size First stage: %d Partial DB size Second stage: %d Partial DB size Third stage: %d" %
        #     (var.collection_list[0].size(DbGenType.BasicOptimized),
        #     var.collection_list[1].size(DbGenType.BasicOptimized),
        #     var.collection_list[2].size(DbGenType.BasicOptimized)))
        # print("Final DB size : %d" % var.getDBsize(DbGenType.BasicOptimized))
        # print("BasicOptimized List of absolute minimum support levels : ", var.getAbsMinSupLev(DbGenType.BasicOptimized))
        # print("BasicOptimized List of relative minimum support levels : ", var.getRelMinSupLev(DbGenType.BasicOptimized))
        # print("BasicOptimized Satisfy the inverse mining property? : ", var.satisfyInverseMiningProp(DbGenType.BasicOptimized))
        #
        # print("Gamma-------------------------------------------------------------------------------------------------")
        # startTime = time.time()
        # var.dbGenGamma()
        # elapsedTime = time.time() - startTime
        # print(
        #     "\nPartial DB # elements First stage: %d Partial DB # elements Second stage: %d Partial DB # elements Third stage: %d " %
        #     (var.collection_list[0].getDBNumElements(DbGenType.Gamma),
        #      var.collection_list[1].getDBNumElements(DbGenType.Gamma),
        #      var.collection_list[2].getDBNumElements(DbGenType.Gamma)))
        #
        # print("Final DB # elements : ", var.getNumElements(DbGenType.Gamma))
        # print("\0Gamma running time : ", (elapsedTime * 1000))
        #
        # print(
        #     "\nPartial DB size First stage: %d Partial DB size Second stage: %d Partial DB size Third stage: %d " %
        #    (var.collection_list[0].size(DbGenType.Gamma),
        #     var.collection_list[1].size(DbGenType.Gamma),
        #     var.collection_list[2].size(DbGenType.Gamma)))
        # print("Final DB size : %d" % var.getDBsize(DbGenType.Gamma))
        # print("Gamma List of absolute minimum support levels : ", var.getAbsMinSupLev(DbGenType.Gamma))
        # print("Gamma List of relative minimum support levels : ", var.getRelMinSupLev(DbGenType.Gamma))
        # print("Gamma Satisfy the inverse mining property? : ", var.satisfyInverseMiningProp(DbGenType.Gamma))
        #
        # print(
        #     "GammaOptimized-------------------------------------------------------------------------------------------------")
        # startTime = time.time()
        # var.dbGenGammaOptimized()
        # elapsedTime = time.time() - startTime
        # print(
        #     "\nPartial DB # elements First stage: %d Partial DB # elements Second stage: %d Partial DB # elements Third stage: %d " %
        #     (var.collection_list[0].getDBNumElements(DbGenType.GammaOptimized),
        #      var.collection_list[1].getDBNumElements(DbGenType.GammaOptimized),
        #      var.collection_list[2].getDBNumElements(DbGenType.GammaOptimized)))
        #
        # print("Final DB # elements : ", var.getNumElements(DbGenType.GammaOptimized))
        # print("\0GammaOptimized running time : ", (elapsedTime * 1000))
        #
        # print(
        #     "\nPartial DB size First stage: %d Partial DB size Second stage: %d Partial DB size Third stage: %d " %
        #     (var.collection_list[0].size(DbGenType.GammaOptimized),
        #      var.collection_list[1].size(DbGenType.GammaOptimized),
        #      var.collection_list[2].size(DbGenType.GammaOptimized)))
        # print("Final DB size : %d" % var.getDBsize(DbGenType.GammaOptimized))
        # print("GammaOptimized List of absolute minimum support levels : ", var.getAbsMinSupLev(DbGenType.GammaOptimized))
        # print("GammaOptimized List of relative minimum support levels : ", var.getRelMinSupLev(DbGenType.GammaOptimized))
        # print("GammaOptimized Satisfy the inverse mining property? : ", var.satisfyInverseMiningProp(DbGenType.GammaOptimized))
        #
        # print(
        #     "Hypergraph-------------------------------------------------------------------------------------------------")
        # startTime = time.time()
        # var.dbGenHypergraph()
        # elapsedTime = time.time() - startTime
        # print(
        #     "\nPartial DB # elements First stage: %d Partial DB # elements Second stage: %d Partial DB # elements Third stage: %d " %
        #     (var.collection_list[0].getDBNumElements(DbGenType.Hypergraph),
        #      var.collection_list[1].getDBNumElements(DbGenType.Hypergraph),
        #      var.collection_list[2].getDBNumElements(DbGenType.Hypergraph)))
        #
        # print("Final DB # elements : ", var.getNumElements(DbGenType.Hypergraph))
        # print("\0Hypergraph running time : ", (elapsedTime * 1000))
        #
        # print(
        #     "\nPartial DB size First stage: %d Partial DB size Second stage: %d Partial DB size Third stage: %d " %
        #     (var.collection_list[0].size(DbGenType.Hypergraph),
        #      var.collection_list[1].size(DbGenType.Hypergraph),
        #      var.collection_list[2].size(DbGenType.Hypergraph)))
        # print("Final DB size : %d" % var.getDBsize(DbGenType.Hypergraph))
        # print("Hypergraph List of absolute minimum support levels : ",
        #       var.getAbsMinSupLev(DbGenType.Hypergraph))
        # print("Hypergraph List of relative minimum support levels : ",
        #       var.getRelMinSupLev(DbGenType.Hypergraph))
        # print("Hypergraph Satisfy the inverse mining property? : ", var.satisfyInverseMiningProp(DbGenType.Hypergraph))
        #
        #
        #
        # # print("Optimized and Hypergraph are equal? : ", var.equalDB())

if __name__ == "__main__":
        main()
