
import re
from urlextract import URLExtract
from wordcloud import WordCloud
import pandas as pd
from collections import Counter
import emoji
import numpy as np

# ---------------- LOAD MODELS ---------------- #

# with open('phishing.pkl', 'rb') as f:
#     phishing_model = pickle.load(f)
#
# with open('vectoriser.pkl', 'rb') as f:
#     vectorizer = pickle.load(f)
import os
import pickle

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    with open(os.path.join(BASE_DIR, "phishing.pkl"), "rb") as f:
        phishing_model = pickle.load(f)

    with open(os.path.join(BASE_DIR, "vectoriser.pkl"), "rb") as f:
        vectorizer = pickle.load(f)

except Exception as e:
    import streamlit as st
    st.error("❌ Failed to load phishing detection model")
    st.exception(e)


extract = URLExtract()

# ---------------- URL VALIDATION + TRUST ---------------- #

def is_valid_url(url):
    pattern = re.compile(
        r'^(https?:\/\/)?'          # http or https
        r'([a-zA-Z0-9-]+\.)+'       # domain
        r'[a-zA-Z]{2,}'             # TLD
        r'(\/\S*)?$'                # path
    )
    return bool(pattern.match(url))


TRUSTED_DOMAINS = [
    "google.com",
    "docs.google.com",
    "forms.gle",
    "whatsapp.com",
    "chat.whatsapp.com",
    "aicte-india.org"
]


def is_trusted_domain(url):
    for domain in TRUSTED_DOMAINS:
        if domain in url:
            return True
    return False

# ---------------- BASIC STATS ---------------- #

def fetch_stats(selected_user, df):
    if selected_user != "Overall Group":
        df = df[df['user'] == selected_user]

    num_messages = df.shape[0]

    words = []
    for message in df['message']:
        words.extend(message.split())

    num_media_messages = df[df['message'] == '<Media omitted>\n'].shape[0]

    links = []
    for message in df['message']:
        links.extend(extract.find_urls(message))

    return num_messages, len(words), num_media_messages, len(links)


def most_busy_users(df):
    x = df['user'].value_counts().head()
    df = round((df['user'].value_counts() / df.shape[0]) * 100, 2) \
            .reset_index().rename(columns={'index': 'name', 'user': 'percent'})
    return x, df

# ---------------- WORD CLOUD ---------------- #

def create_wordcloud(selected_user, df):
    if selected_user != "Overall Group":
        df = df[df['user'] == selected_user]

    with open(os.path.join(BASE_DIR, "stop_hinglish.txt"), "r", encoding="utf-8") as f:
        stop_words = f.read()

    temp = df[df['user'] != 'group_notification']
    temp = temp[temp['message'] != '<Media omitted>\n']

    def remove_stop_words(message):
        return " ".join(
            word for word in message.lower().split()
            if word not in stop_words
        )

    wc = WordCloud(
        width=500,
        height=500,
        min_font_size=10,
        background_color='white'
    )

    temp['message'] = temp['message'].apply(remove_stop_words)
    df_wc = wc.generate(temp['message'].str.cat(sep=" "))
    return df_wc

# ---------------- MOST COMMON WORDS ---------------- #

def most_common_words(selected_user, df):
    if selected_user != 'Overall Group':
        df = df[df['user'] == selected_user]

    with open('stop_hinglish.txt', 'r') as f:
        stop_words = f.read()

    temp = df[df['user'] != 'group_notification']
    temp = temp[temp['message'] != '<Media omitted>\n']

    words = []
    for message in temp['message']:
        for word in message.lower().split():
            if word not in stop_words:
                words.append(word)

    return pd.DataFrame(
        Counter(words).most_common(20),
        columns=['Word', 'Frequency']
    )

# ---------------- EMOJI ANALYSIS ---------------- #

