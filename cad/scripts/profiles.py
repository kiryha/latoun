"""Read current source profiles and simplify decorative outlines."""
import math
import json


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



def input_loop(name):
    from sw_helpers import INPUT
    path=INPUT/'profiles'/(name+'.json')
    data=json.loads(path.read_text())
    return [tuple(p[:2]) for p in data['loops'][0]['points_mm']]
