#!/usr/bin/python

from optparse import OptionParser
from os import mkdir
from os import chmod
from os import walk
from os.path import join
from random import randint
from re import match
from re import search
from sys import argv
from subprocess import call, Popen, PIPE

def normalize(lst, lnorm):
    s = sum(map(lambda x: x**lnorm, lst))
    return map(lambda x: float(x)/s, lst)

def dot(lst1, lst2):
    return sum(map(lambda x: x[0] * x[1], zip(lst1, lst2)))

def filterCommonWords(lst):
    f = open('common_words', 'r')
    common_words = f.read().strip().split()
    f.close()

    result = []
    for w in lst:
        if w[0] not in common_words:
            result.append(w)
    return result

def generateLdaK(k, prefix, research_path, html_path, data_module, minimum, clabel_file):
    serialized_path = join(research_path, 'data', prefix, 'serialized')
    f = open(join(html_path, 'final.gamma'), 'r')
    g = open(join(research_path, join('data', join(prefix, '%s.index' % (prefix)))), 'r')

    lst = map(lambda x: normalize(x, 1), 
              map(lambda x: 
                  map(lambda y: float(y), x.split()), 
                  f.read().split('\n'))[:-1])
    lst1 = map(int, g.read().split())

    f.close()
    g.close()

    m = dict([(i, j) for i, j in zip(lst1, lst)])
    n = {}

    #f = open(join(research_path, 'data', prefix, '%s.abstract.matrix.clabel' % (prefix)), 'r')
    #f = open(join(research_path, 'data', prefix, '%s.abstract.count.clabel' % (prefix)), 'r')
    f = open(join(research_path, 'data', prefix, '%s.%s' % (prefix, clabel_file)), 'r')
    words = f.read().strip().split()
    f.close()

    f = open(join(html_path, 'final.beta'), 'r')
    data = map(lambda x: zip(words, map(float, x.split())), f.read().strip().split('\n'))
    f.close()
    
    for i in range(k):
        print '%d.html' % (i)
        h = open(join(html_path, '%d.html' % (i)), 'w')

        lst = filterCommonWords(sorted(data[i], key=lambda x: -x[1]))

        h.write('<table border="1">\n')
        for j in lst[:20]:
            h.write('<tr><td>%s</td><td>%s</td></tr>\n' % j)
        h.write('</table>\n')

        for y in sorted(m.items(), key=lambda y: -y[1][i]):
            f = open(join(serialized_path, '%s.serialize' % (str(y[0]))), 'r')
            pm = eval(f.read())
            f.close()

            pm['TOPIC SCORE'] = y[1][i]
            data_module.build_lda_html(h, pm, map(lambda x: x[0], lst[:20]))
        h.close()

    '''
    # TODO: fix stats generation
    # generate stats
    clusters = map(lambda x: int(match('%s-results-([0-9]+)' % (prefix), x).groups()[0]), 
                   filter(lambda x: search('%s-results-[0-9]+' % (prefix), x),  
                          walk('scluster').next()[1]))
    for c in clusters:
        f = open(join(research_path, 'data/%s/%s.out.clustering.%s' % (prefix, prefix, c)), 'r')
        cluster_groups = map(int, f.read().split())
        f.close()
        info = {'lda': k}
        s = {}
        for i in range(c):
            s[i] = []
                
        for i, j in zip(cluster_groups, lst):
            #calculate simliarities
            s[i].append(j)

        print "sampling with c = %d" % (c)
        for i in range(c):
            print 'generating stats info for i = %d and c = %d' % (i, c)

            sample_size = (len(lst) ** 2) / 10
            incluster = 0.0
            outcluster = 0.0
            for j in range(sample_size):
                # incluster
                x1 = randint(0, len(s[i])-1)
                x2 = x1
                while x2 == x1:
                    x2 = randint(0, len(s[i])-1)

                incluster += dot(s[i][x1], s[i][x2])

                # outcluster
                x1 = randint(0, len(s[i])-1)
                a = i
                while a == i:
                    a = randint(0, c-1)
                    
                x2 = randint(0, len(s[a])-1)
                outcluster += dot(s[i][x1], s[a][x2])
                
            info[i] = {'IN' : incluster / float(sample_size),
                       'OUT' : outcluster / float(sample_size)}
            print 'stored info for i = %d' % (i)

        print 'Writing info to file: ' + str(info)
        print 'write to file scluster/%s-results-%s/lda-%d.serialize' % (prefix, c, k)

        f = open(join(html_path, 'scluster/%s-results-%s/lda-%d.serialize' % (prefix, c, k)), 'w')
        f.write(str(info))
        f.close()
    '''

