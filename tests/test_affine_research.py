"""Research certificates: analytical counterexamples and production trace checks."""
import unittest
from pathlib import Path
from tools.affine_research import (F, Metric, certify_segment, sqrt_upper, adaptive_run,
                                  classify_events, transition_times, order_events)
from tools.run_affine_research import metrics, event_experiment, weighted_experiment
from tools.replay_error_budget import CASES
from tools.audit_affine_replay import ROOT, audit_case, captured_replays, bounded, integrators, ScalarRC, load_case


class MetricTests(unittest.TestCase):
    def test_sqrt_rounds_outward(self):
        for q in (F(0), F(2), F(1,10**60), F(4)):
            self.assertGreaterEqual(sqrt_upper(q)**2,q)
        self.assertEqual(sqrt_upper(F(4)),2)

    def test_weighted_lmi_verified(self):
        m = metrics(CASES[2])[1]
        self.assertEqual(m.mu,F(-1,4))
        self.assertEqual(m.coordinate_factor,2)
        with self.assertRaises(ValueError):
            Metric.weighted(CASES[2].matrix,m.matrix,F(-1),m.lower,m.upper)
        with self.assertRaises(ValueError):
            Metric.weighted(CASES[3].matrix,m.matrix,F(-1,4),m.lower,m.upper)

    def test_forged_metric_rejected(self):
        with self.assertRaises(ValueError):
            certify_segment(((F(1),),),(F(0),),(F(1),),(F(1),),F(1),F(0),Metric('bad',F(-1)))

    def test_inherited_error_is_not_reset(self):
        a=((F(0),),)
        c=certify_segment(a,(F(1),),(F(0),),(F(1),),F(1),F(1,10),Metric.infinity(a))
        self.assertEqual(c.defect,0)
        self.assertEqual(c.endpoint_radius,F(1,10))

    def test_same_trace_weighted_long_horizon_improvement(self):
        rows=weighted_experiment()['rows']
        self.assertLess(F(rows[-1]['physical_endpoint_radius']), F(rows[-2]['physical_endpoint_radius']))


class EventTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results=event_experiment()

    def test_two_crossings_with_same_endpoint_sign(self):
        r=self.results['cases']['paired']
        self.assertEqual(r['status'],'CROSSINGS')
        self.assertEqual(len(r['events']),2)
        for e,t in zip(r['events'],(F(1,4),F(3,4))):
            self.assertLessEqual(F(e['time_lower']),t)
            self.assertGreaterEqual(F(e['time_upper']),t)
        self.assertEqual(self.results['paired_order'],'STRICT_ORDER')

    def test_grazing_unresolved(self):
        self.assertEqual(self.results['cases']['grazing']['status'],'UNKNOWN')

    def test_no_crossing(self):
        self.assertEqual(self.results['cases']['no_crossing']['status'],'NO_CROSSING')

    def test_threshold_uncertainty_enclosed(self):
        e=self.results['cases']['threshold_uncertainty']['events'][0]
        self.assertEqual(e['status'],'CROSSING')
        self.assertLessEqual(F(e['time_lower']),F(49,100))
        self.assertGreaterEqual(F(e['time_upper']),F(51,100))

    def test_exhaustion_and_order_do_not_claim_success(self):
        self.assertEqual(self.results['cases']['exhausted']['status'],'UNKNOWN')
        self.assertEqual(self.results['overlap_order'],'SIMULTANEOUS_OR_ORDER_UNRESOLVED')

    def test_timing_minkowski_and_invalid_delay(self):
        e={'time_lower':'1/2','time_upper':'3/4','status':'CROSSING'}
        r=transition_times(e,(F(1,10),F(1,5)),(F(-1,100),F(1,100)))
        self.assertEqual(F(r['time_lower']),F(59,100))
        self.assertEqual(F(r['time_upper']),F(96,100))
        with self.assertRaises(ValueError):
            transition_times(e,(F(0),F(1)),(F(-1),F(0)))


class AdaptiveTests(unittest.TestCase):
    def test_all_policies_certify_whole_path_and_count_failed_work(self):
        for policy in ('adaptive_heun','adaptive_reference','adaptive_mixed'):
            r=adaptive_run(CASES[0],metrics(CASES[0])[0],F(1,1000),policy)
            self.assertEqual(r['status'],'CERTIFIED')
            self.assertEqual(F(r['reached_time']),2)
            self.assertLessEqual(F(r['maximum_physical_tube_radius']),F(1,1000))
            t=F(0)
            for row in r['segments']:
                self.assertEqual(F(row['time'])-t,F(row['certificate']['step']))
                self.assertLessEqual(F(row['certificate']['fresh_radius_upper']),F(row['allocation']))
                t=F(row['time'])
            w=r['work']
            self.assertEqual(w['certificate_evaluations'],w['candidate_attempts']+w['reference_attempts'])
            self.assertGreater(w['rejected_trials'],0)

    def test_attempt_exhaustion_retains_original_state(self):
        r=adaptive_run(CASES[0],metrics(CASES[0])[0],F(1,10**12),'adaptive_heun',maximum_attempts=1)
        self.assertEqual(r['status'],'UNKNOWN')
        self.assertEqual(r['reached_time'],'0')
        self.assertEqual(r['final_state'],['1'])

    def test_invalid_attempt_budget(self):
        with self.assertRaises(ValueError):
            adaptive_run(CASES[0],metrics(CASES[0])[0],F(1,1000),'adaptive_heun',maximum_attempts=True)

    def test_scheduled_event_not_straddled(self):
        r=adaptive_run(CASES[4],metrics(CASES[4])[0],F(1,1000),'adaptive_reference')
        self.assertIn('1',[s['time'] for s in r['segments']])


class ProductionTests(unittest.TestCase):
    def test_wrappers_restore_on_exception(self):
        a,b=bounded.integrate_reference_window_with_stats,integrators.implicit_step
        with self.assertRaisesRegex(RuntimeError,'test'):
            with captured_replays():
                raise RuntimeError('test')
        self.assertIs(a,bounded.integrate_reference_window_with_stats)
        self.assertIs(b,integrators.implicit_step)

    def test_actual_traces_and_replays_cover_closed_form(self):
        for p in ('examples/rc_step.json','benchmarks/runtime/cases/switched_rc_bank-n001.json'):
            r=audit_case(ROOT/p,initial_radius=F(1,100000))
            self.assertTrue(r['instrumentation_equivalent'])
            self.assertTrue(r['all_closed_form_crosschecks'])
            self.assertGreater(r['selected_replay_windows'],0)
            for row in r['points']:
                if row['replay']:
                    self.assertGreater(F(row['replay']['inherited_anchor_radius']),0)


if __name__=='__main__':
    unittest.main()
