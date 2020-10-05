import math
import random as rand

# hospital locations
# 1. (170, 180)
# 2. (310, 150)
#
# staging locations
# 1. (100, 210)
# 2. (170, 180)
# 3. (310, 150)
# 4. (510, 240)
HospitalLocs = [(170, 180), (310, 150)]
StagingLocs = [(100, 210), (170, 180), (310, 150), (510, 240)]
Speed = 250 # km/h

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
        return rand.uniform(xmin, xmax), rand.uniform(ymin, ymax)


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

    def assign_utility(self, util):
        self.utility = util


class Medevac:
    staging_loc = (0, 0)
    timing = ()
    zone = 0
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
        best_dist = float('nan')
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
            print('WARNING: Medevac already assigned for specified time interval. Nothing assigned.')
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

        casualty.assign_utility(t1 + t2)

    def get_status(self, time):
        if len(self.timing) == 0:
            return 0
        t0, t1, t2, t3 = self.timing
        if t1 > time >= t0:
            return 1
        elif t2 > time >= t1:
            return 2
        elif not math.isclose(t3, t2) and t3 > time >= t2:
            return 3
        elif time >= t3:
            return 0

def define_grid():
    # grid is (605 x 350) km
    # zone 1: x = 0-120 km
    # zone 2: x = 120-220 km
    # zone 3: x = 220-370 km
    # zone 4: x = 370-605, y = 180->top (from bottom)
    grid = Grid(0, 605, 0, 350)
    zone_limits = [(0, 120, 0, 350), (120, 220, 0, 350), (220, 370, 0, 350), (370, 605, 180, 350)]
    for xmin, xmax, ymin, ymax in zone_limits:
        grid.add_zone(xmin, xmax, ymin, ymax)
    return grid

def generate_casualties(grid):
    # generate date based on data basic information from paper
    N = 100
    T = 100
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
    zprobs = [0.004, 0.004 + 0.073, 0.004 + 0.073 + 0.585]
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


if __name__ == "__main__":
    n_heli = 2
    grid = define_grid()
    casualties = generate_casualties(grid)
    medevacs = [[Medevac(loc, grid.zone_from_loc(loc), Speed) for _ in range(n_heli)] for loc in StagingLocs]
    policy = 'Myopic'
    for casualty in casualties:
        if policy == 'Myopic':
            medevacs_flat = [medevac for list in medevacs for medevac in list]
            fastest_time = float('inf')
            fastest_heli = -1
            for idx, medevac in enumerate(medevacs_flat):
                if medevac.get_status(casualty.time) > 0:
                    continue
                time_est = medevac.get_expected_time(casualty.location)
                if time_est < fastest_time:
                    fastest_time = time_est
                    fastest_heli = idx
            if fastest_heli == -1:
                print('{:6d}: Casualty in zone {:2d} at location ({:5.1f}, {:5.1f}) NOT assigned due to oversubscribed '
                      'medevacs'.format(casualty.time, casualty.zone, *casualty.location))
                continue
            heli = medevacs_flat[fastest_heli]
            heli.assign_casualty(casualty)
            print('{:6d}: Casualty in zone {:2d} at location ({:5.1f}, {:5.1f}) assigned to medevac in zone {:2d} at '
                  'location ({:03.1f}, {:03.1f})'.format(casualty.time, casualty.zone, *casualty.location, heli.zone,
                                                         *heli.staging_loc))
