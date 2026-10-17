"""Mathematical helpers extracted unchanged from the original harness."""
import json, hashlib, itertools
from pathlib import Path

def dump(p, obj):
    Path(p).write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')

def sha(b): return hashlib.sha256(b).hexdigest()

def validate(games):
    if not isinstance(games,list) or not games: raise ValueError('Expected nonempty list of games')
    ids, matrices = set(), set()
    for g in games:
        if not isinstance(g,dict): raise ValueError('Game must be object')
        ident=g.get('game_id',g.get('id'))
        if not isinstance(ident,str) or not ident or ident in ids: raise ValueError('Missing/duplicate string ID')
        ids.add(ident); p=g.get('payoffs')
        if not isinstance(p,list) or len(p)!=2 or any(not isinstance(r,list) or len(r)!=2 for r in p): raise ValueError('Expected payoffs[row][column][player]')
        if any(not isinstance(c,list) or len(c)!=2 for r in p for c in r): raise ValueError('Expected two payoffs per cell')
        for player in range(2):
            v=[p[r][c][player] for r in range(2) for c in range(2)]
            if any(type(x)!=int for x in v) or sorted(v)!=[1,2,3,4]: raise ValueError('Strict ordinal ranks must be exactly 1,2,3,4 per player')
        key=json.dumps(p)
        if key in matrices: raise ValueError('Duplicate payoff matrix')
        matrices.add(key)
    return games

def generated():
    games=[]
    for a,b in itertools.product(itertools.permutations(range(1,5)),repeat=2):
        games.append({'game_id':f'generated-{len(games):04d}', 'payoffs':[[[a[2*r+c],b[2*r+c]] for c in range(2)] for r in range(2)]})
    return games

def oracle(p):
    br={}
    for player,opp,act in itertools.product(range(2),repeat=3):
        v=lambda a: p[a][opp][0] if player==0 else p[opp][a][1]
        br[f'br_{player}_{opp}_{act}']=v(act)>=v(1-act)
    return {
        'pure_nash':{f'ne_{r}_{c}':br[f'br_0_{c}_{r}'] and br[f'br_1_{r}_{c}'] for r,c in itertools.product(range(2),repeat=2)},
        'strict_dominance':{f'dom_{pl}_{a}':all(br[f'br_{pl}_{o}_{a}'] for o in range(2)) for pl,a in itertools.product(range(2),repeat=2)},
        'best_response':br}

def request(p,task):
    state={'payoffs':p,'convention':'payoffs[row][column][player]; player 0 chooses row, player 1 chooses column. Actions are 0 and 1. Higher ranks are preferred.'}
    q={}
    if task=='pure_nash':
        for r,c in itertools.product(range(2),repeat=2):
            q[f'ne_{r}_{c}']={'type':'noul','instructions':f'Is (row {r}, column {c}) a pure Nash equilibrium, meaning neither player can improve their own payoff by unilaterally changing action?'}
    elif task=='strict_dominance':
        for pl,a in itertools.product(range(2),repeat=2):
            q[f'dom_{pl}_{a}']={'type':'noul','instructions':f'Does action {a} strictly dominate the other action for player {pl}, giving a strictly higher own payoff for each possible opponent action?'}
    else:
        for pl,o,a in itertools.product(range(2),repeat=3):
            q[f'br_{pl}_{o}_{a}']={'type':'noul','instructions':f'Is action {a} a best response for player {pl} when the opponent chooses action {o}, maximizing that player\'s own payoff?'}
    return {'state':state,'questions':q}
