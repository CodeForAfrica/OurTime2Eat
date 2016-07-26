from flask import (Flask, g, request, session, redirect,
        url_for, render_template, jsonify)
from flask_script import Manager
import redis, os
from normality import slugify
from OurTime2Eat.otte import config as config_file

app = Flask(__name__,
        template_folder=os.getenv('OTTE_TEMPLATES'),
        static_folder=os.getenv('OTTE_STATIC'))
app.config.from_object(config_file)

def get_db():
    if not hasattr(g, 'redis'):
        g.redis = redis.StrictRedis(**app.config['REDIS'])
    return g.redis


def todigit(number=""):
    '''
    returns number in digits

    currently supports numbers in the format:
    'xx million'  ,  'xx billion' , 'xx thousand' , 'xx hundred'
    '''
    notations = dict(million="000000", billion="000000000", thousand="000", hundred="00")
    if str(number).isdigit():
        return int(float(number))
    else:
        try:
            num, notation = number.split(' ')
        except ValueError:
            print "ERROR: Unknown number format"
            return 0
        if notation not in notations.keys():
            print "ERROR: Unknown notation"
            return 0
        else:
            try:
                whole, fraction = num.split('.')
            except ValueError:
                whole = num
                fraction = 0

            whole_num = "%s%s" % (whole, notations[notation])
            fract_num = float("0.%s" % fraction) * int("1%s" % notations[notation])
            number_dig = int(whole_num) + int(fract_num)
            return number_dig


### VIEWS

@app.route('/')
def home():
    '''
    index.html

    data:  [ {cou:xx, ttl:ttl, hos:hos, trv:trv, rnk:rnk} ]
    '''


    # get the data
    rds = get_db()
    county_data = []
    for county in app.config['COUNTIES']:
        if not county in app.config['NODATA']:
            resp = eval(rds.get(slugify(county)))
            travel_budget = todigit(resp['travel']['budget'] + ' million')
            hospitality_budget = todigit(resp.get('hospitality_budget', 0))
            total_budget = todigit(resp.get('total_budget', 0))
            gov = resp['governance']

            hospitality_ratio = (hospitality_budget / total_budget) * 100.0
            travel_ratio = (float(travel_budget) / float(total_budget)) * 100.0
            ratio = (hospitality_budget + travel_budget) / float(total_budget) * 100

            # ranking
            rank = 0
            county_payload = dict(
                    county=county,
                    governor=gov['governor'],
                    governor_img=resp['governor_image'],
                    rank=rank
                    )

            county_data.append(county_payload)
            print "Added %s (%s percent) to final list" % (county, int(ratio))
    
    return render_template('index.html', county_rankings=county_data)


### END OF VIEWS

manager = Manager(app)

if __name__ == "__main__":
    manager.run()