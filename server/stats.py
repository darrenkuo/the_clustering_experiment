import web
from web import form

from os import mkdir
from os.path import join
from re import match

import unicodedata

def getLdaSclusterResultForm(prefix, lda_k, scluster_k):
    f = open('server/static/data/lda/%s/%s/final.other' % 
             (prefix, lda_k), 'r')
    alpha = float(f.read().split('\n')[-2].split()[1])
    f.close()
    
    f = open('server/static/data/lda/%s/%s/final.gamma' % 
             (prefix, lda_k), 'r')
    topic_scores = map(lambda x: normalize(map(lambda y: float(y)-alpha, 
                                               x.split())), 
                       f.read().split('\n')[:-1])
    f.close()
    
    f = open('data/%s/%s.index' % (prefix, prefix), 'r')
    indices = f.read().split()
    f.close()
    
    f = open('data/%s/%s.out.clustering.%s' % (prefix, prefix, scluster_k), 
             'r')
    clusters = map(int, f.read().split())
    f.close()
        
    avg_results = []
    for i in range(int(scluster_k)):
        avg_results.append([0.0] * int(lda_k))
        
    total = [0] * int(scluster_k)
    
    data = zip(clusters, topic_scores)
    for i, j in data:
        total[int(i)] += 1
        avg_results[i] = map(lambda x: x[0] + x[1], zip(j, avg_results[i]))

    for i in range(len(total)):
        for j in range(len(avg_results[i])):
            avg_results[i][j] /= float(total[i])

    t = avg_results
    for i in t:
        s = float(sum(i))
        for j in range(len(i)):
            i[j] /= s

    sim_results = dict([(i, []) for i in range(int(scluster_k))])
    for i, j in data:
        sim_results[i].append(j)

    in_sims = [0.0] * int(scluster_k)
    ex_sims = [0.0] * int(scluster_k)

    total = 0
    total_sim = 0.0
    for i in sim_results:
        t = 0
        for j in range(len(sim_results[i])):
            for k in range(len(sim_results[i])):
                if j != k:
                    t += 1
                    in_sims[i] += dot(sim_results[i][j], sim_results[i][k])**2
        total += t
        total_sim += in_sims[i]
        in_sims[i] /= float(t)

    for i in sim_results:
        t = 0
        for a in sim_results[i]:
            for j in sim_results:
                if i != j:
                    for b in sim_results[j]:
                        t += 1
                        ex_sims[i] += dot(a, b)**2
        total_sim += ex_sims[i]
        total += t
        ex_sims[i] /= float(t)
    
    global_sim = (total_sim/float(total))

    sim_category = range(int(scluster_k))

    total = [0] * int(scluster_k)
    for c in clusters:
        total[int(c)] += 1

    mat = []
    for t in range(0, len(topic_scores[0])):
        mat.append([0] * int(scluster_k))

    top = 20
    for i in range(0, len(topic_scores[0])):
        l = sorted(data, key=lambda x: x[1][i])[0:top]
        for j in l:
            mat[i][j[0]] += 1

    mat = transpose(mat)
    for j in mat:
        s = float(sum(j))
        for x in range(len(j)):
            j[x] /= s

    components = [form.Table('normalize average topic scores', 
                             h_category=range(int(lda_k)),
                             v_category=[i for i in range(len(avg_results))],
                             cross='lda/scluster',
                             use_id=True, pairs=avg_results, 
                             border="1", cellspacing="0", cellpadding="3",),
                  form.tr(''), form.tr(''),
                  form.Table('average internal similarities',
                             h_category=sim_category,
                             pairs=[in_sims], use_id=True,
                             border="1", cellspacing="0", cellpadding="3",),
                  form.tr(''), form.tr(''),
                  form.Table('internal ratio', h_category=sim_category, 
                             use_id=True,
                             pairs=[map(lambda x: x/global_sim, in_sims)],
                             border="1", cellspacing="0", cellpadding="3",),
                  form.tr(''), form.tr(''),
                  form.Table('average external similarities', 
                             h_category=sim_category,
                             pairs=[ex_sims], use_id=True,
                             border="1", cellspacing="0", cellpadding="3",),
                  form.tr(''), form.tr(''),
                  form.Table('external ratio', h_category=sim_category,
                             use_id=True,
                             pairs=[map(lambda x: x/global_sim, ex_sims)],
                             border="1", cellspacing="0", cellpadding="3",),
                  form.tr(''), form.tr(''),
                  form.Table('#docs among top 20 in topic i that are in cluster j normalized by the number of nodes in each scluster:', 
                             h_category=range(int(lda_k)), pairs=mat,
                             v_category=[i for i in range(len(mat))],
                             use_id = True, cross='lda/scluster',
                             border="1", cellspacing="0", cellpadding="3",),
                  form.tr(''),                  
                  ]
    js = form.js('script', 'function create_graph(id) { alert(id);}')

    return apply(form.Form, components, {'js': js})()


