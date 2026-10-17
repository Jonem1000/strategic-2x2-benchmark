"""Offline scorer: incomplete runs retain full denominators and no overall score."""
import argparse, collections, json, statistics
from pathlib import Path
import exam,ordinal
ROOT=Path(__file__).resolve().parent

def score(cases,key,predictions):
    lookup={c['case_id']:c for c in cases};pred={}
    for r in predictions:
        i=r['case_id']
        if i not in lookup or i in pred:raise ValueError('Unknown or duplicate prediction ID: '+i)
        pred[i]=r if r.get('status','ok')=='ok' else {k:v for k,v in r.items() if k not in ('answers','probabilities')}
    report={}
    for track in ['all','exclude_inferred_154']:
        selected=[c for c in cases if track=='all' or not c['inferred_154']];sections={}
        for section in exam.SECTIONS:
            subset=[c for c in selected if c['section']==section];correct=exact=valid=0;invalid=missing=0;briers=[];lat=[];by_level={str(k):{'correct':0,'total':len(subset)*2} for k in range(1,4)};by_ne=collections.defaultdict(lambda:{'cases':0,'exact':0})
            for c in subset:
                i=c['case_id'];gold=key[i];r=pred.get(i);a=r.get('answers') if r else None
                good=isinstance(a,dict) and set(a)==set(gold) and all(type(a[k])==type(v) and (type(v)==bool or a[k] in exam.LABELS) for k,v in gold.items())
                if c['section']=='pure_nash':by_ne[str(sum(gold.values()))]['cases']+=1
                if not r:missing+=1
                elif not good:invalid+=1
                if not good:continue
                valid+=1;correct+=sum(a[k]==v for k,v in gold.items());exact+=a==gold
                if section=='level_k':
                    for k in range(1,4):by_level[str(k)]['correct']+=sum(a[f'p{pl}k{k}']==gold[f'p{pl}k{k}'] for pl in range(2))
                if section=='pure_nash':by_ne[str(sum(gold.values()))]['exact']+=a==gold
                if 'elapsed_seconds' in r:lat.append(r['elapsed_seconds'])
                for k,dist in r.get('probabilities',{}).items():
                    if k not in gold:raise ValueError('Unexpected probability ID')
                    target=str(gold[k]).lower() if type(gold[k])==bool else gold[k]
                    # Binary Brier uses P(true); multiclass uses sum across categories.
                    briers.append((dist['true']-int(gold[k]))**2 if type(gold[k])==bool else sum((v-int(label==target))**2 for label,v in dist.items()))
            total=sum(len(key[c['case_id']]) for c in subset)
            sections[section]={'cases':len(subset),'valid_cases':valid,'missing':missing,'invalid':invalid,'perfect_cases':exact,'exact_accuracy_all':exact/len(subset) if subset else None,'correct_answers':correct,'total_answers':total,'answer_accuracy_all':correct/total if total else None,'answer_accuracy_valid':correct/sum(len(key[c['case_id']]) for c in subset if c['case_id'] in pred and isinstance(pred[c['case_id']].get('answers'),dict) and set(pred[c['case_id']]['answers'])==set(key[c['case_id']]) and all(type(pred[c['case_id']]['answers'][k])==type(v) and (type(v)==bool or pred[c['case_id']]['answers'][k] in exam.LABELS) for k,v in key[c['case_id']].items())) if valid else None,'brier_valid':statistics.mean(briers) if briers else None,'median_seconds_valid':statistics.median(lat) if lat else None}
            if section=='level_k':sections[section]['by_level']=by_level
            if section=='pure_nash':sections[section]['by_equilibrium_count']=dict(by_ne)
        complete=all(s['cases'] and s['valid_cases']==s['cases'] for s in sections.values())
        report[track]={'sections':sections,'equal_section_exact_accuracy':statistics.mean(s['exact_accuracy_all'] for s in sections.values()) if complete else None,'overall_status':'complete' if complete else 'incomplete: do not rank as a full exam'}
    # Consistency is diagnostic, never a correction to model answers.
    by_matrix=collections.defaultdict(dict)
    for c in cases:
        a=pred.get(c['case_id'],{}).get('answers')
        if c['section']!='level_k' and isinstance(a,dict) and set(a)==set(key[c['case_id']]) and all(type(v)==bool for v in a.values()):by_matrix[json.dumps(c['payoffs'])][c['section']]=a
    checked=violations=0
    for parts in by_matrix.values():
        if not all(s in parts for s in exam.SECTIONS[:-1]):continue
        br=parts['best_response'];ne=parts['pure_nash'];dom=parts['strict_dominance']
        for r in range(2):
            for c in range(2):checked+=1;violations+=ne[f'ne_{r}_{c}']!=(br[f'br_0_{c}_{r}'] and br[f'br_1_{r}_{c}'])
        for pl in range(2):
            for a in range(2):checked+=1;violations+=dom[f'dom_{pl}_{a}']!=all(br[f'br_{pl}_{o}_{a}'] for o in range(2))
    report['logical_consistency']={'comparisons':checked,'violations':violations}
    # Exhaustive action relabelling comparisons where both predictions are available.
    checks=bad=0
    for c in cases:
        if c['section']=='level_k':continue
        origin=by_matrix.get(json.dumps(c['payoffs']),{}).get(c['section'])
        if origin is None:continue
        for rs,cs in [(1,0),(0,1),(1,1)]:
            p=[[c['payoffs'][r^rs][col^cs] for col in range(2)] for r in range(2)]
            other=by_matrix.get(json.dumps(p),{}).get(c['section'])
            if other is None:continue
            for k,v in origin.items():
                parts=k.split('_');kind=parts[0];nums=list(map(int,parts[1:]))
                if kind=='ne':target=f'ne_{nums[0]^rs}_{nums[1]^cs}'
                elif kind=='dom':target=f'dom_{nums[0]}_{nums[1]^(rs if nums[0]==0 else cs)}'
                else:
                    pl,o,a=nums;target=f'br_{pl}_{o^(cs if pl==0 else rs)}_{a^(rs if pl==0 else cs)}'
                checks+=1;bad+=other[target]!=v
    report['action_relabelling']={'directed_proposition_comparisons':checks,'violations':bad}
    return report

def main():
    a=argparse.ArgumentParser();a.add_argument('predictions',type=Path);a.add_argument('--out',type=Path,required=True);a.add_argument('--pilot',action='store_true');args=a.parse_args()
    cases=exam.rows(ROOT/'data/metadata/cases.jsonl');key={r['case_id']:r['answers'] for r in exam.rows(ROOT/'data/answers/answers.jsonl')}
    if args.pilot:
        ids=set(json.loads((ROOT/'data/questions/pilot.json').read_text()));cases=[c for c in cases if c['case_id'] in ids]
    ordinal.dump(args.out,score(cases,key,exam.rows(args.predictions)))
if __name__=='__main__':main()
