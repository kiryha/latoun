"""Read the supplied 004 DXF line profiles without changing the reference archive."""
import math
import zipfile
from collections import defaultdict
from pathlib import Path

ARCHIVE=Path(__file__).resolve().parents[1]/'inputs/004/LATOUN_004_nominal_CAD.zip'


def line_segments(name):
    with zipfile.ZipFile(ARCHIVE) as archive:
        text=archive.read('nominal_DXF/'+name+'.dxf').decode('ascii')
    rows=[s.strip() for s in text.splitlines() if s.strip()]
    pairs=list(zip(rows[::2],rows[1::2]))
    result=[]
    current={}
    kind=None
    for k,v in pairs+[('0','EOF')]:
        if k=='0':
            if kind=='LINE':
                result.append(((float(current['10']),float(current['20'])),
                               (float(current['11']),float(current['21']))))
            current={}
            kind=v
        else:
            current[k]=v
    return result


def ordered_loop(name):
    graph=defaultdict(set)
    positions={}
    for a,b in line_segments(name):
        ka,kb=tuple(round(v,4) for v in a),tuple(round(v,4) for v in b)
        if ka==kb:
            continue
        positions[ka],positions[kb]=a,b
        graph[ka].add(kb)
        graph[kb].add(ka)
    if any(len(neighbors)!=2 for neighbors in graph.values()):
        raise ValueError('Profile not a single clean loop: '+name)
    start=min(graph)
    order=[start]
    prev=None
    cur=start
    while True:
        nxt=next(k for k in sorted(graph[cur]) if k!=prev)
        if nxt==start:
            break
        order.append(nxt)
        prev,cur=cur,nxt
        if len(order)>len(graph):
            raise ValueError('Loop traversal failed')
    if len(order)!=len(graph):
        raise ValueError('Multiple loops in '+name)
    return [positions[k] for k in order]


def distance_to_segment(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]
    t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy)))
    return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)


def rdp(points,tolerance):
    if len(points)<=2:
        return points
    d,i=max((distance_to_segment(p,points[0],points[-1]),i) for i,p in enumerate(points[1:-1],1))
    if d<=tolerance:
        return [points[0],points[-1]]
    return rdp(points[:i+1],tolerance)[:-1]+rdp(points[i:],tolerance)


def simplified_loop(name,tolerance=.015):
    p=ordered_loop(name)
    opposite=max(range(1,len(p)),key=lambda i:math.dist(p[0],p[i]))
    q=rdp(p[:opposite+1],tolerance)[:-1]+rdp(p[opposite:]+p[:1],tolerance)[:-1]
    return q


if __name__=='__main__':
    for name in ('raised_L/Z29.001','raised_L/Z29.15','raised_L/Z29.299'):
        original=ordered_loop(name)
        simplified=simplified_loop(name)
        print(name,len(original),'points ->',len(simplified),'native sketch edges')