# helper function
def getDatasetInfo():
    f = open('data/data.serialize', 'r')
    data = eval(f.read())
    f.close()
    return data

def getLdaDataset():
    results = []
    lda_dir = join('server', 'static', 'data', 'lda')
    for d in walk(lda_dir).next()[1]:
        for e in walk(join(lda_dir, d)).next()[1]:
            results.append(d + ' - ' + e)

    return results

def normalize(lst):
    #return lst
    s = sum(map(lambda x: x**2, lst))**0.5
    return map(lambda x: x/s, lst)

def transpose(mat):
    lst = [[] for i in range(len(mat[0]))]
    return [map(lambda x:x[i], mat) for i in range(len(lst))]

def dot(lst1, lst2):
    s = 0
    for i in range(len(lst1)):
        s += (lst1[i] * lst2[i])
    return s

def make_html_path(prog, prefix, k):
    html_path = join('server', 'static', 'data', prog, prefix, k)
    print 'trying to make path', html_path
    try:
        mkdir(join('server', 'static', 'data', prog, prefix))
    except:
        print '%s is already created' % (join('server', 'static', 'data', 
                                              prog, prefix))
        
    try:
        mkdir(html_path)
    except:
        print '%s is already created' % (html_path)

    return html_path

def handle_scluster_vs_vcluster_tfidf_form(scluster_vs_vcluster_tfidf_form_):
    prefix = scluster_vs_vcluster_tfidf_form_['sv-tfidf-dataset'].value
    k = scluster_vs_vcluster_tfidf_form_['sv-tfidf-k'].value

    from runcluster import scluster, vcluster_tfidf
    import paper

    print "running scluster on %s with cluster %s" % (prefix, k)
    s_html_path = make_html_path('scluster', prefix, k)
    scluster(int(k), prefix, '.', s_html_path, paper, 0)

    print "running vcluster on %s with cluster %s" % (prefix, k)
    v_html_path = make_html_path('vcluster_tfidf', prefix, k)
    vcluster_tfidf(int(k), prefix, '.', v_html_path, paper, 0)
    raise web.seeother('/scluster_vs_vcluster_tfidf?prefix=%s&k=%s' % (prefix, k))

def handle_scluster_vs_vcluster_form(scluster_vs_vcluster_form_):
    prefix = scluster_vs_vcluster_form_['sv-dataset'].value
    k = scluster_vs_vcluster_form_['sv-k'].value

    from runcluster import scluster, vcluster
    import paper

    print "running scluster on %s with cluster %s" % (prefix, k)
    s_html_path = make_html_path('scluster', prefix, k)
    scluster(int(k), prefix, '.', s_html_path, paper, 0)

    print "running vcluster on %s with cluster %s" % (prefix, k)
    v_html_path = make_html_path('vcluster', prefix, k)
    vcluster(int(k), prefix, '.', v_html_path, paper, 0)
    raise web.seeother('/scluster_vs_vcluster?prefix=%s&k=%s' % (prefix, k))
    

def handle_high_degree_form(high_degree_form_):
    prefix = high_degree_form_['high-degree-dataset'].value
    l = high_degree_form_['high-degree-l'].value
    k = high_degree_form_['high-degree-k'].value
    new_prefix = '_'.join(prefix.split('_')[:-1]) + '_' + l
    
    from runcluster import scluster
    from abstractparser import create_outputs1
    import paper
    
    create_outputs1(prefix, 'data', new_prefix, int(l))
    
    html_path = make_html_path('scluster', prefix, k)
    scluster(int(k), prefix, '.', html_path, paper, 0)
    
    html_path = make_html_path('scluster', new_prefix, k)
    scluster(int(k), new_prefix, '.', html_path, paper, 0)
    raise web.seeother('/degree_compare?prefix1=%s&prefix2=%s&k=%s&l=%s' % (prefix, new_prefix, k, l))

