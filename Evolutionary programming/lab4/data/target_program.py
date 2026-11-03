"""Synthetic, side-effect-free integer rules used as the coverage subject."""


def order(x, y, z):
    if x < 0:
        if y == -17:
            return 1
        return 2
    elif x == 37:
        if y == x + 11:
            if z == y - 7:
                return 3
            return 4
        return 5
    elif x + y > 80:
        if z < 0:
            return 6
        return 7
    return 8


def shipping(x, y, z):
    if x > 60:
        if y < -40:
            if z == 2 * x + y:
                return 1
            return 2
        return 3
    elif x == -61:
        if y == 23:
            if z == 7:
                return 4
            return 5
        return 6
    elif y - z > 40:
        return 7
    return 8


def admission(x, y, z):
    if x * x < 100:
        if y == 11:
            if z == x + y:
                return 1
            return 2
        return 3
    elif x < -60:
        if y + z == 0:
            return 4
        return 5
    elif x == 40:
        if y == 37:
            if z == -11:
                return 6
            return 7
        return 8
    return 9