def generateClusterK(k, prefix, research_path, html_path, data_module, minimum, prog):
    serialized_path = join(research_path, 'data', prefix, 'serialized')
    getNeighbors = data_module.getNeighbors
    setNeighbors = data_module.setNeighbors

    if prog == 'scluster':
        f = open(join(research_path, 'data/%s/%s.out.clustering.%d' % (prefix, prefix, k)), 'r')
    elif prog == 'vcluster':
        f = open(join(research_path, 'data/%s/%s.mat.clustering.%d' % (prefix, prefix, k)), 'r')
    else:
        f = open(join(research_path, 'data/%s/%s.abstract.matrix.clustering.%d' % (prefix, prefix, k)), 'r')
    g = open(join(research_path, 'data/%s/%s.index' % (prefix, prefix)), 'r')

    m = dict([(i,[]) for i in range(k)])
    if prog == 'vcluster' or prog == 'vcluster_tfidf':
        m[-1] = []
    n = {}

    clusters = map(int, f.read().split())
    indices = g.read().split()
    for i, j, l in zip(clusters, indices, range(len(clusters))):
        m[int(i)].append((j, l))
        n[int(j)] = int(i)
    
    f.close()
    g.close()

    try:
        mkdir(html_path)
        chmod(html_path, 0755)
    except:
        print '%s has already been created' % (html_path)
        
    results = {'nodes' : [], 'links' : []}
    
    file_ds = [open(join(html_path, '%s.html' % (i)), 'w') for i in m]

    if minimum > 0:
        cluster_mapping = {}
        for c, index in zip(clusters, indices):
            f = open(join(serialized_path, '%s.serialize' % (index)), 'r')
            data = eval(f.read())
            if len(getNeighbors(data)) >= minimum:
                cluster_mapping[index] = c
    else:
        cluster_mapping = dict([(index, c) for c, index in zip(clusters, indices)])

    mapping = dict([(i[0], count) for count, i in zip(range(len(cluster_mapping)), cluster_mapping.items())])

    def add_links(source, target):
        weight = 1.0
        """
        if cluster_mapping[source] == cluster_mapping[source]:
        weight = 50.0
        """
        results['links'].append({'source' : mapping[source], 'target' : mapping[target], 'value' : weight})

    dataset = dict([(i,[]) for i in range(k)])

    for index, c in cluster_mapping.iteritems():
        f = open(join(serialized_path, '%s.serialize' % (index)), 'r')
        data = eval(f.read())
        #data['IN-REF'] = []
        #data['OUT-REF'] = []
        results['nodes'].append({'nodeName' : str(index), 'group' : int(c)})
        setNeighbors(data, filter(lambda x: x in cluster_mapping, getNeighbors(data)))
        map(lambda r: add_links(index, r), getNeighbors(data))
        #data['IN-REF'] = filter(lambda x: cluster_mapping[x] == c, getNeighbors(data))
        #data['OUT-REF'] = map(lambda x: (x, cluster_mapping[x]),
        #                      filter(lambda x: cluster_mapping[x] != c, getNeighbors(data)))
        data_module.build_scluster_html(file_ds[c], data, cluster_mapping)
        
    if prog == 'scluster':
        h = open('server/static/js/%s-results-%s-S.js' % (prefix, str(k)), 'w')
    else:
        h = open('server/static/js/%s-results-%s-V.js' % (prefix, str(k)), 'w')
    h.write('var data = %s;' % (str(results)))
    h.close()

    try:
        import networkx as nx
        #constructNetworkXGraph(nx, 
    except ImportError:
        print "networkx module doesn't exist"

        
    f = open(join(research_path, 'data/%s/%s-%s.gv' % (prefix, prefix, k)), 'w')
    gv_txt = "graph G {\n"
    mapping = dict(zip(range(len(results['nodes'])), results['nodes']))
    for i in results['nodes']:
        gv_txt += '%s;\n' % (i['nodeName'])

    for i in results['links']:
        id1 = mapping[i['source']]['nodeName']
        id2 = mapping[i['target']]['nodeName']
        gv_txt += '%s -> %s;\n' % (id1, id2)
    gv_txt += '}\n'
    f.write(gv_txt)
    f.close()

