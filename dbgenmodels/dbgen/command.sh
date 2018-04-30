./eclat -f"," -s-50 -k"," -Z groceries.csv output-orig
./eclat -f"," -s-50 -k"," -Z x_groceries.csv output-gen


java -cp exe/itemset-mining-1.0.jar itemsetmining.main.ItemsetMining -i 100 -f example.dat -v 