def handle_lda_scluster_form(lda_scluster_form_):
    prefix = lda_scluster_form_['lda-scluster-dataset'].value
    lda_k = lda_scluster_form_['lda-k'].value
    scluster_k = lda_scluster_form_['scluster-k'].value
    
    from runcluster import scluster
    from runcluster import lda
    import paper
    
    html_path = make_html_path('scluster', prefix, scluster_k)
    scluster(int(scluster_k), prefix, '.', html_path, paper, 0)
    
    html_path = make_html_path('lda', prefix, lda_k)
    lda(int(lda_k), prefix, '.', html_path, paper, 0)
    
    raise web.seeother('/lda_scluster?prefix=%s&lda_k=%s&scluster_k=%s' %
                       (prefix, lda_k, scluster_k))

def getMatches(lines):
    WORDS = '[a-zA-Z]+'
    SPACES = '[\s]+'
    NUMBERS = '[\d]+'
    SIM = '[+-\.\d]+'

    matches = []
    category_regex = ('[\s]*' + '(%s)' % (WORDS) + SPACES + '(%s)' % (WORDS) +
                      SPACES + '(%s)' % (WORDS) + SPACES + '(%s)' % (WORDS) +
                      SPACES + '(%s)' % (WORDS) + SPACES + '(%s)' % (WORDS) + 
                      SPACES + '|' + SPACES + '\n' )

    stats_regex = (SPACES + '(%s)' % (NUMBERS) + SPACES + '(%s)' % (NUMBERS) +
                   SPACES + '(%s)' % (SIM) + SPACES + '(%s)' % (SIM) +
                   SPACES + '(%s)' % (SIM) + SPACES + '(%s)' % (SIM) + 
                   SPACES + '|' + SPACES + '\n' )
    category = None
    for x in lines:
        y = match(stats_regex, x)
        if y:
            matches.append(list(y.groups()))
        else:
            y = match(category_regex, x)
            if y:
                category = list(y.groups())

    return (matches, category)