def scluster(k, prefix, research_path, html_path, data_module, minimum):

    f = open(join(research_path, 'data', prefix, '%s.out.clustering.%d.output' % (prefix, k)), 'w')

    proc = Popen([join(research_path, 'lib/cluto-2.1.1/Linux/scluster'), 
                  join(research_path, 'data', prefix, '%s.out' % (prefix)),
                  str(k)], stdout = f)
    print ' '.join([join(research_path, 'lib/cluto-2.1.1/Linux/scluster'), 
                  join(research_path, 'data', prefix, '%s.out' % (prefix)),
                  str(k)])
    proc.communicate()
    print 'retcode:', proc.wait()
    f.close()

    if html_path:
        generateClusterK(k, prefix, research_path, html_path, data_module, minimum, 'scluster')

'''
def getSVSimiliar(prefix, k):
    f = open('data/%s/%s.out.clustering.%s' % (prefix, prefix, k), 'r')
    g = open('data/%s/%s.mat.clustering.%s' % (prefix, prefix, k), 'r')
    h = open('data/%s/%s.index' % (prefix, prefix), 'r')

    scluster = f.read().split()
    vcluster = g.read().split()
    indices = h.read().split()

    f.close()
    g.close()
    h.close()
    
    new_data = {}
    new_clusters = []
    for c, i in zip(clusters, indices):
        f = open('data/%s/serialized/%s.serialize' % (prefix1, i), 'r')
        data = eval(f.read())
        if (len(data['REF']) >= l):
            data['NEW-REF'] = set(data['REF'])
            new_data[i] = (c, data)
            new_clusters.append(c)

    for i, j in new_data.iteritems():
        for r in j[1]['NEW-REF']:
            if r != i and r in new_data:
                new_data[r][1]['NEW-REF'].add(i)


    in_stats = [0] * int(k)
    out_stats = [0] *int(k)
    total = [0] * int(k)
    for i in new_data:
        total[int(new_data[i][0])] += 1
        for r in new_data[i][1]['NEW-REF']:
            if r in new_data and r != i:
                if new_data[r][0] == new_data[i][0]:
                    in_stats[int(new_data[i][0])] += 1
                else:
                    out_stats[int(new_data[i][0])] += 1

    similarities = []
    for i, j in enumerate(zip(in_stats, out_stats)):
        similarities.append((j[0]/float(total[i] * (total[i] - 1)),
                             j[1]/float((len(new_data)-total[i]) * total[i])))

    results = {'in-stats': in_stats,
               'out-stats': out_stats,
               'g0-similarities': similarities,
               'total': total,
               'new_clusters': new_clusters}

    return results

'''

def filterWithI(prefix1, k, l, infix):
    f = open('data/%s/%s.%s.clustering.%s' % (prefix1, prefix1, infix, k), 'r')
    g = open('data/%s/%s.index' % (prefix1, prefix1), 'r')

    clusters = f.read().split()
    indices = g.read().split()

    f.close()
    g.close()

    new_data = {}
    new_clusters = []

    indexToCluster = dict(zip(indices, clusters))
    for c, i in zip(clusters, indices):
        f = open('data/%s/serialized/%s.serialize' % (prefix1, i), 'r')
        data = eval(f.read())
        if (len(data['REF']) >= l):
            data['NEW-REF'] = set(data['REF'])
            new_data[i] = (c, data)
            new_clusters.append(c)

    for i, j in new_data.iteritems():
        for r in j[1]['NEW-REF']:
            if r != i and r in new_data:
                new_data[r][1]['NEW-REF'].add(i)

    #(internal, external)
    total = [0] * int(k)
    in_stats = [0] * int(k)
    out_stats = [0] *int(k)

    for i in new_data:
        if int(new_data[i][0]) != -1:
            total[int(new_data[i][0])] += 1
            for r in new_data[i][1]['NEW-REF']:
                if int(indexToCluster[r]) != -1:
                    if r in new_data and r != i:
                        if new_data[r][0] == new_data[i][0]:
                            in_stats[int(new_data[i][0])] += 1
                        else:
                            out_stats[int(new_data[i][0])] += 1

    similarities = []
    for i, j in enumerate(zip(in_stats, out_stats)):
        similarities.append((j[0]/float(total[i] * (total[i] - 1)),
                             j[1]/float((len(new_data)-total[i]) * total[i])))

    results = {'in-stats': in_stats,
               'out-stats': out_stats,
               'g0-similarities': similarities,
               'total': total,
               'new_clusters': new_clusters}

    return results
    

