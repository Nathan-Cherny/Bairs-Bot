from main import *
import json

"""
{
  "Authorization": "Bearer 93634826a62dcc30116ac70d0a71d43a"
}
"""

def readJSON():
    with open("bigboyplayers.json", "r") as f:
        return json.load(f)

def getSinglesIdFromEvents(events):
    for event in events:
        if event['name'] == 'SSBU Singles' or event['name'] == 'Friday Bracket' or event['name'] == 'Singles - 1v1' or event['name'] == 'SSBU - 1v1':
            return event['id']
    return None

def removePlayerSponsor(player):
    if "|" in player:
        return removeWhiteSpace(player.split("|")[-1])
    return player

bigboyplayers = readJSON()

def createDataDictionary():
    dictionary = {}
    playerNames = [player[0] for player in bigboyplayers]
    
    i = 0
    j = 0

    while(i < len(playerNames)):
        playerDict = {"placements": 0}
        while(j < len(playerNames)):
            playerDict[playerNames[j]] = [0, 0] # (sets, games)
            j += 1

        dictionary[playerNames[i]] = playerDict
        
        i += 1
        j = 0
        

    return dictionary
      
def getAllSetsFromEvent(tourney):
    events = tourney[0]["events"]
    
    singlesID = getSinglesIdFromEvents(events)
    if not singlesID:
        print(f"there isnt a singles bracket for {tourney}")
        return

    allSets = []
    parsedSets = json.loads(getSetsFromEvent(singlesID, 1))
    pages = parsedSets['data']['event']['sets']['pageInfo']['totalPages']

    for page in range(pages):
      sets = getSetsFromEvent(singlesID, page)
      parsedSets = json.loads(sets)
      for set_ in parsedSets['data']['event']['sets']['nodes']:
        allSets.append(set_)

    return allSets

def parseAllSets(allSets):
    allParsedSets = []
    for set_ in allSets:
        parsedSet = {}

        player1 = set_['slots'][0]['entrant']['id']
        player2 = set_['slots'][1]['entrant']['id']

        bigboyplayerIds = [bigboyplayer[-1] for bigboyplayer in bigboyplayers]

        if set_['displayScore'] != "DQ" and player1 in bigboyplayerIds and player2 in bigboyplayerIds:

            s = set_['displayScore'].split("-")
            gameCount = [s[0][-2], s[1][-1]] # if someoen has a - in their tag
            parsedSet["winner"] = {"id": set_['slots'][0]['entrant']['id'], "tag": set_['slots'][0]['entrant']['name'], "games": int(gameCount[0])}
            parsedSet["loser"] = {"id": set_['slots'][1]['entrant']['id'], "tag": set_['slots'][1]['entrant']['name'], "games": int(gameCount[1])}

            allParsedSets.append(parsedSet)
    
    return allParsedSets

def compileData():
    dictionary = createDataDictionary()
    parsedSets = parseAllSets(getAllSetsFromEvent(getRecentBairs()))

    for set_ in parsedSets:
        winner = set_['winner']
        loser = set_['loser']

        winvlose4Winner = dictionary[removePlayerSponsor(winner['tag'])][removePlayerSponsor(loser['tag'])]
        winvlose4Loser = dictionary[removePlayerSponsor(loser['tag'])][removePlayerSponsor(winner['tag'])]

        winvlose4Winner[0] += 1
        winvlose4Winner[1] += winner['games']

        winvlose4Loser[1] += loser['games']

    return dictionary
    

"""
getting every bairs and their id - maybe like 50 queries? not bad

then to reduce query complexity do a different query using the ids for the sets

doubling scores?

"""