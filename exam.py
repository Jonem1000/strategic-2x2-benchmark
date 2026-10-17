# SPDX-License-Identifier: Apache-2.0
"""Four-section exam: exact reference, native typed prompts and strict output parsing."""
from fractions import Fraction as F
import json, math
import ordinal
SECTIONS=('best_response','strict_dominance','pure_nash','level_k')
LABELS={'first':[1,0],'second':[0,1],'equal':[F(1,2),F(1,2)]}
def reference(case):
    p=case['payoffs'];section=case['section']
    if section!='level_k':return ordinal.oracle(p)[section]
    previous=[[F(str(v)) for v in dist] for dist in case['level_0']];out={}
    for k in range(1,4):
        nxt=[]
        for player in range(2):
            u=[sum(previous[1-player][o]*F(str(p[a][o][0] if player==0 else p[o][a][1])) for o in range(2)) for a in range(2)]
            label='equal' if abs(u[0]-u[1])<=F(1,10**10) else ('first' if u[0]>u[1] else 'second')
            out[f'p{player}k{k}']=label;nxt.append(LABELS[label])
        previous=nxt
    return out

def independent_reference(case):
    """Separate comparisons and integer-scaled recurrence; does not call primary oracle."""
    m=case['payoffs'];section=case['section'];out={}
    if section=='level_k':
        # Probabilities here are only 0, 1/2, 1; use twice their value.
        weights=[[int(F(str(v))*2) for v in d] for d in case['level_0']]
        for depth in (1,2,3):
            r0=weights[1][0]*m[0][0][0]+weights[1][1]*m[0][1][0]
            r1=weights[1][0]*m[1][0][0]+weights[1][1]*m[1][1][0]
            c0=weights[0][0]*m[0][0][1]+weights[0][1]*m[1][0][1]
            c1=weights[0][0]*m[0][1][1]+weights[0][1]*m[1][1][1]
            decisions=['equal' if x==y else 'first' if x>y else 'second' for x,y in [(r0,r1),(c0,c1)]]
            weights=[{'equal':[1,1],'first':[2,0],'second':[0,2]}[d] for d in decisions]
            for player in (0,1):out[f'p{player}k{depth}']=decisions[player]
        return out
    if section=='pure_nash':
        for r in (0,1):
            for c in (0,1):out[f'ne_{r}_{c}']=all(m[r][c][0]>=m[x][c][0] for x in (0,1)) and all(m[r][c][1]>=m[r][y][1] for y in (0,1))
    elif section=='strict_dominance':
        for a in (0,1):
            out[f'dom_0_{a}']=min(m[a][0][0]-m[1-a][0][0],m[a][1][0]-m[1-a][1][0])>0
            out[f'dom_1_{a}']=min(m[0][a][1]-m[0][1-a][1],m[1][a][1]-m[1][1-a][1])>0
    else:
        for opp in (0,1):
            for a in (0,1):
                out[f'br_0_{opp}_{a}']=m[a][opp][0]==max(m[0][opp][0],m[1][opp][0])
                out[f'br_1_{opp}_{a}']=m[opp][a][1]==max(m[opp][0][1],m[opp][1][1])
    return out

def payload(case):
    if case['section']=='level_k':return case['frozen_payload']
    return ordinal.request(case['payoffs'],case['section'])

from contracts import parse

def rows(path):return [json.loads(s) for s in path.read_text().splitlines()]
def jsonl(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(''.join(json.dumps(x,sort_keys=True,allow_nan=False)+'\n' for x in data))
