#!/usr/bin/env python3

import os
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

class CrossVector(RangeSetVector):
    def __init__(self, func, rtn, values):
        self.func = func
        self.rtn = rtn
        self.values = values

    def get_func_name(self):
        return self.func

    def get_rtn(self):
        return self.rtn

    '''
    def get_missing_stores(self, threshold):
        (myself_diff, avg_diff) = self.get_diffs("@LOG_STORE")
        if avg_diff == []:
            return ""
        
        total_impact = 0
        msto_str = "{{{-- "
        for ad in avg_diff:
            (impact, rs) = (ad[0], ad[1])
            assert(rs.start == rs.end)
            symbol = self.symbol_tbl.get_symbol_string( int(rs.start) )
            assert(symbol is not None)
            msto_str += "<%.5s, %s%s%s> " % \
                       (impact, Color.HEADER, symbol, Color.ENDC)

            total_impact += impact
            if total_impact >= threshold:
                break
        msto_str += "}}}"
        return msto_str
    '''

    def __repr__(self):
        return "'%s'" % self

    def __str__(self):
        return "%s:%s %d\n  "  % (self.func, self.rtn, len(self.values))

class CrossChecker(BaseChecker):
    def __init__(self, rtn, pathbin, symbol_tbl):
        BaseChecker.__init__(self, pathbin)
        self.rtn = rtn
        self.symbol_tbl = symbol_tbl

    def report(self, report_all = True):
        return
        print("%s[C] [%7s] [%.6s] [%23s] [%s]%s"% \
              (Color.HEADER,\
               "Ranking", "Distance", "Funtion", "Missing Updates", \
               Color.ENDC))
        for (ranking, result) in enumerate(self.results):
            distance = result[0]
            sv = result[1]
            if not report_all and distance <= self.avg_distance:
                break
            (cc, ac, l) = self._get_color_code(result)
            delta = distance - self.avg_distance
            print("%s[%s]  %7s   %.6s   %23s   %s%s"% \
                  (cc, ac, \
                   ranking+1, delta, \
                   ''.join((sv.get_func_name(), \
                            ':', \
                            errno_to_str(sv.get_rtn()))), \
                   Color.ENDC, \
                   sv.get_missing_stores(delta * 0.7)))
        print("")
    def _build_vector(self, funcs):
        return

    def check(self, funcs):
        '''
        we know a function to analyze. 
        but we still parse to others.
        '''
        svs = []

        # for each function
        for func in funcs:
            # collect LHS of @LOG_STORE for the specified return value
            rtn_dic = self.pathbin[func]
            rhs_set = set()

            # we get rtn and retpaths
            for (rtn, retpaths) in rtn_dic.items():
                # for each retpath
                for retpath in retpaths:
                    stores = retpath.get_stores()
                    if stores == None:
                        continue
                    for store in stores:
                        # check stores.rhs
                        # remove duplicate one.
                        assert(store.rhs is not None)

                        rhs_set.add(filter_out_non_args(store.rhs)) # filter out rhs arguments
            
            '''
            # change them to symbol id 
            sym_id_set = set()
            for symbol in symbol_set:
                fo_symbol = filter_out_non_args(symbol)
                if have_args(fo_symbol):
                    sym_id= self.symbol_tbl.get_symbol_id(fo_symbol)
                    sym_id_set.add( str(sym_id) )
            '''
            
            sv = CrossVector(func, self.rtn, rhs_set)
            svs.append(sv)
        return svs
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
                        self.rhs.add(filter_out_non_args(store.rhs)) # filter out rhs arguments
                        print(filter_out_non_args(store.rhs)) # filter out rhs arguments
                        print(type(store), type(filter_out_non_args(store.rhs))) # filter out rhs arguments
        print('kkk==', len(self.rhs))
    def report(self, report_all = True):
        # simply gathering report from all cross checkers
        # map(lambda ck: ck.report(report_all), self.cks)
        print('report', len(self.rhs))
        #print(self.r)
        return

if __name__ == '__main__':
    utils.install_pdb()

    # option parsing
    parser = optparse.OptionParser()
    parser.add_option("--pickle", help="pickle directory", default=PICKLE_DIR)
    parser.add_option("--fs", help="List of fs", default=None)
    (opts, args) = parser.parse_args()

    fs = "*"
    if opts.fs:
        fs = opts.fs.split(",")
    log_d = opts.pickle

    # run return check
    #runner = CheckerRunner(type(CrossCheckers()), "fss-ckcross-", log_d, fs, *args)
    runner = CheckerRunner(type(CrossCheckers()), "fss-ckcross-", log_d, fs, check_all=True, debug=True)
    runner.run_check()

