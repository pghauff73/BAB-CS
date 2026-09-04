"""Run all four affine research experiments; preserve prior evidence directories."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.audit_affine_replay import audit_case
from tools.affine_research import (F, Metric, certify_segment, identity, sqrt_upper,
                                  adaptive_run, classify_events, transition_times, order_events)
from tools.replay_error_budget import CASES, point_step


def metrics(case):
    if len(case.initial) == 1:
        return [Metric.infinity(case.matrix)]
    result = [Metric.weighted(case.matrix, identity(2), F(0), F(1), F(1), 'euclidean')]
    if case.name == 'rlc_damped':
        result.append(Metric.weighted(case.matrix, ((F(3,2), F(1,2)), (F(1,2), F(1,2))),
                                      F(-1,4), F(1,4), F(2), 'lyapunov'))
    return result


def weighted_experiment():
    case = CASES[2]
    norms = metrics(case)
    radii = [sqrt_upper(m.upper)*F(1,1000) for m in norms]
    x, h, rows = case.initial, F(1,20), []
    for i in range(1,401):
        y = point_step(case.matrix, case.offset(F(0)), x, h, 'trapezoidal')
        for j,m in enumerate(norms):
            cert = certify_segment(case.matrix, case.offset(F(0)), x, y, h, radii[j], m)
            radii[j] = cert.endpoint_radius
            if i in (40,200,400):
                rows.append({'time': str(i*h), 'metric': m.data(),
                             'physical_endpoint_radius': str(m.physical_radius(radii[j]))})
        x = y
    return {'case': case.name, 'step': str(h), 'initial_euclidean_radius': '1/1000',
            'same_state_trace_for_all_metrics': True, 'rows': rows}


def event_experiment():
    a = ((F(0),F(1)),(F(0),F(0)))
    b = (F(0),F(2))
    rows = {}
    for name, height, uncertainty in [('paired', F(3,16), F(0)),
                                      ('grazing', F(1,4), F(0)),
                                      ('no_crossing', F(1,2), F(0)),
                                      ('uncertain_pair', F(3,16), F(1,1000))]:
        cert = certify_segment(a,b,(height,F(-1)),(height,F(1)),F(1),uncertainty,Metric.infinity(a))
        rows[name] = classify_events(cert,0,(F(0),F(0)),F(1,1000))
    cert = certify_segment(((F(0),),),(F(1),),(F(-1,2),),(F(1,2),),F(1),F(0),Metric.infinity(((F(0),),)))
    rows['threshold_uncertainty'] = classify_events(cert,0,(F(-1,100),F(1,100)),F(1,1000))
    rows['exhausted'] = classify_events(cert,0,(F(0),F(0)),F(1,1000),maximum_cells=1)
    event = rows['threshold_uncertainty']['events'][0]
    transition = transition_times(event,(F(1,100),F(2,100)),(F(-1,1000),F(1,1000)))
    return {'cases':rows, 'delayed_transition':transition,
            'paired_order':order_events(rows['paired']['events']),
            'overlap_order':order_events([transition,dict(transition)])}


def production_events(audit):
    """Keep every possible root cell, including unresolved segment-boundary roots."""
    events, inspected = [], 0
    for point in audit['points']:
        for s in point['accepted_output_segment']['segments']:
            a = tuple(tuple(F(v) for v in row) for row in s['matrix'])
            b = tuple(F(v) for v in s['offset'])
            cert = certify_segment(a,b,(F(s['start_state']),),(F(s['end_state']),),
                                   F(s['end_time'])-F(s['start_time']),
                                   F(s['certificate']['initial_radius']),Metric.infinity(a))
            result = classify_events(cert,0,(F(1,2),F(1,2)),F(1,10**8),maximum_cells=512)
            inspected += result['inspected_cells']
            for e in result['events']:
                events.append({**e, 'time_lower':str(F(e['time_lower'])+F(s['start_time'])),
                               'time_upper':str(F(e['time_upper'])+F(s['start_time']))})
    return {'threshold':'1/2', 'events':events, 'order':order_events(events),
            'inspected_cells':inspected,
            'scope':'all segment candidate windows retained; overlapping windows are not counted as distinct physical events'}


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    audits = [audit_case(ROOT/p) for p in ('examples/rc_step.json','benchmarks/runtime/cases/switched_rc_bank-n001.json')]
    for audit in audits:
        audit['threshold_event_audit'] = production_events(audit)
    weighted = weighted_experiment()
    adaptive = [adaptive_run(case,metric,tolerance,policy) for case in CASES for metric in metrics(case)
                for tolerance in (F(1,1000),F(1,10000))
                for policy in ('adaptive_heun','adaptive_reference','adaptive_mixed')]
    reports = {'production-replay.json':audits, 'weighted-norms.json':weighted,
               'adaptive-effort.json':adaptive, 'events.json':event_experiment()}
    for name,data in reports.items():
        (output/name).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    sources = [*sorted((ROOT/'src/babcs').glob('*.py')),
               *(ROOT/p for p in ('tools/affine_research.py','tools/audit_affine_replay.py',
                 'tools/run_affine_research.py','tools/replay_error_budget.py','tests/test_affine_research.py'))]
    manifest = {'schema':'babcs-affine-research-v2',
                'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                'report_sha256':{name:hashlib.sha256((output/name).read_bytes()).hexdigest() for name in reports},
                'adaptive_configurations':len(adaptive),
                'adaptive_certified':sum(r['status']=='CERTIFIED' for r in adaptive),
                'scope':'research harness and offline audit; production acceptance logic unchanged'}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if not k.endswith('sha256')},indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-directory', type=Path, required=True)
    run(parser.parse_args().output_directory)
