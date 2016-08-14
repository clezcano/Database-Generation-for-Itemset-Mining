def main():

        # apriori parameter settings http://www.borgelt.net/doc/apriori/apriori.html
        # Format: apriori [options] infile [outfile]
        # Example: apriori.exe -f, -k, -s2 -tm groceries.csv -

        input_item_delimeter = "-f,"
        output_item_delimeter = "-k,"
        minimum_support_list = [("-s" + str(x).strip()) for x in [5.5, -1, 10.5]] # positive: percentage of transactions, negative: exact number of transactions
        targetype = "-tm"  # frequest (s) maximal (m) closed (c)
        output_format = '-v" "' # empty support information for output result
        inputfile = "test.csv" # "groceries.csv"
        maximalout = "-" # "-" for standard output

        from dbgenlibrary import dbgenbasic
        dbgenbasic(input_item_delimeter, output_item_delimeter, minimum_support_list, targetype, output_format, inputfile, maximalout)

if __name__ == "__main__":
        main()