def getSclusterVsVclusterTfidf(prefix, k):
    format_float = '%.5f'

    from runcluster import filterWithI
    results = filterWithI(prefix, k, 0, 'abstract.matrix')

    f = open('data/%s/%s.out.clustering.%s.output' % (prefix, prefix, k), 'r')
    g = open('data/%s/%s.abstract.matrix.clustering.%s.output' % (prefix, prefix, k), 'r')

    s_stats = f.read().split('\n')
    v_stats = g.read().split('\n')

    (s_matches, category) = getMatches(s_stats)
    (v_matches, _) = getMatches(v_stats)

    f.close()
    g.close()

    f = open('data/%s/%s.out.clustering.%s' % (prefix, prefix, k), 'r')
    g = open('data/%s/%s.abstract.matrix.clustering.%s' % (prefix, prefix, k), 'r')

    clusters1 = f.read().split()
    clusters2 = g.read().split()

    total1 = [0] * (int(k))
    total2 = [0] * (int(k))

    for i in clusters1:
        total1[int(i)] += 1

    for i in clusters2:
        total2[int(i)] += 1

    total = results['total']

    cov = [[0] * (int(k)) for i in range(int(k))]
    for i, j in zip(clusters1, clusters2):
        cov[int(i)][int(j)] += 1
    
    total_nodes = sum(total)

    cov1 = []
    for i in cov:
        s = float(sum(i))
        lst = []
        for j in range(len(i)):
            lst.append(i[j] / s)
            i[j] /= s
            i[j] -= (total[j]/float(total_nodes))
        cov1.append(lst)

    fractions = [j/float(total_nodes) for j in total]

    print 'total', total
    g0_similarities = map(lambda x: [x], total)
    map(lambda x: x[0].extend(x[1]), 
        zip(g0_similarities, 
            results['g0-similarities']))
    tmp = [(i, g0_similarities[i]) for i in range(len(g0_similarities))]
    tmp = sorted(tmp, key=lambda x: -x[1][0])
    g0_similarities = map(lambda x: x[1], tmp)
    g0_v_category = map(lambda x: x[0], tmp)

    for i in g0_similarities:
        for j in range(2, len(i)):
            sign = '-'
            if i[j] > 0:
                sign = '+'
            i[j] = sign + format_float % i[j]

    g0_category = list(category)
    g0_category.pop(3)
    g0_category.pop(4)
    g0_category.pop(0)

    print_cov = []
    for i in cov:
        lst = []
        for j in i:
            lst.append(format_float % j)
        print_cov.append(lst)

    components = [#form.Table('Ref stats', use_id=True, border="1", 
                  #           cellspacing="0", cellpadding="3",
                  #           h_category=range(int(k)),
                  #           v_category=['in-stats', 'out-stats', 'total-nodes'],
                  #           pairs=[results['in-stats'], results['out-stats'],
                  #                  results['total']]),
                  #form.tr(''),
                  #form.tr(''),
                  form.Table('SCluster Similarities', use_id=True, border="1", 
                             cellspacing="0", cellpadding="3", 
                             h_category=category, v_category=range(len(s_matches)),
                             pairs=s_matches),
                  form.tr(''),
                  form.tr(''),
                  form.Table('VCluster Similarities', use_id=True, 
                             border="1", cellspacing="0", cellpadding="3",
                             v_category=range(len(v_matches)),
                             h_category=category, pairs = v_matches),
                  form.tr(''),
                  form.tr(''),
                  form.Table('G0 Similarities', use_id=True, border="1", 
                             cellspacing="0", cellpadding="3", 
                             h_category=g0_category, v_category=g0_v_category,
                             cross='cid', pairs=g0_similarities),
                  form.tr(''),
                  form.tr(''),
                  form.Table('Total', use_id=True, border="1", 
                             cellspacing="0", cellpadding="3",
                             h_category=range(0, len(total)), pairs=[total]),
                  form.tr(''),
                  form.Table('Total1', use_id=True, border="1", 
                             cellspacing="0", cellpadding="3",
                             h_category=range(0, len(total1)), pairs=[total1]),
                  form.tr(''),

                  form.Table('Total2', use_id=True, border="1", 
                             cellspacing="0", cellpadding="3",
                             h_category=range(0, len(total2)), pairs=[total2]),
                  form.tr(''),

                  form.Table('fractions', use_id=True, border="1", 
                             cellspacing="0", cellpadding="3",
                             h_category=range(0, len(fractions)), pairs=[fractions]),
                  form.tr(''),
                  
                  
                  form.Table('Cov', use_id=True, border="1", 
                             cellspacing="0", cellpadding="3",
                             h_category=range(0, int(k)), pairs = print_cov),
                  form.tr(''),
                  #form.Table('Cov', use_id=True, border="1", 
                  #           cellspacing="0", cellpadding="3",
                  #           h_category=range(0, int(k)), pairs = cov1),
                  #form.tr(''),

                  ]

    j = 0
    for i in cov:
        r = sorted(zip(i, range(0, int(k))), key=lambda x: -x[0])

        pairs = map(lambda x: format_float % (x[0]), r)
        cate = map(lambda x: str((x[1], format_float % fractions[x[1]])), r)
        
        components.append(form.Table('cov%d' % (j), border="1",
                                     cellspacing="0", cellpadding="3",
                                     h_category=cate, v_category=[j],
                                     pairs=[pairs],
                                     use_id=True))
        j += 1
        components.append(form.tr(''))
    
    variables = 'var link = "/van_graph?prefix1=%s&prefix2=%s&k=%s&l=0";\n' % (prefix, prefix, k)
    js = form.js('script', variables + 'function create_graph(id) { window.open(link + "&cell=" + id + "@s@v_tfidf");}\n')

    return apply(form.Form, components, {'js':js})()


