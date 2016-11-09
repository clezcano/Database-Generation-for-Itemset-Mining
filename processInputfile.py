import csv
from collections import Counter

def deleteFirstCol():
    csvFile = open('dataset-75000.csv', 'w', newline='')
    csvWriter = csv.writer(csvFile, delimiter=',', lineterminator='\n')
    with open('75000-out1.csv', 'r') as f:
        for line in f.readlines():
            csvWriter.writerow([i.strip() for i in line.split(',')[1:]])
    f.close()
    csvFile.close()

def maxsupfile(filename, input_item_delimeter):
    with open(filename, 'r') as f:
        fileMaxSup = Counter()
        for itemset in [{i.strip() for i in line.strip().split(input_item_delimeter)} for line in f.readlines()]:
            fileMaxSup.update({}.fromkeys(itemset, 1))
    print("Elements support : ", fileMaxSup.most_common())
    return max(fileMaxSup.values())

def main():
    file = "dataset-93371.csv"
    #input_item_delimeter = ','
    input_item_delimeter = ' '
    print("Singleton Maximum support for file %s : is %d" % (file, maxsupfile(file, input_item_delimeter)))

if __name__ == "__main__":
    main()
