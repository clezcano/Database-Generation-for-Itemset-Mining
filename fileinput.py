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


def satisfyContainmentProp(
        self):  # check if the maximal collections satisfy the containment property. Ex: Mk [ Mk-1 [ ... [ M2 [ M1
    numberCollections = self.getNumCollections()
    if numberCollections == 1:
        return True
    i = 0
    while i < (numberCollections - 1):
        j = i + 1
        mc1 = [itemset.getItemSet() for itemset in self.collection_list[i].getDataBase()]  # returns a list of ItemSet
        mc2 = [itemset.getItemSet() for itemset in self.collection_list[j].getDataBase()]
        for itemset2 in mc2:
            isSubset = False
            for itemset1 in mc1:
                if itemset2.issubset(itemset1):
                    isSubset = True
                    break
            if not isSubset:
                return False
        i += 1
    return True


count = 0
for itemset in self.getDataBase():
    if xitemset.getItemSet().issubset(itemset.getItemSet()):
        count += 1
return count