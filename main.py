from graphqlclient import GraphQLClient
import json
import tweepy
import matplotlib.pyplot as plt
from upsetFactor import getUpsetFactor
from time import sleep
from collections import Counter
import numpy as np
import time

# start.gg stuff
authToken = ''
apiVersion = ''
client = GraphQLClient('https://api.start.gg/gql/' + apiVersion)
client.inject_token('Bearer ' + authToken)

# some helper functions
def removeWhiteSpace(str_):
  while " " in str_:
    str_ = str_.replace(" ", "")
  return str_

def removeDuplicates(list_):
  l = []
  for obj in list_:
    if obj not in l:
      l.append(obj)
  return l

def checkUpset(set):
    if set['displayScore'] == "DQ": return None
    players = []

    player1 = set['slots'][0]['entrant']
    player2 = set['slots'][1]['entrant']

    players.append(player1)
    players.append(player2)

    if set['winnerId'] == player1['id']:
        winner = player1
        loser = player2
    else:
        winner = player2
        loser = player1
    
    if winner['initialSeedNum'] > loser['initialSeedNum']:
        
        if player1['name'] == "C-" or player2['name'] == "C-": # lol
           set['displayScore'] = set['displayScore'].replace("C-", "C minus")
           
        s = set['displayScore'].split("-")
        gameCount = [s[0][-2], s[1][-1]]
        gameCount.sort(reverse=True)
        record = "-".join(gameCount)

        up = getUpsetFactor(winner['initialSeedNum'], loser['initialSeedNum'])
        parsedSet = {
            "upsetFactor": up,
            "round": set['fullRoundText'],
            "info": f"In {set['fullRoundText']}, {winner['name']} (seed: {winner['initialSeedNum']}) beat {loser['name']} (seed: {loser['initialSeedNum']}) {record} for an upset factor of {up}"
        }

        return parsedSet
    
def getRecentBairs():
   result = client.execute('''
        query FindBairs($perPage: Int, $coordinates: String!, $radius: String!) {
        tournaments(query: {
            perPage: $perPage
            filter: {
            location: {
                distanceFrom: $coordinates,
                distance: $radius
            }
            past: true
            }
        }) {
            nodes {
            id
            name
            slug
            events {
                id
                slug
                name
            }
            }
        }
        }''',
        {
        "perPage": 2,
        "coordinates": "40.179272,-75.105637",
        "radius": "5mi"
    })
   
   parsedResults = json.loads(result)['data']['tournaments']['nodes']
   return parsedResults

def getRecentSinglesUltBracketInfo():
  tournaments = getRecentBairs()
  for tourney in tournaments:
    if "B-A" in tourney['name']:
        for event in tourney['events']:
            if event['name'] == "SSBU - 1v1":
                return {"id": event['id'], "tourney": tourney['name'], "link": "start.gg/" + event['slug']}

# main 'get' function
def getSetsFromEvent(SinglesID, page):
  sets = client.execute('''
  query EventSets($eventId: ID!, $page: Int!, $perPage: Int!) {
    event(id: $eventId) {
      id
      name
      sets(
        page: $page
        perPage: $perPage
        sortType: STANDARD
      ) {
        pageInfo {
          total
          totalPages
        }
        nodes {
          fullRoundText
          winnerId
          displayScore
          slots {
            entrant {
              id
              name
              initialSeedNum
            }
          }
        }
      }
    }
  }''',
  {
    "eventId": SinglesID,
    "page": page,
    "perPage": 5
  })
  return sets

def getFinalUpsetList(upsets):
    def getUP(element):
        return element['upsetFactor']
   
    final = []
    upsets.sort(reverse = True, key=getUP)
    for upset in upsets:
        final.append(upset['info'])

    final = removeDuplicates(final)
    return final

def getTotalUpsetFactor(upsets):
    totalUpsetFactor = 0
    for s in upsets:
       totalUpsetFactor += s['upsetFactor']
    return totalUpsetFactor

def getAllInfo():
    upsets = []

    info = getRecentSinglesUltBracketInfo()
    singlesID = info['id']
    parsedSets = json.loads(getSetsFromEvent(singlesID, 1))
    pages = parsedSets['data']['event']['sets']['pageInfo']['totalPages']

    for page in range(pages):
      sets = getSetsFromEvent(singlesID, page)
      parsedSets = json.loads(sets)
      for set_ in parsedSets['data']['event']['sets']['nodes']:
        checked = checkUpset(set_)
        if checked:
            upsets.append(checked)

    finalUpsets = getFinalUpsetList(upsets)
    totalUpsetFactor = getTotalUpsetFactor(upsets)
    return {"upsets": finalUpsets, 
            "totalUpsetFactor": totalUpsetFactor,
            "link": info['link'],
            "tourneyName": info['tourney']
            }

