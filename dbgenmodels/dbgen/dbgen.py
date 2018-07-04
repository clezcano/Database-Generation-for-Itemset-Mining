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
import re, os
import gensim
from gensim import corpora
import time
import tempfile
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
def eclat(infname):
    """
    runs eclat on input db
    returns nr of frequent itemsets found and save them on file.
    """
    bname = os.path.splitext(os.path.basename(infname))[0]
    outfname = "out/eclat-{}.itemsets".format(bname)
    cmd = ["exe/eclat", "-f,", "-s{}".format(args.minsup), "-k,", "-Z", infname, outfname] # -Z prints number of items per size

    fd, temp_path = tempfile.mkstemp()
    with open(temp_path, 'w') as tmpout:
        logging.info("running: {}".format(" ".join(cmd)))
        call(cmd, stdout=tmpout)
        logging.info("wrote frequent itemset file {}".format(outfname))

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


class IIMLearnGen:
    """
    DB Generator module that uses IIM Model of Fowkes & Sutton
    from paper "A Bayesian Network Model for Interesting Itemsets"
    """

    def __init__(self, indb):
        self.dbfile = indb
        self.newdbfile = "db/iim-" + os.path.basename(indb)
        self.modelfname = None     # to be determined on learn execution, depends on parameters
        self.iims = None
        self.wordtoid = dict()
        self.idtoword = dict()
        # translate to FIMI
        self.fimifile = "db/iim-" + os.path.splitext(os.path.basename(indb))[0] + ".fimi"
        self.m = 0    # nr of transactions in original db

        with open(self.fimifile, 'w') as outf:
            nextid = 1
            with open(args.dbfile) as inf:
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

        logging.info("translated input file {} to fimi format in {}; {} transactions found with {} items".format(self.dbfile, self.fimifile, self.m, len(self.wordtoid)))

    def load(self):
        self.iims = []
        with open(self.modelfname) as inf:
            for line in inf:
                itemset = line.strip().split(",")
                prob = float(inf.readline().strip())
                self.iims.append((itemset, prob))
        logging.info("loaded IIM model from file {}".format(self.modelfname))


    def save(self):
        """ saves state to model file """
        with open(self.modelfname, 'w') as outf:
            for (itemset, p) in self.iims:
                outf.write(",".join(itemset) + "\n")
                outf.write(str(p) + "\n")
        logging.info("wrote IIM model file to {}".format(self.modelfname))

    @print_timing
    def learn(self, npasses):
        self.modelfname = "models/iimmodel_passes{}".format(npasses)
        if os.path.exists(self.modelfname):
            self.load()
        else:
            logging.info("running IIM inference on corpus; passes = {}".format(npasses))

            cmd = ["java", "-cp", "exe/itemset-mining-1.0.jar", "itemsetmining.main.ItemsetMining", "-i", str(npasses), "-f", self.fimifile, "-v"]

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
        with open(self.newdbfile, 'w') as outf:
            ntrans = 0
            for i in range(self.m):
                newtrans = []
                for (items, p) in self.iims:
                    # bernoulli trial
                    if np.random.binomial(1, p):
                        logging.debug("===> adding iim {} to current transaction {}".format(items, i))
                        newtrans += items
                newitems = ",".join(sorted(newtrans))
                if len(newtrans):
                    outf.write(newitems + "\n")
                    logging.debug("writing transaction to new db: {}".format(newitems))
                    ntrans += 1
                # REPORT progress
                if i and i % 1000 == 0:
                    logging.info("\tprocessed {} transactions of {} ({:0.1f}%).".format(i, self.m, 100.0*i/self.m))

        logging.info("wrote synthetic database to file {}, with {} transactions ({:0.1f}%)".format(self.newdbfile, ntrans, 100.0*ntrans/self.m))

        return self.newdbfile


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
                    for l,w in enumerate(items):
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

