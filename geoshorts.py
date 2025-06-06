import streamlit as st
import requests
from datetime import datetime, timedelta
from collections import Counter
import pandas as pd

try:
    import plotly.express as px
except ImportError:
    st.error("Plotly is not installed. Please run `pip install plotly` in your environment.")
    st.stop()

# YouTube API Key
API_KEY = "AIzaSyDXJjwWDp4JDTwmFmjb0-atLV6Qtww28Zg"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# Streamlit App Title
st.set_page_config(layout="wide")
st.title("📊 YouTube Map Shorts Analyzer - Advanced Tool")

# Input Fields
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)
selected_topics = st.multiselect("Filter by topic keyword:", ["usa", "europe", "history", "borders", "world"], default=[])

# Niche keywords
keywords = [
    "map animation", "geolayers", "After Effects map", "geography shorts", "usa map", 
    "historical borders", "country borders", "world map", "before and after maps",
    "map transformation", "geopolitics animation", "geography facts", "geo shorts"
]

# Fetch Data Button
if st.button("Fetch Data"):
    try:
        start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
        all_results = []
        word_counter = Counter()

        for keyword in keywords:
            st.write(f"🔍 Searching for keyword: {keyword}")
            search_params = {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "order": "viewCount",
                "publishedAfter": start_date,
                "maxResults": 5,
                "key": API_KEY,
            }

            response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
            data = response.json()
            if "items" not in data or not data["items"]:
                continue

            videos = data["items"]
            video_ids = [v["id"]["videoId"] for v in videos if "id" in v and "videoId" in v["id"]]
            channel_ids = [v["snippet"]["channelId"] for v in videos if "snippet" in v and "channelId" in v["snippet"]]

            if not video_ids or not channel_ids:
                continue

            stats_params = {"part": "statistics,contentDetails", "id": ",".join(video_ids), "key": API_KEY}
            stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
            stats_data = stats_response.json()

            channel_params = {"part": "statistics", "id": ",".join(channel_ids), "key": API_KEY}
            channel_response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
            channel_data = channel_response.json()

            if "items" not in stats_data or "items" not in channel_data:
                continue

            for video, stat, channel in zip(videos, stats_data["items"], channel_data["items"]):
                title = video["snippet"].get("title", "N/A")
                description = video["snippet"].get("description", "")[:200]
                video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
                views = int(stat["statistics"].get("viewCount", 0))
                subs = int(channel["statistics"].get("subscriberCount", 0))
                channel_url = f"https://www.youtube.com/channel/{channel['id']}"
                duration = stat["contentDetails"].get("duration", "N/A")

                if selected_topics and not any(t in (title + description).lower() for t in selected_topics):
                    continue

                all_results.append({
                    "Title": title,
                    "Description": description,
                    "URL": video_url,
                    "Views": views,
                    "Subscribers": subs,
                    "Duration": duration,
                    "Channel URL": channel_url
                })

                word_counter.update(title.lower().split())

        if all_results:
            st.success(f"✅ Found {len(all_results)} results.")
            df = pd.DataFrame(all_results).sort_values(by="Views", ascending=False)

            for _, result in df.iterrows():
                st.markdown(
                    f"**Title:** {result['Title']}  \n"
                    f"**Description:** {result['Description']}  \n"
                    f"**Video URL:** [Watch Video]({result['URL']})  \n"
                    f"**Views:** {result['Views']}  \n"
                    f"**Subscribers:** {result['Subscribers']}  \n"
                    f"**Duration:** {result['Duration']}  \n"
                    f"**Channel:** [Visit Channel]({result['Channel URL']})"
                )
                st.write("---")

            st.download_button("📥 Download CSV", df.to_csv(index=False), "youtube_data.csv")

            st.subheader("📈 Views Distribution")
            fig = px.bar(df.head(10), x="Title", y="Views", title="Top 10 Videos by Views", labels={"Views": "View Count"})
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("🔑 Top Trending Words in Titles")
            for word, count in word_counter.most_common(10):
                st.write(f"{word}: {count} times")

            st.subheader("💡 Suggested Video Ideas")
            st.markdown("- Before and After Map of USA in 1900 vs Today")
            st.markdown("- Why [Country] Changed Borders in [Year] — Explained with Map")
            st.markdown("- Top 5 Most Changed Country Borders in History")
            st.markdown("- WW2 Borders Explained in 20 Seconds")

        else:
            st.warning("No matching videos found.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