def lda_tfidf(k, prefix, research_path, html_path, paper, minimum):
    lda(k, prefix, research_path, html_path, paper, minimum, 'abstract.ldain', 'abstract.matrix.clabel')

def lda_word_count(k, prefix, research_path, html_path, paper, minimum):
    lda(k, prefix, research_path, html_path, paper, minimum, 'abstract.count', 'abstract.count.clabel')

# TODO: fix global variables
def lda(k, prefix, research_path, html_path, paper, minimum, lda_input, clabel_input):
    f = open(join(research_path, 'data/%s/%s.out.lda.%d.output' % (prefix, prefix, k)), 'w')
    command = [join(research_path, 'lib/lda-c-dist/lda'),
               'est', str(1), str(k), 
               join(research_path, 'lib/lda-c-dist/settings.txt'),
               #join(research_path, 'data/%s/%s.abstract.matrix' % (prefix, prefix)),
               #join(research_path, 'data/%s/%s.abstract.count' % (prefix, prefix)),
               join(research_path, 'data/%s/%s.%s' % (prefix, prefix, lda_input)),
               'random', html_path]#'lda/%s/results-%s' % (prefix, k)]
    print ' '.join(command)
    proc = Popen(command, stdout=f)
    o = proc.communicate()
    print 'retcode',  proc.wait()
    print 'output', o
    f.close()

    if html_path:
        chmod(html_path, 0755)
        generateLdaK(k, prefix, research_path, html_path, paper, minimum, clabel_input)

def vcluster(k, prefix, research_path, html_path, paper, minimum):
    f = open(join(research_path, 'data/%s/%s.mat.clustering.%d.output' %
                  (prefix, prefix, k)), 'w')
    proc = Popen([join(research_path, 'lib/cluto-2.1.1/Linux/vcluster'),
                  join(research_path, 'data/%s/%s.mat' % (prefix, prefix)), str(k)], stdout = f)
    proc.communicate()
    proc.wait()
    f.close()

    if html_path:
        generateClusterK(k, prefix, research_path, html_path, paper, minimum, 'vcluster')

def vcluster_tfidf(k, prefix, research_path, html_path, paper, minimum):
    f = open(join(research_path, 'data/%s/%s.abstract.matrix.clustering.%d.output' %
                  (prefix, prefix, k)), 'w')
    proc = Popen([join(research_path, 'lib/cluto-2.1.1/Linux/vcluster'),
                  join(research_path, 'data/%s/%s.abstract.matrix' % (prefix, prefix)), str(k)], stdout = PIPE)
    (o, e) = proc.communicate()
    f.write(o)
    proc.wait()
    f.close()

    if html_path:
        generateClusterK(k, prefix, research_path, html_path, paper, minimum, 'vcluster_tfidf')


def getStats(lda_folder, scluster_folder):
    pass
    
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-k', '--kval', dest = 'k',
                      help = 'the desired number of clusters for the data')
    parser.add_option('-p', '--prefix', dest = 'prefix',
                      help = 'prefix of the input and output files')
    parser.add_option('-c', '--cluster', dest = 'cluster',
                      help = 'clustering algorithm ["scluster", "lda", "vcluster"]')
    parser.add_option('-r', '--research', dest = 'research',
                      help = 'research path for data and cluster programs')
    parser.add_option('-d', '--directory', dest = 'directory', default = None,
                      help = 'html output directory')
    parser.add_option('-t', '--threshold', dest = 'threshold', default = 0,
                      help = 'only display nodes that have degree > threshold')
    parser.add_option('-m', '--module', dest = 'module', default = None,
                      help = 'module to access serialized data structure and to generate html code')
    parser.add_option('-n', '--nographics', dest = 'nographics', default = False,
                      action='store_true', help = 'disable graphics for cluster visualization')
                      

    (options, args) = parser.parse_args()

    no_graphics = options.nographics

    data_module = __import__(options.module)
    
    eval(options.cluster)(int(options.k), options.prefix, options.research, options.directory, data_module, int(options.threshold))
