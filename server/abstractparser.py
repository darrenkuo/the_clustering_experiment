#!/usr/bin/python

from optparse import OptionParser
from os import mkdir
from os.path import join
from re import match
from re import search
from re import sub
from subprocess import *
from sys import argv
from sys import exit
from sys import stdin
from tempfile import TemporaryFile

class Indexer:
    def __init__(self):
        self.realToNew = {}
        self.newToReal = {}
        self.reals = []
        self.new = 1

    def addReal(self, real):
        if real not in self.realToNew:
            id = self.new
            self.realToNew[real] = id
            self.newToReal[id] = real
            self.new += 1
            self.reals.append(real)
            return id
        else:
            return self.getNew(real)

    def getNew(self, real):
        if real in self.realToNew:
            return self.realToNew[real]
        else:
            return -1
        
    def getReal(self, new):
        if new in self.newToReal:
            return self.newToReal[new]
        else:
            return -1
    
    def length(self):
        return self.new

PAPERTITLE = '#\\*'
AUTHOR = r'#@'
YEAR = '#year'
CONF = r'#conf'
CITATION = r'#citation'
INDEX = r'#index'
ARNETID = r'#arnetid'
REF = r'#%'
ABSTRACT = r'#!'

map1 = [('PAPERTITLE', PAPERTITLE),
        ('AUTHOR', AUTHOR),
        ('YEAR', YEAR),
        ('CONF', CONF),
        ('CITATION', CITATION),
        ('INDEX', INDEX),
        ('ARNETID', ARNETID),
        ('REF', REF),
        ('ABSTRACT', ABSTRACT)]

p_title = None

def parse(line):
    global p_title
    if p_title:
        t = p_title
        p_title = None
        return t

    for x, y in map1:
        if match(y, line):
            return (x, sub('\n', '', sub(y, '', line)))
    return None

def blank():
    map = {'PAPERTITLE' : None,
           'AUTHOR' : None,
           'YEAR': None,
           'CONF': None,
           'CITATION': None,
           'INDEX': None,
           'ARNETID': None,
           'REF': set(),
           'ABSTRACT' : None }
    
    return map

row = '<tr>\n\t<td>%s</td>\n\t<td>%s</td>\n</tr>\n'
link = '<a href="%s.html">%s</a>'

def build_htmls_serializes(output_directory, prefix, pm):
    global row, link

    serialize_directory = join(output_directory, "serialized")
    try:
        mkdir(serialize_directory)
    except:
        print 'serialize directory already created'
    
    f = open(join(output_directory, "%s.html" % (prefix)), 'w')
    for i in pm:
        g = open(join(serialize_directory, "%s.serialize" % (str(i))), 'w')
        g.write(str(pm[i]))
        g.close()
                
        f.write('<h4> <a name="%s">Information about %s</a></h4>\n' % (str(i), pm[i]['PAPERTITLE']))
        f.write('<table border="0">\n')

        for field in ['AUTHOR', 'YEAR', 'CONF', 'INDEX', 'CITATION', 'ARNETID', 'ABSTRACT']:
            f.write(row % (field, pm[i][field]))

        f.write(row % ('REFS', " ".join(map(lambda x: (link % (str(x), str(x))), list(pm[i]['REF'])))))
        f.write("</table>\n<hr>\n")
    
    f.close()
        
def check_abstract(abstract, keywords):
    for i in keywords:
        if not search(i, abstract.lower()):
            return False
    return True

def next_paper(f, keywords):
    m = blank()
    for x in f:
        p = parse(x.strip())

        if not p:
            continue;
        
        if p[0] == 'PAPERTITLE':
            if m != None:
                if (not m["ABSTRACT"] or 
                    not check_abstract(m['ABSTRACT'], keywords)):# or 
                    #not (len(m['REF']) >= minimum)):
                    continue

                yield m
            m = blank()
        
        if p[0] == 'REF':
            m['REF'].add(p[1])
        else:
            m[p[0]] = p[1]

    if (m["ABSTRACT"] and
        check_abstract(m['ABSTRACT'], keywords)):# and
        #(len(m['REF']) >= minimum)):
        yield m

    yield None

#TODO: fix global variables
#TODO: make new prefix directory

