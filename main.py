#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import logging
import csv
from collections import defaultdict

import webapp2
from webapp2_extras import json
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

import config
from tripit_facade import TripItFacade

AIRPORTS_ID = 1
MATRIX_ID = 2

class BlobModel(ndb.Model):
    payload = ndb.PickleProperty(compressed=True)

    @classmethod
    def by_name(cls, name_value):
        return cls.query(name=name_value)


class HomeHandler(webapp2.RequestHandler):

    def get(self):
        template_values = {}
        template = config.JINJA_ENVIRONMENT.get_template('views/home.html')
        self.response.write(template.render(template_values))


class AirportListHandler(webapp2.RequestHandler):

    def get(self):
        self.response.headers['Content-Type'] = 'application/csv'
        airports = BlobModel.get_by_id(AIRPORTS_ID)
        colors = ['#AF81C9', '#F89A7E', '#F2CA85', '#54D1F1', '#7C71AD', '#445569']
        writer = csv.writer(self.response.out)
        writer.writerow(['name', 'color'])
        for i, value in enumerate(airports.payload):
            writer.writerow([value, colors[i % len(colors)]])


class AirportMatrixHandler(webapp2.RequestHandler):

    def get(self):
        self.response.content_type = 'application/json'
        matrix = BlobModel.get_by_id(MATRIX_ID)
        self.response.write(json.encode(matrix.payload))


class TripItHandler(webapp2.RequestHandler):

    def get(self):
        logging.info('Scheduling tripit fetch')
        taskqueue.add(url='/tripit/worker')

    def post(self):
        tripit = TripItFacade(config.TRIPIT_USERNAME, config.TRIPIT_PASSWORD)
        flight_segments = tripit.list_flight_segments()
        logging.info('Flight segments retrieved!')

        airports = set()
        matrix = defaultdict(int)
        for s in flight_segments:
            origin, destination = s['start_airport_code'], s['end_airport_code']
            matrix[origin, destination] += 1
            airports.add(origin)
            airports.add(destination)

        airports = list(airports) # to guarantee order
        weights = []

        for i in airports:
            current_line = [0] * len(airports)
            for j, value in enumerate(airports):
                current_line[j] = matrix[i, value]
            weights.append(current_line)

        if len(weights) > 0:
            tripit_airport = BlobModel(id=AIRPORTS_ID, payload=airports)
            tripit_airport.put()
            tripit_matrix = BlobModel(id=MATRIX_ID, payload=weights)
            tripit_matrix.put()
            logging.info('Updated datastore entries with matrix and airport information')
        else:
            logging.error('Ignoring datastore update due to missing information, check log for errors')



app = webapp2.WSGIApplication([
    ('/', HomeHandler),
    ('/airports/matrix.json', AirportMatrixHandler),
    ('/airports/list.csv', AirportListHandler),
    ('/tripit/schedule', TripItHandler),
    ('/tripit/worker', TripItHandler)
], debug=True)
