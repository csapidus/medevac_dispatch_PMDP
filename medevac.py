import math

# grid is (605 x 350) km
# zone 1: x = 0-120 km
# zone 2: x = 120-220 km
# zone 3: x = 220-370 km
# zone 4: x = 370-605, y = 180->top (from bottom)
#
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
                return i


class Casualty:
    location = (0, 0)
    time = 0
    # tuple of patient and severity
    # 1 urgent, 2 priority, and 1 routine would be (3, 2, 2, 1)
    severity = ()
    zone = 0

    def __init__(self, loc, zone, time, severity):
        self.location = loc
        self.time = time
        self.severity = severity
        self.zone = zone


class Medevac:
    staging_loc = (0, 0)
    timing = []
    vel = 0

    def __init__(self, loc, vel):
        self.staging_loc = loc
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
        xh, yh = self.get_nearest_hosp()
        x, y = loc
        return math.sqrt((xh - x) ** 2 + (yh - y) ** 2) / self.vel

    def get_expected_time(self, loc):
        time = self.get_time_from_staging(loc)
        time += self.get_time_to_hosp(loc)
        return time

    def assign_casualty(self, casualty):
        t0 = casualty.time
        if len(self.timing) > 0 and self.timing[-1] < t0:
            print()
        self.timing.clear()
        xc, yc = casualty.location
        # [assigned time,
        # time after travel to casulty,
        # time after casulty delivered to hospital,
        # time after return to staging location]
        t1 = self.get_time_from_staging(casualty.location)
        t2 = self.get_time_to_hosp(casualty.location)
        t3 = self.get_time_from_staging(self.get_nearest_hosp(casualty.location))
        self.timing.append([t0, t0 + t1, t0 + t1 + t2, t0 + t1 + t2 + t3])