def merge_files(output_dir, prefixes, new_prefix):
    
    pm = {}
    indexer = Indexer()
    new_prefix_dir = join(output_dir, new_prefix)
    try:
        mkdir(new_prefix_dir)
    except:
        print "new prefix directory already created"
    
    f = open(join(output_dir, 'data.serialize'), 'r')
    descriptions = eval(f.read())
    f.close()

    keyword_set = set()
    min_degree = 1e300

    cluster_map = {}
    for c, p in enumerate(prefixes):
        cur_dir = join(output_dir, p)
        f = open(join(cur_dir, 'data.index'), 'r')
        indices = f.read().split()
        f.close()

        for i in indices:
            cluster_map[i] = c
            f = open(join(cur_dir, join('serialized', '%s.serialize' % (i))), 'r')
            pm[i] = eval(f.read())
            f.close()

            if pm[i]['INDEX'] != i:
                print "ERROR! different index"


        groups = match('Filtered using keywords in ([\s\S]+) with minimum node degree of ([\d]+)',
                       descriptions[p])

        if groups:
            groups = groups.groups()
            keywords = eval(groups[0])
            for k in keywords:
                keyword_set.add(k)

            min_degree = min(int(groups[1]), min_degree)

    clean_ref(pm)
    indexer_ref(pm, indexer)
    for i in pm:
        pm[i]['REF'] = pm[i]['IN-REF'].union(pm[i]['OUT-REF'])

    f = open(join(new_prefix_dir, 'merge.clusters'), 'w')
    for r in indexer.reals:
        f.write(str(cluster_map[r]) + '\n')
    f.close()

    output_description(list(keyword_set), min_degree, new_prefix_dir, new_prefix)
    build_htmls_serializes(new_prefix_dir, new_prefix, pm)
    build_outputs(new_prefix_dir, new_prefix, pm, indexer)

def output_description(keywords, degree, output_dir, prefix):
    description = 'Filtered using keywords in %s with minimum node degree of %d' % (str(keywords), degree)
    f = open(join(output_dir, '../data.serialize'), 'r')
    descriptions = eval(f.read())
    f.close()

    descriptions[prefix] = description

    f = open(join(output_dir, '../data.serialize'), 'w')
    f.write(str(descriptions))
    f.close()


def bidirectional(pm):
    for index in pm:
        pm[index]['REF'] = set(filter(lambda r: (r in pm and r != index), pm[index]['REF']))
        map(lambda r: pm[r]['REF'].add(index), pm[index]['REF'])

def build_abstract_count(output_directory, prefix, pm):
    f = open(join(output_directory, 'data.abstract.count'), 'w')
    indexer = Indexer()
    
    for i in pm:
        m = {}
        for w in pm[i]['ABSTRACT'].strip().split():
            id = indexer.addReal(w)
            if id not in m:
                m[id] = 0
            m[id] += 1
        f.write('%d ' % (len(m)))
        for j in m:
            f.write('%s:%s ' % (j, m[j]))
        f.write('\n')
    f.close()        

    f = open(join(output_directory, 'data.abstract.count.clabel'), 'w')
    for i in indexer.reals:
        f.write('%s\n' % (i))
    f.close()        

def build_outputs(output_directory, prefix, pm, indexer):
    
    f = open(join(output_directory, "data.out"), 'w')
    g = open(join(output_directory, "data.index"), 'w')
    a = open(join(output_directory, "data.abstract"), 'w')
    b = open(join(output_directory, "data.mat"), 'w')

    build_abstract_count(output_directory, prefix, pm)

    total_edge = 0
    for i in pm:
        total_edge += len(pm[i]['REF'])

    f.write("%d %d\n" % (len(pm), total_edge))
    b.write("%d %d %d\n" % (len(pm), len(pm), total_edge))
    for i in range(1, indexer.length()):
        if (indexer.getReal(i) == -1):
            print "this is not good..."
            
        g.write(indexer.getReal(i) + "\n")
        a.write(pm[indexer.getReal(i)]["ABSTRACT"] + "\n")

        for r in pm[indexer.getReal(i)]['REF']:
            if indexer.getNew(r) != -1:
                f.write("%d 1.0 " % (indexer.getNew(r)))
                b.write("%d 1.0 " % (indexer.getNew(r)))
            else:
                print "ERROR! unknown reference...."
        f.write('\n')
        b.write('\n')

    for i in pm:
        for r in pm[i]['REF']:
            if r not in pm or i not in pm[r]['REF'] or r == i:
                print "ERROR! sanity check...", r not in pm, i not in pm[r]['REF'], r == i
    
    f.close()
    g.close()
    a.close()
    b.close()

