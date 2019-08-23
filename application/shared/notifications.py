import requests
import json
from copy import deepcopy

__fcm_server_token = 'AAAAtseIilM:APA91bHABqaXHpWsLRTqjN4KJwCbBHLwec57S5R47OU4mZfNH_vXi0GgMkZybuNoAePQ7OJwAmUEmEwe9xOxRLrc5ISndmLLhGO-zdUKP3UIebQp2WoeEe0K0i0dFM0PUGtCH799_3oY'

__fcm_url = 'https://fcm.googleapis.com/fcm/send'
__fcm_data = {
    "notification": {
        "title": "Leave Request",
        "body": "Someone submitted request"
    },
    "priority": "high",
    "data": {
        "click_action": "FLUTTER_NOTIFICATION_CLICK",
    },
}
__fcm_headers = {
    'Content-Type': 'application/json',
    'Authorization': 'key={}'.format(__fcm_server_token)
}


def send_push(to, title, body, custom_data={}):
    if to is None or title is None or body is None:
        return
    data = deepcopy(__fcm_data)
    data['data'].update(custom_data)
    data['notification']['body'] = body
    data['notification']['title'] = title
    data['to'] = to
    print('Send push to {}'.format(to))
    requests.post(__fcm_url, data=json.dumps(data), headers=__fcm_headers)