def getSclusterVsVcluster(prefix, k):
    format_float = '%.5f'

    f = open('data/%s/%s.out.clustering.%s.output' % (prefix, prefix, k), 'r')
    g = open('data/%s/%s.mat.clustering.%s.output' % (prefix, prefix, k), 'r')

    s_stats = f.read().split('\n')
    v_stats = g.read().split('\n')

    (s_matches, category) = getMatches(s_stats)
    (v_matches, _) = getMatches(v_stats)

    f.close()
    g.close()

    f = open('data/%s/%s.out.clustering.%s' % (prefix, prefix, k), 'r')
    g = open('data/%s/%s.mat.clustering.%s' % (prefix, prefix, k), 'r')


    clusters1 = f.read().split()
    clusters2 = g.read().split()

    cov = [[0] * (int(k)+1) for i in range(int(k))]
    for i, j in zip(clusters1, clusters2):
        cov[int(i)][int(j)+1] += 1
    
    total = [0] * (int(k)+1)
    for c in clusters2:
        total[int(c)+1] += 1
    
    total_nodes = sum(total)
    for i in cov:
        s = float(sum(i))
        for j in range(len(i)):
            i[j] /= s
            i[j] -= (total[j]/float(total_nodes))

    fractions = [j/float(total_nodes) for j in total]

    print_cov = []
    for i in cov:
        lst = []
        for j in i:
            lst.append(format_float % j)
        print_cov.append(lst)
        
    components = [#form.Table('Ref stats', use_id=True, border="1", 
                  #           cellspacing="0", cellpadding="3",
                  #           h_category=range(int(k)),
                  #           v_category=['in-stats', 'out-stats', 'total-nodes'],
                  #           pairs=[results['in-stats'], results['out-stats'],
                  #                  results['total']]),
                  #form.tr(''),
                  #form.tr(''),
                  form.Table('SCluster Similarities', use_id=True, border="1", 
                             cellspacing="0", cellpadding="3", 
                             h_category=category, v_category=range(len(s_matches)),
                             pairs=s_matches),
                  form.tr(''),
                  form.tr(''),
                  form.Table('VCluster Similarities', use_id=True, 
                             border="1", cellspacing="0", cellpadding="3",
                             v_category=range(len(v_matches)),
                             h_category=category, pairs = v_matches),
                  form.tr(''),
                  form.Table('Cov', use_id=True, border="1", 
                             cellspacing="0", cellpadding="3",
                             h_category=range(-1, int(k)), pairs = print_cov),
                  form.tr(''),
                  ]

    j = 0
    for i in cov:
        r = sorted(zip(i, range(-1, int(k))), key=lambda x: -x[0])

        pairs = map(lambda x: format_float % (x[0]), r)
        cate = map(lambda x: str((x[1], format_float % fractions[x[1]])), r)
        
        components.append(form.Table('cov%d' % (j), border="1",
                                     cellspacing="0", cellpadding="3",
                                     h_category=cate, v_category=[j],
                                     pairs=[pairs],
                                     use_id=True))
        j += 1
        components.append(form.tr(''))
    
    variables = 'var link = "/van_graph?prefix1=%s&prefix2=%s&k=%s&l=%s";\n' % (prefix, prefix, k, 0)
    js = form.js('script', variables + 'function create_graph(id) { window.open(link + "&cell=" + id + "@s@v");}\n')

    return apply(form.Form, components, {'js':js})()

