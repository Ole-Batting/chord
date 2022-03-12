import numpy as np
from chord import Guitar
from datetime import datetime
from multiprocessing import Pool
import pickle
import sys



def proc(machine, job, n_strings=6):
    init_dt = datetime.now()

    ### Standard tuning ###
    guitar = Guitar(n_strings=n_strings)
    _,standard_stats = guitar.tuning_gain()

    best_tuning_m = ['E4','B3','G3','D3','A2','E2']
    best_tuning_f = ['E4','B3','G3','D3','A2','E2']
    best_tuning_r = ['E4','B3','G3','D3','A2','E2']
    best_tuning_v = ['E4','B3','G3','D3','A2','E2']

    best_tuning_m_companions = []
    best_tuning_f_companions = []
    best_tuning_r_companions = []
    best_tuning_v_companions = []

    best_stat_m = standard_stats['m']
    best_stat_f = standard_stats['f']
    best_stat_r = standard_stats['r']
    best_stat_v = standard_stats['v']
    ### --- ###

    t_start = machine * 12**5 + job * 12**3
    t_end = machine * 12**5 + (job + 1) * 12**3
    n_tunings = 0

    start_dt = datetime.now()
    for t in range(t_start, t_end):
            tu = t

            strings = []
            for i in range(n_strings):
                r = tu % 12
                tu = tu // 12
                strings.append(r)

            tuning = [Guitar(n_strings=n_strings).number_to_ipn(s) for s in strings]

            retval, stats = Guitar(tuning=tuning).tuning_gain()

            if retval:
                n_tunings += 1
                if all([
                    stats['m'] <= standard_stats['m'],
                    stats['f'] <= standard_stats['f'],
                    stats['r'] <= standard_stats['r'],
                    stats['v'] <= standard_stats['v'],
                ]) and not all([
                    stats['m'] == standard_stats['m'],
                    stats['f'] == standard_stats['f'],
                    stats['r'] == standard_stats['r'],
                    stats['v'] == standard_stats['v'],
                ]):
                    payload = {
                        'id': t,
                        'strings': strings,
                        'tuning': tuning,
                        'stats': stats,
                    }
                    pickle.dump(payload, open(f'tmp/better/payload_{t}.bin', 'wb'))
                    n_tunings += 1


                if stats['m'] < best_stat_m:
                    best_stat_m = stats['m']
                    best_tuning_m = tuning
                    best_tuning_m_companions = []
                elif stats['m'] < best_stat_m:
                    best_tuning_m_companions.append(tuning)

                if stats['f'] < best_stat_f:
                    best_stat_f = stats['f']
                    best_tuning_f = tuning
                    best_tuning_f_companions = []
                elif stats['f'] < best_stat_f:
                    best_tuning_f_companions.append(tuning)

                if stats['r'] < best_stat_r:
                    best_stat_r = stats['r']
                    best_tuning_r = tuning
                    best_tuning_r_companions = []
                elif stats['r'] < best_stat_r:
                    best_tuning_r_companions.append(tuning)

                if stats['v'] < best_stat_v:
                    best_stat_v = stats['v']
                    best_tuning_v = tuning
                    best_tuning_v_companions = []
                elif stats['v'] < best_stat_v:
                    best_tuning_v_companions.append(tuning)

    end_dt = datetime.now()
    payload = {
        'machine': machine,
        'job': job,
        'best_tuning_m': best_tuning_m,
        'best_tuning_f': best_tuning_f,
        'best_tuning_r': best_tuning_r,
        'best_tuning_v': best_tuning_v,
        'best_tuning_m_companions': best_tuning_m_companions,
        'best_tuning_f_companions': best_tuning_f_companions,
        'best_tuning_r_companions': best_tuning_r_companions,
        'best_tuning_v_companions': best_tuning_v_companions,
        'best_stat_m': best_stat_m,
        'best_stat_f': best_stat_f,
        'best_stat_r': best_stat_r,
        'best_stat_v': best_stat_v,
        'init_dt': init_dt,
        'start_dt': start_dt,
        'end_dt': end_dt,
        'total_duration': end_dt-init_dt,
        'runtime': end_dt-start_dt,
    }
    pickle.dump(payload, open( f'tmp/job/payload_{machine}_{job}.bin', 'wb'))

if __name__ == '__main__':
    """machine = int(sys.argv[1])
    m1, m2 = np.meshgrid([machine], range(144))
    args = zip(m1.ravel(),m2.ravel())
    with Pool(processes=4) as pool:
        print(pool.starmap(proc, args))
    """
    start = datetime.now()
    proc(0,0)
    end = datetime.now()
    print(end-start)
