import math
import sys
import random as rand
from itertools import product
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection

# hospital locations
# 1. (170, 180)
# 2. (310, 150)
#
# staging locations
# 1. (100, 210)
# 2. (170, 180)
# 3. (310, 150)
# 4. (510, 240)
HospitalLocs = [(170.0, 180.0), (310.0, 150.0)]
StagingLocs = [(100.0, 210.0), (170.0, 180.0), (310.0, 150.0), (510.0, 240.0)]
Speed = 250.0  # km/h

class Grid:
    limits = ()
    zones = []

    def __init__(self, xmin, xmax, ymin, ymax):
        self.limits = (xmin, xmax, ymin, ymax)

    def add_zone(self, xmin, xmax, ymin, ymax):
        self.zones.append((xmin, xmax, ymin, ymax))

    def zone_from_loc(self, loc):
        for i, (xmin, xmax, ymin, ymax) in enumerate(self.zones):
            if xmin <= loc[0] <= xmax and ymin <= loc[1] <= ymax:
                return i + 1

    def generate_rand_loc(self, zone):
        xmin, xmax, ymin, ymax = self.zones[zone - 1]
        x, y = -100, -100
        while not (xmin <= x <= xmax) or not (ymin <= y <= ymax):
            x = np.random.normal(StagingLocs[zone - 1][0], 30)
            y = np.random.normal(StagingLocs[zone - 1][1], 30)
        return x, y


class Casualty:
    location = (0, 0)
    time = 0
    # tuple of patient and severity
    # 1 urgent, 2 priority, and 1 routine would be (3, 2, 2, 1)
    severity = ()
    zone = 0
    utility = 0

    def __init__(self, loc, zone, time, severity):
        self.location = loc
        self.time = time
        self.severity = severity
        self.zone = zone
        if severity == 3:
            self.utility = 10
        elif severity == 2:
            self.utility = 1
        else:
            self.utility = 0


class Medevac:
    staging_loc = (0, 0)
    timing = ()
    zone = 0
    casualty_zone = 0
    vel = 0

    def __init__(self, loc, zone, vel):
        self.staging_loc = loc
        self.zone = zone
        self.vel = vel

    def get_time_from_staging(self, loc):
        x, y = loc
        xs, ys = self.staging_loc
        return math.sqrt((x - xs)**2 + (y - ys)**2) / self.vel

    def get_nearest_hosp(self, loc):
        best_dist = float('inf')
        best_loc = (0, 0)
        x, y = loc
        for xh, yh, in HospitalLocs:
            dist = math.sqrt((xh - x) ** 2 + (yh - y) ** 2)
            if dist < best_dist:
                best_dist = dist
                best_loc = (xh, yh)
        return best_loc

    def get_time_to_hosp(self, loc):
        xh, yh = self.get_nearest_hosp(loc)
        x, y = loc
        return math.sqrt((xh - x) ** 2 + (yh - y) ** 2) / self.vel

    def get_expected_time(self, loc):
        time = self.get_time_from_staging(loc)
        time += self.get_time_to_hosp(loc)
        return time

    def assign_casualty(self, casualty):
        t0 = casualty.time
        if self.get_status(t0) > 0:
            # print('WARNING: Medevac already assigned for specified time interval. Nothing assigned.')
            return
        xc, yc = casualty.location
        # [assigned time,
        # time after travel to casulty,
        # time after casulty delivered to hospital,
        # time after return to staging location]
        t1 = self.get_time_from_staging(casualty.location)
        t2 = self.get_time_to_hosp(casualty.location)
        t3 = self.get_time_from_staging(self.get_nearest_hosp(casualty.location))
        self.timing = (t0, t0 + t1, t0 + t1 + t2, t0 + t1 + t2 + t3)
        self.casualty_zone = casualty.zone

    def get_casualty_time(self):
        return self.timing[2] - self.timing[0] + 0.25

    def clear_casualty(self):
        self.timing = ()
        self.casualty_zone = 0

    def get_status(self, time):
        if len(self.timing) == 0:
            return 0
        t0, t1, t2, t3 = self.timing
        # if t1 > time >= t0:
        #     return 1
        # elif t2 > time >= t1:
        #     return 2
        # elif not math.isclose(t3, t2) and t3 > time >= t2:
        #     return 3
        # elif time >= t3:
        #     return 0
        if t0 <= time <= t3:
            return self.casualty_zone
        else:
            return 0

def define_grid():
    # grid is (605 x 350) km
    # zone 1: x = 0-120 km
    # zone 2: x = 120-220 km
    # zone 3: x = 220-370 km
    # zone 4: x = 370-605, y = 180->top (from bottom)
    grid = Grid(0.0, 605.0, 0.0, 350.0)
    zone_limits = [(0.0, 120.0, 0.0, 350.0), (120.0, 220.0, 0.0, 350.0), (220.0, 370.0, 0.0, 350.0),
                   (370.0, 605.0, 180.0, 350.0)]
    for xmin, xmax, ymin, ymax in zone_limits:
        grid.add_zone(xmin, xmax, ymin, ymax)
    return grid

