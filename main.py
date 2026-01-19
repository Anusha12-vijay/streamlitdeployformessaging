import streamlit as st
import re
import preprocessor
import helper
import matplotlib.pyplot as plt
import seaborn as sns

st.sidebar.title("Messaging Data Analytics & Threat Detection Tool")

uploaded_file =st.sidebar.file_uploader("Choose the chat file")
if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    data = bytes_data.decode("utf-8")
    # st.text(data)
    df=preprocessor.preprocess(data)


    #fetch unique users
    user_list =df['user'].unique().tolist()
    user_list.remove('group_notification')
    user_list.sort()
    user_list.insert(0,"Overall Group")

    selected_user=st.sidebar.selectbox("Show analysis for ",user_list)
    st.title("General Analysis")

    if st.sidebar.button("Show Analysis"):

        #numerical Analysis
        num_messages,words,num_media_messages,num_links =helper.fetch_stats(selected_user,df)
        col1 ,col2,col3,col4 = st.columns(4)


        # with col1:
        #     st.header("Total Messages")
        #     st.title(num_messages)
        # with col2:
        #     st.header("Total Words")
        #     st.title(words)
        # with col3:
        #     st.header("Media shared")
        #     st.title(num_media_messages)
        # with col4:
        #     st.header("Links shared")
        #     st.title(num_links)
        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Messages", num_messages)
        col2.metric("Total Words", words)
        col3.metric("Media Shared", num_media_messages)
        col4.metric("Links Shared", num_links)

        #monthly timeline
        st.title("Monthly Timeline")
        timeline=helper.monthly_timeline(selected_user,df)
        fig,ax = plt.subplots()
        ax.plot(timeline['time'],timeline['message'],color='green')
        plt.xticks(rotation='vertical')
        st.pyplot(fig)

        #Daily timeline
        st.title("Daily Timeline")
        daily_timeline = helper.daily_timeline(selected_user, df)
        fig, ax = plt.subplots()
        ax.plot(daily_timeline['date_'], daily_timeline['message'], color='green')
        plt.xticks(rotation='vertical')
        st.pyplot(fig)

        #activity map
        st.title('Activity Map')
        col1,col2 = st.columns(2)

        with col1:
            st.header("Most Busy Day")
            busy_day=helper.week_activity_map(selected_user,df)
            fig,ax=plt.subplots()
            ax.bar(busy_day.index,busy_day.values)
            plt.xticks(rotation='vertical')
            st.pyplot(fig)

        with col2:
            st.header("Most Busy Month")
            busy_month = helper.month_activity_map(selected_user, df)
            fig, ax = plt.subplots()
            ax.bar(busy_month.index, busy_month.values,color='purple')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)

        st.title("Weekly Activity Map")
        user_heatmap=helper.activity_heatmap(selected_user,df)
        fig, ax = plt.subplots(figsize=(14, 6))
        sns.heatmap(
            user_heatmap,
            cmap='rocket',
            linewidths=0.5,
            annot=False
        )
        ax.set_title('Weekly Activity Heatmap', fontsize=16)
        ax.set_xlabel('Time Period')
        ax.set_ylabel('Day')
        st.pyplot(fig)

        #finding the busiest users in the group(Group Level)

        if selected_user=='Overall Group':
            st.title('Most Busy Users')
            x,new_df=helper.most_busy_users(df)
            fig,ax=plt.subplots()

            col1,col2 = st.columns(2)

            with col1:
                ax.bar(x.index, x.values,color='red')
                plt.xticks(rotation='vertical')
                st.pyplot(fig)
            with col2:
                st.dataframe(new_df)

            #wordcloud
            df_wc=helper.create_wordcloud(selected_user,df)
            fig,ax=plt.subplots()
            ax.imshow(df_wc)
            st.pyplot(fig)

            #most common words
            most_common_words=helper.most_common_words(selected_user,df)

            st.title('Most Common Words')

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.barh(
                most_common_words['Word'],
                most_common_words['Frequency']
            )
            ax.invert_yaxis()

            plt.xticks(rotation=45)
            ax.set_xlabel('Words')
            ax.set_ylabel('Frequency')
            st.pyplot(fig)

            st.dataframe(most_common_words)

            #emoji analysis
            emoji_df =helper.emoji_helper(selected_user,df)
            st.dataframe(emoji_df)

            # ================================
            # 🔐 URL Phishing Detection
            # ================================

            st.title("🔐 URL Phishing Detection")

            filtered_df = df if selected_user == "Overall Group" else df[df['user'] == selected_user]
            url_predictions = helper.predict_urls_phishing(filtered_df)

            if url_predictions is None:
                st.success("No URLs found in chat 🎉")
            else:
                col1, col2 = st.columns(2)

                with col1:
                    phishing_count = (url_predictions['Result'] == 'Phishing').sum()
                    st.metric("Phishing URLs 🚨", phishing_count)

                with col2:
                    safe_count = (url_predictions['Result'] == 'Safe').sum()
                    st.metric("Safe URLs ✅", safe_count)

                phishing_df = url_predictions[url_predictions['Result'] == 'Phishing']

                if phishing_df.shape[0] > 0:
                    st.subheader("⚠️ Detected Phishing URLs")
                    st.dataframe(
                        phishing_df[['url', 'Result_Display', 'Confidence']]                        ,
                        use_container_width=True
                    )
                else:
                    st.success("No phishing URLs detected 🎉")

                with st.expander("Show all scanned URLs"):
                    st.dataframe(
                        url_predictions[['url', 'Result_Display', 'Confidence']],
                        use_container_width=True
                    )


# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
