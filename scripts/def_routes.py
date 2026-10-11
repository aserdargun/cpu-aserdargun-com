"""Extract routed centerlines, respecting DEF wildcard coordinates across paths."""
import re

def route_segments(nets,unit):
    segments=[];count=0
    for net in re.finditer(r'^\s*-\s+(\S+)\s+(.*?);',nets,re.M|re.S):
        count+=1;last=None
        for path in re.finditer(r'(?:ROUTED|NEW)\s+(\S+)\s+(.+?)(?=\s+NEW |$)',net[2],re.S):
            previous=None
            for xy in re.finditer(r'\(\s+(-?\d+|\*)\s+(-?\d+|\*)(?:\s+-?\d+)?\s*\)',path[2]):
                if '*' in xy.groups() and last is None:raise ValueError(f'{net[1]}: wildcard without a prior coordinate')
                point=[last[i] if xy[i+1]=='*' else int(xy[i+1])/unit for i in range(2)]
                if previous is not None and point!=previous:segments.append([net[1],path[1],*previous,*point])
                previous=last=point
    return segments,count
