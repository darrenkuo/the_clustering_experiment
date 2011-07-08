import web
from web import form

from os import walk
from os.path import join
from threading import Thread

import threading

from abstractparser import create_outputs
from abstractparser import create_outputs1

import runcluster
import paper

create_button_txt = 'Create dataset'
shrink_button_txt = 'Filter by degree'
merge_button_txt = 'Merge datasets'
request_button_txt = 'Run request'

def getDatasetInfo():
    f = open('data/data.serialize', 'r')
    data = eval(f.read())
    f.close()
    return data

def getDatasetForm():
    components = [form.Textarea('keywords', description='Filter by keywords:',
                                style='resize: none;', cols='50', rows='2'),
                  form.tr(""),
                  form.Textbox('prefix', style='resize: none;', size='50', 
                               description='Name for the dataset'),
                  form.tr(""),
                  form.Button(create_button_txt, 'submit', 
                              description='Create a new dataset', 
                              value='submit!'),
                  form.tr(""),
                  form.Dropdown('degree_dataset', 
                                map(lambda x: (x[0], x[0] + '-' + x[1]), 
                                    getDatasetInfo().items()), 
                                description='dataset:'),
                  form.tr(""),
                  form.Textbox('new_prefix', size='50',
                               description='Name for the new prefix'),
                  form.tr(""),
                  form.Textbox('threshold', value='0', 
                               style='resize: none;', 
                               size='5', row='1', 
                               description='Minimum degree'),
                  form.tr(""),
                  form.Button(shrink_button_txt, 'submit', 
                              description="Shrink by degree", 
                              value='submit!'),
                  form.tr(""),]

    new_components = []
    for i in getDatasetInfo().keys():
        new_components.append(form.Checkbox(i, 
                                            value='using dataset %s' % (i), 
                                            checked=False))
        new_components.append(form.tr(''))

    if new_components:
        components.extend(new_components)
        components.extend([form.Button(merge_button_txt, 'submit', 
                                       description='Submit merge request', 
                                       value='submit!'),
                           form.tr("")])
                  
    return apply(form.Form, components)()
    
def getJobInputForm(text=None):
    components = [form.Dropdown('dataset', map(lambda x: (x[0], x[0] + ' - ' + x[1]), 
                                               filter(lambda x: x[0].split('_')[-1] == '0', getDatasetInfo().items())), 
                                description='dataset:'),
                  form.tr(""),
                  form.Textbox('request_threshold', value='0', size='5', 
                               descrption='Minimum degree'),
                  form.tr(""),
                  form.Textbox('k', description='k:', size='5'),
                  form.tr(""),
                  form.Checkbox('scluster', value='run scluster', 
                                checked=False),
                  form.tr(""),
                  form.Checkbox('vcluster', value='run vcluster', 
                                checked=False),
                  form.tr(""),
                  form.Checkbox('lda', value='run lda', checked=False),
                  form.tr(''),
                  form.Button(request_button_txt, 'submit', 
                              description='submit', 
                              value='submit!')
                  ]
    if text:
        components.append(form.tr(""))
        components.append(form.Strong('wrong', text))

    return apply(form.Form, components)()

def getSclusterResultForm(folder):
    components = []
    for i in walk(folder).next()[2]:
        components.append(form.Link(i, link=join(folder, i), 
                                    value='cluster data'))
    return apply(form.Form, components)()
                   

def getSclusterForm():
    cluster_path = 'server/static/data/scluster/'
    results = []
    for x in walk(cluster_path).next()[1]:
        links = map(lambda y: form.Link('k = %s' % (y), 
                                        link='/scluster_results?r=%s' % (
                    '%s-%s' % (x, y)),
                                        value='cluster data'),
                    walk(join(cluster_path, x)).next()[1])
        results.append((x, apply(form.Form, links)()))

    return results
    
def getLdaForm():
    cluster_path = 'http://eecs.berkeley.edu/~darrenk/research/lda'
    clusters = filter(lambda x: search('results-[0-9]+', x),
                      walk('lda').next()[1])
    links = map(lambda x: form.Link('k = %s' %
                                    (match('results-([0-9]+)', 
                                           x).groups()[0]),
                                    link=join(cluster_path, 
                                              join(x, 'index.html')), 
                                    value='lda data'), clusters)
    brs = [form.tr("")] * len(clusters)
    components = [item for items in zip(links, brs) for item in items]
    return apply(form.Form, components)()

lda_scluster_button_txt = 'Get LDA Scluster Stats!'
def getLdaSclusterForm():
    # TODO: forloop data
    components = [form.Dropdown('lda-scluster-dataset', 
                                map(lambda x: (x[0], x[0] + ' - ' + x[1]), 
                                    filter(lambda x: x[0].split('_')[-1] == '0', 
                                           getDatasetInfo().items())), 
                                description="Dataset:"),
                  form.tr(''),
                  form.Textbox('lda-k', size='5', description='LDA k'),
                  form.tr(''),
                  form.Textbox('scluster-k', size='5', description='Scluster k'),
                  form.tr(''),
                  form.Button(lda_scluster_button_txt, 'submit', 
                              description='Get stats!', value='submit!'),
                  form.tr('')]

    return apply(form.Form, components)()

