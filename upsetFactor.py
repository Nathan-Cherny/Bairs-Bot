from collections import Counter

def returnPlacementsByAttendees(attendeeCount):
    placements = [
        1,
        2,
        3,
        4
    ]

    placement = 5
    factor = 2

    while placements.__len__() < attendeeCount:
        for i in range(factor): # first loop in pair (5 in the pair of 5 and 7)
            placements.append(placement)
        for i in range(factor): # second loop in pair (7 in the pair of 5 and 7) and account for factor
            placements.append(placement + factor)
        factor = factor * 2
        placement = placement + factor
        
    placements = placements[:attendeeCount]
    return placements

def breakList(l):
    counter = Counter(l)
    common = counter.most_common()

    broken = []
    for i in common:
        new = []
        for j in range(i[1]): # how common it is
            new.append(i[0])
        broken.append(new)
    return sorted(broken)

def getPlacementBySeed(seed, broken):
    i = 0
    for l in broken:
        for v in l:
            i += 1
            if i == seed:
                return broken.index(l)

placements = returnPlacementsByAttendees(100)
broken = breakList(placements)

def getUpsetFactor(winnerSeed, loserSeed):
    # first we need to determine what placement the seed is projected to get
    # then we subtract the higher ones index by the lower one
    # thats your upset factor

    a = getPlacementBySeed(winnerSeed, broken)
    b = getPlacementBySeed(loserSeed, broken)
    return a - b