def create_outputs1(main_prefix, data_dir, new_prefix, minimum):
    print "TH:" , minimum
    output_dir = join(data_dir, new_prefix)
    f = open(join(data_dir, main_prefix, 'data.index'), 'r')
    indices = f.read().split()
    f.close()

    f = open(join(data_dir, 'data.serialize'), 'r')
    descriptions = eval(f.read())
    f.close()

    pm = {}
    for i in indices:
        f = open(join(data_dir, main_prefix, 'serialized', '%s.serialize' % (str(i))), 'r')
        pm[i] = eval(f.read())
        f.close()

    indexer = Indexer()
    for i in pm.keys():
        if len(pm[i]['REF']) < minimum:
            pm.pop(i)

    for i in pm:
        indexer.addReal(i)
        new_ref = set()
        for r in pm[i]['REF']:
            if r in pm:
                new_ref.add(r)
        pm[i]['REF'] = new_ref
        
        new_in_ref = set()
        for r in pm[i]['IN-REF']:
            if r in pm:
                new_in_ref.add(r)
        pm[i]['IN-REF'] = new_in_ref
        
        new_out_ref = set()
        for r in pm[i]['OUT-REF']:
            if r in pm:
                new_out_ref.add(r)
        pm[i]['OUT-REF'] = new_out_ref

    try:
        mkdir(output_dir)
    except:
        print "prefix output directory is created already"


    groups = match('Filtered using keywords in ([\s\S]+) with minimum node degree of ([\d]+)',
                   descriptions[main_prefix]).groups()

    output_description(eval(groups[0]), minimum, output_dir, new_prefix)
    build_htmls_serializes(output_dir, new_prefix, pm)
    build_outputs(output_dir, new_prefix, pm, indexer)

    #TODO: please fix this shit....
    tf = TemporaryFile()
    proc = Popen(['lib/doc2mat-1.0/doc2mat', 'data/%s/data.abstract' % (new_prefix), 
                  'data/%s/data.abstract.matrix' % (new_prefix)], stdout=tf)
    print ' '.join(['lib/doc2mat-1.0/doc2mat', 'data/%s/data.abstract' % (new_prefix), 
                    'data/%s/data.abstract.matrix' % (new_prefix)])
    o = proc.communicate()
    retcode = proc.wait()
    tf.close()

    f = open('data/%s/data.abstract.matrix' % (new_prefix), 'r')
    g = open('data/%s/data.abstract.matrix.ldain' % (new_prefix), 'w')
    proc = Popen(['lib/doc2mat-1.0/matToLdaIn.py'], stdin=f, stdout=g)
    proc.communicate()
    retcode = proc.wait()

    f.close()
    g.close()


def handle_ref(pm, minimum, indexer):
    for i in pm:
        if len(pm[i]['REF']) < minimum:
            pm.pop(i)
        else:
            indexer.addReal(i)

    clean_ref(pm)
    for i in pm:
        for r in pm[i]['REF']:
            pm[r]['REF'].add(i)

def clean_ref(pm):
    for i in pm:
        new_ref = set()
        pm[i]['OLD-REF'] = set(pm[i]['REF'])
        if i in pm[i]['OLD-REF']:
            pm[i]['OLD-REF'].remove(i)
        
        for r in pm[i]['REF']:
            if r in pm and r != i:
                new_ref.add(r)
        pm[i]['REF'] = new_ref
        pm[i]['IN-REF'] = set()
        pm[i]['OUT-REF'] = set(new_ref)

def indexer_ref(pm, indexer):
    for i in pm:
        indexer.addReal(i)
        for r in pm[i]['REF']:
            pm[r]['IN-REF'].add(i)

def create_outputs(main_filename, keywords, data_dir, prefix):
    minimum = 0
    output_dir = join(data_dir, prefix)
    f = open(main_filename, 'r')
    indexer = Indexer()
    pm = {}
    paper_gen = next_paper(f, keywords)

    m = paper_gen.next()
    while m:
        pm[m['INDEX']] = m
        m = paper_gen.next()

    clean_ref(pm)
    indexer_ref(pm, indexer)
    for i in pm:
        pm[i]['REF'] = pm[i]['IN-REF'].union(pm[i]['OUT-REF'])

    try:
        mkdir(output_dir)
    except:
        print "prefix output directory is created already"

    description = 'Filtered using keywords in %s with minimum node degree of %d' % (str(keywords), minimum)

    output_description(keywords, minimum, output_dir, prefix)
    build_htmls_serializes(output_dir, prefix, pm)
    build_outputs(output_dir, prefix, pm, indexer)

    proc = Popen(['lib/doc2mat-1.0/doc2mat', 'data/%s/data.abstract' % (prefix), 
                  'data/%s/data.abstract.matrix' % (prefix)], stdout=PIPE)
    proc.communicate()
    retcode = proc.wait()

    f = open('data/%s/data.abstract.matrix' % (prefix), 'r')
    g = open('data/%s/data.abstract.matrix.ldain' % (prefix), 'w')
    proc = Popen(['lib/doc2mat-1.0/matToLdaIn.py'], stdin=f, stdout=g)
    proc.communicate()
    retcode = proc.wait()

    f.close()
    g.close()

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('-t', '--threshold', dest = 'threshold', default = 0,
                      help = 'the minimum of degree the nodes are allowed.')
    parser.add_option('-k', '--keyword', dest = 'keywordfile', default = None,
                      help = 'file that contains a list of keywords.')
    parser.add_option('-a', '--all', dest = 'all', default = None,
                      help = 'main file that contains all the data')
    parser.add_option('-o', '--output', dest = 'output', default = '.',
                      help = 'Output directory')
    parser.add_option('-p', '--prefix', dest = 'prefix',
                      help = 'prefix for output file')
    parser.add_option('-m', '--mainprefix', dest = 'mainprefix',
                      help = 'main prefix to generate data off')
    

    (options, args) = parser.parse_args()

    prefix = options.prefix
    keywords = []
    if options.keywordfile:
        f = open(options.keywordfile, 'r')
        keywords = f.read().split()
        f.close()

    if options.all:
        create_outputs(options.all, keywords, options.output, prefix)
    elif options.mainprefix:
        create_outputs1(options.mainprefix, options.output, prefix, int(options.threshold))
