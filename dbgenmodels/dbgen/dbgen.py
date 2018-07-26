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
import argparse
import numpy as np
import logging
from subprocess import call
import re
import os
import gensim
from gensim import corpora
import time
import tempfile
import fileinput
from itertools import combinations

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
def eclat(infname, minsup):
    """
    runs eclat on input db
    returns nr of frequent itemsets found and save them on file.
    """
    bname = os.path.splitext(os.path.basename(infname))[0]
    infnamePath = os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "db", infname)
    outfnamePath = os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "out", "eclat-{}-{}.itemsets".format(bname, minsup))
    cmd = [os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "exe", "eclat.exe"), '-f" "', "-s{}".format(minsup), '-k" "', "-Z", infnamePath, outfnamePath]  # -Z prints number of items per size

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
        if m:
            nfreqitemsets = int(m.group(1))

    os.close(fd)
    os.remove(temp_path)

    return nfreqitemsets

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class IIMLearnGen:
    """
    DB Generator module that uses IIM Model of Fowkes & Sutton
    from paper "A Bayesian Network Model for Interesting Itemsets"
    """

    def __init__(self, indb):
        self.origDBfileName = indb
        self.origDBfilePath = os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "db", self.origDBfileName)  # Original DB file name e.g. chess.dat
        self.GenDBfilePath = os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "db", "gen-iim-{}".format(os.path.basename(self.origDBfileName)))  # Newly generated DB file name.
        self.modelFileName = None     # to be determined on learn execution, depends on parameters
        self.iims = None
        self.wordtoid = dict()
        self.idtoword = dict()
        # translate to FIMI
        self.fimifile = "db/iim-" + os.path.splitext(os.path.basename(indb))[0] + ".fimi"
        self.m = 0    # nr of transactions in original db

    def getFimiFile(self):
        with open(self.fimifile, 'w') as outf:
            nextid = 1
            with open(args.origDBfilePath) as inf:
                for row in inf:
                    transaction = [item.strip().replace(" ", "_") for item in row.strip().split(',')]
                    for item in transaction:
                        if item not in self.wordtoid:
                            self.wordtoid[item] = nextid
                            self.idtoword[nextid] = item
                            nextid += 1
                    # write transaction to fimi file
                    fimi_transaction = sorted([self.wordtoid[item] for item in transaction])
                    logging.debug("translating transaction {} to FIMI format as {}".format(transaction, fimi_transaction))
                    outf.write(" ".join([str(x) for x in fimi_transaction]) + "\n")
                    self.m += 1
        logging.info("translated input file {} to fimi format in {}; {} transactions found with {} items".format(self.origDBfileName, self.fimifile, self.m, len(self.wordtoid)))

    @print_timing
    def learn(self, npasses):
        self.modelFileName = os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "models", "iim-model-{}-passes{}".format(self.origDBfileName, npasses))
        if os.path.exists(self.modelFileName):
            self.load()
        else:
            logging.info("running IIM inference on corpus; passes = {}".format(npasses))
            cmd = ["java", "-cp", os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "exe", "itemset-mining-1.0.jar"), "itemsetmining.main.ItemsetMining", "-i", str(npasses), "-f", self.fimifile, "-v"]
            fd, temp_path = tempfile.mkstemp()
            with open(temp_path, 'w') as tmpout:
                logging.info("running: {}".format(" ".join(cmd)))
                call(cmd, stdout=tmpout)
                logging.info("wrote iim output file {}".format(temp_path))
            # now, parse temp output file to retrieve iim model
            self.iims = parse_iim_output(temp_path, self.idtoword)
            # cleanup
            os.close(fd)
            os.remove(temp_path)
            # save state for future runs
            self.save()
        return len(self.iims)

    @print_timing
    def gen(self):
        """
        from learned model, generate synthetic database using probabilistic model iim
        returns new database file name
        """
        with open(self.GenDBfilePath, 'w') as outf:
            ntrans = 0
            for i in range(self.m):
                newtrans = set()
                for (items, p) in self.iims:
                    # bernoulli trial
                    if np.random.binomial(1, p):
                        logging.debug("===> adding iim {} to current transaction {}".format(items, i))
                        newtrans |= set(items)
                newitems = ",".join(sorted(newtrans))
                if len(newtrans):
                    outf.write(newitems + "\n")
                    logging.debug("writing transaction to new db: {}".format(newitems))
                    ntrans += 1
                # REPORT progress
                if i and i % 1000 == 0:
                    logging.info("\tprocessed {} transactions of {} ({:0.1f}%).".format(i, self.m, 100.0*i/self.m))
        logging.info("wrote synthetic database to file {}, with {} transactions ({:0.1f}%)".format(self.GenDBfilePath, ntrans, 100.0*ntrans/self.m))
        return self.GenDBfilePath

    def load(self):
        self.iims = []
        with open(self.modelFileName) as inf:
            for line in inf:
                itemset = line.strip().split(" ")
                prob = float(inf.readline().strip())
                self.iims.append((itemset, prob))
        logging.info("loaded IIM model from file {}".format(self.modelFileName))

    def save(self):
        """ saves state to model file """
        with open(self.modelFileName, 'w') as outf:
            for (itemset, p) in self.iims:
                outf.write(" ".join(itemset) + "\n")
                outf.write(str(p) + "\n")
        logging.info("wrote IIM model file to {}".format(self.modelFileName))

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class LDALearnGen:
    """
    DB Generator module that uses Latent Dirichlet Allocation
    """

    def __init__(self, indb):
        self.dbfile = indb
        self.newdbfile = "db/lda-" + os.path.basename(indb)
        self.modelfname = None     # to be determined on learn execution, depends on parameters
        self.K = None
        self.npasses = None
        self.lda = None             # model parameters
        self.dictionary = None      # link between item descriptions and ids
        # parse input file, figure out various statistics from dbfile
        self.db = []
        items = set()
        with open(args.dbfile) as infile:
            for row in infile:
                transaction = [item.strip().replace(" ", "_") for item in row.strip().split(',')]
                items |= set(transaction)
                self.db.append(sorted(transaction))

        logging.info("Nr of transactions in {}: {}, Nr. of items: {}".format(args.dbfile, len(self.db), len(items)))

    def load(self):
        self.lda = gensim.models.LdaModel.load(self.modelfname)
        logging.info("loaded persistent model from file {}".format(self.modelfname))

    def save(self):
        self.lda.save(self.modelfname)
        logging.info("saved model in file '{}'".format(self.modelfname))

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
        self.dictionary = corpora.Dictionary(self.db)
        transaction_matrix = [self.dictionary.doc2bow(trans) for trans in self.db]

        logging.info("Size of transaction matrix: {}".format(len(transaction_matrix)))

        self.modelfname = "models/ldamodel_K{}_passes{}".format(K, npasses)
        if os.path.exists(self.modelfname):
            self.load()
        else:
            logging.info("running LDA inference on corpus; K = {}, passes = {}".format(K, npasses))
            self.lda = gensim.models.ldamodel.LdaModel(transaction_matrix, num_topics=K, id2word = self.dictionary, passes=int(npasses), alpha = 'auto')
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

        newdb = []
        m = len(self.db)    # use same size of original database
        for i in range(m):
            # use same length of transaction as original database
            n = len(self.db[i])
            # use multinomial for transaction according to fitted lda model
            mixture = self.lda[self.dictionary.doc2bow(self.db[i])]
            logging.debug("topic mixture for transaction {}: {}".format(i, mixture))
            # chose topics accoring to multinomial mixture, for all words at once
            trans_topics = np.random.multinomial(n, [x for _, x in mixture])
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
                            logging.debug("--adding word id {} which is {}, {} times".format(l, self.dictionary[l], w))
                            this_transaction.add(self.dictionary[l])
            # add created transaction to new db
            newdb.append(sorted(this_transaction))
            logging.debug(">>original transaction size {}, generated transaction size {}".format(n, len(this_transaction)))
            logging.debug(">>original transaction: {}, generated transaction: {}".format(sorted(self.db[i]), sorted(this_transaction)))
            # REPORT progress
            if i and i % 1000 == 0:
                logging.info("\tprocessed {} transactions of {} ({:0.1f}%).".format(i, m, 100.0*i/m))

        # write result to file
        outf = open(self.newdbfile, "w")
        for trans in newdb:
            newitems = ",".join(sorted(trans))
            outf.write(newitems + "\n")
            logging.debug("writing transaction to new db: {}".format(newitems))
        outf.close()
        logging.info("wrote synthetic database to file {}".format(self.newdbfile))

        return self.newdbfile

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class IGMGen:
    """
       This DB Generator (IGM) is based on the model described in the paper
       "Connection between mining frequent itemsets and learning generative models" by Laxman et.al.
    """

    def __init__(self, indb):
        self.origDBfileName = indb
        self.origDBfilePath = os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "db", indb)  # Original DB file name e.g. chess.dat
        self.GenDBfilePath = os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "db", "gen-igm-" + indb)  # Newly generated DB file name.
        self.modelFileName = None  # to be determined on learn execution, depends on parameters. Same as igm class variable but this one is saved in file.
        self.originalDB = []  #  this one saves the original DB.         #  parse input file, figure out various statistics from dbfile
        self.igmModel = None  # model parameters [(itemset, prob),...]
        self.itemAlphabet = set()  # This is used to know the number of different items in original DB. It saves the item's alphabet.
        with open(self.origDBfilePath) as infile:
            for row in infile:
                transaction = [item.strip() for item in row.strip().split(" ")]  # transaction = [item.strip().replace(" ", "_") for item in row.strip().split(',')]
                self.itemAlphabet |= set(transaction)
                self.originalDB.append(sorted(transaction))
            logging.info("Nr of transactions in {}: {}, Nr. of items: {}".format(self.origDBfileName, len(self.originalDB), len(self.itemAlphabet)))

    def loadIgmModelFromFile(self):
        self.igmModel = []
        with open(self.modelFileName) as inf:
            for line in inf:
                itemset = line.strip().split(" ")
                prob = float(inf.readline().strip())
                self.igmModel.append((itemset, prob))
            logging.info("IGM model loaded from file {}".format(self.modelFileName))

    def saveIgmModeltoFile(self):
        with open(self.modelFileName, 'w') as modelFile:
            for (itemset, p) in self.igmModel:
                modelFile.write(",".join(itemset) + "\n")
                modelFile.write(str(p) + "\n")
            logging.info("wrote IGM model file to {}".format(self.modelFileName))

    @print_timing
    def getFI(self, minsup):
        """ runs eclat on input db. Prints the frequent itemsets on a file and returns them as well
            Input DB format: other vegetables,whole milk (7.48348)  Obs: Ensure not to use the nr of transaction but the ratio """
        bname = os.path.splitext(os.path.basename(self.origDBfilePath))[0]  # returns groceries from groceries.dat
        outfname = os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "out", "eclat-igm-{}{}.itemsets".format(minsup, bname))
        eclatPath = os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "exe", "eclat.exe")
        cmd = [eclatPath, '-f" "', "-s{}".format(minsup), "-k,", self.origDBfilePath, outfname]
        logging.info("running eclat command: {} over the original file : {}".format(" ".join(cmd), self.origDBfileName))
        call(cmd)
        logging.info("wrote frequent itemsets in file {}".format(outfname))
        fi = []
        with open(outfname) as fiFile:
            for line in fiFile:
                if len(line):
                    m = re.match(r'(.+)\(([\d\.]+)\)', line)
                    if m:
                        itemset = [item.strip() for item in m.group(1).strip().split(',')]
                        freq = float(m.group(2).strip())
                        fi.append((itemset, freq))
            logging.info("frequent itemsets loaded from file {}".format(outfname))
        return fi

    def filterFI(self, fi):
        interestingFI = []
        for (itemset, frequency) in fi:   # fi = [ ([2,5,8,3], 74), ... ]
            threshold = 100 * (1 / (2 ** len(itemset)))
            if frequency > threshold:
                interestingFI.append((itemset, frequency))
        return interestingFI

    def chooseItemset(self):
        freq = [p for (itemset, p) in self.igmModel]
        sumFreq = sum(freq)
        return np.random.choice(len(freq), [p / sumFreq for p in freq])

    def choosePattern(self, itemsetIndex):
        (itemset, p) = self.igmModel[itemsetIndex]
        subsets = []
        for i in range(1, len(itemset)):
            subsets.extend([list(comb) for comb in combinations(itemset, i)])
        uniformProb = (1 - (p / 100)) / (2 ** len(itemset) - 1)
        freqList = [p] + [100 * uniformProb] * len(subsets)
        sumfreq = sum(freqList)
        subsets = [itemset] + subsets
        return np.random.choice(subsets, [freq / sumfreq for freq in freqList])

    def chooseNoise(self, itemsetIndex):
        (itemset, p) = self.igmModel[itemsetIndex]
        noise = list(self.itemAlphabet.difference(set(itemset)))
        subsets = []
        for i in range(1, len(noise)):
            subsets.extend([list(comb) for comb in combinations(noise, i)])
        uniformProb = 1 / (2 ** (len(self.itemAlphabet) - len(itemset)))
        subsets = [noise] + subsets
        freqList = [100 * uniformProb] * len(subsets)
        sumfreq = sum(freqList)
        return np.random.choice(subsets, [freq / sumfreq for freq in freqList])

    @print_timing
    def learn(self, minsup):
        self.modelFileName = os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "models", "igm-model-{}{}".format(self.origDBfileName, args.igm_minsup))
        if os.path.exists(self.modelFileName):
            self.loadIgmModelFromFile()
        else:
            logging.info("running IGM inference; minsup = {} on file: {}".format(args.igm_minsup, self.origDBfileName))
            fi = self.getFI(args.igm_minsup)  # get the frequent itemsets of the original DB. (e.g. using eclat) Format: [(itemset, prob),...]
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
                pattern = self.choosePattern(itemsetIndex)
                noise = self.chooseNoise(itemsetIndex)
                newTransaction = pattern + noise   # both parameters should be sets.
                newTrans = " ".join(sorted(newTransaction))
                (itemset, p) = self.igmModel[itemsetIndex]
                logging.debug("===> generating transaction nr: {}; freq. itemset selected: {}; pattern selected: {}; noise pattern selected: {}".format(i, itemset, pattern, noise))
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

