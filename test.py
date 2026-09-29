from bs4 import BeautifulSoup
import json

# data = dict()

# with open("/home/sto-ormik/programming/python/projects/alarm/radar_data/radar.html", mode="r", encoding="utf-8") as f:
#     html = f.read()
    
# soup = BeautifulSoup(markup=html, features="html.parser")


# main_info = soup.find_all("div", attrs={"class": "tgme_widget_message_text"})

# views = soup.find_all("span", attrs={"class": "tgme_widget_message_views"})

# date_time = soup.find_all("time", attrs={"class": "time"})
# date_time = [i.get("datetime").split("T") for i in date_time]


# for t, v in zip(date_time, views):
#     data[f"{t[0]} | {t[1][:8]}"] = 
    
# print(data)

# with open("/home/sto-ormik/programming/python/projects/alarm/radar_data/data.json", mode="w", encoding="utf-8") as f:
#     json.dump(
#         data,
#         f,
#         ensure_ascii=False,
#         indent=4,
#     )

import re 

test = "Борисоглебск Воронежская область Опасность по БПЛА❗️Радар по всей России - @radarrussiia🌐 Обход белых списков - @Internet_Boost_bot"

pattern = r"❗️Радар по всей России"

match = re.search(pattern, test)

print(match)

print(test.find("❗️"))
print(test[:50])
