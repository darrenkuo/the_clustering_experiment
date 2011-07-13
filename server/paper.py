from re import search

fields = ['AUTHOR', 'YEAR', 'CONF', 'INDEX', 'CITATION', 'ARNETID', 'ABSTRACT']
row = '<tr>\n\t<td>%s</td>\n\t<td>%s</td>\n</tr>\n'
in_link = '<a href="#%s">%s</a>'
out_link = '<a href="%s.html#%s">%s</a>'

def getID(mapping):
    return mapping['INDEX']

def getNeighbors(mapping):
    return mapping['REF']

def setNeighbors(mapping, neighbors):
    mapping['REF'] = neighbors

def build_scluster_html(f, pm, indexToCluster):
    global fields, row, in_link, out_link

    f.write('<h4><a name="%s">Information about %s</a></h4>\n' % (str(pm['INDEX']), pm['PAPERTITLE']))
    f.write('<table border="0">\n')

    [f.write(row % (field, pm[field])) for field in fields]
    
    f.write(row % ('IN-CLUSTER', ' '.join(map(lambda x: (in_link % (str(x), str(x))), 
                                              list(pm['IN-REF'])))))

    f.write(row % ('OUT-CLUSTER', " ".join(map(lambda x: (out_link % (str(indexToCluster[x]), str(x), str(x))), 
                                      list(pm['OUT-REF'])))))
    f.write("</table>\n<hr>\n")

build_vcluster_html = build_scluster_html
    
def build_lda_html(f, pm, lst):
    global fields, row, in_link, out_link

    f.write('<h4><a name="%s">Information about %s</a></h4>\n' % (str(pm['INDEX']), pm['PAPERTITLE']))
    f.write('<table border="0">\n')

    for field in fields:
        f.write(row % (field, highlight(pm[field], lst)))

    f.write(row % ('TOPIC SCORE', pm['TOPIC SCORE']))   
    
    f.write("</table>\n<hr>\n")

matches = 0
def highlight(txt, lst):
    global matches
    result = ''
    for w in txt.split():
        if matchWords(w, lst):
            matches += 1
            result += '<font color=red>%s</font> ' % (w)
        else:
            result += '%s ' % (w)
    return result

def matchWords(w, lst):
    for i in lst:
        if search(i ,w.lower()):
            return True
    return False
