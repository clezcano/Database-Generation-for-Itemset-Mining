"""
.. module:: dbgen
dbgen
******
:Description: dbgen
    input is a transactional database;
    generates various synthetic dbs based on statistical properties of input db
    using various probabilistic approaches
:Authors:
    marias@cs.upc.edu
:Version: 0.1
:Date:  17/11/2017
"""
from __future__ import print_function, division
import time
import tempfile
import fileinput
from sys import platform
from itertools import combinations
import argparse
import numpy as np
import logging
from subprocess import call
import re
import os
import warnings
warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')
import gensim
from gensim import corpora

__author__ = 'marias'

def parse_iim_output(fname, dictionary):
    # syntax is:  '{2, 13}	prob: 0,17160 	int: 1,00000'
    # translate back to string as well
    pattern = re.compile(r'\{(.+)\}(\s+)prob: ([\d,]+)(\s+)int')
    iims = []
    with open(fname) as inf:
        logging.info("parsing iim output file {}".format(fname))
        for line in inf:
            m = re.match(pattern, line)
            if m:
                itemset = sorted([dictionary[int(item)] for item in m.group(1).strip().split(",")])
                prob_str = m.group(3).strip().replace(",", ".")
                iims.append((itemset, float(prob_str)))
                logging.debug("adding interesting itemset {}".format((itemset, prob_str)))
    return iims

def print_timing(func):
  def wrapper(*arg):
    t1 = time.time()
    res = func(*arg)
    t2 = time.time()
    t = int(t2-t1)
    s = t % 60
    m = t // 60
    h = t // 3600
    logging.info("{} took {:0.3f}s [{}h, {}m, {}s]".format(func.__name__, (t2-t1), h, m, s))
    return res
  return wrapper

def head(fname, nlines=5):
    with open(fname) as inf:
        logging.info("\n" + "".join(inf.readlines()[0:nlines]))
    inf.close()

