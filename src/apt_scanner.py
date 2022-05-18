import datetime
import requests
import time
import hashlib

from twilio.rest import Client

# url = 'https://ttp.cbp.dhs.gov/schedulerapi/slots?orderBy=soonest&limit=3&locationId=5142&minimum=1'

# START CONFIG

# List of airport codes here:
#  https://ttp.cbp.dhs.gov/schedulerapi/locations/?temporary=false&inviteOnly=false&operational=true&serviceName=Global%20Entry

code_num = [
    '5140', 
    '5142', 
    '6480',
    ]

code_to_airport = {
    '5140': 'JFK',
    '5142': 'IAD',
    '6480': 'Bowling Greene',
}

# Too lazy to make a person obj lol
config_dict = {
    '5142': 'Jojo',
    '5140': 'thommy',
    '6480': 'thommy',
}

phone_dict = {
    'Jojo': '7035551234',
    'thommy': '7035551234',
}

# only look for dates before this
desired_dates = {
    'thommy': '2022-07-01T00:00',
    'Jojo': '2022-04-05T00:00',
}

TEST_MODE = False

# END CONFIG

print('starting app bro bro. test mode:', TEST_MODE)

ttl_cache = {}

def send_text(apt_time, airport, person):
    account_sid = 'twilio_sid'
    auth_token = 'twilio_token'
    from_number = 'twilio_num'
    to_number = phone_dict[person]

    print('NEW DATE! sending texts for: ', person, apt_time, airport)

    client = Client(account_sid, auth_token)
    body = 'Yello, {}! Global Entry Appointment available! {} at {}. Hurry! https://ttp.cbp.dhs.gov/'.format(person, apt_time, airport)
    client.messages.create(body=body, to=to_number, from_=from_number)
    client.messages.create(body=body, to='7035551234', from_=from_number) # i also send it to myself to ensure that the app is working properly


def should_send_text(person, code, apt_time):
    """
    Checks to see if we should send text based on ttl cache. 
    Returns true if we should send, false if else
    """

    # hashing from biggest
    hash_obj = person + code + apt_time
    date_hash = hashlib.md5(hash_obj.encode()).hexdigest()
    now = datetime.datetime.now()
    print('hash', hash_obj, now, date_hash)

    # if it exists in hash
    if date_hash in ttl_cache:
        # if time in cache is older than one hour, update with now() and send text
        if ttl_cache.get(date_hash) < now - datetime.timedelta(hours=1):
            ttl_cache[date_hash] = now
            print('hash exists but > 60 minutes, sending text')
            return True
        # if time in cache was added less than an hour ago, don't send text
        print('hash exists within 60 minutes, not sending text')
        return False

    # if it doesn't exist in cache, add it and send text
    ttl_cache[date_hash] = now
    print('hash does not exist, sending text')
    return True
                

def check_appointments(res, code, person):

    # get desired dates for each person
    desired_date = desired_dates.get(person)

    for apt in res:
        apt_time = apt['startTimestamp']
        apt_time = datetime.datetime.strptime(apt_time, '%Y-%m-%dT%H:%M')
        try:
            desired_date = datetime.datetime.strptime(str(desired_date), '%Y-%m-%dT%H:%M')
        except Exception:
            desired_date = datetime.datetime.strptime(str(desired_date), '%Y-%m-%d %H:%M:%S')
        if (desired_date > apt_time):
            # format date -- '%Y-%m-%dT%H:%M' -- '%m.%d.%Y %I:%M %p'
            apt_time = datetime.datetime.strftime(apt_time, '%m.%d.%Y %I:%M %p')

            # TTL cache
            if should_send_text(person, code, apt_time):
                if not TEST_MODE:
                    send_text(apt_time, code_to_airport.get(code), person)
                else:
                    print('TEST: Yello, {}! Global Entry Appointment available! {} at {}. Hurry! https://ttp.cbp.dhs.gov/'.format(
                        person, apt_time, code_to_airport.get(code)))


# MAIN
def main():
    while (True):
        for code in code_num:
            url = 'https://ttp.cbp.dhs.gov/schedulerapi/slots?orderBy=soonest&limit=3&locationId={}&minimum=1'.format(code)
            res = []
            try:
                res = requests.get(url).json()
            except Exception:
                print('errored, continuing', Exception)

            if not len(res) == 0:
                # get people for code
                person = config_dict.get(code)

                # check appointments for each person
                check_appointments(res, code, person)
        time.sleep(5)

if __name__ == "__main__":
    main()