class IGMGen:
    """
       This DB Generator (IGM) is based on the model described in the paper
       "Connection between mining frequent itemsets and learning generative models" by Laxman et.al.
    """

    def __init__(self, indb):
        self.originalDBfile = indb # Original DB file name
        self.originalDB = []  # this one saves the original DB.         # parse input file, figure out various statistics from dbfile
        self.modelFileName = None     # to be determined on learn execution, depends on parameters. Same as igm class variable but this one is saved in file.
        self.igmModel = None             # model parameters [(itemset, prob),...]
        self.GeneratedDBfile = "db/igm-" + os.path.basename(indb)  # Newly generated DB file name.
        self.items = set() # This is used to know the number of different items in original DB.
        with open(args.originalDBfile) as infile:
            for row in infile:
                transaction = [item.strip().replace(" ", "_") for item in row.strip().split(',')]
                self.items |= set(transaction)
                self.originalDB.append(sorted(transaction))
            logging.info("Nr of transactions in {}: {}, Nr. of items: {}".format(args.originalDBfile, len(self.originalDB), len(self.items)))

    def loadIgmModelFromFile(self):
        self.igmModel = []
        with open(self.modelFileName) as inf:
            for line in inf:
                itemset = line.strip().split(",")
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
        bname = os.path.splitext(os.path.basename(self.originalDBfile))[0]
        outfname = "out/eclat-igm-{}.itemsets".format(bname)
        cmd = ["exe/eclat", "-f,", "-s{}".format(minsup), "-k,", self.originalDBfile, outfname]
        logging.info("running eclat command: {} over the original file".format(" ".join(cmd), self.originalDBfile))
        call(cmd)
        logging.info("wrote frequent itemsets in file {}".format(outfname))
        fi = []
        with open(outfname) as fiFile:
            for line in fiFile:
                if len(line):
                    m = re.match(r'(.+)\(([\d\.]+)\)', line)
                    if m:
                        itemset = [item.strip().replace(" ", "_") for item in m.group(1).strip().split(',')]
                        freq = float(m.group(2).strip())
                        fi.append((itemset, freq))
            logging.info("frequent itemsets loaded from file {}".format(outfname))
        return fi

    def filterFI(self, fi):
        interestingFI = []
        for (itemset, frequency) in fi:
            threshold = 100 * (1 / (2 ** len(itemset)))
            if frequency > threshold:
                interestingFI.append((itemset, frequency))
        return interestingFI

    @print_timing
    def learn(self, minsup):
        self.modelFileName = "models/igmmodel_minsup{}".format(minsup)
        if os.path.exists(self.modelFileName):
            self.loadIgmModelFromFile()
        else:
            logging.info("running IGM inference; minsup = {}".format(minsup))
            fi = self.getFI(minsup)  # get the frequent itemsets of the original DB. (e.g. using eclat) Format: [(itemset, prob),...]
            self.igmModel = self.filterFI(fi) # Select the set of interesting itemsets following the concept proposed by Laxman et.al.
            self.saveIgmModeltoFile()
        return len(self.igmModel)

    def chooseItemset(self):
        # remember to return a list or set
        freq = [p for (itemset, p) in self.igmModel]
        sumFreq = sum(freq)
        itemsetIndex = list(np.random.multinomial(1, [p / sumFreq for p in freq])).index(1)
        return itemsetIndex

    def choosePattern(self, patternIndex):
        (itemset, p) = self.igmModel[patternIndex]
        subsets = []
        for i in range(1, len(itemset)):
            subsets.extend([list(comb) for comb in combinations(itemset, i)])
        uniformProb = (1 - (p / 100)) / (2 ** len(itemset) - 1)
        freqList = [p] + [100 * uniformProb] * len(subsets)
        sumfreq = sum(freqList)
        subsets = [itemset] + subsets
        patternIndex = list(np.random.multinomial(1, [freq / sumfreq for freq in freqList])).index(1)
        # remember to return a set
        return subsets[patternIndex]

    def chooseNoise(self, pattern):
        noise = list(self.items.difference(set(pattern)))
        subsets = []
        for i in range(1, len(noise)):
            subsets.extend([list(comb) for comb in combinations(noise, i)])
        uniformProb = 1 / (2 ** (len(self.items) - len(pattern)))
        subsets = [noise] + subsets
        freqList = [100 * uniformProb] * len(subsets)
        sumfreq = sum(freqList)
        noiseIndex = list(np.random.multinomial(1, [freq / sumfreq for freq in freqList])).index(1)
        # remember to return a list or set
        return subsets[noiseIndex]

    @print_timing
    def gen(self):
        with open(self.GeneratedDBfile, 'w') as genFile:
            ntrans = 0
            for i in range(len(self.originalDB)):
                newTransaction = []
                itemsetIndex = self.chooseItemset()
                pattern = self.choosePattern(itemsetIndex)
                noise = self.chooseNoise(pattern)
                newTransaction = set(pattern).union(set(noise))   # both parameters should be sets.
                newTrans = ",".join(sorted(newTransaction))
                # (itemset, p) = self.igmModel[itemsetIndex]
                logging.debug("===> generating transaction nr: {}; freq. itemset selected: {}; pattern selected: {}; noise pattern selected: {}".format(i, itemset, pattern, noise))
                if len(newTrans):
                    genFile.write(newTrans + "\n")
                    logging.debug("writing transaction to new db: {}".format(newTrans))
                    ntrans += 1
                # REPORT progress
                if i and i % 1000 == 0:
                    logging.info("\tprocessed {} transactions of {} ({:0.1f}%).".format(i, len(self.originalDB), 100.0 * i / len(self.originalDB)))
            logging.info("wrote synthetic database to file {}, with {} transactions ({:0.1f}%)".format(self.GeneratedDBfile, ntrans, 100.0 * ntrans / len(self.originalDB)))
        return len(self.GeneratedDBfile)