@print_timing
def eclatLDA(infname, minsup):
    """
    runs eclat on input db
    returns nr of frequent itemsets found and save them on file.
    """
    bname = os.path.splitext(os.path.basename(infname))[0]
    infnamePath = os.path.join(os.getcwd(), "db", infname)
    outfnamePath = os.path.join(os.getcwd(),"out", "eclat-lda-{}-minsup-{}.itemsets".format(bname, minsup))
    eclatName = ""
    if platform == "win32":
        eclatName = "eclat.exe"
    elif platform == "linux" or platform == "linux2":
        eclatName = "eclat"
    cmd = [os.path.join(os.getcwd(), "exe", eclatName), '-f" "', "-s{}".format(minsup), "-k{}".format(" "), "-Z", infnamePath, outfnamePath]  # -Z prints number of items per size
    # logging.info("eclatLDA : {}".format(cmd))
    fd, temp_path = tempfile.mkstemp()
    with open(temp_path, 'w') as tmpout:
        logging.info("running: {}".format(" ".join(cmd)))
        call(cmd, stdout=tmpout)
        logging.info("wrote frequent itemset file {}".format(outfnamePath))
    with open(temp_path) as inf:
        stat_str = inf.readlines()
        logging.info("eclat stats on file {}: {}".format(infname, stat_str))
    nfreqitemsets = 0
    if len(stat_str):
        m = re.match(r'all: (\d+)', stat_str[0])
        # print("m : ", m)
        if m:
            nfreqitemsets = int(m.group(1))
    os.close(fd)
    os.remove(temp_path)
    return nfreqitemsets

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class KrimpGen:
    def __init__(self, indb):
        # Item data -> Categorical data -> Krimp format -> Categorical data -> Item data.
        self.origDBfileName = indb  # Original DB file name e.g. chess.dat
        self.origDBbaseName = os.path.splitext(os.path.basename(indb))[0]
        self.origDBfilePath = os.path.join(os.getcwd(), "KrimpBinSource", "data", "datasets", self.origDBfileName)  # Original DB file name e.g. chess.dat
        self.CategDBfilePath = os.path.join(os.getcwd(), "KrimpBinSource", "data", "datasets", "krimpCateg{}".format(self.origDBfileName))  # Categorical DB file name which feed.
        self.krimpfileBaseName = None
        self.GenDBfilePath = os.path.join(os.getcwd(), "KrimpBinSource", "data", "datasets", "gen-krimp-{}-{}".format(self.origDBbaseName, args.krimp_minsup))  # Newly generated DB file name.
        self.originalDB = []  # this one saves the original DB.         # parse input file, figure out various statistics from dbfile
        self.categoricalDB = []  # input DB formatted as a categorical DB.
        self.modelFileName = None     # to be determined on learn execution, depends on parameters. Same as igm class variable but this one is saved in file.
        self.krimpModel = None        # Krimp Code Table (CT)     # model  [(itemset, frequency),...] # frequency is over the cover and not over the original DB
        self.items = set()  # This is used to know the number of different items in original DB.
        self.itemAlphabet = []  # Original DB alphabet
        self.itemToDomain = dict()  # map an item to its domain.
        self.domainToItem = dict()  # map any element of a domain to its item.
        self.categToKrimp = dict()  # map categorical format to krimp's
        self.krimpToCateg = dict()  # map krimp's format to categorical format.
        with open(self.origDBfilePath) as infile:
            for row in infile:
                transaction = sorted([int(item.strip()) for item in row.strip().split(" ")])
                self.items |= set(transaction)
                self.originalDB.append(transaction)
            logging.info("Nr of transactions in {}: {}, Nr. of items: {}".format(self.origDBfileName, len(self.originalDB), len(self.items)))
        self.itemAlphabet = sorted(list(self.items))
        self.toCategAlphabet()
        self.toCategDB()

    def toCategAlphabet(self):
        counter = 0
        for item in self.itemAlphabet:
            self.itemToDomain[item] = [counter, counter + 1]  # [exist, not exist] or [purchased item, not purchased item]
            self.domainToItem[counter] = item     # even values = exist, odd values = not exist
            self.domainToItem[counter + 1] = item
            counter = counter + 2

    def toCategDB(self):  # convert the item database into a categorical one.
        emptyTrans = [self.itemToDomain[item][1] for item in self.itemAlphabet]  # This line empties the array by assigning each element the "not exist" value
        for trans in self.originalDB:
            auxTrans = emptyTrans[:]
            for item in trans:
                auxTrans[auxTrans.index(self.itemToDomain[item][1])] = self.itemToDomain[item][0]
            self.categoricalDB.append(auxTrans)
        self.saveCategDBtoFile()

    def saveCategDBtoFile(self):
        with open(self.CategDBfilePath, 'w') as categFile:
            for trans in self.categoricalDB:
                categFile.write(" ".join(map(str, trans)) + "\n")
            logging.info("wrote categorical DB file to {}".format(self.CategDBfilePath))

    @print_timing
    def getCT(self):  # Categorical data -> Krimp format -> Categorical data.
        self.datadirConf()
        self.convertdbConf()
        self.toKrimpFormat()
        self.compressConf()

    def datadirConf(self):  # file setup: datadir.conf
        for line in fileinput.input(os.path.join(os.getcwd(), "KrimpBinSource", "bin", "datadir.conf"), inplace=1):
            if "dataDir =" in line:
                line = "dataDir = " + os.path.join(os.getcwd(), "KrimpBinSource", "data").replace('\\', '/') + '/'
            elif "expDir =" in line:
                line = "expDir = " + os.path.join(os.getcwd(), "KrimpBinSource", "xps").replace('\\', '/') + '/'
            print(line.rstrip('\n'))

    def convertdbConf(self):  # set up file: convertdb.conf
        logging.info("convert categorical DB to Krimp DB; categorical DB name = {}".format(os.path.basename(self.CategDBfilePath)))
        bname = os.path.splitext(os.path.basename(self.CategDBfilePath))[0]
        for line in fileinput.input(os.path.join(os.getcwd(), "KrimpBinSource", "bin", "convertdb.conf"), inplace=1):
            if "dbName =" in line:
                line = "dbName = " + bname
            print(line.rstrip('\n'))
        cmd = [os.path.join(os.getcwd(), "KrimpBinSource", "bin", "krimp.exe"), os.path.join(os.getcwd(), "KrimpBinSource", "bin", "convertdb.conf")]
        logging.info("converting categorical DB to Krimp-formatted DB >> cmd : {}".format(cmd))
        try:
            call(cmd, timeout=2)
        except:
            pass
        self.krimpfileBaseName = bname + ".db"
        logging.info("categ. DB converted to krimp format in file: {}".format(self.krimpfileBaseName))

    def toKrimpFormat(self):
        krimpDBfileName = os.path.join(os.getcwd(), "KrimpBinSource", "data", "datasets", self.krimpfileBaseName)
        krimpFormat = []
        categFormat = []
        with open(krimpDBfileName) as inf:
            for line in inf.readlines()[:7]:
                if line.startswith("ab :"):  # krimp format
                    krimpFormat = [int(item.strip()) for item in line.split(":")[1].strip().split(" ")]
                elif line.startswith("it :"):  # categorical format
                    categFormat = [int(item.strip()) for item in line.split(":")[1].strip().split(" ")]
        self.krimpToCateg = dict(zip(krimpFormat, categFormat))  #  map krimp's format to categorical format.
        self.categToKrimp = dict(zip(categFormat, krimpFormat))  #  map categorical format to krimp's

    def compressConf(self):
        bname = os.path.splitext(os.path.basename(self.krimpfileBaseName))[0]
        logging.info("Krimp compression ; Krimp format DB name = {}".format(self.krimpfileBaseName))
        for line in fileinput.input(os.path.join(os.getcwd(), "KrimpBinSource", "bin", "compress.conf"), inplace=1):
            if line.startswith("iscName ="):
                line = "iscName = " + bname + "-" + args.krimp_type + "-" + str(args.krimp_minsup) + "d"
            elif line.startswith("dataType ="):
                line = "dataType = bai32"
            print(line.rstrip('\n'))
        cmd = [os.path.join(os.getcwd(), "KrimpBinSource", "bin", "krimp.exe"), os.path.join(os.getcwd(), "KrimpBinSource", "bin", "compress.conf")]
        call(cmd)
        logging.info("Krimp inference; minsup = {}".format(args.krimp_minsup))

    @print_timing
    def learn(self, minsup):
        self.modelFileName = os.path.join(os.getcwd(), "models", "krimp-model-{}{}".format(self.origDBfileName, minsup))
        if os.path.exists(self.modelFileName):
            self.loadKrimpModelFromFile()
        else:
            self.getKrimpModel()
            self.saveKrimpModeltoFile()
        return len(self.krimpModel)

    def loadKrimpModelFromFile(self):
        self.krimpModel = []
        with open(self.modelFileName) as inf:
            for line in inf:
                itemset = [int(item.strip()) for item in line.strip().split(" ")]
                prob = int(inf.readline().strip())
                self.krimpModel.append((itemset, prob))
            logging.info("Krimp model loaded from file {}".format(self.modelFileName))

    def saveKrimpModeltoFile(self):
        with open(self.modelFileName, 'w') as modelFile:
            for (itemset, p) in self.krimpModel:
                modelFile.write(" ".join(map(str, itemset)) + "\n")
                modelFile.write(str(p) + "\n")
            logging.info("wrote Krimp model file to {}".format(self.modelFileName))

    def getKrimpModel(self):
        # syntax is:  '0 1 2 3 4 5 6 7 9 11 (2573,2573)'
        auxModelFileName = os.path.join(os.getcwd(), "KrimpBinSource", "xps", "compress", args.krimp_CTfilename)
        self.krimpModel = []
        pattern = re.compile(r'(.+)(\s+)\((.+)\)')
        with open(auxModelFileName) as inf:
            for line in inf.readlines()[2:]:
                m = re.match(pattern, line)
                if m:
                    itemset = sorted([int(item.strip()) for item in m.group(1).strip().split(" ")])
                    prob = int(list(m.group(3).strip().split(","))[0])
                    self.krimpModel.append((itemset, prob))
            logging.info("Krimp model loaded from file {}".format(auxModelFileName))

    def chooseItemset(self, CTavailableIndexes, domain):
        auxCT = []
        availableCT = [self.krimpModel[i] for i in CTavailableIndexes]
        for (itemset, frequency) in availableCT:  # itemset is categorical
            krimpFormatDom = {self.categToKrimp[self.itemToDomain[domain][0]], self.categToKrimp[self.itemToDomain[domain][1]]}
            if krimpFormatDom.intersection(set(itemset)):
                auxCT.append((itemset, frequency))
        itemsets = [itemset for (itemset, p) in auxCT]
        freq = [p for (itemset, p) in auxCT]
        sumFreq = sum(freq)
        return np.random.choice(itemsets, p=[p / sumFreq for p in freq])

    def getDomains(self, itemset):  # itemset must be in Krimp format
        return [self.domainToItem[self.krimpToCateg[item]] for item in itemset]

    def removeCTelements(self, CTavailableIndexes, itemset):
        return [index for index in CTavailableIndexes if set(self.getDomains(self.krimpModel[index][0])).intersection(set(self.getDomains(itemset))) == set()]

    def convertToItemsets(self, krimpItemset):
        return [self.domainToItem[i] for i in [self.krimpToCateg[item] for item in krimpItemset] if i % 2 == 0]  # even values means the item exists

    @print_timing
    def gen(self):  # Categorical data -> Item data
        with open(self.GenDBfilePath, 'w') as genFile:
            ntrans = 0
            for i in range(len(self.originalDB)):
                newTransaction = []
                domains = self.items.copy()  # each alphabet's item represents a domain.  # domains is not categorical
                CTavailableIndexes = range(len(self.krimpModel))
                while domains:
                    chosenDomain = np.random.choice(list(domains))
                    itemset = self.chooseItemset(CTavailableIndexes, chosenDomain)  # itemset is categorical
                    newTransaction += itemset  # must be an union of disjoint itemsets.
                    domains -= set(self.getDomains(itemset))
                    CTavailableIndexes = self.removeCTelements(CTavailableIndexes, itemset)
                newTrans = " ".join(sorted(self.convertToItemsets(newTransaction)))
                logging.debug("===> generating transaction nr: {}; generated transaction: {}".format(i, newTrans))
                if len(newTrans):
                    genFile.write(newTrans + "\n")
                    logging.debug("writing transaction to new db: {}".format(newTrans))
                    ntrans += 1
                # REPORT progress
                if i and i % 1000 == 0:
                    logging.info("\tprocessed {} transactions of {} ({:0.1f}%).".format(i, len(self.originalDB), 100.0 * i / len(self.originalDB)))
            logging.info("wrote synthetic database to file {}, with {} transactions ({:0.1f}%)".format(self.GenDBfilePath, ntrans, 100.0 * ntrans / len(self.originalDB)))
        return len(self.GenDBfilePath)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class IGMGen:
    """
       This DB Generator (IGM) is based on the model described in the paper
       "Connection between mining frequent itemsets and learning generative models" by Laxman et.al.
    """

    def __init__(self, indb):
        self.origDBfileName = indb
        self.origDBbaseName = os.path.splitext(os.path.basename(indb))[0]
        self.origDBfilePath = os.path.join(os.getcwd(), "db", indb)  # Original DB file name e.g. chess.dat
        self.GenDBfilePath = os.path.join(os.getcwd(), "db", "gen-igm-{}-minsup-{}".format(self.origDBbaseName, args.igm_minsup))  # Newly generated DB file name.
        self.originalDB = []  # this one saves the original DB.         #  parse input file, figure out various statistics from dbfile
        self.modelFileName = None  # to be determined on learn execution, depends on parameters. Same as igm class variable but this one is saved in file.
        self.igmModel = None  # model parameters [(itemset, prob),...]
        self.itemAlphabet = set()  # This is used to know the number of different items in original DB. It saves the item's alphabet.
        with open(self.origDBfilePath) as infile:
            for row in infile:
                transaction = [int(item.strip()) for item in row.strip().split(" ")]  # transaction = [item.strip().replace(" ", "_") for item in row.strip().split(',')]
                self.itemAlphabet |= set(transaction)
                self.originalDB.append(sorted(transaction))
            logging.info("Nr of transactions in {}: {}, Nr. of items: {}".format(self.origDBfileName, len(self.originalDB), len(self.itemAlphabet)))

    @print_timing
    def learn(self, minsup):
        self.modelFileName = os.path.join(os.getcwd(), "models", "igm-model-{}-minsup-{}".format(self.origDBbaseName, minsup))
        if os.path.exists(self.modelFileName):
            self.loadIgmModelFromFile()
        else:
            logging.info("running IGM inference; minsup = {} on file: {}".format(minsup, self.origDBfileName))
            fi = self.getFI(minsup)  # get the frequent itemsets of the original DB. (e.g. using eclat) Format: [(itemset, prob),...]
            self.igmModel = self.filterFI(fi)  # Select the set of interesting itemsets following the concept proposed by Laxman et.al.
            self.saveIgmModeltoFile()
        return len(self.igmModel)

    @print_timing
    def gen(self):
        with open(self.GenDBfilePath, 'w') as genFile:
            ntrans = 0
            for i in range(len(self.originalDB)):
                newTransaction = []
                itemsetIndex = self.chooseItemset()
                logging.info("itemset index selected : {} for transaction {}".format(itemsetIndex, i))
                pattern = self.choosePattern(itemsetIndex)
                logging.info("pattern selected : {} for transaction  {}".format(pattern, i))
                noise = self.chooseNoise(itemsetIndex)
                logging.info("noise selected : {} for transaction  {}".format(noise, i))
                newTransaction = pattern + noise
                newTrans = " ".join(map(str,sorted(newTransaction)))
                (itemset, p) = self.igmModel[itemsetIndex]
                logging.info("===> generating transaction nr: {}; freq. itemset selected: {}; pattern selected: {}; noise pattern selected: {}".format(i, itemset, pattern, noise))
                if len(newTrans):
                    genFile.write(newTrans + "\n")
                    logging.info("writing transaction to new db: {}".format(newTrans))
                    ntrans += 1
                # REPORT progress
                if i and i % 1000 == 0:
                    logging.info("\tprocessed {} transactions of {} ({:0.1f}%).".format(i, len(self.originalDB), 100.0 * i / len(self.originalDB)))
            logging.info("wrote synthetic database to file {}, with {} transactions ({:0.1f}%)".format(self.GenDBfilePath, ntrans, 100.0 * ntrans / len(self.originalDB)))
        return len(self.GenDBfilePath)

    def loadIgmModelFromFile(self):
        self.igmModel = []
        with open(self.modelFileName) as inf:
            for line in inf:
                itemset = sorted([int(item.strip()) for item in line.strip().split(" ")])
                prob = float(inf.readline().strip())
                # print("itemset: ", itemset,  "freq: " , prob)
                self.igmModel.append((itemset, prob))
            logging.info("IGM model loaded from file {}".format(self.modelFileName))

    def saveIgmModeltoFile(self):
        with open(self.modelFileName, 'w') as modelFile:
            for (itemset, p) in self.igmModel:
                modelFile.write(" ".join(map(str, itemset)) + "\n")
                modelFile.write(str(p) + "\n")
            logging.info("wrote IGM model file to {}".format(self.modelFileName))

    @print_timing
    def getFI(self, minsup):
        """ runs eclat on input db. Prints the frequent itemsets on a file and returns them as well
            Input DB format: other vegetables,whole milk (7.48348)  Obs: Ensure not to use the nr of transaction but the ratio """
        outfname = os.path.join(os.getcwd(), "out", "eclat-igm-{}-{}.itemsets".format(self.origDBbaseName, minsup))
        if platform == "win32":
            eclatPath = os.path.join(os.getcwd(), "exe", "eclat.exe")
        elif platform == "linux" or platform == "linux2":
            eclatPath = os.path.join(os.getcwd(), "exe", "eclat")
        cmd = [eclatPath, '-f" "', "-s{}".format(minsup), "-k{}".format(" "), self.origDBfilePath, outfname]
        logging.info("running eclat command: {} over the original file : {}".format(" ".join(cmd), self.origDBfileName))
        call(cmd)
        logging.info("wrote frequent itemsets in file {}".format(outfname))
        fi = []
        with open(outfname) as fiFile:
            for line in fiFile:
                if len(line):
                    m = re.match(r'(.+)\(([\d\.]+)\)', line)
                    if m:
                        itemset = [int(item.strip()) for item in m.group(1).strip().split(" ")]
                        freq = float(m.group(2).strip())
                        # print("itemset: ", itemset , "freq: " , freq)
                        fi.append((itemset, freq))
            logging.info("frequent itemsets loaded from file {} total {}".format(outfname, len(fi)))
        return fi

    def filterFI(self, fi):
        interestingFI = []
        for (itemset, frequency) in fi:   # fi = [ ([2,5,8,3], 74.5), ... ]
            threshold = 100 * (1 / (2 ** len(itemset)))
            if frequency > threshold:
                interestingFI.append((itemset, frequency))
        return interestingFI

    def chooseItemset(self):
        freq = [p for (itemset, p) in self.igmModel]
        sumFreq = sum(freq)
        return np.random.choice(len(self.igmModel), p=[p / sumFreq for p in freq])

    def choosePattern(self, itemsetIndex):
        (itemset, p) = self.igmModel[itemsetIndex]
        subsets = []
        for i in range(1, len(itemset)):
            subsets.extend([list(comb) for comb in combinations(itemset, i)])
        uniformProb = (1 - (p / 100)) / (2 ** len(itemset) - 1)
        freqList = [p] + ([100 * uniformProb] * len(subsets))
        sumfreq = sum(freqList)
        print("pattern before subsets: ", subsets)
        subsets = [itemset] + subsets
        print("pattern after subsets: ", subsets)
        print("pattern freqList: ", freqList)
        return subsets[np.random.choice(len(subsets), p=[freq / sumfreq for freq in freqList])]
        # return np.random.choice(subsets, p=[freq / sumfreq for freq in freqList])

    def choosePattern(self, itemsetIndex):
        (itemset, p) = self.igmModel[itemsetIndex]
        if np.random.binomial(1, p):
            return itemset
	    else:
	        nr_subsets = 2 ** len(itemset) - 2 # not include itemset nor empty
	        chosen_index = np.random.choice(len(nr_subsets), 1) # consider discrete uniform distribution.
	        i = 1
	        sum = len(combinations(itemset, i))
	        while sum - 1 < chosen_index:
	        	i += 1
	        	sum += len(combinations(itemset, i))
	        subset_i = [list(comb) for comb in combinations(itemset, i)]
	        return subset_i[]

    def chooseNoise(self, itemsetIndex):
        (itemset, p) = self.igmModel[itemsetIndex]
        newAlphabet = set()
        for (auxitemset, _) in self.igmModel:
            newAlphabet |= set(auxitemset)
        # print("newAlphabet :", len(newAlphabet))
        noise = sorted(list(newAlphabet.difference(set(itemset))))
        subsets = []
        for i in range(1, len(noise)):
            subsets.extend([list(comb) for comb in combinations(noise, i)])
        uniformProb = 1 / (2 ** (len(newAlphabet) - len(itemset)))
        subsets = [noise] + subsets
        print("noise subsets: ", subsets)
        freqList = [100 * uniformProb] * len(subsets)
        print("noise freqList: ", freqList)
        sumfreq = sum(freqList)
        # return np.random.choice(subsets, p=[freq / sumfreq for freq in freqList])
        return subsets[np.random.choice(len(subsets), p=[freq / sumfreq for freq in freqList])]

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class LDALearnGen:
    """
    DB Generator module that uses Latent Dirichlet Allocation
    """

    def __init__(self, indb):
        self.origDBfileName = indb
        self.origDBbaseName = os.path.splitext(os.path.basename(indb))[0]
        self.origDBfilePath = os.path.join(os.getcwd(), "db", self.origDBfileName)  # Original DB file name e.g. chess.dat
        self.GenDBfilePath = os.path.join(os.getcwd(), "db", "gen-lda-{}-minsup-{}-passes{}".format(os.path.basename(self.origDBbaseName), args.lda_minsup, args.lda_passes))  # Newly generated DB file name.
        self.modelFilePath = None  # to be determined on learn execution, depends on parameters
        self.K = None
        self.npasses = None
        self.lda = None  # model parameters
        self.dictionary = None  # link between item descriptions and ids
        # parse input file, figure out various statistics from dbfile
        self.originalDB = []
        self.itemAlphabet = set()
        with open(self.origDBfilePath) as infile:
            for row in infile:
                transaction = [item.strip() for item in row.strip().split(" ")]
                self.itemAlphabet |= set(transaction)
                self.originalDB.append(sorted(transaction))
        logging.info("Nr of transactions in {}: {}, Nr. of items: {}".format(self.origDBfileName, len(self.originalDB),
                                                                    len(self.itemAlphabet)))

    @print_timing
    def learn(self, K, npasses):
        """
        learns lda model from input db (as list of lists -- i.e. transaction itemsets)
        parameters are
            K: nr of topics;
            npasses: nr of passes over db
        output model is saved to file for persistent storage
        """
        # record parameter settings
        self.K = K
        self.npasses = npasses
        # load db
        self.dictionary = corpora.Dictionary(self.originalDB)
        transaction_matrix = [self.dictionary.doc2bow(trans) for trans in self.originalDB]
        logging.info("Size of transaction matrix: {}".format(len(transaction_matrix)))
        self.modelFilePath = os.path.join(os.getcwd(), "models", "lda_model_{}_K{}_minsup{}_passes{}".format(self.origDBbaseName, K, args.lda_minsup, npasses))
        if os.path.exists(self.modelFilePath):
            self.load()
        else:
            logging.info("running LDA inference on corpus; K = {}, passes = {}".format(K, npasses))
            self.lda = gensim.models.ldamodel.LdaModel(transaction_matrix, num_topics=K, id2word=self.dictionary,
                                                       passes=int(npasses), alpha='auto')
            # save model to file for future reference
            self.save()
        for k in range(K):
            logging.debug(self.lda.print_topic(k))

    @print_timing
    def gen(self):
        """
        from learned model, generate synthetic database using probabilistic model
        returns new database file name
        """
        topics = self.lda.get_topics()
        genDB = []
        genDBsize = len(self.originalDB)  # use same size of original database
        for i in range(genDBsize):
            # use same length of transaction as original database
            transSize = len(self.originalDB[i])
            # use multinomial for transaction according to fitted lda model
            mixture = self.lda[self.dictionary.doc2bow(self.originalDB[i])]
            logging.debug("topic mixture for transaction {}: {}".format(i, mixture))
            # chose topics acording to multinomial mixture, for all words at once
            trans_topics = np.random.multinomial(transSize, [x for _, x in mixture])
            # now, generate words for each of the chosen topics
            this_transaction = set()
            for j, x in enumerate(trans_topics):
                if x:
                    items = np.random.multinomial(x, topics[j])
                    logging.debug("generated words: {}".format(items))
                    for l, w in enumerate(items):
                        if w:
                            # add word l w-times -- but since it is a set, we will loose words
                            # also, may chose a word already put into the transaction so adding
                            # it won't increase the current transaction
                            logging.debug(
                                "--adding word id {} which is {}, {} times".format(l, self.dictionary[l], w))
                            this_transaction.add(self.dictionary[l])
            # add created transaction to new db
            genDB.append(sorted(this_transaction))
            logging.debug(">>original transaction size {}, generated transaction size {}".format(transSize, len(
                this_transaction)))
            logging.debug(">>original transaction: {}, generated transaction: {}".format(sorted(self.originalDB[i]),
                                                                                         sorted(this_transaction)))
            # REPORT progress
            if i and i % 1000 == 0:
                logging.info(
                    "\tprocessed {} transactions of {} ({:0.1f}%).".format(i, genDBsize, 100.0 * i / genDBsize))
        # write result to file
        outf = open(self.GenDBfilePath, "w")
        for trans in genDB:
            newitems = " ".join(map(str, sorted(map(int, trans))))
            outf.write(newitems + "\n")
            logging.debug("writing transaction to new db: {}".format(newitems))
        outf.close()
        logging.info("wrote synthetic database to file {}".format(self.GenDBfilePath))
        return self.GenDBfilePath

    def load(self):
        self.lda = gensim.models.LdaModel.load(self.modelFilePath)
        logging.info("loaded persistent model from file {}".format(self.modelFilePath))

    def save(self):
        self.lda.save(self.modelFilePath)
        logging.info("saved model in file '{}'".format(self.modelFilePath))

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class IIMLearnGen:
    """
    DB Generator module that uses IIM Model of Fowkes & Sutton
    from paper "A Bayesian Network Model for Interesting Itemsets"
    """

    def __init__(self, indb):
        self.origDBfileName = indb
        self.origDBbaseName = os.path.splitext(os.path.basename(indb))[0]
        self.origDBfilePath = os.path.join(os.getcwd(), "db", self.origDBfileName)  # Original DB file name e.g. chess.dat
        self.GenDBfilePath = os.path.join(os.getcwd(), "db", "gen-iim-{}-passes-{}".format(os.path.basename(self.origDBbaseName), args.iim_passes))  # Newly generated DB file name.
        self.modelFilePath = None     # to be determined on learn execution, depends on parameters
        self.iimsModel = None
        self.originalDB = []
        self.itemAlphabet = set()
        with open(self.origDBfilePath) as inf:
            for row in inf:
                    transaction = sorted([int(item.strip()) for item in row.strip().split(" ")])
                    self.originalDB.append(transaction)
                    self.itemAlphabet |= set(transaction)
        logging.info("load input file {} ; {} transactions found with {} items".format(self.origDBfileName, len(self.originalDB), len(self.itemAlphabet)))

    @print_timing
    def learn(self, npasses):
        self.modelFilePath = os.path.join(os.getcwd(), "models", "iim-model-{}-passes-{}".format(self.origDBbaseName, npasses))
        if os.path.exists(self.modelFilePath):
            self.loadfromFile()
        else:
            logging.info("running IIM inference on corpus; passes = {}".format(npasses))
            # cmd = ["java", "-Xmx100g", "-cp", os.path.join(os.getcwd(), "exe", "itemset-mining-1.0.jar"), "itemsetmining.main.ItemsetMining", "-i", str(npasses), "-f", self.origDBfilePath, "-v"]
            cmd = ["java", "-cp", os.path.join(os.getcwd(), "exe", "itemset-mining-1.0.jar"), "itemsetmining.main.ItemsetMining", "-i", str(npasses), "-f", self.origDBfilePath, "-v"]
            fd, temp_path = tempfile.mkstemp()
            with open(temp_path, 'w') as tmpout:
                logging.info("running: {}".format(" ".join(cmd)))
                call(cmd, stdout=tmpout)
                logging.info("wrote iim output file {}".format(temp_path))
            # now, parse temp output file to retrieve iim model
            self.iimsModel = self.getiimsModel(temp_path)
            print("iim model size", len(self.iimsModel))
            # cleanup
            os.close(fd)
            os.remove(temp_path)
            # save state for future runs
            self.saveiimsModel()
        return len(self.iimsModel)

    @print_timing
    def gen(self):
        """
        from learned model, generate synthetic database using probabilistic model iim
        returns new database file name
        """
        with open(self.GenDBfilePath, 'w') as outf:
            ntrans = 0
            oriDBsize = len(self.originalDB)
            logging.info("total records for generating: {}".format(oriDBsize))
            for i in range(oriDBsize):
                newTrans = set()
                for (itemset, p) in self.iimsModel:
                    # bernoulli trial
                    if np.random.binomial(1, p):
                        logging.debug("===> adding itemset {} to current transaction {}".format(itemset, i))
                        newTrans |= set(itemset)
                genTrans = " ".join(map(str, sorted(newTrans)))
                if len(newTrans):
                    outf.write(genTrans + "\n")
                    logging.debug("writing transaction to new db: {}".format(genTrans))
                    ntrans += 1
                # REPORT progress
                if i and i % 1000 == 0:
                    logging.info("\tprocessed {} transactions of {} ({:0.1f}%).".format(i, oriDBsize, 100.0*i/oriDBsize))
        logging.info("wrote synthetic database to file {}, with {} transactions ({:0.1f}%)".format(self.GenDBfilePath, ntrans, 100.0*ntrans/oriDBsize))
        return self.GenDBfilePath

    def getiimsModel(self, fname):
        # syntax is:  '{2, 13}	prob: 0,17160 	int: 1,00000'
        # translate back to string as well
        pattern = re.compile(r'\{(.+)\}(\s+)prob: ([\d,.]+)(\s+)int')
        model = []
        with open(fname) as inf:
            logging.info("parsing iim output file {}".format(fname))
            for line in inf:
                m = re.match(pattern, line)
                if m:
                    itemset = sorted([int(item.strip()) for item in m.group(1).strip().split(",")])
                    prob = m.group(3).strip().replace(",", ".")
                    model.append((itemset, float(prob)))
                    logging.info("adding interesting itemset {}".format((itemset, prob)))
        return model

    def loadfromFile(self):
        self.iimsModel = []
        with open(self.modelFilePath) as inf:
            for line in inf:
                itemset = [int(item.strip()) for item in line.strip().split(" ")]
                prob = float(inf.readline().strip())
                self.iimsModel.append((itemset, prob))
        logging.info("loaded IIM model from file {}".format(self.modelFilePath))

    def saveiimsModel(self):
        """ saves state to model file """
        with open(self.modelFilePath, 'w') as outf:
            for (itemset, p) in self.iimsModel:
                outf.write(" ".join(map(str,itemset)) + "\n")
                outf.write(str(p) + "\n")
        logging.info("wrote IIM model file to {}".format(self.modelFilePath))

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':

    # arguments setup
    os.chdir("/lustre_rdlabfs/CLUSTER/usuaris/clezcano/03sept2018LastCode/Database-Generation-for-Itemset-Mining/dbgenmodels/dbgen/")

    parser = argparse.ArgumentParser()
    parser.add_argument('--logfile', default=None, help='Log file')
    parser.add_argument('--dbfile', default='dataset377.dat', help='Input database (only format accepted .dat)')

    parser.add_argument('--lda_minsup', default=60, help='Nr of passes over input data for lda parameter estimation')
    parser.add_argument('--lda_passes', default=200, help='Nr of passes over input data for lda parameter estimation')

    parser.add_argument('--iim_passes', default=500, help='Nr of iterations over input data for iim parameter estimation')

    parser.add_argument('--igm_minsup', default=50, help='positive: percentage of transactions, negative: exact number of transactions e.g. 50 or -50')

    parser.add_argument('--krimp_minsup', default=2397, help='<integer>--Absolute minsup (e.g. 10, 42, 512)')
    parser.add_argument('--krimp_type', default='all', help='Candidate type determined by [ all | cls | closed ]')
    parser.add_argument('--krimp_CTfilename', default=None, help='CT name file')

    # parser.add_argument('--minsup', default=75, help='Minimum support threshold')

    args = parser.parse_args()
    args.dbname = os.path.basename(args.dbfile)
    # logging setup
    if args.logfile:
        logging.basicConfig(filename=args.logfile, format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    else:
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    # for reproducibility
    np.random.seed(50)

    # first, run eclat on original file to do comparisons

    # K = eclatLDA(args.dbfile, args.lda_minsup)
    # logging.info("Nr of frequent itemsets found is: '{}' (future K for lda generator)".format(K))
    # # now, run first generator model (lda) and then eclat on synthetic db
    # lda = LDALearnGen(args.dbfile)
    # lda.learn(K, args.lda_passes)
    # lda.gen()

    # eclatLDA(lda.newdbfile)
    # -------------------------------------------------------------
    # run iim generator model (iim)

    # iim = IIMLearnGen(args.dbfile)
    # iim.learn(args.iim_passes)
    # iim.gen()

    # eclatLDA(iim.GenDBfilePath, args.minsup)
    # -------------------------------------------------------------
    # IGM generator model (igm)

    igm = IGMGen(args.dbfile)
    igm.learn(args.igm_minsup)
    igm.gen()

    # eclatLDA(igm.GenDBfilePath, args.igm_minsup)
    # -------------------------------------------------------------
    # Krimp generator model (krimp)
    # krimp = KrimpGen(args.dbfile)
    # krimp.getCT()
    # krimp.learn(args.krimp_minsup)
    # krimp.gen()
    # eclatLDA(krimp.GenDBfilePath, args.krimp_minsup)