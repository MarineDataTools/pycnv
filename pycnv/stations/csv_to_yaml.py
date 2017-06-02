import yaml

f = open('iow_stations.csv')
f2 = open('iow_stations.yaml','w')

stations = {'stations':[]}

for l in f:
    ll      = l.split('\t')
    name    = ll[0]
    lon     = float(ll[1].replace(',','.'))
    lat     = float(ll[2].replace(',','.'))
    country = ll[3]
    print(name,lon,lat,country)
    st = {'name': name,'latitude':lat,'longitude':lon}#,'country':country}
    stations['stations'].append(st)

#e = {'name': 'Two','Hallo':'peter'}
#stations['stations'].append(d)
#stations['stations'].append(e)
#print(e['stations'][1])
#f = '../rules/standard_names.yaml'
#rules = yaml.safe_load(open(f))
#print(rules)
#print(d)

d = yaml.dump(stations,default_flow_style=False)
e = yaml.safe_load(d)
f2.write(d)
f2.close()