class KrimpGen:
    """
       This DB Generator (IGM) is based on the model described in the paper
       "Connection between mining frequent itemsets and learning generative models" by Laxman et.al.
    """

    def __init__(self, indb):
        self.originalDBfile = indb # Original DB file name
        self.originalDB = []  # this one saves the original DB.         # parse input file, figure out various statistics from dbfile
        self.categoricalDB = []  # input DB formatted as a categorical DB.
        self.modelFileName = None     # to be determined on learn execution, depends on parameters. Same as igm class variable but this one is saved in file.
        self.krimpModel = None        # Krimp Code Table (CT)     # model  [(itemset, frequency),...] # frequency is over the cover and not over the original DB
        self.GeneratedDBfile = "db/krimp-" + os.path.basename(indb)  # Newly generated DB file name.
        self.items = set() # This is used to know the number of different items in original DB.
        self.itemAlphabet = [] # Original DB alphabet
        self.itemToDomain = dict() # map an item to its domain.
        self.domainToItem = dict()  # map any element of a domain to its item.
        with open(args.originalDBfile) as infile:
            for row in infile:
                transaction = [item.strip().replace(" ", "_") for item in row.strip().split(',')] # [bottled_water cling_film/bags cream_cheese tropical_fruit]
                self.items |= set(transaction)
                self.originalDB.append(sorted(transaction))
            logging.info("Nr of transactions in {}: {}, Nr. of items: {}".format(args.originalDBfile, len(self.originalDB), len(self.items)))
        self.mapToCategoricalDB()
        self.toCategoricalDB()

    def mapToCategoricalDB(self):
        self.itemAlphabet = list(self.items)
        counter = 0
        for item in self.itemAlphabet:
            self.itemToDomain[item] = [counter, counter + 1]  #  [exist, not exist] or [purchased item, not purchased item]
            self.domainToItem[counter] = item
            self.domainToItem[counter + 1] = item
            counter = counter + 2

    def toCategoricalDB(self):
        auxTrans =  [self.itemToDomain[item][1] for item in self.itemAlphabet] # This line empties the array by assigning each element the "not exist" value
        for origTrans in self.originalDB:
            catTrans = auxTrans[:]
            for item in origTrans:
                catTrans[catTrans.index(self.itemToDomain[item][1])] = self.itemToDomain[item][0]
            self.categoricalDB.append(catTrans)

    @print_timing
    def learn(self, minsup):
        self.modelFileName = "models/igmmodel_minsup{}".format(minsup)
        if os.path.exists(self.modelFileName):
            self.loadIgmModelFromFile()
        else:
            logging.info("running IGM inference; minsup = {}".format(minsup))
            fi = self.getFI(minsup)  # get the frequent itemsets of the original DB. (e.g. using eclat) Format: [(itemset, prob),...]
            self.igmModel = self.filterFI(fi) # Select the set of interesting itemsets following the concept proposed by Laxman et.al.
            self.saveIgmModeltoFile()
        return len(self.igmModel)

    @print_timing
    def gen(self):
        with open(self.GeneratedDBfile, 'w') as genFile:
            ntrans = 0
            for i in range(len(self.originalDB)):
                newTransaction = []
                domainCounter = 0
                while domainCounter < len(self.itemAlphabet): # each alphabet item represents a domain.
                    dom = self.chooseDomain()
                    itemset = self.chooseItemset(dom)
                    newTransaction = set(pattern).union(itemset)  # both parameters should be sets.


                newTrans = ",".join(sorted(newTransaction))
                logging.debug("===> generating transaction nr: {}; freq. itemset selected: {}; pattern selected: {}; noise pattern selected: {}".format(i, itemset, pattern, noise))
                if len(newTrans):
                    genFile.write(newTrans + "\n")
                    logging.debug("writing transaction to new db: {}".format(newTrans))
                    ntrans += 1
                # REPORT progress
                if i and i % 1000 == 0:
                    logging.info("\tprocessed {} transactions of {} ({:0.1f}%).".format(i, len(self.originalDB),100.0 * i / len(self.originalDB)))
            logging.info("wrote synthetic database to file {}, with {} transactions ({:0.1f}%)".format(self.GeneratedDBfile, ntrans, 100.0 * ntrans / len(self.originalDB)))
        return len(self.GeneratedDBfile)

