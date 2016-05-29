#!/usr/bin/python
# -*- coding: utf-8 -*-

# Sport ID to Datadog integration
#
# Fetch sporting stats from sportid.ee and send them off to Datadog
# Enables to track people's sporting habits (km run per day) in Datadog graphs
#
# This is not a "done" script, rather a proof-of-concept.
# TODO: Develop this into a proper checks.d integration
#
# Usage: run this script with the following environment variables set:
#   - COOKIE: 'sportid_session' cookie value, encoded, as sent by the browser. This is the 'login' bit.
#   - APP_KEY: Datadog APP key
#   - API_KEY: Datadog API key
#
# Author: Ando Roots <ando@sqroot.eu> 2016-05
# License: MIT

from datadog import initialize
from datadog import api
import requests
from os import environ
import time
import logging
import sys

def send_metric(name, distance, points):
  """Send person's stats to Datadog over HTTP API"""
  metrics = [{
    'metric': 'sportid.workout.distance',
    'points': [float(distance)],
    'tags': ['name:' + name],
    'host': environ.get('HOST', ''),
    'type': 'gauge'
  },
  {
    'metric': 'sportid.workout.points',
    'points': [float(points)],
    'tags': ['name:' + name],
    'host': environ.get('HOST', ''),
    'type': 'gauge'
  }]
  
  r = api.Metric.send(metrics)
  logging.info("Sending metrics to Datadog... %s" % r['status'])
  logging.info(metrics)


def init():
  """Setup logging and init Datadog API"""
  root = logging.getLogger()
  root.setLevel(logging.INFO)
  ch = logging.StreamHandler(sys.stdout)
  ch.setLevel(logging.INFO)
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  ch.setFormatter(formatter)
  root.addHandler(ch)

  logging.info('Initializing Datadog...')
  initialize(api_key=environ['API_KEY'], app_key=environ['APP_KEY'])


def get_stats():
  """Load stats from sportid.ee"""
  logging.info('Loading stats from SportID...')
  
  # time_interval in days
  payload = {
    'overview': 'true',
    'time_interval': 7
  }

  headers = {
    'User-Agent': 'dd-stats-monitor 0.1',
    'Accept': 'application/json',
    'Cookie': 'sportid_session=%s' % environ['COOKIE']
  }
  r = requests.get('https://api.sportid.ee/user/9121/workout/stats', params=payload, headers=headers)
  r.raise_for_status()

  return r.json()

def main():
  """Main loop - execute every X seconds to send stats from SportID to Datadog"""
  try:
    stats = get_stats()
  except requests.exceptions.HTTPError as error:
    logging.error("Unable to fetch stats from SportID: %s" % format(error))
    return

  for row in stats:
    send_metric(row['name'], row['distance'], row['points'])

  
if __name__ == "__main__":
  init()

  # Run the main loop every X seconds
  try:
    interval = int(environ.get('INTERVAL', 20))
    i = interval
    while True:
      if i >= interval:
        i = 0
        logging.info('Time to refresh stats...')
        main()
      i+=1
      time.sleep(1)
  except KeyboardInterrupt:
    logging.warning('User interrupt, exiting.')
    sys.exit(0)