def makeThread():
    info = getAllInfo()

    # twitter stuff
    API_KEY = ""
    API_KEY_SECRET = ""
    ACCESS_TOKEN = ""
    ACCESS_TOKEN_SECRET = ""
    BEARER = ""
    CLIENT_ID = ""
    CLIENT_ID_SECRET = ""

    tclient=tweepy.Client(bearer_token=BEARER, consumer_key=API_KEY, consumer_secret=API_KEY_SECRET, access_token=ACCESS_TOKEN, access_token_secret=ACCESS_TOKEN_SECRET)
    
    upsets = info['upsets']   
    totalUpsetFactor = info['totalUpsetFactor']
    link = info['link']
    tourneyName = info['tourneyName']

    before = tclient.create_tweet(text=f"Upsets for {tourneyName}! Total upset factor was {totalUpsetFactor}! \n Link: {link}")
    for upset in upsets:
        before = tclient.create_tweet(in_reply_to_tweet_id=before.data['id'], text=upset)

# other stuff besides weekly thing
# ---------------------------------------------------------------------------------

def getBairs(page):
  tournamentsWithSSBU = client.execute(
    '''
    query TournamentsByVideogames($perPage: Int, $page: Int, $videogameIds: [ID], $coordinates: String, $radius: String){
    tournaments(query: {
      perPage: $perPage
      page: $page
      sortBy: "startAt desc"
      filter: {
        past: true
        videogameIds: $videogameIds
        location: {
          distanceFrom: $coordinates,
          distance: $radius
        }
      }
    }) {
    pageInfo {
          total
          totalPages
        }
      nodes {
        events {
          name
          id
          numEntrants
        }
        name
      }
    }
  },''',
    {
    "perPage": 50,
		"page": page,
    "videogameIds": [1386],
    "coordinates": "40.179272,-75.105637",
    "radius": "5mi"
  })

  parsed = json.loads(tournamentsWithSSBU)
  tournaments = parsed['data']['tournaments']['nodes']
  pages = parsed['data']['tournaments']['pageInfo']['totalPages']
  bairs = []
  for tournament in tournaments:
     if "b-a" in tournament['name'].lower() and "On-Line" not in tournament['name']:
        bairs.append(tournament)
  return {
     "bairs": bairs,
     "pages": pages
  }

def getAllBairs():
  allBairs = []
  bairs = getBairs(1)
  pages = bairs['pages']
  allBairs = allBairs + bairs['bairs']
  i = 2
  while(i <= pages):
    allBairs = allBairs + getBairs(i)['bairs'] 
    i+= 1
  return allBairs

def getSinglesEventForEachBairs():
  info = []
  bairs = getAllBairs()
  for bair in bairs:
    events = bair['events']
    for event in events:
        if event['name'] == 'SSBU Singles' or event['name'] == 'Friday Bracket' or event['name'] == 'Singles - 1v1' or event['name'] == 'SSBU - 1v1':
          info.append({"name": bair['name'], "event": event})
          break
  return info

def getAttendeesForEachBairs():
  list_ = []
  for bair in getSinglesEventForEachBairs():
    list_.append({"name": bair['name'], "attendees": bair['event']['numEntrants']})
  return list_

def graphAttendeesForEachBairs():
  data = getAttendeesForEachBairs()

  x = []
  y = []

  for bairs in data:
    x.append(bairs['name'])
    y.append(bairs['attendees'])

  plt.rcParams.update({'font.size': 3})

  x = np.array(x)
  y = np.array(y)

  plt.barh(x, y)
  plt.show()

def getWinnerOfEvent(eventID): # todo get id of people's user not the player because itd be different?
   winner = client.execute('''
      query EventStandings($eventId: ID!, $page: Int!, $perPage: Int!) {
        event(id: $eventId) {
          id
          name
          standings(query: {
            perPage: $perPage,
            page: $page
          }){
            nodes {
              placement
              entrant {
                id
                name
              }
            }
          }
        }
      },''',
      {
        "eventId": eventID,
        "page": 1,
        "perPage": 1
      }
    )
   winner = json.loads(winner)
   return winner['data']['event']['standings']['nodes'][0]['entrant']['name']

def dumpWinnersOfEachBairs(): # this takes quite a while because of rate limits
  winners = {}
  info = getSinglesEventForEachBairs()
  i = 0
  for bair in info:
    i += 1
    if i == 50:
        time.sleep(61)
        i = 0
    id_ = bair['event']['id']
    winner = getWinnerOfEvent(id_)
    winners[bair['name']] = winner
    print(winners)
  
  with open('winners.json', 'w') as file:
     json.dump(winners, file, indent=6)
  
  return winners

def loadWinners():
  with open('winners.json', 'r') as file:
    winners = json.load(file)

  return winners

def getModeOfWinners():
  w = loadWinners()
  allWinners = list(w.values())
  for i, winner in enumerate(allWinners):
    if winner.split("|").__len__() > 1:
      winner = winner.split("|")[1][1::]
    allWinners[i] = winner
  allWinners = Counter(allWinners)
  return allWinners

def makePieChartOfWinners():
  winners = getModeOfWinners()

  vals = []
  winnerNames = []
  
  for key, value in dict(sorted(winners.items(), key=lambda item: item[1], reverse=False)).items():
     vals.append(value)
     winnerNames.append(key)

  rects = plt.barh(winnerNames, vals)

  for rect in rects:
    plt.text(1 + rect.get_width(), rect.get_y()+0.5*rect.get_height(), # THANK YOU STACKOVERFLOW 🔥🔥🔥🔥
                  '%d' % int(rect.get_width()),
                  ha='center', va='center')

  plt.show()

# makeThread()

