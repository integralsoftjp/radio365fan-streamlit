import datetime
import io
import pickle
import base64
from PIL import Image
from functools import wraps

import streamlit as st
import streamlit.components.v1 as componentsv1
import feedparser
import pandas as pd
import numpy as np
import pydub
import xlsxwriter
from urllib.request import urlopen
from bs4 import BeautifulSoup
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

st.set_page_config(page_title="RADIO365 DJ's Fan",)

html_width = 80

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
program_sound_times = []
program_image_urls = []
program_summarys = []
program_sound_urls = []

dj_img_datas = []

secret_user = st.secrets['dbuser']
secret_passwd = st.secrets['dbpassword']
CONN_URI = "mongodb+srv://" + secret_user + ":" + secret_passwd + "@mycluster0.p0yno.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"

# CONN_URI = "mongodb://localhost:27017/"

# @st.cache(hash_funcs={MongoClient: id})
# def get_client():
#     return  MongoClient()

def provide_db_connection(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        conn = MongoClient(CONN_URI)
        result =  func(conn=conn, *args, **kwargs)
        conn.close()
        return result
    return wrapper

@st.cache(suppress_st_warning=True)
def read_image(program_image_url:str) -> bytes:
    img_data = io.BytesIO(urlopen(program_image_url).read())
    return img_data

# @st.cache(suppress_st_warning=True)
def read_sound_data(program_sound_url:str) -> bytes:
    sound_data = io.BytesIO(urlopen(program_sound_url).read())
    return sound_data

def get_sound_time(sound_url:str, sound_data:bytes) -> str:
    au_sound = pydub.AudioSegment.from_file(sound_data, sound_url[-3:])
    au_time = au_sound.duration_seconds
    au_time_str = str(int(au_time / 60)) + ":" + str(int(au_time % 60))
    return au_time_str

def to_excel(df):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1')
    writer.save()
    processed_data = output.getvalue()
    return processed_data

def get_table_download_link(df):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    val = to_excel(df)
    b64 = base64.b64encode(val)  # val looks like b'...'
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="extract.xlsx">Download csv file</a>' # decode b'abc' => abc

@st.cache
@provide_db_connection
def read_sidebar_photos(conn) -> bytes:
    global dj_img_datas
    db = conn.test
    image_df = pd.DataFrame.from_records(db.image_df.find())
    for i, dj_image_url in enumerate(dj_images_urls):
        try:
            mongo_key = "image_" + dj_ids[i]
            cnt = db.image_df.count_documents({'name': mongo_key})
            if cnt > 0:
                filter_one_imagedata = db.image_df.find({'name': mongo_key})
                pickled = filter_one_imagedata[0]['imagedata']
                image_data = pickle.loads(pickled)
                dj_img_datas.append(image_data)
            else:
                image_data = io.BytesIO(urlopen(dj_image_url).read())
                dj_img_datas.append(image_data)
                # pickle
                pickled = pickle.dumps(image_data)
                db.image_df.insert( { 'name':mongo_key, 'imagedata': pickled } )
        except DuplicateKeyError:
            print('Name duplication error!')
    return dj_img_datas

def set_hrefs(dj_hrefs:list) -> list:
    htmls = []
    for i, href in enumerate(dj_hrefs):
        if href in '':
            htmls.append(f'<img src="{dj_images_urls[i]}" alt="dj" width="{html_width}" style="border:solid 1px #FFFFFF">')
        else:
            htmls.append(f'<a href="{dj_hrefs[i]}" target="_blank"><img src="{dj_images_urls[i]}" alt="dj" width="{html_width}" style="border:solid 1px #FFFFFF"></a>')
    return htmls

def main():
    COLOR = "black"
    BACKGROUND_COLOR = "#fff"
    max_width = 1000
    padding_top = 5
    padding_right = 1
    padding_left = 1
    padding_bottom = 10
    
    dj_contents = dj_soup.select(".prof dl")
    for i, element in enumerate(dj_contents):
        dj_ids.append(element.select('dt')[0]['id'])
        dj_images_urls.append(element.select('dt')[0].select('img')[0]['src'])
        dj_href = element.select('a')[0]['href']
        if '/programs/' in dj_href:
            dj_hrefs.append(domain + dj_href)
        else:
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
        # -- 担当番組Program
        contents = dj_dicts[name]
        if '担当番組' in contents:
            dj_haveprograms.append(contents['担当番組'])
        else:
            dj_haveprograms.append('')

        # -- 誕生日Birth
        if '誕生日' in contents:
            dj_births.append(contents['誕生日'])
        else:
            dj_births.append('')

        # -- 血液型Blood
        if '血液型' in contents:
            dj_bloods.append(contents['血液型'])
        else:
            dj_bloods.append('')

        # -- 身長Hight
        if '身長' in contents:
            dj_heights.append(contents['身長'])
        else:
            dj_heights.append('')

        # -- 趣味Hobbys
        if '趣味' in contents:
            dj_hobbys.append(contents['趣味'])
        else:
            dj_hobbys.append('')

        # -- 特技Skills
        if '特技' in contents:
            dj_skills.append(contents['特技'])
        else:
            dj_skills.append('')


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
    df.index = np.arange(1, len(df)+1)
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
        program_image_urls.append(entrie['mobileimg']['src'])
        program_summarys.append(entrie['summary'])
        program_sound_urls.append(program_base + mark + href)
        datestr = entrie['published']
        program_pubdates.append(datetime.datetime.strptime(datestr, '%a, %d %b %Y %H:%M:%S %z').strftime('%Y/%m/%d'))
        program_djnames.append('　')
        program_sound_times.append('　')

    # program_djnames 追加
    for i, dj_id in enumerate(program_ids):
        if dj_id in dj_ids:
            program_djnames[i] = dj_names[dj_ids.index(dj_id)]
        else:
            program_djnames[i] = ''

    df2 = pd.DataFrame({
    'id': program_ids,
    'Program': program_titles,
    '番組名': program_subtitles,
    'DJName': program_djnames,
    '配信日Pubday': program_pubdates,
    '再生時間SoundTime': program_sound_times
    })
    df2.index = np.arange(1, len(df2)+1)
    df2 = df2.style.set_properties(**{'text-align': 'left'})

    st.title("RADIO365 DJ's Fan site")

    hedder_text = """
    Radio365 DJ ファンサイトです。
    再生ボタンで番組をお楽しみください。初期ボリューム音声にご注意ください。
    左上の「 Select program 」で番組(1～100迄)の切替ができます。（本家からデータを自動取得）
    """
    st.text(hedder_text)

    selector = st.sidebar.selectbox("Select program (1 - 100):",program_titles)
    select_indexNumber = int(selector.split(':')[0])-1

    dark_theme = st.sidebar.checkbox("Dark Theme", False)
    if dark_theme:
        # global COLOR
        # global BACKGROUND_COLOR
        print('a')
        BACKGROUND_COLOR = "rgb(17,17,17)"
        COLOR = "#fff"

    st.markdown(
    f"""
    <style>
        .reportview-container .main .block-container{{
            max-width: {max_width}px;
            padding-top: {padding_top}rem;
            padding-right: {padding_right}rem;
            padding-left: {padding_left}rem;
            padding-bottom: {padding_bottom}rem;
        }}
        .reportview-container .main {{
            color: {COLOR};
            background-color: {BACKGROUND_COLOR};
        }}
    </style>
    """,
            unsafe_allow_html=True,
        )

    markdown_str = "#### " + '<font color="Gray">' + program_subtitles[select_indexNumber] + '</font>'
    st.markdown(markdown_str, unsafe_allow_html=True)

    #===== read sidebar image file =======
    img_data = read_image(program_image_urls[select_indexNumber])
    st.image(img_data, caption=selector, use_column_width=True)

    # sound update
    sound_data = read_sound_data(program_sound_urls[select_indexNumber])
    st.audio(sound_data, format='audio/aac')

    st.markdown(program_summarys[select_indexNumber], unsafe_allow_html=True)

    # DJ photo & profile
    htmls = set_hrefs(dj_hrefs)
    html_height = (int(len(htmls) / 8) + 1) * 62
    joinhtml = "".join(htmls)
    html = f"""{joinhtml}"""
    with st.beta_expander("DJ Photo (please click to see profile)",expanded=True):
        componentsv1.html(html,height = html_height, scrolling=True)

    st.sidebar.text('')

    # Sidebar DJ photo
    temp_text = str(len(dj_images_urls)) + " DJ member:"
    st.sidebar.text(temp_text)

    dj_img_datas = read_sidebar_photos()
    for i, dj_image_url in enumerate(dj_images_urls):
        st.sidebar.image(dj_img_datas[i], caption=dj_names[i], use_column_width='True')

    # for i, program_sound_url in enumerate(program_sound_urls):
    #     sound_data = read_sound_data(program_sound_urls[i])
    #     program_sound_times[i] = get_sound_time(program_sound_urls[i], sound_data)

    # DJ List
    with st.beta_expander("DJ List",expanded=True):
        st.dataframe(df)
        st.markdown(get_table_download_link(df), unsafe_allow_html=True)
    # Program List
    with st.beta_expander('Program List',expanded=True):
        st.dataframe(df2)
        st.markdown(get_table_download_link(df2), unsafe_allow_html=True)

if __name__ == "__main__":
    main()