def getDegreeComparison(prefix1, prefix2, k, l):
    format_float = '%.5f'

    from runcluster import filterWithI
    results = filterWithI(prefix1, k, l, 'out')
    results['g0-similarities'] = [map(lambda x: x[i], 
                                      results['g0-similarities']) 
                                  for i in range(2)] 

    WORDS = '[a-zA-Z]+'
    SPACES = '[\s]+'
    NUMBERS = '[\d]+'
    SIM = '[+-\.\d]+'

    f = open('data/%s/%s.out.clustering.%s.output' % 
             (prefix2, prefix2, k), 'r')
    g = open('data/%s/%s.out.clustering.%s' % (prefix2, prefix2, k), 'r')

    clusters1 = results['new_clusters']
    clusters2 = g.read().split()

    cov = [[0] * int(k) for i in range(int(k))]
    for i, j in zip(clusters1, clusters2):
        cov[int(i)][int(j)] += 1
    
    total = results['total']
    total_nodes = sum(total)
    for i in cov:
        s = float(sum(i))
        for j in range(len(i)):
            i[j] /= s
            i[j] -= (total[j]/float(total_nodes))

    fractions = [j/float(total_nodes) for j in total]

    matches = []
    category_regex = ('[\s]*' + '(%s)' % (WORDS) + SPACES + '(%s)' % (WORDS) +
                      SPACES + '(%s)' % (WORDS) + SPACES + '(%s)' % (WORDS) +
                      SPACES + '(%s)' % (WORDS) + SPACES + '(%s)' % (WORDS) + 
                      SPACES + '|' + SPACES + '\n' )

    stats_regex = (SPACES + '(%s)' % (NUMBERS) + SPACES + '(%s)' % (NUMBERS) +
                   SPACES + '(%s)' % (SIM) + SPACES + '(%s)' % (SIM) +
                   SPACES + '(%s)' % (SIM) + SPACES + '(%s)' % (SIM) + 
                   SPACES + '|' + SPACES + '\n' )
    category = None
    for x in f:
        y = match(stats_regex, x)
        if y:
            matches.append(list(y.groups()))
        else:
            y = match(category_regex, x)
            if y:
                category = list(y.groups())

    g0_similarities = map(lambda x: [x], total)
    map(lambda x: x[0].extend(x[1]), 
        zip(g0_similarities, 
            transpose(results['g0-similarities'])))
    tmp = [(i, g0_similarities[i]) for i in range(len(g0_similarities))]
    tmp = sorted(tmp, key=lambda x: -x[1][0])
    g0_similarities = map(lambda x: x[1], tmp)
    g0_v_category = map(lambda x: x[0], tmp)

    for i in g0_similarities:
        for j in range(2, len(i)):
            sign = '-'
            if i[j] > 0:
                sign = '+'
            i[j] = sign + format_float % i[j]

    g0_category = list(category)
    g0_category.pop(3)
    g0_category.pop(4)

    print_cov = []
    for i in cov:
        lst = [i[0]]
        for j in i[1:]:
            lst.append(format_float % j)
        print_cov.append(lst)

    components = [form.Table('Ref stats', use_id=True, border="1", 
                             cellspacing="0", cellpadding="3",
                             h_category=range(int(k)),
                             v_category=['in-stats', 'out-stats', 'total-nodes'],
                             pairs=[results['in-stats'], results['out-stats'],
                                    results['total']]),
                  form.tr(''),
                  form.tr(''),
                  form.Table('G0 Similarities', use_id=True, border="1", 
                             cellspacing="0", cellpadding="3", 
                             h_category=g0_category, v_category=g0_v_category,
                             pairs=g0_similarities),
                  form.tr(''),
                  form.tr(''),
                  form.Table('G%s Similarities' % (l), use_id=True, 
                             border="1", cellspacing="0", cellpadding="3",
                             v_category=range(len(matches)),
                             h_category=category, pairs = matches),
                  form.tr(''),
                  form.Table('Cov', use_id=True, border="1", 
                             cellspacing="0", cellpadding="3",
                             h_category=range(int(k)), pairs = print_cov),
                  form.tr(''),
                  ]

    j = 0
    for i in cov:
        r = sorted(zip(i, range(int(k))), key=lambda x: -x[0])
        pairs = map(lambda x: format_float % (x[0]), r)
        cate = map(lambda x: str((x[1], format_float % fractions[x[1]])), r)
        
        components.append(form.Table('cov%d' % (j), border="1", 
                                     cellspacing="0", cellpadding="3",
                                     h_category=cate, v_category=[j],
                                     pairs=[pairs],
                                     use_id=True))
        j += 1
        components.append(form.tr(''))
        
    variables = 'var link = "/van_graph?prefix1=%s&prefix2=%s&k=%s&l=%s";\n' % (prefix1, prefix2, k, l)
    js = form.js('script', variables + 'function create_graph(id) { window.open(link + "&cell=" + id + "@s@s");}\n')

    return apply(form.Form, components, {'js':js})()

def getClusterAndIndex(prefix, k, tag):
    if tag == 's':
        f = open('data/%s/%s.out.clustering.%s' % (prefix, prefix, k), 'r')
    elif tag == 'v':
        f = open('data/%s/%s.mat.clustering.%s' % (prefix, prefix, k), 'r')
    else:
        f = open('data/%s/%s.abstract.matrix.clustering.%s' % (prefix, prefix, k), 'r')
    g = open('data/%s/%s.index' % (prefix, prefix), 'r')

    clusters = f.read().split()
    indices = g.read().split()

    f.close()
    g.close()
    return zip(indices, clusters)

def convertUnicode(s):
    return unicodedata.normalize('NFKD', s).encode('ascii','ignore')

