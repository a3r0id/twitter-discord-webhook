from json import load
from tweepy import OAuthHandler, API, StreamListener, Stream
from discord_webhook import DiscordWebhook
from requests import get

build_version = ["1", "0", "0"]

# BASIC UPDATE NOTIFICATION
r = get(("https://raw.githubusercontent.com"
    "/hostinfodev/twitter-discord-webhook/main/.version"))

current_version = r.text.strip("\n").split(".")
i = 0
for c in current_version:
    if c != build_version[i]:
        print(c + " != " + build_version[i])
        print("\nUpdate available!\nCurrent Version: %s\nUpdate Version: %s" % (".".join(build_version), r.text,))
        if i < 2:
            _=input("Update required!\nHit enter to exit...")
            exit(0)   
        break
    i += 1

# OPEN CONFIG FILE
try:
    config = dict()
    with open('config.json') as CONFIG:
        config = load(CONFIG)
except Exception as f:
    print(f)
    _ = input("Press enter to exit...")
    exit(0)
    
# PARSE CONFIG FILE
try:
    consumer = config['consumer']
    consumer_s = config['consumer_s']
    token = config['token']
    token_s = config['token_s']
    bool_only_author = config['only_push_tweets_from_author']
    users = config['usernames_to_watch']
    webhooks = config['webhook_urls']
    bool_retweet = config['retweet']
except Exception as f:
    print(f)
    _ = input("[ERROR IN CONFIGURATION FILE (config.json)] Press enter to exit...")
    exit(0)

# 0AUTH
try:
    auth = OAuthHandler(consumer, consumer_s)
    auth.set_access_token(token, token_s)
    auth.secure = True
    api = API(auth) 
except Exception as f:
    print(f)
    _ = input("[INVALID AUTH OR COULDN'T REACH TWITTER.COM] Press enter to exit...")
    exit(0)

# VALIDATE USERS TO FOLLOW AND CREATE USERS OBJECT
feed = []
for username in users:
    try:
        user = api.get_user(screen_name=username)
        feed.append(str(user.id))
    except Exception as f:
        print("[%s] -> Failed to add %s to feed! (%s)" % (username, username, str(f), ))
        continue

    print("[%s] -> Successfully added %s @%s to feed!" % (username, user.name, username, ))

# CLASS OUR STREAM LISTENER
class MyStreamListener(StreamListener):
    
    # ON STATUS
    def on_status(self, status):

        if bool_only_author and status.author.screen_name not in users:
            return 

        if bool_retweet:
            api.retweet(status.id)    

        # CALL DISCORD WEBHOOK OBJECT
        webhook = DiscordWebhook(
            url=webhooks,
            username="%s @%s" % (status.author.name, status.author.screen_name,),
            avatar_url=status.author.profile_image_url,
            content= "https://twitter.com/%s/status/%s" % (status.author.screen_name, status.id,)
            )

        # SEND TO WEBHOOK/S    
        _ = webhook.execute()
    
    # ON ERROR - RESETS STREAM
    def on_error(self, status_code):
        if status_code == 420:
            #returning False in on_error disconnects the stream
            return False        

# MAKE SURE FEED IS POPULATED W/ @ LEAST 1 VALID USER 
if not len(feed):
    _ = input("[FEED IS EMPTY - NO VALID USERS] Press enter to exit...")
    exit(0)

# INITIALIZE THE LISTENER AND STREAM
while True:
    try:
        myStreamListener = MyStreamListener()
        myStream = Stream(auth = api.auth, listener=myStreamListener)
        print("[LISTENING TO STREAM]")
        myStream.filter(follow=feed)
    except Exception as f:
        print("[ERROR] -> %s" % (f,))
        print("[RESTARTING]")