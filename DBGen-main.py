from dbgenlibrary import *

def main():

        # apriori parameter settings http://www.borgelt.net/doc/apriori/apriori.html
        # Format: apriori [options] infile [outfile]
        # Example: apriori.exe -f, -k, -s2 -tm groceries.csv -

        input_item_delimeter = "-f,"
        output_item_delimeter = "-k,"
        minimum_support_list = [("-s" + str(x).strip()) for x in [5.5, -1, 10.5]]  # positive: percentage of transactions, negative: exact number of transactions
        targetype = "-tm"  # frequest (s) maximal (m) closed (c)
        output_format = '-v" "'  # empty support information for output result
        inputfile = "test.csv"  # "groceries.csv"
        maximalout = "-"  # "-" for standard output

        var = DbGen(input_item_delimeter, output_item_delimeter, minimum_support_list, targetype, output_format, inputfile, maximalout)
        var.dbGenBasic()
        print("dbGenBasic")
        print("List of absolute minimum support levels : " + var.getAbsMinSupLev(DbGenType.Basic))
        print("List of relative minimum support levels : " + var.getRelMinSupLev(DbGenType.Basic))
        print("Satisfy the inverse mining property? :" + var.satisfyInverseMiningProp(DbGenType.Basic))
        print("DBGen database : \n", var.printDB(DbGenType.Basic))
        var.dbGenOptimized()
        print("dbGenOptimized")
        print("List of absolute minimum support levels : " + var.getAbsMinSupLev(DbGenType.Optimized))
        print("List of relative minimum support levels : " + var.getRelMinSupLev(DbGenType.Optimized))
        print("Satisfy the inverse mining property? :" + var.satisfyInverseMiningProp(DbGenType.Optimized))
        print("DBGen database : \n", var.printDB(DbGenType.Optimized))

if __name__ == "__main__":
        main()
