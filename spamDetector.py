import tweepy
from tweepy import StreamListener
from tweepy import Stream
import json, time, sys
import time

import difflib

consumer_key = 'yL8Ovw2FIrAkp6f1aaeep4gj1'
consumer_secret = 'LSuMNmgKpcJpiOm1KyORiv9v2rdYzIxHEv18ia82HKXoTvCKDL'
access_token = '320231359-e6vNkdXHLXwN2swrpwJNNwACiRho9QlqR2vMFyjR'
access_token_secret = 'fV2oWtQUpj1P9FOZjPvJrWdK5Sxz7i6gK4uRkiWprEZAl'
 
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
 
api = tweepy.API(auth)

def is_spammer(user):
    frp = friend_ratio_point(user)
    fup = fake_username_point(user.name)
    tp = temporal_point(user)
    fafp = favorites_and_followers_point(user)
    raop = retweeted_and_original_point(user)
    dtp = dupl_tweets_point(user)
    total_points = frp + fup + tp + fafp + raop + dtp
    print("friend_ratio_point: ", frp, '\n')
    print("fake_username_point: ", fup, '\n')
    print("temporal_point: ", tp, '\n')
    print("favorites_and_followers_point: ", fafp, '\n')
    print("retweeted_and_original_point: ", raop, '\n')
    print("dupl_tweets_point: ", dtp, '\n')
    return total_points

def friend_ratio_point(user):
    FRIEND_RATIO = 5
    if user.followers_count > 0:
        if ( user.friends_count / float(user.followers_count) ) > FRIEND_RATIO:
            return 1
        else:
            return 0
    else:
        return 1
    
def fake_username_point(string):
    DIGITS_RATIO = 0.5
    digits = 0
    for ch in string:
        if ch.isdigit():
            digits += 1
    if (digits / float(len(string)) > DIGITS_RATIO):
        return 1
    else:
        return 0

def temporal_point(user):
    MAX_TWEETS = 5
    DEV_RANGE = 60
    EXP_RANGE = 600
    
    timeline = tweepy.Cursor(api.user_timeline, id=user.screen_name).items(MAX_TWEETS)

    values = []
    for tweet in timeline:
        time_str = tweet.created_at
        time_float = time.mktime(time_str.timetuple())
        values.append(time_float)

    values.sort
    ranges = []
    for i in range(0,len(values)- 1):
       ranges.append(values[i] - values[i + 1])

    expect = 0
    for elem in ranges:
        expect += elem
    expect /= len(ranges)

    deviation = 0

    for elem in ranges:
        deviation += (elem - expect) ** 2

    deviation /= (len(ranges) - 1)
    if (expect < EXP_RANGE) or (deviation < DEV_RANGE ** 2):
        return 1
    else:
        return 0

def favorites_and_followers_point(user):
    FAVORITES_FOLLOWERS_RATIO = 0.0001
    MAX_TWEETS = 10
    favorites = 0
    timeline = tweepy.Cursor(api.user_timeline, id = user.screen_name).items(MAX_TWEETS)
    for status in timeline: 
        favorites += status.favorite_count
    if (user.followers_count > 0):
        ratio = favorites / float(user.followers_count)
    else:
        return 1
    if ( ratio < FAVORITES_FOLLOWERS_RATIO ):
        return 1
    else:
        return 0

def retweeted_and_original_point(user):
    RATIO = 2
    MAX_TWEETS = 100
    timeline = tweepy.Cursor(api.user_timeline, id = user.screen_name).items(MAX_TWEETS)
    original = 0
    retweeted = 0
    for status in timeline: 
        if status.retweeted:
            retweeted += 1
        else:
            original += 1
    print("retweeted: ", retweeted, "original: ", original, '\n')
            
    if original != 0:
        ratio = retweeted / float(original)
    else:
        if retweeted != 0:
            return 1

    if (ratio > RATIO):
        return 1
    else:
        return 0

def twit_diff_point(twit_1, twit_2):
    DIFF_RATIO = 0.1
    #f1 = open("C:/Python34/dif1.txt" , "r")
    #f2 = open("C:/Python34/dif2.txt" , "r")
    #out = open("C:/Python34/result.txt" , "w")

    #lines_1 = f1.readlines()
    #lines_2 = f2.readlines()
    text_1 = twit_1.text.encode('ascii', 'ignore').decode('ascii')
    text_2 = twit_2.text.encode('ascii', 'ignore').decode('ascii')
    lines_1 = text_1.split()
    lines_2 = text_2.split()
    diff = difflib.ndiff(lines_1, lines_2)
    same_cnt = 0
    new_cnt = 0
    old_cnt = 0
    for item in diff:
        #out.write("%s\n" % item)
        #print(item)
        if (len(item) > 1) and (item[0] == ' '):
            same_cnt += 1
        if (item[0] == '+'):
            new_cnt += 1
        if (item[0] == '-'):
            old_cnt += 1
        
    #print(same_cnt,' ', new_cnt, ' ', old_cnt, '\n')
    #print(" twit1: \n", text_1, '\n', "twit2: \n", text_2, '\n')
    overall = same_cnt + new_cnt + old_cnt
    if overall == 0:
        return 1
    else:
        if (same_cnt / float(overall) > DIFF_RATIO):
            return 1
        else:
            return 0

def dupl_tweets_point(user):
    MAX_TWEETS = 5
    RATIO = 0.1
    timeline = tweepy.Cursor(api.user_timeline, id = user.screen_name).items(MAX_TWEETS)

    result = 0
    for twit_1 in timeline:
        for twit_2 in timeline:
            if twit_1.id != twit_2.id:
                result += twit_diff_point(twit_1, twit_2)
                #time.sleep(1)
        
    ratio = result / (MAX_TWEETS ** 2)
        
    if ratio > RATIO:
        return 1
    else:
        return 0

class StdOutListener(StreamListener):
    ''' Handles data received from the stream. '''

    def __init__(self, api):
        self.fo = open("C:\Python34\log.txt" , "w")
        self.api = api
        self.list = []
        
    def on_status(self, status):
        string = status.text.encode('ascii', 'ignore').decode('ascii') + '\n'

        points = is_spammer(status.user)
        if (points < 3):
            api.create_friendship(status.user.id, True)
            print(status.user.name + str(points), '\n')
            time.sleep(1)
        else:
            print(str(points))
            time.sleep(1)

        self.fo.write(string + '\n')
        return True
 
    def on_error(self, status_code):
        print('Got an error with status code: ' + str(status_code))
        return True
 
    def on_timeout(self):
        print('Timeout...')
        return True 
 
if __name__ == '__main__':
    listener = StdOutListener(api)
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

 
    user = api.get_user("bloggeroom")
    print(is_spammer(user))
    #stream = Stream(auth, listener)
    #stream.filter(follow=[], track=['Follow'])

