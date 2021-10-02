import requests

for each in range(60,101):
    mm ="ID_"+str(each)
    x = requests.post(url="https://mviis-kanban-app.herokuapp.com/store",json={"uniqname":mm})
    print(x.json())