def generate_casualties(grid, N, T):
    # generate date based on data basic information from paper
    # N = 100
    # T = 100
    times = []
    for i in range(0, N):
        times.append(int(rand.uniform(0, T)))
    times.sort()
    severities = []
    sprobs = [0.11, 0.23]
    for i in range(0, N):
        num = rand.random()
        if num < sprobs[0]:
            severities.append(3)
        elif sprobs[0] < num < sprobs[1]:
            severities.append(2)
        else:
            severities.append(1)
    zones = []
    zprobs = [0.004, 0.004 + 0.585, 0.004 + 0.585 + 0.338]
    for i in range(0, N):
        num = rand.random()
        if num < zprobs[0]:
            zones.append(1)
        elif zprobs[0] < num < zprobs[1]:
            zones.append(2)
        elif zprobs[1] < num < zprobs[2]:
            zones.append(3)
        else:
            zones.append(4)
    locs = []
    for zone in zones:
        locs.append(grid.generate_rand_loc(zone))
    casualties = []
    for loc, zone, time, severity in zip(locs, zones, times, severities):
        casualties.append(Casualty(loc, zone, time, severity))
    return casualties

def possible_actions(s, A):
    return [a for hi, h in enumerate(s[:4]) if h == 0 for a in A if a[0] == hi + 1 and a[1] == s[4]]

def calc_optimal_policy(medevacs):
    w = [0, 1, 2]  # Medevac in zone 1 can be idle or vist zone 1 or 2
    x = [0, 1, 2, 3]
    y = [0, 2, 3, 4]
    z = [0, 3, 4]
    c = [1, 2, 3, 4]
    p = [1, 2, 3]

    S = [s for s in product(w, x, y, z, c, p)]
    A = [(1, 1), (1, 2), (2, 1), (2, 2), (2, 3), (3, 2), (3, 3), (3, 4), (4, 3), (4, 4)]
    Q = {}
    NN = {}
    for s in S:
        a_choices = possible_actions(s, A)
        # print(a_choices)
        for a in a_choices:
            Q[s, a] = 0.0
            NN[s, a] = 0.0

    gamma = 0.95
    alpha = 0.95
    lam = 0.7
    N = 100
    for epoch in range(N):
        casualties = generate_casualties(grid, N=100, T=300)
        if epoch % 20 == 0:
            print('Entering epoch {}/{}...'.format(epoch, N))
        for medevac in medevacs:
            medevac.clear_casualty()
        for lcasualty, casualty in zip(casualties, casualties[1:]):
            ls = [m.get_status(lcasualty.time) for m in medevacs]
            ls.append(lcasualty.zone)
            ls.append(lcasualty.severity)
            ls = tuple(ls)
            la_choices = possible_actions(ls, A)
            if len(la_choices) > 0:
                la = rand.choice(la_choices)
                medevacs[la[0] - 1].assign_casualty(lcasualty)
                s = [m.get_status(casualty.time) for m in medevacs]
                s.append(casualty.zone)
                s.append(casualty.severity)
                s = tuple(s)
                a_choices = possible_actions(s, A)
                if len(a_choices) > 0:
                    a = rand.choice(a_choices)
                    NN[ls, la] += 1.0
                    medevacs[a[0] - 1].assign_casualty(casualty)
                    r = 0 if medevacs[la[0] - 1].get_casualty_time() > 1.0 else lcasualty.utility
                    delta = r + gamma * Q[s, a] - Q[ls, la]
                    for s in S:
                        for a in possible_actions(s, A):
                            Q[s, a] += alpha*delta*NN[s, a]
                            NN[s, a] *= gamma*lam

    policy = {}
    with open('Q.out', 'w') as f:
        with open('NN.out', 'w') as ff:
            for s in S:
                f.write('{}: '.format(s))
                ff.write('{}: '.format(s))
                a_choices = possible_actions(s, A)
                if len(a_choices) > 0:
                    choices = [Q[s, a] for a in a_choices]
                    [f.write(' {}->{:2.2f}'.format(a, Q[s, a])) for a in a_choices]
                    [ff.write(' {}->{}'.format(a, NN[s, a])) for a in a_choices]
                    policy[s] = a_choices[choices.index(max(choices))]
                f.write('\n')
                ff.write('\n')
    for medevac in medevacs:
        medevac.clear_casualty()
    return policy

