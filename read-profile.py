#!/usr/bin/env python2
#
# Read Profile
# Analyse profiling data

import argparse
import pstats

parser = argparse.ArgumentParser(description='Analyse profiling data.')
parser.add_argument('profile', action='store')
args = parser.parse_args()

stats = pstats.Stats(args.profile)
stats.sort_stats('cumtime')
stats.print_stats(100)
