import web
from web import form

from os import mkdir
from os import walk
from os import system
from os.path import abspath
from os.path import join
from random import randint
from re import search
from re import match
from sys import argv
from sys import path
from threading import enumerate
from threading import Thread

import threading

from abstractparser import create_outputs
from abstractparser import create_outputs1
from main_form import *
from stats import *

import paper
import runcluster

web.config.debug = True

urls = ('/', 'main', 
        '/scluster', 'scluster', 
        '/lda', 'lda', 
        '/scluster_results', 'scluster_results',
        '/degree_compare', 'degree_compare',
        '/lda_scluster', 'lda_scluster',
        '/van_graph', 'van_graph',
        '/scluster_vs_vcluster', 'scluster_vs_vcluster',
        '/scluster_vs_vcluster_tfidf', 'scluster_vs_vcluster_tfidf')

class main:
    def GET(self):
        return render.main(getDatasetForm(), getJobInputForm(), 
                           getHighDegreeTestForm(), getLdaSclusterForm(),
                           getSclusterVsVclusterForm(), getSclusterVsVclusterTfidfForm())

    def POST(self):
        dataset_form_ = getDatasetForm()
        high_degree_form_ = getHighDegreeTestForm()
        job_input_form_ = getJobInputForm()
        lda_scluster_form_ = getLdaSclusterForm()
        scluster_vs_vcluster_form_ = getSclusterVsVclusterForm()
        scluster_vs_vcluster_tfidf_form_ = getSclusterVsVclusterTfidfForm()

        if dataset_form_.validates():
            handle_dataset_form(dataset_form_)
            
        if (job_input_form_.validates() and 
            job_input_form_[request_button_txt].value == 'submit!'):
            handle_job_input_form(job_input_form_)

        if (high_degree_form_.validates() and
            high_degree_form_[high_degree_button_txt].value == 'submit!'):
            handle_high_degree_form(high_degree_form_)

        if (lda_scluster_form_.validates() and
            lda_scluster_form_[lda_scluster_button_txt].value == 'submit!'):
            handle_lda_scluster_form(lda_scluster_form_)

        if (scluster_vs_vcluster_form_.validates() and
            scluster_vs_vcluster_form_[sv_button_txt].value == 'submit!'):
            handle_scluster_vs_vcluster_form(scluster_vs_vcluster_form_)

        if (scluster_vs_vcluster_tfidf_form_.validates() and
            scluster_vs_vcluster_tfidf_form_[sv_tfidf_button_txt].value == 'submit!'):
            handle_scluster_vs_vcluster_tfidf_form(scluster_vs_vcluster_tfidf_form_)

        return render.main(getDatasetForm(), getJobInputForm(), 
                           getHighDegreeTestForm(), getLdaSclusterForm(),
                           getSclusterVsVclusterForm(), getSclusterVsVclusterTfidfForm())

class lda_scluster:
    def GET(self):
        user_data = web.input()
        return render.lda_scluster(getLdaSclusterResultForm(
                user_data.prefix, user_data.lda_k, user_data.scluster_k))

    def POST(self):
        user_data = web.input()
        return render.lda_scluster(getLdaSclusterResultForm(
                user_data.prefix, user_data.lda_k, user_data.scluster_k))    
class scluster:
    def GET(self):
        return render.scluster(getSclusterForm())

    def POST(self):
        return render.scluster(getSclusterForm())

class lda:
    def GET(self):
        return render.lda(getLdaForm())

    def POST(self):
        return render.lda(getLdaForm())

class scluster_results:
    def GET(self):
        user_data = web.input()
        t = user_data.r.split('-')
        (f1, f2) = (t[0], t[1])
        return render.scluster_results(
            f2, getSclusterResultForm('server/static/data/scluster/%s/%s/' % 
                                      (f1, f2)),
            '%s-results-%s-S.js' % (f1, f2), False)

    def POST(self):
        return None

class vcluster_results:
    def GET(self):
        user_data = web.input()
        t = user_data.r.split('-')
        (f1, f2) = (t[0], t[1])
        return render.vcluster_results(
            f2, getVclusterResultForm('server/static/data/vcluster/%s/%s/' % 
                                      (f1, f2)),
            '%s-results-%s-V.js' % (f1, f2), False)

    def POST(self):
        return None

class degree_compare:
    def GET(self):
        user_data = web.input()
        t = getDegreeComparison(user_data.prefix1, user_data.prefix2,
                                int(user_data.k), int(user_data.l))
        return render.degree_compare(t)

    def POST(self):
        user_data = web.input()
        t = getDegreeComparison(user_data.prefix1, user_data.prefix2,
                                int(user_data.k), int(user_data.l))
        return render.degree_compare(t)

class scluster_vs_vcluster:
    def GET(self):
        user_data = web.input()
        t = getSclusterVsVcluster(user_data.prefix, int(user_data.k))
        return render.scluster_vs_vcluster(t)
    
    def POST(self):
        return self.GET()

class scluster_vs_vcluster_tfidf:
    def GET(self):
        user_data = web.input()
        t = getSclusterVsVclusterTfidf(user_data.prefix, int(user_data.k))
        return render.scluster_vs_vcluster_tfidf(t)

    def POST(self):
        return self.get()

class van_graph:
    def GET(self):
        user_data = web.input()
        prefix1 = user_data.prefix1
        prefix2 = user_data.prefix2
        k = user_data.k
        l = user_data.l
        
        cell = user_data.cell.split('@')
        c1 = int(cell[1])
        c2 = int(eval(cell[2])[0])
        c1_tag = cell[4]
        c2_tag = cell[5]
        (data_paths, names, colors) = getVanGraphDataPath(prefix1, prefix2, k, l, c1, c2, c1_tag, c2_tag)
        return render.van_graph(data_paths, names, colors, k)
    
    def POST(self):
        return self.GET()

def run(p):
    global app, render

    parent_folder = abspath('..')
    if parent_folder not in path:
        path.insert(0, parent_folder)

    app = web.application(urls, globals(), True)
    render = web.template.render(join(p, 'templates/'))
    app.run()

if __name__ == '__main__':
    global app, render
    app = web.application(urls, globals(), True)
    render = web.template.render('templates/')
    app.run()
