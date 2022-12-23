from graphqlclient import GraphQLClient
import json
import tweepy

def get1v1Id(parsed): # remember to make this not a dictionary later
    results = []
    for tourney in parsed:
        if "B-Airs" in tourney['name']:
            for event in tourney['events']:
                if event['name'] == "SSBU - 1v1":
                    results.append({"id": event['id'], "tourney": tourney['name']})
    return results

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
        parsedSet = {
            "upsetFactor": winner['initialSeedNum'] - loser['initialSeedNum'],
            "round": set_['fullRoundText'],
            "info": f"In {set_['fullRoundText']}, {winner['name']} (seed: {winner['initialSeedNum']}) beat {loser['name']} (seed: {loser['initialSeedNum']}) for an upset factor of {winner['initialSeedNum'] - loser['initialSeedNum']}"
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

# not gonna post this on github lol but its in the actual file idk how to use github bruh

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

SinglesID = get1v1Id(parsedResults)[1]['id']

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
  "page": 1,
  "perPage": 999
})

parsedSets = json.loads(sets)
upsets = []
for set_ in parsedSets['data']['event']['sets']['nodes']:
    checked = checkUpset(set_)
    if checked:
        upsets.append(checked)

def getUpsetFactor(element):
    return element['upsetFactor']

final = []
upsets.sort(reverse = True, key=getUpsetFactor)
for upset in upsets:
    final.append(upset['info'])

print(final)
client=tweepy.Client(bearer_token=BEARER, consumer_key=API_KEY, consumer_secret=API_KEY_SECRET, access_token=ACCESS_TOKEN, access_token_secret=ACCESS_TOKEN_SECRET)

def makeThread(data):
    before = client.create_tweet(text=f"Here is an automated thread of all the upsets for Bairs 358. Hope this works. This soon will be on a seperate account!")
    for upset in final:
        before = client.create_tweet(in_reply_to_tweet_id=before.data['id'], text=upset)
        
makeThread(final)