class KrimpGen:
    def __init__(self, indb):
        # Item data -> Categorical data -> Krimp format -> Categorical data -> Item data.
        self.origDBfileName = indb  # Original DB file name e.g. chess.dat
        self.origDBfilePath = os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "KrimpBinSource", "data", "dataset", self.origDBfileName)  # Original DB file name e.g. chess.dat
        self.CategDBfilePath = os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "KrimpBinSource", "data", "dataset", "krimp-categ-" + self.origDBfileName)  # Categorical DB file name which feed.
        self.GenDBfilePath = os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "KrimpBinSource", "xps", "compress", "krimp-out-" + self.origDBfileName)  # Newly generated DB file name.
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
                transaction = [int(item.strip()) for item in row.strip().split(" ")]  # [bottled_water cling_film/bags cream_cheese tropical_fruit]
                self.items |= set(transaction)
                self.originalDB.append(sorted(transaction))
            logging.info("Nr of transactions in {}: {}, Nr. of items: {}".format(args.originalDBfile, len(self.originalDB), len(self.items)))
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
        auxTrans = [self.itemToDomain[item][1] for item in self.itemAlphabet]  # This line empties the array by assigning each element the "not exist" value
        for origTrans in self.originalDB:
            catTrans = auxTrans[:]
            for item in origTrans:
                catTrans[catTrans.index(self.itemToDomain[item][1])] = self.itemToDomain[item][0]
            self.categoricalDB.append(catTrans)
        self.saveCategDBtoFile()

    def saveCategDBtoFile(self):
        with open(self.CategDBfilePath, 'w') as categFile:
            for trans in self.categoricalDB:
                categFile.write(" ".join(trans) + "\n")
            logging.info("wrote categorical DB file to {}".format(self.CategDBfilePath))

    @print_timing
    def getCT(self):  # Categorical data -> Krimp format -> Categorical data.
        self.datadirConf()
        self.convertdbConf()
        self.toKrimpFormat()
        self.compressConf()

    def datadirConf(self):  # file setup: datadir.conf
        for line in fileinput.input(os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "KrimpBinSource", "bin", "datadir.conf"), inplace=1):
            if "dataDir =" in line:
                line = "dataDir = " + os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "KrimpBinSource", "data").replace('\\', '/') + '/'
            elif "expDir =" in line:
                line = "expDir = " + os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "KrimpBinSource", "xps").replace('\\', '/') + '/'
            print(line.rstrip('\n'))

    def convertdbConf(self):  # set up file: convertdb.conf
        logging.info("convert categorical DB to Krimp DB; categorical DB name = {}".format(os.path.basename(self.CategDBfilePath)))
        bname = os.path.splitext(os.path.basename(self.CategDBfilePath))[0]
        for line in fileinput.input(os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "KrimpBinSource", "bin", "convertdb.conf"), inplace=1):
            if "dbName =" in line:
                line = "dbName = " + bname
            print(line.rstrip('\n'))
        cmd = [os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "KrimpBinSource", "bin", "krimp.exe"), "convertdb.conf"]
        call(cmd)
        logging.info("categ. DB converted to krimp format in file: {}".format(bname + ".db"))

    def toKrimpFormat(self):
        krimpfileBaseName = os.path.splitext(os.path.basename(self.CategDBfilePath))[0] + ".db"
        krimpDBfileName = os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "KrimpBinSource", "data", "dataset", krimpfileBaseName)
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
        bname = os.path.splitext(os.path.basename(self.CategDBfilePath))[0]
        logging.info("Krimp compression ; Krimp format DB name = {}.db".format(bname))
        for line in fileinput.input(os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "KrimpBinSource", "bin", "compress.conf"), inplace=1):
            if line.startswith("iscName ="):
                line = "iscName = " + bname + "-" + args.krimp_type + "-" + args.krimp_minsup + "d"
            elif line.startswith("dataType ="):
                line = "dataType = bai32"
            print(line.rstrip('\n'))
        cmd = [os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "KrimpBinSource", "bin", "krimp.exe"), "compress.conf"]
        call(cmd)
        logging.info("Krimp inference; minsup = {}".format(args.krimp_minsup))

    @print_timing
    def learn(self, minsup):
        self.modelFileName = os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "models", "krimp-model-{}{}".format(self.origDBfileName, minsup))
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
                modelFile.write(" ".join(itemset) + "\n")
                modelFile.write(str(p) + "\n")
            logging.info("wrote Krimp model file to {}".format(self.modelFileName))

    def getKrimpModel(self):
        # syntax is:  '0 1 2 3 4 5 6 7 9 11 (2573,2573)'
        auxModelFileName = os.path.join(os.getcwd(), "dbgenmodels", "dbgen", "KrimpBinSource", "xps", "compress", args.krimp_CTfilename)
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
        return np.random.choice(itemsets, [p / sumFreq for p in freq])

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