def q_learning(medevacs):
    w = [0, 1, 2]  # Medevac in zone 1 can be idle or vist zone 1 or 2
    x = [0, 1, 2, 3]
    y = [0, 2, 3, 4]
    z = [0, 3, 4]
    c = [1, 2, 3, 4]
    p = [1, 2, 3]

    S = [s for s in product(w, x, y, z, c, p)]
    A = [(1, 1), (1, 2), (2, 1), (2, 2), (2, 3), (3, 2), (3, 3), (3, 4), (4, 3), (4, 4)]
    Q = {}
    gamma = 0.5 #0.5
    alpha = 0.75 #0.75
    epsilon = 0.1

    for s in S:
        for a in possible_actions(s, A):
            Q[s, a] = 0.0

    for epoch in range(100):
        casualties = generate_casualties(grid, N=1000, T=5000)
        print('epoch: {}/100'.format(epoch))
        for casualty, casualtyp in zip(casualties, casualties[1:]):
            sl = [m.get_status(casualty.time) for m in medevacs]
            sl.append(casualty.zone)
            sl.append(casualty.severity)
            s = tuple(sl)
            sl[4] = casualtyp.zone
            sl[5] = casualtyp.severity
            sp = tuple(sl)
            actions = possible_actions(s, A)
            if len(actions) > 0:
                if rand.random() < epsilon:
                    a = rand.choice(actions)
                else:
                    idx = np.argmax(np.array([Q[s, ap] for ap in actions]))
                    a = actions[idx]
                medevacs[a[0] - 1].assign_casualty(casualty)
                r = 0 if medevacs[a[0] - 1].get_casualty_time() > 1.0 else casualty.utility
                actionsp = possible_actions(sp, A)
                if len(actionsp) > 0:
                    Q[s, a] += alpha*(r + gamma*max([Q[sp, ap] for ap in actionsp]) - Q[s, a])
                    # print(Q)
    policy = {}
    with open('Q.out', 'w') as f:
        for s in S:
            f.write('{}: '.format(s))
            a_choices = possible_actions(s, A)
            if len(a_choices) > 0:
                choices = [Q[s, a] for a in a_choices]
                [f.write(' {}->{:2.2f}'.format(a, Q[s, a])) for a in a_choices]
                policy[s] = a_choices[choices.index(max(choices))]
            f.write('\n')
    for medevac in medevacs:
        medevac.clear_casualty()
    return policy



def value_iteration(medevacs):
    w = [0, 1, 2]  # Medevac in zone 1 can be idle or vist zone 1 or 2
    x = [0, 1, 2, 3]
    y = [0, 2, 3, 4]
    z = [0, 3, 4]
    c = [1, 2, 3, 4]
    p = [1, 2, 3]

    serve = [w, x, y, z]

    S = [s for s in product(w, x, y, z, c, p)]
    A = [(1, 1), (1, 2), (2, 1), (2, 2), (2, 3), (3, 2), (3, 3), (3, 4), (4, 3), (4, 4)]
    Q = {}
    NN = {}
    phi = {}
    phi_n = {}
    mu = {}
    alpha = 0.8
    lam = 1/327
    N = 1500

    casualties = generate_casualties(grid, N=N, T=500)
    for idx, casualty in enumerate(casualties):
        if idx % 20 == 0:
            print('Training phi and mu progress: {:0.1f}%'.format(100*(idx/N)))
        for s in S:
            for a in possible_actions(s, A):
                medevacs[a[0] - 1].assign_casualty(casualty)
                key = (*a, casualty.severity)
                t = medevacs[a[0] - 1].get_casualty_time()
                medevacs[a[0] - 1].clear_casualty()
                r = 0 if t > 1.0 else casualty.utility
                if key in phi:
                    phi[key] += alpha * (r - phi[key])
                    mu[a] += alpha * (t - mu[a])
                else:
                    phi[key] = alpha * r
                    mu[a] = alpha * t
    print(phi)
    print(mu)

    beta = [max([1/mu.get((h, zp), 0.0001) for zp in range(1, 5)]) for h in range(1, 5)]
    v = lam + sum(beta)
    J = {}
    S = [s for s in product(w, x, y, z)]

    pk = [0.1587, 0.1574, 0.6839]
    Jn = {s: 0.0 for s in S}
    Jnp1 = Jn
    sl = [0, 0, 0, 0]
    for n in range(500):
        for s in S:
            # for term 1, helicopter becoming idle
            t1 = 0
            for heli, status in enumerate(s):
                if status != 0:
                    sp = [v for v in s]
                    sp[heli] = 0
                    sp = tuple(sp)
                    t1 += mu[heli + 1, status]*Jn[sp]
            # for term 2, request receieved
            t2 = 0
            for z in range(1, 5):
                for k in range(1, 4):
                    l = []
                    for heli, status in enumerate(s):
                        if status == 0:
                            sp = [v for v in s]
                            sp[heli] = z
                            sp = tuple(sp)
                            if sp in S:
                                l.append(Jn[sp] + v*phi[heli + 1, z, k])
                    if len(l) > 0:
                        t2 += lam*pk[k - 1]*max(l)
            # for term 3, doing nothing
            t3 = v - lam
            for heli, status in enumerate(s):
                if status != 0:
                    t3 -= mu[heli + 1, status]
            t3 *= Jn[s]

            Jn[s] = (1/v)*(t1 + t2 + t3)

    print(Jn)


