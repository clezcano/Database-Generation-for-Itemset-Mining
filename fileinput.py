import csv
filein = 'groceries.csv'
#list = []
with open(filein, 'r') as f:
    w = csv.reader(f, delimiter=',')
    for i, row in enumerate(w, start=1):
        print(i, ") ", end='')
        for col in row:
            print(col, end=' , ')
        print ('\n')
