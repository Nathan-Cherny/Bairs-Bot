from graphqlclient import GraphQLClient
import json
import tweepy
from upsetFactor import getUpsetFactor

def get1v1Id(parsed):
  for tourney in parsed:
      if "B-Airs" in tourney['name']:
          for event in tourney['events']:
              if event['name'] == "SSBU - 1v1":
                  return {"id": event['id'], "tourney": tourney['name']}


def checkUpset(set):
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
        up = getUpsetFactor(winner['initialSeedNum'], loser['initialSeedNum'])
        parsedSet = {
            "upsetFactor": up,
            "round": set['fullRoundText'],
            "info": f"In {set['fullRoundText']}, {winner['name']} (seed: {winner['initialSeedNum']}) beat {loser['name']} (seed: {loser['initialSeedNum']}) for an upset factor of {up}"
        }
        return parsedSet


authToken = ''
apiVersion = 'alpha'
client = GraphQLClient('https://api.start.gg/gql/' + apiVersion)
client.inject_token('Bearer ' + authToken)

API_KEY = ""
API_KEY_SECRET = ""
ACCESS_TOKEN = ""
ACCESS_TOKEN_SECRET = ""
BEARER = ""
CLIENT_ID = ""
CLIENT_ID_SECRET = ""


results = client.execute('''
query FindBairs($perPage: Int, $coordinates: String!, $radius: String!) {
  tournaments(query: {
    perPage: $perPage
    filter: {
      location: {
        distanceFrom: $coordinates,
        distance: $radius
      }
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
  "perPage": 10,
  "coordinates": "40.179272,-75.105637",
  "radius": "5mi"
})

parsedResults = json.loads(results)['data']['tournaments']['nodes']

Singles = get1v1Id(parsedResults)
SinglesID = Singles['id']
TourneyName = Singles['tourney']

def getSetsFromEvent(ID, page):
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
    "perPage": 20
  })
  return sets

def makeThread(tweet):
    parsedSets = json.loads(getSetsFromEvent(SinglesID, 1))
    pages = parsedSets['data']['event']['sets']['pageInfo']['totalPages']
    upsets = []

    for page in range(pages):
      sets = getSetsFromEvent(SinglesID, page)
      parsedSets = json.loads(sets)
      for set_ in parsedSets['data']['event']['sets']['nodes']:
          checked = checkUpset(set_)
          if checked:
              upsets.append(checked)

    def getUP(element):
        return element['upsetFactor']

    final = []
    upsets.sort(reverse = True, key=getUP)
    for upset in upsets:
        final.append(upset['info'])
    
    print(final)

    """
    if tweet:
      before = tclient.create_tweet(text=f"Upsets for {TourneyName}! If there are any errors, please let me know!")
      for upset in final:
         before = tclient.create_tweet(in_reply_to_tweet_id=before.data['id'], text=upset)
  """

tclient=tweepy.Client(bearer_token=BEARER, consumer_key=API_KEY, consumer_secret=API_KEY_SECRET, access_token=ACCESS_TOKEN, access_token_secret=ACCESS_TOKEN_SECRET)

makeThread(True)