def getVanGraphDataPath(prefix1, prefix2, k, l, c1, c2, c1_tag, c2_tag):
    data1 = getClusterAndIndex(prefix1, k, c1_tag)
    data2 = getClusterAndIndex(prefix2, k, c2_tag)

    cluster_lookup = {}
    ref_lookup = {}

    group1 = '%s %s' % (convertUnicode(prefix1), c1)
    group2 = '%s %s' % (convertUnicode(prefix2), c2)

    data1 = filter(lambda x: int(x[1]) == int(c1), data1)
    new_data1 = []
    for i, j in data1:
        f = open('data/%s/serialized/%s.serialize' % (prefix1, i))
        x = eval(f.read())
        f.close()
        
        if len(x['REF']) >= int(l):
            new_data1.append(i)
            cluster_lookup[i] = group1
            ref_lookup[i] = x['REF']

    common_cluster = max(c1, c2) + 1
    new_data2 = []
    new_data_common = []

    for i, j in data2:
        if int(j) == c2:
            new_data2.append(i)

            if i in cluster_lookup:
                cluster_lookup[i] = 'COMMON'
                new_data_common.append(i)
            else:
                cluster_lookup[i] = group2

            if i not in ref_lookup:
                f = open('data/%s/serialized/%s.serialize' % (prefix1, i))
                x = eval(f.read())
                f.close()
                ref_lookup[i] = x['REF']

    for i in ref_lookup:
        lst = filter(lambda x: x in ref_lookup, ref_lookup[i])
        ref_lookup[i] = lst

    nodes = set(new_data1).union(set(new_data2))
    new_mapping = dict(zip(nodes, range(len(nodes))))
    new_mapping1 = dict(zip(new_data1, range(len(new_data1))))
    new_mapping2 = dict(zip(new_data2, range(len(new_data2))))
    new_mapping_common = dict(zip(new_data_common, range(len(new_data_common))))

    results = {'nodes' : [{'nodeName' : i, 'group' : cluster_lookup[i]} for i in nodes],
               'links' : []}

    results1 = {'nodes' : [{'nodeName' : i, 'group' : cluster_lookup[i]} for i in new_data1],
                'links' : []}

    results2 = {'nodes' : [{'nodeName' : i, 'group' : cluster_lookup[i]} for i in new_data2],
                'links' : []}

    names = [group1, group2, 'COMMON']
    colors = ["RED", "BLUE", "GREEN"]

    results_common = {'nodes' : [{'nodeName' : i, 'group' : 'common'} for i in new_data_common],
                'links' : []}

    for i in ref_lookup:
        for r in ref_lookup[i]:
            results['links'].append({'source' : new_mapping[i], 'target' : new_mapping[r], 'value' : 1.0})

    for i in new_data1:
        for r in ref_lookup[i]:
            if r in new_data1:
                results1['links'].append({'source' : new_mapping1[i], 'target' : new_mapping1[r], 'value' : 1.0})

    for i in new_data2:
        for r in ref_lookup[i]:
            if r in new_data2:
                results2['links'].append({'source' : new_mapping2[i], 'target' : new_mapping2[r], 'value' : 1.0})

    for i in new_data_common:
        for r in ref_lookup[i]:
            if r in new_data_common:
                results_common['links'].append({'source' : new_mapping_common[i], 'target' : new_mapping_common[r], 'value' : 1.0})
                
    
    js_data_path = 'server/static/js/%s-%s-%s-%s-%s-%s.js' % (prefix1, prefix2, k, l, c1, c2)
    h = open(js_data_path, 'w')
    h.write('var data = %s;' % (str(results)))
    h.close()

    js_data_path_c1 = 'server/static/js/%s-%s-%s-%s-%s.js' % (prefix1, k, l, c1, c1_tag)
    h = open(js_data_path_c1, 'w')
    h.write('var data_c1 = %s;' % (str(results1)))
    h.close()

    js_data_path_c2 = 'server/static/js/%s-%s-%s-%s-%s.js' % (prefix2, k, l, c2, c2_tag)
    h = open(js_data_path_c2, 'w')
    h.write('var data_c2 = %s;' % (str(results2)))
    h.close()

    js_data_path_common = 'server/static/js/%s-%s-%s-%s-%s-%s-common.js' % (prefix1, prefix2, k, l, c1, c2)
    h = open(js_data_path_common, 'w')
    h.write('var data_common = %s;' % (str(results_common)))
    h.close()
    print 'common path', js_data_path_common

    return ([js_data_path.split('/')[-1], js_data_path_c1.split('/')[-1], 
            js_data_path_c2.split('/')[-1], js_data_path_common.split('/')[-1]], names, colors)
   