def emoji_helper(selected_user, df):
    if selected_user != 'Overall Group':
        df = df[df['user'] == selected_user]

    emojis = []
    for message in df['message']:
        for char in message:
            if emoji.is_emoji(char):
                emojis.append(char)

    return pd.DataFrame(
        Counter(emojis).most_common(),
        columns=['Emoji', 'Count']
    )

# ---------------- TIMELINES ---------------- #

def monthly_timeline(selected_user, df):
    if selected_user != 'Overall Group':
        df = df[df['user'] == selected_user]

    timeline = df.groupby(
        ['year', 'month_num', 'month']
    ).count()['message'].reset_index()

    timeline['time'] = timeline['month'] + "-" + timeline['year'].astype(str)
    return timeline


def daily_timeline(selected_user, df):
    if selected_user != 'Overall Group':
        df = df[df['user'] == selected_user]

    return df.groupby('date_').count()['message'].reset_index()


def week_activity_map(selected_user, df):
    if selected_user != 'Overall Group':
        df = df[df['user'] == selected_user]

    return df['day_name'].value_counts()


def month_activity_map(selected_user, df):
    if selected_user != 'Overall Group':
        df = df[df['user'] == selected_user]

    return df['month'].value_counts()

# ---------------- HEATMAP ---------------- #

def activity_heatmap(selected_user, df):
    if selected_user != 'Overall Group':
        df = df[df['user'] == selected_user]

    heatmap_data = df.pivot_table(
        index='day_name',
        columns='period',
        values='message',
        aggfunc='count'
    ).fillna(0)

    day_order = [
        'Monday', 'Tuesday', 'Wednesday',
        'Thursday', 'Friday', 'Saturday', 'Sunday'
    ]

    heatmap_data = heatmap_data.reindex(day_order)
    return heatmap_data

# ---------------- PHISHING DETECTION (FIXED) ---------------- #
def predict_urls_phishing(df):
    urls = []

    for msg in df['message']:
        extracted = extract.find_urls(msg)
        valid_urls = [u for u in extracted if is_valid_url(u)]
        urls.extend(valid_urls)

    if not urls:
        return None

    url_df = pd.DataFrame(urls, columns=['url'])

    X = vectorizer.transform(url_df['url'])
    predictions = phishing_model.predict(X)

    if hasattr(phishing_model, "predict_proba"):
        confidence = phishing_model.predict_proba(X).max(axis=1)
    else:
        confidence = [None] * len(predictions)

    url_df['Prediction'] = predictions

    def final_result(row):
        if is_trusted_domain(row['url']):
            return 'Safe'
        return 'Phishing' if row['Prediction'] == 'bad' else 'Safe'

    # LOGIC result (no emoji)
    url_df['Result'] = url_df.apply(final_result, axis=1)

    # DISPLAY result (emoji)
    url_df['Result_Display'] = url_df['Result'].map({
        'Phishing': 'Phishing 🚨',
        'Safe': 'Safe ✅'
    })

    url_df['Confidence'] = confidence

    return url_df

# def predict_urls_phishing(df):
#     urls = []
#
#     for msg in df['message']:
#         extracted = extract.find_urls(msg)
#         valid_urls = [u for u in extracted if is_valid_url(u)]
#         urls.extend(valid_urls)
#
#     if not urls:
#         return None
#
#     url_df = pd.DataFrame(urls, columns=['url'])
#
#     X = vectorizer.transform(url_df['url'])
#     predictions = phishing_model.predict(X)
#
#     if hasattr(phishing_model, "predict_proba"):
#         confidence = phishing_model.predict_proba(X).max(axis=1)
#     else:
#         confidence = [None] * len(predictions)
#
#     url_df['Prediction'] = predictions
#
#     def final_result(row):
#         if is_trusted_domain(row['url']):
#             return 'Safe ✅'
#         return 'Phishing 🚨' if row['Prediction'] == 'bad' else 'Safe ✅'
#
#     url_df['Result'] = url_df.apply(final_result, axis=1)
#     url_df['Confidence'] = confidence
#
#     return url_df
