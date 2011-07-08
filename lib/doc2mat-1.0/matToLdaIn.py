#!/usr/bin/python

from sys import stdin

if __name__ == "__main__":
    stdin.next()

    for x in stdin:
        lst = x.split()
        print len(lst)/2, 
        for i in range(0, len(lst)/2):
            print "%s:%s" % (lst[2*i], lst[2*i+1]), 
        print
        
