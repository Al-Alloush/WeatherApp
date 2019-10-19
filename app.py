import time
from datetime import datetime
from flask import Flask, render_template,json, jsonify, request
from flask_socketio import SocketIO
import pytz
import configparser
import requests
import sys
import redis
import pandas as pd
import numpy as np

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
cache = redis.Redis(host='redis', port=6379, charset="utf-8", decode_responses=True)


# get berlin Time Zone
tz = pytz.timezone('Europe/Berlin')
#date_now = datetime.now(tz).strftime("%Y/%m/%d %H:%M:%S")

# my API key
apiKey = 'dea1c2172d5e61f0371ad313d56189a8'

#
@app.route('/')
def index():
    return render_template("index.html")
@app.route('/home')
def home():
    return render_template("index.html")
@app.route('/news')
def news():
    return render_template("news.html")

# set the current weather in cache
def cache_current_weather(data, postal):
    print('+++++++++ - def cache_current_weather(data, dt, postal):')
    # get this data
    dt = str(data['dt']+7200)
    '''
    after check, if they're more than x times between the last insert and current time,
    maybe the API Server has not updated the data jet, for that chech the dt time '''
    # check if the dt time not existed before adding the new dt in a cdb
    if  cache.exists(postal+':current_dt', dt):
        # get the curent date with berlin timezone
        date = datetime.now(tz).strftime("%Y/%m/%d %H:%M:%S")
        # start pipelining
        pipe = cache.pipeline()
        # looping over all labels in WeatherData
        for label in data:
            '''
            because every label in weather data has special form
            use if condations to to decide which form matches with code
            '''
            if  label == 'visibility' or label == 'timezone' or label == 'name':
                #print(label + ' => ' + label +':'+ str(data[label]) )
                pipe.hset(postal+':current:'+dt, label , data[label] )
            elif label == 'weather':
                for sublabel in data[label][0]:
                    #print(label + ' => ' + sublabel +':'+ str(data[label][0][sublabel]) )
                    pipe.hset(postal+':current:'+dt, sublabel , data[label][0][sublabel] )
            elif label == 'main' or label == 'sys' or label == 'wind':
                for sublabel in data[label]:
                    #print(label + ' => ' + sublabel +':'+ str(data[label][sublabel]) )
                    pipe.hset(postal+':current:'+dt, sublabel , data[label][sublabel] )
        # End for loop

        pipe.hset(postal+':current:'+dt, 'date',date  )
        # time list
        pipe.lpush(postal+':current_dt', dt  )
        # executed pipe after setting the all pipe orders execution
        pipe.execute()

    # return the new Weather data
    return cache.hgetall(postal+':current:'+dt)

def cach_5days_weather(data, postal):
    print('+++++++++ - def cach_5days_weather(data, postal):')
    '''
    needed data inside the Weather forecast in label "list",
    and because every label inside "list" has special form
    use if condations to to decide which form matches with code
    '''
    # get the curent date with berlin timezone
    date = datetime.now(tz).strftime("%Y/%m/%d %H:%M:%S")

    for i in range(len(data['list'])):
        for label in data['list'][i]:
            #print('='+ str(data['list'][i]))
            # get and convert current utctime to strng, need this label in a variable with every loop
            dt = str(data['list'][i]['dt'])


            if cache.exists(postal+':forecast_dt', dt):
                print('true')
            else:
                print('false')
                cache.lpush(postal+':forecast_dt', dt  )

                

            if  label == 'visibility' or label == 'timezone' or label == 'name' or label == 'dt' or label == 'dt_txt':
                #print(label + ' => ' + label +':'+ str(data['list'][i][label]) )
                cache.hset(postal+':forecast:'+dt, label , str(data['list'][i][label] ))

            elif label == 'weather':
                for sublabel in data['list'][i][label][0]:
                    #print(label + ' => ' + sublabel +':'+ str(data['list'][i][label][0][sublabel]) )
                    cache.hset(postal+':forecast:'+dt, sublabel , str(data['list'][i][label][0][sublabel]) )
            elif label == 'main' or label == 'sys' or label == 'wind':
                for sublabel in data['list'][i][label]:
                    #print(label + ' => ' + sublabel +':'+ str(data['list'][i][label][sublabel]) )
                    cache.hset(postal+':forecast:'+dt, sublabel ,str(data['list'][i][label][sublabel]) )



            # add date to hash
            cache.hset(postal+':forecast:'+dt, 'add_date', date  )
            cache.hset(postal+':forecast:'+dt, 'fc_date', data['list'][i]['dt_txt'])

    print('Add,  end')