if __name__ == '__main__':

    # arguments setup
    parser = argparse.ArgumentParser()
    parser.add_argument('--logfile', default=None, help='Log file')
    parser.add_argument('--dbfile', default='db/groceries.csv', help='Input database')
    parser.add_argument('--minsup', default=75, help='Minimum support threshold')
    parser.add_argument('--lda_passes', default=200, help='Nr of passes over input data for lda parameter estimation')
    parser.add_argument('--iim_passes', default=500, help='Nr of iterations over input data for iim parameter estimation')
    parser.add_argument('--igm_minsup', default=75, help='Minimum support threshold (percentage %)')
    parser.add_argument('--krimp_minsup', default=75, help='Minimum support threshold (percentage %)')

    args = parser.parse_args()
    args.dbname = os.path.basename(args.dbfile)

    # logging setup
    if args.logfile:
        logging.basicConfig(filename=args.logfile, format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    else:
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    # for reproducibility
    np.random.seed(43)

    # first, run eclat on original file to do comparisons
    K = eclat(args.dbfile)
    logging.info("Nr of frequent itemsets found is: '{}' (future K for lda generator)".format(K))

    # IGM generator model (igm)
    # REMEMBER TO CONSIDER ECLAT INPUT DB DELIMITER
    igm = IGMGen(args.dbfile)
    igm.learn(args.igm_minsup)
    igm.gen()
    eclat(igm.GeneratedDBfile)

    # Krimp generator model (krimp)
    # REMEMBER TO CONSIDER ECLAT INPUT DB DELIMITER
    krimp = KrimpGen(args.dbfile)
    krimp.learn(args.krimp_minsup)
    krimp.gen()
    eclat(krimp.GeneratedDBfile)

    # now, run first generator model (lda) and then eclat on synthetic db
    # lda = LDALearnGen(args.dbfile)
    # lda.learn(K, args.lda_passes)
    # lda.gen()
    # eclat(lda.newdbfile)
    #
    # # run iim generator model (iim)
    # iim = IIMLearnGen(args.dbfile)
    # iim.learn(args.iim_passes)
    # iim.gen()
    # eclat(iim.newdbfile)


