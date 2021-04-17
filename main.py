import datetime
import io
from PIL import Image

import streamlit as st
import streamlit.components.v1 as componentsv1
import feedparser
import pandas as pd
from urllib.request import urlopen
from bs4 import BeautifulSoup


domain = "https://www.radio365.net"

dj_base = 'https://www.radio365.net/navigator/'
dj_res = urlopen(dj_base)

dj_soup = BeautifulSoup(dj_res, "html.parser")
dj_res.close()

program_base = 'https://www.radio365.net/programs/archive'
program_res = feedparser.parse('https://www.radio365.net/programs/rss.xml')

# dj list
dj_ids = []
dj_names = []
dj_haveprograms = []
dj_births = []
dj_bloods = []
dj_heights = []
dj_hobbys = []
dj_skills = []
dj_images_urls = []
dj_hrefs = []

dj_dicts = dict()
dj_otherDicts = dict()

# program list
program_ids = []
program_titles = []
program_subtitles = []
program_djnames = []
program_pubdates = []
program_times = []
program_images = []
program_summarys = []
program_sound_urls = []

dj_img_datas = []

@st.cache(suppress_st_warning=True)
def read_image():
    image_url = add_listnew[selector][0]
    img_data = io.BytesIO(urlopen(image_url).read())
    return img_data

@st.cache(suppress_st_warning=True)
def read_sound_data():
    sound_url = add_listnew[selector][1]
    sound_data = io.BytesIO(urlopen(sound_url).read())
    return sound_data

def read_sidebar_photos():
    global dj_img_datas
    for i, dj_image_url in enumerate(dj_images_urls):
        dj_img_datas.append(io.BytesIO(urlopen(dj_image_url).read()))
    return dj_img_datas

def set_hrefs():
    htmls = []
    for i, href in enumerate(dj_hrefs):
        if href in '':
            htmls.append(f'<img src="{dj_images_urls[i]}" alt="dj" width="{html_width}" style="border:solid 2px #FFFFFF">')
        else:
            htmls.append(f'<a href="{dj_hrefs[i]}" target="_blank"><img src="{dj_images_urls[i]}" alt="dj" width="{html_width}" style="border:solid 2px #FFFFFF"></a>')
    return htmls

dj_contents = dj_soup.select("div .prof dl")
for i, element in enumerate(dj_contents):
    dj_ids.append(element.select('dt')[0].get('id'))
    dj_images_urls.append(element.select('dt')[0].select('img')[0]['src'])
    dj_href = element.select('a')[0].get('href')
    if '/programs/' in dj_href:
        dj_hrefs.append(domain + dj_href)
    else:
        print(dj_href)
        dj_hrefs.append(dj_href)

    el2 = dj_contents[i].get_text().split('\n')[1:-1]
    key = el2[0].split('：')[1]
    # --
    dj_otherDicts = dict() #init

    for j in el2[1:]:
        key2 = j.split('：')[0]
        value = j.split('：')[1]
        dj_otherDicts.update({key2:value})

    one_dict = {key:dj_otherDicts}
    dj_dicts.update(one_dict)

for element in dj_contents:
    el1 = element.get_text().split('\n')[1:-1]
    name = el1[0].split('：')[1]
    dj_names.append(name)
    # -- 担当番組
    contents = dj_dicts[name]
    if '担当番組' in contents:
        dj_haveprograms.append(contents['担当番組'])
    else:
        dj_haveprograms.append(None)

    # -- 誕生日
    if '誕生日' in contents:
        dj_births.append(contents['誕生日'])
    else:
        dj_births.append(None)

    # -- 血液型
    if '血液型' in contents:
        dj_bloods.append(contents['血液型'])
    else:
        dj_bloods.append(None)

    # -- 身長
    if '身長' in contents:
        dj_heights.append(contents['身長'])
    else:
        dj_heights.append(None)

    # -- 趣味
    if '趣味' in contents:
        dj_hobbys.append(contents['趣味'])
    else:
        dj_hobbys.append(None)

    # -- 特技
    if '特技' in contents:
        dj_skills.append(contents['特技'])
    else:
        dj_skills.append(None)


df = pd.DataFrame({
    'id': dj_ids,
    '名前Name': dj_names,
    '担当番組Program': dj_haveprograms,
    '誕生日Birth': dj_births,
    '血液型Blood': dj_bloods,
    '身長Hight': dj_heights,
    '趣味Hobbys': dj_hobbys,
    '特技Skills': dj_skills,
    '画像URL': dj_images_urls
})
df = df.style.set_properties(**{'text-align': 'left'})


#================================================================
#================================================================
#================================================================

for cnt, entrie in enumerate(program_res.entries):
    program_id = entrie['mobileimg']['src'].split('/')[5]
    mark = "/" + program_id + "/"
    href = entrie['links'][1]['href']
    program_ids.append(program_id)
    program_titles.append(str(cnt+1) + ": " + entrie['title'])
    program_subtitles.append(entrie['mobilesubtitle'])
    program_images.append(entrie['mobileimg']['src'])
    program_summarys.append(entrie['summary'])
    program_sound_urls.append(program_base + mark + href)
    datestr = entrie['published']
    program_pubdates.append(datetime.datetime.strptime(datestr, '%a, %d %b %Y %H:%M:%S %z').strftime('%Y/%m/%d'))
    program_djnames.append('　')
    program_times.append('　')

df2 = pd.DataFrame({
'id': program_ids,
'Program': program_titles,
'番組名': program_subtitles,
'DJName': program_djnames,
'配信日Pubday': program_pubdates,
'再生時間SoundTime': program_times
})
df2 = df2.style.set_properties(**{'text-align': 'left'})

ziplist = list(zip(program_images , program_sound_urls, program_summarys))
add_listnew = dict(zip(program_titles, ziplist))

st.title("RADIO365 DJ's Fan site")

hedder_text = """
こちらのサイトは Radio365 DJを応援するファンサイトです。
画像下に表示されている再生ボタンで番組を聴くことができます。（初期音声にご注意）
番組切り替えは左側「 Select program 」を利用してください。
"""
st.text(hedder_text)

selector = st.sidebar.selectbox("Select program (1 - 100):",program_titles)

#===== read sidebar image file =======
img_data = read_image()
st.image(img_data, caption=selector, use_column_width=True)

# sound update
sound_data = read_sound_data()
st.audio(sound_data, format='audio/aac')

st.markdown(add_listnew[selector][2], unsafe_allow_html=True)

html_width = 80
htmls = set_hrefs()
html_height = (int(len(htmls) / 8) + 1) * 70
joinhtml = "".join(htmls)
html = f"""{joinhtml}"""
with st.beta_expander("DJ Photo (click image)",expanded=True):
    componentsv1.html(html,height = html_height)

if dj_img_datas == []:
    with st.beta_expander("DJ List",expanded=False):
        st.dataframe(df)

if dj_img_datas == []:
    with st.beta_expander('Program List',expanded=False):
        st.dataframe(df2)


st.sidebar.text("Dj's Photo:")

if dj_img_datas == []:
    dj_img_datas = read_sidebar_photos()
    for i, dj_image_url in enumerate(dj_images_urls):
        st.sidebar.image(dj_img_datas[i], caption=dj_names[i], use_column_width='True')