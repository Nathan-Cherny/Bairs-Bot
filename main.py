from graphqlclient import GraphQLClient
import json
import requests
import matplotlib.pyplot as plt
from upsetFactor import getUpsetFactor
from time import sleep
from collections import Counter
import numpy as np
from dotenv import load_dotenv
import time
import os

load_dotenv()

# start.gg stuff
authToken = os.getenv("authToken")
apiVersion = 'alpha'
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
        "perPage": 3,
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

def getHTML(upsets):
  def getUP(element):
    return element['upsetFactor']
  
  def getInfo(element):
    return element['info']
  
  sort_ = []
  upsets.sort(reverse = True, key=getUP)
  for upset in upsets:
    sort_.append(upset)

  final = []
  values = []
  for upset in sort_:
    if(upset["info"] not in values):
      values.append(upset['info'])
      final.append(upset)

  red = 50
  blue = 125
  green = 125
  colors = [(red, blue, green)]

  i = 0
  while i < final[0]["upsetFactor"]:
    red -= 15
    blue += 15
    green += 15
    colors.append((red, blue, green))
    i += 1

  # colors.reverse()

  htmlUpsets = ""
  for upset in final:
    htmlUpsets += f"<p style=\"background-color: rgb{colors[upset['upsetFactor']]}\">{upset['info']}<br></p>\n\t\t\t\t"

  HTML = f"""
  <!DOCTYPE html>
  <html>
    <head>
      <style>
        p, body{{
          margin: 0;
        }}

        p{{
          padding: 5px;
          height: 100%;
        }}
      </style>
    </head>
    <body>
      <div style="display: flex; flex-direction: column; height: 100vh; justify-content: space-between">
        {htmlUpsets}
      </div>
    </body>
  </html>

  """
  with open("upsets.html", "w") as file:
    file.write(HTML)

def getAllInfo():
    upsets = []

    info = getRecentSinglesUltBracketInfo()

    print(info)
    singlesID = info['id']
    parsedSets = json.loads(getSetsFromEvent(singlesID, 1))
    pages = parsedSets['data']['event']['sets']['pageInfo']['totalPages']
    totalSets = 0

    for page in range(pages):
      sets = getSetsFromEvent(singlesID, page)
      parsedSets = json.loads(sets)
      print(parsedSets['data']['event']['sets']['nodes'])
      for set_ in parsedSets['data']['event']['sets']['nodes']:
        totalSets += 1
        checked = checkUpset(set_)
        if checked:
            upsets.append(checked)

    finalUpsets = getFinalUpsetList(upsets)
    totalUpsetFactor = getTotalUpsetFactor(upsets)
    html = getHTML(upsets)
    return {"upsets": finalUpsets, 
            "totalUpsetFactor": totalUpsetFactor,
            "link": info['link'],
            "tourneyName": info['tourney'],
            "totalSets": totalSets,
            "averageUpsetFactor": totalUpsetFactor/totalSets
            }


def makeThread():
  info = getAllInfo()
  CHANNEL_ID = "1533498455144792244"

  url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"

  headers = {
      "Authorization": f"Bot {os.getenv("API_KEY")}",
      "Content-Type": "application/json"
  }

  data = {
      "content": "\n".join(info['upsets'])
  }

  response = requests.post(
      url,
      headers=headers,
      json=data
  )

  return f"<p>Discord response: {response.status_code}</p>"



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
    "coordinates": "40.z179272,-75.105637",
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

def graphChartOfWinners():
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

# ----------------------------------------------------------------------