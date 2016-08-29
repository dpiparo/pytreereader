#! /usr/bin/env python

import ROOT
from PyTreeReader import PyTreeReader
from timeit import default_timer as timer

h = ROOT.TH1F("h","h",1024,-200,200)
fill = h.Fill

f = ROOT.TFile("./hsimple.root")

start = timer()
for event in f.ntuple:
	fill(event.px*event.py*event.pz*event.random)
duration = timer() - start
print "PyROOT: %s" %duration

start = timer()
for event in PyTreeReader(f.ntuple,"*"):
	fill(event.px()*event.py()*event.pz()*event.random())
duration = timer() - start
print "PyTreeReader no cache: %s" %duration

start = timer()
ptr = PyTreeReader(f.ntuple,"*",cache=True)
duration = timer() - start
print "PyTreeReader build cache: %s" %duration

start = timer()
for event in ptr:
    fill(event.px()*event.py()*event.pz()*event.random())
duration = timer() - start
print "PyTreeReader with cache: %s" %duration

h.Draw()

for i in ptr.py_array(): print i
## Are we in need of a method to fill histos from vectors?