high_degree_button_txt = 'Compare with high degree'
def getHighDegreeTestForm():
    components = [form.Dropdown('high-degree-dataset', 
                                map(lambda x: (x[0], x[0] + ' - ' + x[1]), 
                                    filter(lambda x: x[0].split('_')[-1] == '0', 
                                           getDatasetInfo().items())), 
                                description="Dataset:"),
                  form.tr(''),
                  form.Textbox('high-degree-l', size='10', 
                               description='Degree to induce dataset1:'),
                  form.tr(''),
                  form.Textbox('high-degree-k', size='10', 
                               description='Number of clusters:'),
                  form.tr(''),
                  form.Button(high_degree_button_txt, 'submit', 
                              description="Submit high degree comparison request", 
                              value='submit!'),
                  form.tr('')]
    return apply(form.Form, components)()   

sv_button_txt = 'Compare Scluster with Vcluster'
def getSclusterVsVclusterForm():
    components = [form.Dropdown('sv-dataset', 
                                map(lambda x: (x[0], x[0] + ' - ' + x[1]), 
                                           getDatasetInfo().items()),
                                description="Dataset:"),
                  form.tr(''),
                  form.Textbox('sv-k', size='10', 
                               description='Number of clusters:'),
                  form.tr(''),
                  form.Button(sv_button_txt, 'submit', 
                              description="Submit Scluster and Vcluster comparison request", 
                              value='submit!'),
                  form.tr('')]
    return apply(form.Form, components)()   

sv_tfidf_button_txt = 'Compare Scluster with Vcluster TFIDF'
def getSclusterVsVclusterTfidfForm():
    components = [form.Dropdown('sv-tfidf-dataset', 
                                map(lambda x: (x[0], x[0] + ' - ' + x[1]), 
                                           getDatasetInfo().items()),
                                description="Dataset:"),
                  form.tr(''),
                  form.Textbox('sv-tfidf-k', size='10', 
                               description='Number of clusters:'),
                  form.tr(''),
                  form.Button(sv_tfidf_button_txt, 'submit', 
                              description="Submit Scluster and Vcluster TFIDF comparison request", 
                              value='submit!'),
                  form.tr('')]
    return apply(form.Form, components)()   

# form handlers
def handle_dataset_form(dataset_form_):
    keywords = dataset_form_['keywords'].value
    prefix = dataset_form_['prefix'].value
    
    if 'submit!' == dataset_form_[create_button_txt].value:
        print 'creating!'
        keywords = keywords.split()
        
        print 'before starting thread:', threading.enumerate()
        t = Thread(target=getThreadForCreateOutput(keywords, prefix, 
                                                   create_outputs), 
                   name=prefix)
        t.start()
        print 'thread started', threading.enumerate()
    elif 'submit!' == dataset_form_[shrink_button_txt].value:
        print 'shrinking!!'
        dataset = dataset_form_['degree_dataset'].value
        new_prefix = dataset_form_['new_prefix'].value
        threshold = int(dataset_form_['threshold'].value)
        
        create_outputs1(dataset, 'data', new_prefix, threshold)
        
    '''
    lst = check_checkboxes():
    if lst:
    t = Thread(target=getThreadForMerge(
    threshold = dataset_form_['threshold'].value
    
    '''

def handle_job_input_form(job_input_form_):

    progs = []
    if job_input_form_['scluster'].checked:
        progs.append('scluster')
    elif job_input_form_['vcluster'].checked:
        progs.append('vcluster')
    elif job_input_form_['lda'].checked:
        progs.append('lda')
        
    prefix = job_input_form_['dataset'].value
    th = job_input_form_['request_threshold'].value
    new_prefix = '_'.join(prefix.split('_')[:-1]) + '_' + th

    try:
        mkdir(join('data', new_prefx))
    except:
        print "%s is probably created" % (join('data', new_prefix))
                
    create_outputs1(prefix, 'data', new_prefix, int(th))

    prefix = new_prefix

    for prog in progs:
        web.debug('running %s with k = %s' % (
                prog, job_input_form_['k'].value))
        k = job_input_form_['k'].value
        html_path = join('server', 'static', 'data', prog, prefix, k)
        try:
            mkdir(join('server', 'static', 'data', prog, prefix))
        except:
            print '%s is already created' % (join('server', 'static',
                                                          'data', prog, 
                                                          prefix))
        try:
            mkdir(html_path)
        except:
            print '%s is already created' % (html_path)
                
        # make minimum dynamic!
        t = Thread(target=run_prog(eval('runcluster.' + prog), k, prefix, html_path, 
                                   paper), 
                   name='%s %s' % (prog, prefix))
        t.start()
        web.debug('started thread for running %s %s' % (prog, 
                                                        prefix))
        web.debug('Active threads: %s' % (threading.enumerate()))


#helper functions
def getThreadForCreateOutput(keywords, prefix, create_outputs):
    def create_output():
        create_outputs('data/all.txt', keywords, 'data', prefix)
        print "done creating output for keywords %s prefix %s" % (str(keywords), prefix)
        return 'done'
    return create_output

def check_checkboxes():
    pass

def run_prog(prog, k, prefix, html_path, paper):
    def run():
        prog(int(k), prefix, '.', html_path, paper, 0)
    return run
