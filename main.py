import streamlit as st
from PIL import Image
import io
from urllib.request import urlopen
import feedparser
from bs4 import BeautifulSoup
import pandas as pd
import datetime

st.title("RADIO365 DJ's Fan site")
hedder_text = """
こちらのサイトは Radio365 DJを応援するサイトです。
画像下に表示されている再生ボタンで番組を聴くことができます。（音声にご注意）
番組切り替えは左側「 Select program 」を利用してください。
"""
st.text(hedder_text)

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
dj_dicts = dict()
dj_otherDicts = dict()

program_ids = []
program_titles = []
program_subtitles = []
program_djnames = []
program_pubdates = []
program_times = []
program_images = []
program_summarys = []
program_sound_urls = []

dj_contents = dj_soup.select("div .prof dl")
    
for i, element in enumerate(dj_contents):
    dj_ids.append(element.select('dt')[0].get('id'))
    dj_images_urls.append(element.select('dt')[0].select('img')[0]['src'])    
    
    el2 = dj_contents[i].get_text().split('\n')[1:-1]
    key = el2[0].split('：')[1]
    # --
    dj_otherDicts = dict() #初期化

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
    '名前': dj_names,
    '担当番組': dj_haveprograms,
    '誕生日': dj_births,
    '血液型': dj_bloods,
    '身長': dj_heights,
    '趣味': dj_hobbys,
    '特技': dj_skills,
    '画像URL': dj_images_urls
})

#================================================================
#================================================================
#================================================================
for entrie in program_res.entries:
    program_id = entrie['mobileimg']['src'].split('/')[5]
    mark = "/" + program_id + "/"
    href = entrie['links'][1]['href']
    program_ids.append(program_id)
    program_titles.append(entrie['title'])
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
'DJ': program_djnames,
'配信日': program_pubdates,
'再生時間': program_times
})

ziplist = list(zip(program_images , program_sound_urls, program_summarys))
add_listnew = dict(zip(program_titles, ziplist))

selector = st.sidebar.selectbox("Select program:",program_titles)

image_url = add_listnew[selector][0]
img_data = io.BytesIO(urlopen(image_url).read())
st.image(img_data, caption=selector, use_column_width=True)

# sound update
sound_url = add_listnew[selector][1]
data = io.BytesIO(urlopen(sound_url).read())
st.audio(data, format='audio/aac')

st.markdown(add_listnew[selector][2], unsafe_allow_html=True)

st.write('')

# agree = st.checkbox('DJ List', value=True, help='DJリストを表示します。')
# if agree:
#     st.dataframe(df)

# agree2 = st.checkbox('Program', value=True, help='番組リストを表示します。')
# if agree2:
#     st.dataframe(df2)
with st.beta_expander('DJ List',expanded=False):
    st.dataframe(df)
    
with st.beta_expander('Program',expanded=False):
    st.dataframe(df2)

st.sidebar.text("Dj's Photo:")
for i, dj_image_url in enumerate(dj_images_urls):
    dj_img_data = io.BytesIO(urlopen(dj_image_url).read())
    st.sidebar.image(dj_img_data, caption=dj_names[i], use_column_width='True')