def insertInRedisTimeSeries(data, postal):
    #print(cache.execute_command("TS.ADD temp:city 1548149191 49"));
    #print(cache.execute_command("TS.ADD cloud:city 1548149191 49"));
    #print(cache.execute_command("TS.ADD hum:city 1548149191 49"));
    for i in range(len(data['list'])): # get 40 rows
        #get the label name in every row
        for label in data['list'][i]:

            if label == 'main':
                time.sleep(1)
                # get current datetime in Unix form
                date_now_utc = round(datetime.utcnow().timestamp())
                date_now_utc += 7200 # + Two hours
                # convert date_now_utc from Unix datetime to datetime
                date_now = datetime.utcfromtimestamp(date_now_utc).strftime('%Y-%m-%d %H:%M:%S')

                forecast_date =  str(data['list'][i]['dt'])
                postal = str(postal)
                date_now_utc = str(date_now_utc)
                #print(date_now_utc)

                #cache.execute_command("TS.ADD "+postal+":dt * 30 ")
                fc_date = str(data['list'][i]['dt'])


                #cache.execute_command("TS.CREATE temp RETENTION 60000 LABELS area_zip "+postal+" ")
                value_temp = str(data['list'][i]['main']['temp'])
                temp_min = str(data['list'][i]['main']['temp_min'])
                temp_max = str(data['list'][i]['main']['temp_max'])

                # ZRANGEBYSCORE 87437:temp:leabels:temp_max  6 12
                #cache.execute_command("HSET "+postal+":temp "+date_now_utc+" "+ str(data['list'][i]['main']['temp'])+" ")
                #redisTimeAdd( postal, 'temp', date_now_utc, value_temp, 'temp_max', temp_max,'temp_min', temp_min )

                '''
                cache.execute_command("HSET "+postal+":temp "+date_now_utc+" "+ str(data['list'][i]['main']['temp'])+" ")
                cache.execute_command("HSET "+postal+":leabels:"+date_now_utc+"  forecast_date "+ str(data['list'][i]['dt'])+" ")
                cache.execute_command("HSET "+postal+":leabels:"+date_now_utc+"  temp_min "+ str(data['list'][i]['main']['temp_min'])+" ")
                print(cache.execute_command("HGET 87437:leabels:"+date_now_utc+" temp_min"))



                cache.execute_command("TS.ADD "+postal+":temp "+date_now_utc+" "+ str(data['list'][i]['main']['temp'])+" ")
                cache.execute_command("TS.ADD "+postal+":temp_min "+date_now_utc+" "+ str(data['list'][i]['main']['temp_min'])+" ")
                cache.execute_command("TS.ADD "+postal+":temp_max "+date_now_utc+" "+ str(data['list'][i]['main']['temp_max'])+" ")
                cache.execute_command("TS.ADD "+postal+":pressure "+date_now_utc+" "+ str(data['list'][i]['main']['pressure'])+" ")
                cache.execute_command("TS.ADD "+postal+":pressure_sea_level "+date_now_utc+" "+ str(data['list'][i]['main']['sea_level'])+" ")
                cache.execute_command("TS.ADD "+postal+":pressure_grnd_level "+date_now_utc+" "+ str(data['list'][i]['main']['grnd_level'])+" ")
                cache.execute_command("TS.ADD "+postal+":humidity "+date_now_utc+" "+ str(data['list'][i]['main']['humidity'])+" ")
                cache.execute_command("TS.ADD "+postal+":weather_id "+date_now_utc+" "+ str(data['list'][i]['weather'][0]['id'])+" ")
                cache.execute_command("TS.ADD "+postal+":clouds "+date_now_utc+" "+ str(data['list'][i]['clouds']['all'])+" ")
                cache.execute_command("TS.ADD "+postal+":wind_speed "+date_now_utc+" "+ str(data['list'][i]['wind']['speed'])+" ")
                cache.execute_command("TS.ADD "+postal+":wind_degrees "+date_now_utc+" "+ str(data['list'][i]['wind']['deg'])+" ")
                '''

    redisTimeCount(postal,'temp')

# redis Add time series
def redisTimeAdd(path, key, timestamp, value, l1, l1v, l2,l2v):
    '''
    HSET path/key fieldName fieldValue
    TS.Add = HSET
    key (path) => postal:
    (hash Name) => temp
    field(timestamp) => date_now_utc
    value => data[temp]

    Labels:
    if added leabel for a fiels ctarte a hash with fild name, contain leabel name and leable value
    '''
    # if not null or empty
    if path:
        key = ':'+key
    #cache.execute_command("HSET "+path+""+key+" "+timestamp+" "+value+"")
    cache.execute_command("HMSET "+path+""+key+":series:"+timestamp+" "+timestamp+" "+value+"")
    if l1!='':
        cache.execute_command("HMSET "+path+""+key+":leabels:"+timestamp+" "+l1+" "+l1v+" "+l2+" "+l2v+" ")
        cache.execute_command("zadd "+path+""+key+":leabels:"+l1+" "+l1v+" "+timestamp+" ")
        cache.execute_command("zadd "+path+""+key+":leabels:"+l2+" "+l2v+" "+timestamp+" ")
        #cache.HMSET()
# redis Add time series
def redisTimeCount(path, key):
    print('1111111111111111111111111111111111111111111111111111111111111')
    print(cache.execute_command("HLEN "+path+":"+key))
    arr = len(cache.execute_command("HGETALL "+path+":"+key))
    print(arr)

def printJson5DaysResponse(data, postal, country):
    print('-----------------------------')
    print('*****************************')

    for i in range(len(data['list'])):
        print("postal:{}, city:{} ".format(postal,country ))
        print("_____________________")
        for label in data['list'][i]:
            if label == 'weather':
             print(label,' -> ',data['list'][i][label][0])
            else:
                print(label,' -> ',data['list'][i][label])
        print('============================================')

