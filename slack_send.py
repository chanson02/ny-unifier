from secret import slack_webhook
import sys, json, requests

def slack(msg):
    headers = {'Content-Type': 'application/json'}
    data = json.dumps({'text': msg})
    response = requests.post(slack_webhook, data=data, headers=headers)
    return response

if __name__ == '__main__':
    args = sys.argv
    if len(args) > 1:
        slack(args[-1])
