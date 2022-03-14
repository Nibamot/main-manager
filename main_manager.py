import os
import json
import time
import urllib
import logging
import tornado.httpclient
from tornado.web import Application, RequestHandler
from tornado.ioloop import IOLoop


#############################################################################################
################################ Logging #################################
#############################################################################################

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

def logger_setup(name, level=os.environ['LOG_LEVEL']):
    """Setup different loggers here"""

    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(sh)

    return logger

def logger_file_setup(name, file_name, level=os.environ['LOG_LEVEL']):
    """Setup different file-loggers here"""

    file_handler = logging.FileHandler(file_name)
    file_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)

    return logger

general_log = logger_setup(os.environ['LOGGER_NAME'])
time_log = logger_setup(' Timing Main Manager  ')

#general_log = logger_file_setup(os.environ['LOGGER_NAME'],os.environ['LOG_PATH_GENERAL'])
#time_log = logger_file_setup(' Timing Main Manager  ','/logs/mmtime.log')

#############################################################################################
################################ Logging #################################
#############################################################################################




############TENTATIVE DICTS from MM Config###################

sm_dict={}
qtcode_dict={}

def config_startup():
    """ Main Manager startup config handling"""
    config = open(os.environ['LM_CONFIG_JSON'])#'support_message_config.json',encoding="utf8"
    body = json.load(config)
    
    for key,value in body["lms"].items(): 
        for lc in value["local_config"]:
            for qt in lc["qtcode_list"]:
                qtcode_dict.update({qt:lc["message"].get("id")})
                sm_dict.update({lc["message"].get("id"):lc["message"].get("endpoints")})
    
    return sm_dict, qtcode_dict

############TENTATIVE DICTS from MM Config###################



#############################################################################################
################################ API Server #################################
#############################################################################################

class Car_ApiServer(RequestHandler):
    """ API SERVER for handling calls from the cars """
    def post(self, id):
        """Handles the behaviour of POST calls from the car"""
        received_post = time.time()
        sm_dict,qtcode_dict=config_startup()
        car_position = json.loads(self.request.body)["location"]
        if car_position in qtcode_dict.keys():
            for sm in sm_dict[qtcode_dict.get((car_position))]:
                self.write(sm)
                sent_reply = time.time()
                general_log.debug(str((sent_reply-received_post)*1000)+" ms")
    
    def get(self,id):
        """ GET calls handler"""
        received_post = time.time()
        sm_dict,qtcode_dict=config_startup()
        car_position = self.request.uri.replace("/api/item/from_car_api/qtcode/","")
        if car_position in qtcode_dict.keys():
            for sm in sm_dict[qtcode_dict.get((car_position))]:
                self.set_status(200)
                self.set_header("Content-Type", 'application/json')
                self.write(sm)
                sent_reply = time.time()
                general_log.debug(str((sent_reply-received_post)*1000)+" ms")
        else:
            self.set_status(400)
            self.set_header("Content-Type", 'application/json')
            self.write("Not within my scope")
  
    def put(self, id):
        """Handles the behaviour of PUT calls"""
        global items
        new_items = [item for item in items if item['id'] is not int(id)]
        items = new_items
        self.write({'message': 'Item with id %s was updated' % id})


    def delete(self, id):
        """Handles the behaviour of DELETE calls"""
        global items
        new_items = [item for item in items if item['id'] is not int(id)]
        items = new_items
        self.write({'message': 'Item with id %s was deleted' % id})
    
    

class LM_ApiServer(RequestHandler):
    """ clear
    API SERVER for handling calls from the local Manager (TBD) """
    def prepare():
        """ To call some method before the execution of POST/GET/DELETE..."""
        pass

    def post(self, id):
        """Handles the behaviour of POST calls"""
        self.write(json.loads(self.request.body))
        #json_form = json.loads(self.request.body)
  
    def put(self, id):
        """Handles the behaviour of PUT calls"""
        global items
        new_items = [item for item in items if item['id'] is not int(id)]
        items = new_items
        self.write({'message': 'Item with id %s was updated' % id})


    def delete(self, id):
        """Handles the behaviour of DELETE calls"""
        global items
        new_items = [item for item in items if item['id'] is not int(id)]
        items = new_items
        self.write({'message': 'Item with id %s was deleted' % id})
    
    def on_finish():
        pass


def make_app():
  urls = [
    (r"/api/item/from_local_mgr_api/([^/]+)?", LM_ApiServer),
    (r"/api/item/from_car_api/qtcode/([^/]+)?", Car_ApiServer)
  ]
  return Application(urls, debug=True)
#############################################################################################
################################ API Server #################################
#############################################################################################





#############################################################################################
    ################################ API CLients #################################
#############################################################################################

def post_local_mgr_config():
    """ Method to send the local manager its configs """
    config = open('local_manager_config.json')
    body = json.load(config)
    http_client = tornado.httpclient.HTTPClient()
    while True:
      try:
        response_1 = http_client.fetch(os.environ['LOCAL_MANAGER_POST_ADDRESS_ONE'],method='POST'\
                                       ,body=json.dumps(body["lms"]["lm_id1"]))
        #response_2 = http_client.fetch(os.environ['LOCAL_MANAGER_POST_ADDRESS_TWO'],method='POST',body=json.dumps(body["lms"]["lm_id2"]))        
      except Exception as e:
        general_log.debug("Error: %s" % e)
        time.sleep(5)
      else:
        general_log.debug(response_1.body)
        break
        #general_log.debug(response_2.body)

def car_registration():# NOT USED
    """ Method to let the local manager know about the car registration """
    config = open('local_manager_config.json')
    body = json.load(config)
    http_client = tornado.httpclient.HTTPClient()
    try:
        response = http_client.fetch("http://localhost:3500/api/item/from_main_mgr_car_reg_api/1",method='POST',body=json.dumps(body["MECs"][0]))        
    except Exception as e:
        general_log.debug("Errorcheck: %s" % e)
    else:
        general_log.debug(response.body)

#############################################################################################
################################ API CLients Sections#################################
#############################################################################################

  
if __name__ == '__main__':

  app = make_app()
  app.listen(os.environ['API_PORT'])
  post_local_mgr_config()
  print("Started Main Manager REST Server")
  IOLoop.instance().start()
