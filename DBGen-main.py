def main():

        # apriori parameter settings http://www.borgelt.net/doc/apriori/apriori.html
        # Format: apriori [options] infile [outfile]
        # Example: apriori.exe -f, -k, -s2 -tm groceries.csv -

        input_item_delimeter = "-f,"
        output_item_delimeter = "-k,"
        minimum_support_list = [0.5, 1, 1.5] # positive: percentage of transactions, negative: exact number of transactions
        targetype = "-tm"  # frequest (s) maximal (m) closed (c)
        inputfile = "groceries.csv"
        maximalout = "-" # "-" for standard output

        from apriori import aprioriexe
        aprioriexe(input_item_delimeter, output_item_delimeter, minimum_support_list, targetype, inputfile, maximalout)

if __name__ == "__main__":
        main()