def get_current_weather(api_key, location,type):
    url = "https://api.openweathermap.org/data/2.5/weather?{}={}&units=metric&APPID={}".format(type,location, api_key)
    response = requests.get(url)
    return response.json()
def get_n5days_weather(api_key, location,type):
    url = "https://api.openweathermap.org/data/2.5/forecast?{}={}&units=metric&APPID={}".format(type,location, api_key)
    response = requests.get(url)
    return  response.json()


# get weather by postal and country
@socketio.on('weather_current_location')
def handle_message(message):

    date_now_utc = round(datetime.utcnow().timestamp())+ 7200 # + Two hours

    # Allowable time =  before 30 minutes from current time 30/60 = 1800
    allowable_minutes = 1800

    # get te last element added in list
    existing_data = cache.lrange( message["postal"]+':current_dt', '0',  '0' )
    print('!!!!!!!!!!!!!!!!!!!!!!')
    time = 0
    t = 0
    if existing_data:
        for time in existing_data:
            t = int(date_now_utc)-int(time)
            # if the utctime in the cdb is X minutes older than the current utctime
            if t <= allowable_minutes:
                print('date_now_utc-time >= allowable_minutes')
                weather_current = cache.hgetall(message["postal"]+':current:'+time)
            else:
                print('Not => date_now_utc-time >= allowable_minutes')
                # # if the utctime in the cdb is X minutes less than the current utctime
                # get the Data From API, stor these data in cdb
                weather_current= get_current_weather(apiKey, message["postal"]+','+message["country"],'zip')
                weather_current = cache_current_weather(weather_current, str(message["postal"]))
    else:
        # if there are no data in cdb
        weather_current= get_current_weather(apiKey, message["postal"]+','+message["country"],'zip')
        weather_current = cache_current_weather(weather_current, str(message["postal"]))

    print('current time _____: '+ str(date_now_utc))
    print('last time in redis: '+ str(time))
    print('the sub range ____: '+ str(t))
    print(str(type(existing_data)))
    print('??????????????????????')



    # get all keys and values inside a hash, return a list
    #hValueList = cache.hvals('current:dt')
    #hKeysList = cache.hkeys('current:dt')

    # # check if this current date(key) existing inside current:dt(list) before, true/false
    # existing = cache.exists( message["postal"]+':current_dt', dt )
    # if existing:
    #     weather_current = cache.hgetall(message["postal"]+':current:'+dt)
    # else:
    #     weather_current = cache_current_weather(weather_current, dt, message["postal"])
    #
    #
    weather_5days= get_n5days_weather(apiKey, message["postal"]+','+message["country"],'zip')
    cach_5days_weather(weather_5days, message["postal"])

    # to return the object to the page, that were calling this function
    socketio.emit('back_weather_current_location', weather_current)
    #socketio.emit('back_weather_current_location_5', weather_5days)
    #printJson5DaysResponse(weather_5days, message["postal"], message["country"])
    #insertInRedisTimeSeries(weather_5days, message["postal"])

# get the message like a dictionary from submit #form_find_weather in index.html
@socketio.on('geCitytweather')
def handle_message1(message):
    #weather_current= get_current_weather(apiKey, message["city"],'q')
    #weather_5days= get_n5days_weather(apiKey, message["city"],'q')

    # to return the object to the page, that were calling this function
    #socketio.emit('back_currentCityWeather', weather_current)
    socketio.emit('back_currentCity5DaysWeather', weather_5days)


def redisloop_with_pipelining():
    pipe = cache.pipeline()
    program_starts = time.time()
    for i in range(100):
        s = str(i)
        pipe.set('test_p:foo'+s, 'bar'+s).sadd('test_p:faz', 'baz'+s).incr('test_p:auto_number')
    pipe.execute()
    end_time = time.time()
    return end_time-program_starts

def redisloop_without_pipelining():
    program_starts = time.time()
    for i in range(100):
        s = str(i)
        cache.set('test_:foo'+s, 'bar'+s)
    end_time = time.time()
    return end_time-program_starts


@socketio.on('back_message_info_order')
def getMessage(msg):
    back_msg = '-'
    # back_msg1 = redisloop_with_pipelining()
    # back_msg2 = redisloop_without_pipelining()
    #
    # back_msg =  f" pipeling time: {back_msg1} <br> no pipeling t: {back_msg2} <br><br> "
    # socketio.emit('back_message_info', back_msg)


if __name__ == '__main__':
    print('-----------------\n----------------------\n---------------------------\n--------------------------------\n')
    #print(cache.execute_command("TS.ADD temp:city 1548149191 49"));
    #print(cache.execute_command("TS.ADD cloud:city 1548149191 49"));
    #print(cache.execute_command("TS.ADD hum:city 1548149191 49"));



    # deleet all keys in current host
    #cache.flushall(asynchronous=False)
    print('-----------------\n----------------------\n---------------------------\n--------------------------------\n')
    socketio.run(app, host='0.0.0.0')
