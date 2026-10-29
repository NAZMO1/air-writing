"""Rotation-invariant finger geometry and debounced, smoothed pen strokes."""
import math


def angle(a, b, c):
    u = [x-y for x, y in zip(a, b)]
    v = [x-y for x, y in zip(c, b)]
    norm = math.sqrt(sum(x*x for x in u)*sum(x*x for x in v))
    if norm < 1e-8:
        return 0
    return math.degrees(math.acos(max(-1, min(1, sum(x*y for x, y in zip(u,v))/norm))))


def fingers_up(points):
    if len(points) != 21:
        return [False]*5
    d = math.dist
    result = [angle(points[2], points[3], points[4]) > 150 and
              d(points[4], points[5]) > 1.15*d(points[3], points[5])]
    for base in (5, 9, 13, 17):
        pip, dip, tip = base+1, base+2, base+3
        result.append(angle(points[base], points[pip], points[tip]) > 155 and
                      angle(points[pip], points[dip], points[tip]) > 150 and
                      d(points[tip], points[0]) > 1.1*d(points[pip], points[0]))
    return result


class StrokeTracker:
    def __init__(self):
        self.reset()

    def reset(self):
        self.previous = self.raw = self.started = self.last_time = None

    def update(self, point, drawing, now, frame_size):
        if not drawing or point is None:
            self.reset()
            return None
        if self.raw is not None and (math.dist(point, self.raw) > math.hypot(*frame_size)*0.12
                                     or now-self.last_time > 0.25):
            self.reset()
        self.raw, self.last_time = point, now
        if self.started is None:
            self.started, self.previous = now, point
            return None
        if now-self.started < 0.08:
            self.previous = point
            return None
        movement = math.dist(point, self.previous)
        if movement < 2:
            return None
        alpha = min(0.85, 0.25+movement/60)
        filtered = tuple(a+alpha*(b-a) for a,b in zip(self.previous,point))
        segment = tuple(tuple(round(v) for v in p) for p in (self.previous,filtered))
        self.previous = filtered
        return segment