if __name__ == '__main__':

    # arguments setup
    parser = argparse.ArgumentParser()
    parser.add_argument('--logfile', default=None, help='Log file')
    parser.add_argument('--dbfile', default='chess.dat', help='Input database (only format accepted .dat)')
    # parser.add_argument('--minsup', default=75, help='Minimum support threshold')
    parser.add_argument('--lda_passes', default=200, help='Nr of passes over input data for lda parameter estimation')
    parser.add_argument('--iim_passes', default=500, help='Nr of iterations over input data for iim parameter estimation')
    parser.add_argument('--igm_minsup', default=75, help='positive: percentage of transactions, negative: exact number of transactions e.g. 50 or -50')
    parser.add_argument('--krimp_minsup', default=None, help='<integer>--Absolute minsup (e.g. 10, 42, 512), <float>-- Relative minsup (e.g. 0.1 would be 10% of database size)')
    parser.add_argument('--krimp_type', default=all, help='Candidate type determined by [ all | cls | closed ]')
    parser.add_argument('--krimp_CTfilename', default=None, help='CT name file')

    args = parser.parse_args()
    args.dbname = os.path.basename(args.dbfile)
    # logging setup
    if args.logfile:
        logging.basicConfig(filename=args.logfile, format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    else:
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    # for reproducibility
    np.random.seed(43)

    # IGM generator model (igm)
    # REMEMBER TO CONSIDER ECLAT INPUT DB DELIMITER
    # igm = IGMGen(args.dbfile)
    # igm.learn(args.igm_minsup)
    # igm.gen()
    # eclat(igm.GenDBfilePath, args.igm_minsup)

    # Krimp generator model (krimp)
    krimp = KrimpGen(args.dbfile)
    krimp.getCT()
    krimp.learn(args.krimp_minsup)
    krimp.gen()
    eclat(krimp.GenDBfilePath, args.krimp_minsup)

    # first, run eclat on original file to do comparisons
    # K = eclat(args.dbfile)
    # logging.info("Nr of frequent itemsets found is: '{}' (future K for lda generator)".format(K))
    # now, run first generator model (lda) and then eclat on synthetic db
    # lda = LDALearnGen(args.dbfile)
    # lda.learn(K, args.lda_passes)
    # lda.gen()
    # eclat(lda.newdbfile)

    # # run iim generator model (iim)
    # iim = IIMLearnGen(args.dbfile)
    # iim.learn(args.iim_passes)
    # iim.gen()
    # eclat(iim.GenDBfilePath)


