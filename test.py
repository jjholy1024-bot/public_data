import requests

url = 'http://apis.data.go.kr/1262000/IntrlInsttVacancyInfoService/getRecentVacancyInfoList'
params ={'serviceKey' : '5d32cbefc97d315cce1a19bfcb3c347a865e267f29f8123cb37e63480c331ca5', 'numOfRows' : '10', 'pageNo' : '1', 'seq' : '1' }

response = requests.get(url, params=params)
print(response.content)

url = 'http://apis.data.go.kr/1262000/IntrlInsttVacancyInfoService/getInternshipVacancyInfoList'
params ={'serviceKey' : '5d32cbefc97d315cce1a19bfcb3c347a865e267f29f8123cb37e63480c331ca5', 'numOfRows' : '10', 'pageNo' : '1', 'title' : '인턴십', 'seq' : '1' }

response = requests.get(url, params=params)
print(response.content)