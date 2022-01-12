import requests
import json
import config
import random
from time import sleep
from requests_oauthlib import OAuth1Session
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from apscheduler.schedulers.blocking import BlockingScheduler
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument("--headless")
bearer_token = config.BEARER_TOKEN
consumer_key = config.API_KEY
consumer_secret = config.API_KEY_SECRET

search_url = "https://api.twitter.com/2/tweets/search/recent"

#Query
query_params = {'query': '(3DArt OR b3d OR blender3D) -lewd -nsfw -2d -giveaway -drop -nft -nfts -xxx -porn -adult -nftcollector -tezos -btc -eth has:media has:hashtags', 'max_results': 35}

def bearer_oauth(r):
    #Method required by bearer token authentication.
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2RecentSearchPython"
    return r

def connect_to_endpoint(url, params):
    response = requests.get(url, auth=bearer_oauth, params=params)
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()

def authorize():
    # Get request token
    request_token_url = "https://api.twitter.com/oauth/request_token"
    oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)
    try:
        fetch_response = oauth.fetch_request_token(request_token_url)
    except ValueError:
        print(
            "There may have been an issue with the consumer_key or consumer_secret you entered."
        )
    resource_owner_key = fetch_response.get("oauth_token")
    resource_owner_secret = fetch_response.get("oauth_token_secret")
    print("Got OAuth token: %s" % resource_owner_key)

    # Get authorization
    base_authorization_url = "https://api.twitter.com/oauth/authorize"
    authorization_url = oauth.authorization_url(base_authorization_url)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
    driver.get(authorization_url)
    driver.maximize_window()
    sleep(3)

    #enter username
    driver.find_element(By.ID, "username_or_email").send_keys(config.username)
    driver.find_element(By.ID, "password").send_keys(config.password)
    driver.find_element(By.ID, "allow").click()
    sleep(3)

    strUrl = driver.current_url
    verifier = strUrl.split('=')[2]

    # Get the access token
    access_token_url = "https://api.twitter.com/oauth/access_token"
    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        verifier=verifier,
    )
    oauth_tokens = oauth.fetch_access_token(access_token_url)

    access_token = oauth_tokens["oauth_token"]
    access_token_secret = oauth_tokens["oauth_token_secret"]

    # Make the request
    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret,
    )
    driver.quit()
    return oauth

def like_and_retweet():

    oauth = authorize()
    json_response = connect_to_endpoint(search_url, query_params)

    for tweet in json_response['data']:
            payload = {"tweet_id": tweet.get('id')}
            raw_text = tweet.get('text')
            sliced = raw_text[4:]
            handle = {"usernames": str(sliced.split(':')[0])}

            #Like
            response = oauth.post(
                "https://api.twitter.com/2/users/{}/likes".format(config.id), json=payload
            )
            
            #Exit if a 429
            if response.status_code == 429:
                print("429: Cooldown Required")
                break

            #Retweet
            print("Response code: {}".format(response.status_code))
            response = oauth.post(
                "https://api.twitter.com/2/users/{}/retweets".format(config.id), json=payload
            )

            #Exchange @handle for user id
            response = oauth.get(
                "https://api.twitter.com/2/users/by", params=handle
            )

            json_response = response.json()
            try:
                follow_id = {"target_user_id": json_response['data'][0].get('id')}
            except:
                continue

            #Random Follow
            chance = random.randint(0,34)
            print(chance)
            if chance == 16:
                response = oauth.post(
                    "https://api.twitter.com/2/users/{}/following".format(config.id), json=follow_id
                )

            if response.status_code != 200:
                raise Exception(
                    "Request returned an error: {} {}".format(response.status_code, response.text)
                )
    main()

def job():
    like_and_retweet()

def main():
    print("start")
    scheduler = BlockingScheduler()
    scheduler.add_job(job, 'interval', hours=1)
    scheduler.start()

if __name__ == "__main__":
    main()
