#!/usr/bin/env python3

import os
import re
import sys
import dbg
import utils
#import cPickle as pickle
import pickle
from color import Color
import optparse
import collections
import glob
import pdb
from os.path import join

import fsop
import rsf
from argnorm import filter_out_non_args, have_args, errno_to_str
from pathbin import PathBin, get_pickle_name
from rsv import RangeSetVector, calc_average_rsv
from checker import BaseChecker, CheckerRunner, CheckerPlan, SymbolTable

from code import SE, Node, SEmain

ROOT  = os.path.abspath(os.path.dirname(__file__))
PICKLE_DIR = os.path.normpath(os.path.join(ROOT, "./out"))


#import random
class CrossCheckers(BaseChecker):
    def __init__(self):
        BaseChecker.__init__(self)
        self.rtn_funcs_dic = {} # {rtn, [list of functions]}*
        #self.symbol_tbl = SymbolTable()
        self.rhs = set()
        #self.r = random.random()
        self.model_rhs = set()

    def check(self, funcs):
        # collect functions, which return the same value
        rtn_paths_list = self.get_rtn_paths_list(funcs)

        #rhs_set = set()
        # run store check for each (return, functions) pair
        for rtn_paths in rtn_paths_list:
            for (rtn, retpaths) in rtn_paths.items():
                for retpath in retpaths:
                    stores = retpath.get_stores()
                    if stores == None:
                        continue
                    for store in stores:
                        # check stores.rhs
                        # remove duplicate one.
                        assert(store.rhs is not None)
                        rhs_t = store.rhs #filter_out_non_args(store.rhs) # filter out rhs arguments
                        if have_args(rhs_t):
                            print(rhs_t)
                            rhs_t = re.sub('[,\(\)\s#]', '', rhs_t)
                            rhs_t = re.sub('(tmp)+', 'tmp', rhs_t)
                            print(rhs_t)
                            store.rhs = rhs_t
                            #rhs_t = rhs_t.replace(' ', '').replace('(', '').replace(')', '')
                            self.rhs.add(store)
                        #print(filter_out_non_args(store.rhs)) # filter out rhs arguments
                        #print(type(store), type(filter_out_non_args(store.rhs))) # filter out rhs arguments
        print('kkk==', len(self.rhs))
    def report(self, report_all = True):
        # simply gathering report from all cross checkers
        # map(lambda ck: ck.report(report_all), self.cks)
        # self.model_rhs 
        # self.rhs
        
        # lets compare self.rhs and model_rhs 
        print('report', len(self.rhs))
        locations = set()
        for rhs in self.rhs:
            locations.add(rhs.loc)
        with open('results.txt', 'a+') as fp:
            fp.write('\n'.join(locations))
            fp.write('\n')
        
            # the static analysis might not be complete.
            # therefore, we might need to design algorithms to complete it.
            # an intuitive solution is: construct control-flow graphs and iteratively traverse the ending nodes -- the nodes that do not have data dependencies for others. But what's the difference? if a node reach the preceeding nodes must reach the identified not, there is no need to do that.

        #print(self.r)
        return

if __name__ == '__main__':
    utils.install_pdb()

    # option parsing
    parser = optparse.OptionParser()
    parser.add_option("--pickle", help="pickle directory", default=PICKLE_DIR)
    parser.add_option("--fs", help="List of fs", default=None)
    parser.add_option("--out", help="output file", default = "result.txt")
    (opts, args) = parser.parse_args()

    if opts.out:
        if os.path.exists(opts.out):
            os.remove(opts.out)

    fs = "*"
    if opts.fs:
        fs = opts.fs.split(",")
    log_d = opts.pickle

    # run return check
    #runner = CheckerRunner(type(CrossCheckers()), "fss-ckcross-", log_d, fs, *args)
    runner = CheckerRunner(type(CrossCheckers()), "fss-ckcross-", log_d, fs, check_all=True, debug=True)
    runner.run_check(seed = "mysql.smt")
    with open('results.txt', 'r+') as fp:
        content = set(fp.readlines())
        fp.seek(0)
        fp.write(''.join(content))
        fp.truncate()