if __name__ == "__main__":
    n_heli = 1
    grid = define_grid()
    casualties = generate_casualties(grid, N=1000, T=1000)
    medevacs = [Medevac(loc, grid.zone_from_loc(loc), Speed) for loc in StagingLocs]

    ax = plt.gca()
    boxes = []
    for zone in grid.zones:
        xmin, xmax, ymin, ymax = zone
        boxes.append(Rectangle((xmin, ymin), xmax - xmin, ymax - ymin))
    pc = PatchCollection(boxes, alpha=0.6, facecolors=("Blue", "Red", "Orange", "Purple"), edgecolors=("Black"))
    ax.add_collection(pc)

    colors = ["Gray", "Yellow", "Red"]
    severity = ["Routine", "Moderate", "Severe"]
    for i in range(1, 4):
        x = [c.location[0] for c in casualties if c.severity == i]
        y = [c.location[1] for c in casualties if c.severity == i]
        plt.plot(x, y, 'o', markersize=2, color=colors[i - 1], alpha=0.5, label=severity[i - 1])

    xStaging = [x for x, y in StagingLocs]
    yStaging = [y for x, y in StagingLocs]
    plt.plot(xStaging, yStaging, 'o', markersize=8, color="Green", markeredgecolor="Black", label="Staging Locations")

    plt.xlim(0, 650)
    plt.ylim(0, 350)
    plt.legend(loc = "lower right", facecolor="skyblue")
    plt.show()

    # opt_policy = calc_optimal_policy(medevacs)
    # opt_policy_vi = value_iteration(medevacs)
    # opt_policy = q_learning(medevacs)
    opt_policy = value_iteration(medevacs)
    times = []
    s = [0, 0, 0, 0, 0]
    num_skip = 0
    for casualty in casualties:
        sl = [m.get_status(casualty.time) for m in medevacs]
        sl.append(casualty.zone)
        sl.append(casualty.severity)
        s = tuple(sl)
        a = opt_policy.get(s)
        if a is None:
            num_skip += 1
            continue
        medevacs[a[0] - 1].assign_casualty(casualty)
        heli = medevacs[a[0] - 1]
        # print('{:6d}: Casualty in zone {:2d} at location ({:5.1f}, {:5.1f}) assigned to medevac in zone {:2d} at '
        #       'location ({:03.1f}, {:03.1f})'.format(casualty.time, casualty.zone, *casualty.location,
        #                                              heli.zone, *heli.staging_loc))
        times.append(heli.get_casualty_time())
    print('Average time to hospital (Optimal Policy): {:5.3f}'.format(sum(times)/len(times)))
    # print('Skipped: {}\n'.format(num_skip))
    print(opt_policy)
    with open('optimal_policy.policy', 'w') as f:
        for k, v in opt_policy.items():
            f.write('{}: {}\n'.format(k, v))

    times = []
    num_skip = 0
    for m in medevacs:
        m.clear_casualty()
    for casualty in casualties:
        fastest_time = float('inf')
        fastest_heli = -1
        for idx, medevac in enumerate(medevacs):
            if medevac.get_status(casualty.time) > 0 or not any([medevac.zone + 1 == casualty.zone or
                                                                 medevac.zone - 1 == casualty.zone or
                                                                 medevac.zone == casualty.zone]):
                continue
            time_est = medevac.get_expected_time(casualty.location)
            if time_est < fastest_time:
                fastest_time = time_est
                fastest_heli = idx
        if fastest_heli == -1:
            num_skip += 1
            # print('{:6d}: Casualty in zone {:2d} at location ({:5.1f}, {:5.1f}) NOT assigned due to oversubscribed '
            #       'medevacs'.format(casualty.time, casualty.zone, *casualty.location))
            continue
        heli = medevacs[fastest_heli]
        heli.assign_casualty(casualty)
        # print('{:6d}: Casualty in zone {:2d} at location ({:5.1f}, {:5.1f}) assigned to medevac in zone {:2d} at '
        #       'location ({:03.1f}, {:03.1f})'.format(casualty.time, casualty.zone, *casualty.location, heli.zone,
        #                                              *heli.staging_loc))
        times.append(fastest_time)
    print('Average time to hospital (Myopic Policy): {:5.3f}'.format(sum(times) / len(times)))
    # print('Skipped: {}\n'.format(num_skip))