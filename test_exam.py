# SPDX-License-Identifier: Apache-2.0
import json,unittest
from pathlib import Path
import exam,ordinal,score
R=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=exam.rows(R/'data/metadata/cases.jsonl');cls.key={a['case_id']:a['answers'] for a in exam.rows(R/'data/answers/answers.jsonl')}
    def test_all_answers_independently(self):
        for c in self.cases:self.assertEqual(exam.reference(c),exam.independent_reference(c));self.assertEqual(exam.reference(c),self.key[c['case_id']])
    def test_hashes_and_no_answer_leak(self):
        m=json.loads((R/'data/manifest.json').read_text())
        for name,h in m['files'].items():self.assertEqual(ordinal.sha((R/'data'/name).read_bytes()),h)
        for c in self.cases:
            body=exam.payload(c);self.assertEqual(set(body),{'state','questions'});self.assertNotIn('answers',body);self.assertNotIn('case_id',body['state'])
    def test_oracle_scores_and_invariance(self):
        result=score.score(self.cases,self.key,[{'case_id':i,'answers':v} for i,v in self.key.items()])
        self.assertEqual(result['all']['equal_section_exact_accuracy'],1)
        self.assertEqual(result['logical_consistency']['violations'],0);self.assertEqual(result['action_relabelling']['violations'],0);self.assertGreater(result['action_relabelling']['directed_proposition_comparisons'],0)
    def test_empty_predictions_not_perfect(self):
        result=score.score(self.cases,self.key,[]);self.assertIsNone(result['all']['equal_section_exact_accuracy'])
        for s in result['all']['sections'].values():self.assertEqual(s['exact_accuracy_all'],0)
    def test_parser_rejects_invalid(self):
        body={'questions':{'x':{'type':'noul'}}}
        for val in [True,float('nan'),-1,2,'0.5']:
            with self.assertRaises(ValueError):exam.parse({'answers':{'x':{'type':'noul','noul':val}}},body)
        labels,_=exam.parse({'answers':{'x':{'type':'noul','noul':.5}}},body);self.assertFalse(labels['x'])
        with self.assertRaises(ValueError):exam.parse({'answers':{}},body)
    def test_rounded_choices(self):
        body={'questions':{'x':{'type':'choice'}}}
        response={'answers':{'x':{'type':'choice','choice':'first','probabilities':{'first':.55,'second':.33,'equal':.11}}}}
        labels,p=exam.parse(response,body);self.assertEqual(labels['x'],'first');self.assertAlmostEqual(sum(p['x'].values()),1)
        response['answers']['x']['probabilities']['first']=.4
        with self.assertRaises(ValueError):exam.parse(response,body)
    def test_pilot_stratification(self):
        ids=set(json.loads((R/'data/questions/pilot.json').read_text()));self.assertEqual(len(ids),108)
        cases=[c for c in self.cases if c['case_id'] in ids and c['section']=='pure_nash'];self.assertEqual(len(cases),12)
        self.assertEqual({sum(self.key[c['case_id']].values()) for c in cases},{0,1,2})
if __name__=='__main__':unittest.main()
