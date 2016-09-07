import csv
def main():
    csvFile = open('dataset-75000.csv', 'w', newline='')
    csvWriter = csv.writer(csvFile, delimiter=',', lineterminator='\n')
    with open('75000-out1.csv', 'r') as f:
        for line in f.readlines():
            csvWriter.writerow([i.strip() for i in line.split(',')[1:]])
    f.closed
    csvFile.close()

if __name__ == "__main__":
    main()

