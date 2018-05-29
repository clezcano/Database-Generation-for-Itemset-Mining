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
import fileinput
import time
import tempfile

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
    returns nr of frequent itemsets found
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
        self.dbfile = indb
        self.newdbfile = "db/igm-" + os.path.basename(indb)
        self.modelfname = None     # to be determined on learn execution, depends on parameters
        self.K = None
        self.npasses = None
        self.igm = None             # model parameters
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

    @print_timing
    def learn(self, minsup):
        self.modelfname = "models/igmmodel_minsup{}".format(minsup)
        if os.path.exists(self.modelfname):
            self.load()
        else:
            logging.info("running IGM inference; minsup = {}".format(minsup))

            fi = self.getFI(minsup)  # get the frequent itemsets
            self.igm = self.filterFi(fi)

            with open(self.modelfname, 'w') as modelFile:
                for (itemset, p) in self.igm:
                    modelFile.write(",".join(itemset) + "\n")
                    modelFile.write(str(p) + "\n")
            logging.info("wrote IGM model file to {}".format(self.modelfname))

        return len(self.igm)

    @print_timing
    def gen(self):
        with open(self.newdbfile, 'w') as genFile:
            ntrans = 0
            for i in range(len(self.db)):
                newtrans = []
                j = self.chooseFreqItemset()
                p = self.choosePattern(j)
                n = self.chooseNoise(j)
                newtrans = p | n   # both parameteres should be sets.
                newitems = ",".join(sorted(newtrans))
                logging.debug("===> generating transaction nr: {}; freq. itemset selected: {}; pattern selected: {}; noise pattern selected: {}".format(i, j, p, n))
                if len(newtrans):
                    genFile.write(newitems + "\n")
                    logging.debug("writing transaction to new db: {}".format(newitems))
                    ntrans += 1
                # REPORT progress
                if i and i % 1000 == 0:
                    logging.info("\tprocessed {} transactions of {} ({:0.1f}%).".format(i, len(self.db), 100.0 * i / len(self.db)))

        logging.info("wrote synthetic database to file {}, with {} transactions ({:0.1f}%)".format(self.newdbfile, ntrans, 100.0 * ntrans / len(self.db)))
        return self.newdbfile


    def load(self):
        self.igm = []
        with open(self.modelfname) as inf:
            for line in inf:
                itemset = line.strip().split(",")
                prob = float(inf.readline().strip())
                self.igm.append((itemset, prob))
        logging.info("loaded IGM model from file {}".format(self.modelfname))


    def save(self):
        with open(self.modelfname, 'w') as outf:
            for (itemset, p) in self.igm:
                outf.write(",".join(itemset) + "\n")
                outf.write(str(p) + "\n")
        logging.info("wrote IGM model file to {}".format(self.modelfname))

    def filterFi(self, fi):
        fi = []
        return fi

    @print_timing
    def getFI(self, infname):
        """
        runs eclat on input db
        prints the frequent itemsets on a file and returns them as well

        """
        bname = os.path.splitext(os.path.basename(infname))[0]
        outfname = "out/eclat-{}.itemsets".format(bname)
        cmd = ["exe/eclat", "-f,", "-s{}".format(args.minsup), "-k,", infname, outfname]
        logging.info("running eclat command: {} over the input file".format(" ".join(cmd), infname))
        call(cmd)
        logging.info("wrote frequent itemsets in file {}".format(outfname))
        fi = []
        with open(outfname) as fiFile:
            for line in fiFile:
                itemset = line.strip().split(",")
                freq = float(fiFile.readline().strip())
                fi.append((itemset, freq))
        logging.info("loaded frequent itemsets from file {}".format(outfname))
        return fi

    def chooseFreqItemset(self):
        # remember to return a list or set
        for j, x in enumerate(np.random.multinomial(1, [p for (itemset, p) in self.igm])):
            if x:
                return j

    def choosePattern(self, pattern):
        # remember to return a list or set
        return 0

    def chooseNoise(self, pattern):
        # remember to return a list or set
        return 0


if __name__ == '__main__':

    # arguments setup
    parser = argparse.ArgumentParser()
    parser.add_argument('--logfile', default=None, help='Log file')
    parser.add_argument('--dbfile', default='db/groceries.csv', help='Input database')
    parser.add_argument('--minsup', default=75, help='Minimum support threshold')
    parser.add_argument('--lda_passes', default=200, help='Nr of passes over input data for lda parameter estimation')
    parser.add_argument('--iim_passes', default=500, help='Nr of iterations over input data for iim parameter estimation')

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
    igm = IGMGen(args.dbfile)
    igm.learn(args.minsup)
    igm.gen()
    eclat(igm.newdbfile)

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


