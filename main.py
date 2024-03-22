from googleapiclient.discovery import build 
from google_auth_oauthlib.flow import InstalledAppFlow 
import os
import pickle

SCOPES = ['https://www.googleapis.com/auth/gmail.modify'] 

tokenDir = "token.pickle"
credsDir = "credentials.json"

if os.path.exists(tokenDir): 
    with open(tokenDir, 'rb') as token: 
        creds = pickle.load(token)
else: 
    flow = InstalledAppFlow.from_client_secrets_file(credsDir, SCOPES) 
    creds = flow.run_local_server(port=0) 
    with open(tokenDir, 'wb') as token: 
        pickle.dump(creds, token) 

service = build('gmail', 'v1', credentials=creds)

def applyLabels():

    pageToken = None

    counter = 0

    while True:
        response = service.users().messages().list(userId='me', pageToken=pageToken).execute() 
        messages = response["messages"]

        if not messages:
            break

        for message in messages:

            print(f"Counter: {counter}")

            messageId = message["id"]
            print(f"ID: {messageId}")

            messageContent = service.users().messages().get(userId='me', id=messageId).execute()

            headers = messageContent["payload"]["headers"]
            for headersDict in headers:
                if headersDict["name"] == "From":
                    sender = headersDict["value"]
                    try:
                        sender = sender[sender.index("<")+1:sender.index(">")]
                    except ValueError as e:
                        print(f"Error processing sender: {e}")
                        continue
                    senderDomain = sender.split("@")[1]
            print(f"Sender: {sender}")
            print(f"Sender domain: {senderDomain}")

            labelsList = service.users().labels().list(userId='me').execute()["labels"] # list of dicts containing data about each label
            messageLabelsIds = messageContent["labelIds"] # list of ids of all labels applied to the message
            
            senderDomainLabelExists = False
            for label in labelsList:
                if label["name"] == senderDomain:
                    senderDomainLabelId = label["id"]
                    senderDomainLabelExists = True
                    print(f"Label '{senderDomain}' found, ID: {senderDomainLabelId}")
            print(f"Label '{senderDomain}' exists: {senderDomainLabelExists}")
            
            if senderDomainLabelExists:
                service.users().messages().modify(userId='me', id=messageId, body={"addLabelIds": [senderDomainLabelId]}).execute()
                print(f"Applied label '{senderDomain}' with ID: {senderDomainLabelId} to email with ID: {messageId}")

            else:
                newLabel = service.users().labels().create(userId="me", body={'name': senderDomain, 'messageListVisibility': 'show', 'labelListVisibility': 'labelShow', 'color': {'textColor': '#ffffff', 'backgroundColor': '#4a86e8'}}).execute()
                print(f"Created label '{newLabel['name']}' with ID: {newLabel['id']}")
                service.users().messages().modify(userId='me', id=messageId, body={"addLabelIds": [newLabel["id"]]}).execute()
                print(f"Applied label '{newLabel['name']}' with ID: {newLabel['id']} to email with ID: {messageId}")

            print()

            counter += 1

        pageToken = response.get("nextPageToken")

        if not pageToken:
            break
    CreateUI()

def deleteAllLabels():
    labelsList = service.users().labels().list(userId='me').execute()["labels"] 
    for label in labelsList:
        if not label['type'] == 'system':
            service.users().labels().delete(userId='me', id=label['id']).execute()
            print(f"Deleted label '{label['name']}'")
    CreateUI()

def CreateUI():
    while True:
        choice = input("""
Enter action ID:
                       
ID | Action
---|--------------------------------------------
 1 | Apply labels
 2 | Delte labels (does not delete emails)

>>> """)
        if choice == "1":
            applyLabels()
        elif choice == "2":
            deleteAllLabels()
        else:
            print("Error: invalid input")

if __name__ == "__main__":
    CreateUI()
