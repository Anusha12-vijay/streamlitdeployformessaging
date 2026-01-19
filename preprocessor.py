import re
import pandas as pd

def preprocess(data):
    pattern = r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s-\s'
    messages = re.split(pattern, data)[1:]
    date = re.findall(pattern, data)
    df = pd.DataFrame({'user_message': messages, 'message_date': date})
    # convert the date format
    df['message_date'] = pd.to_datetime(df['message_date'], format='%d/%m/%Y, %H:%M - ')
    df.rename(columns={'message_date': 'date'}, inplace=True)
    users = []
    messages = []

    # Check if column exists before running to avoid KeyError
    if 'user_message' in df.columns:
        for message in df['user_message']:
            # Use r'' for raw string to fix SyntaxWarning
            entry = re.split(r'([\w\W]+?):\s', message)

            if entry[1:]:  # Check if split was successful
                users.append(entry[1])
                messages.append(entry[2])
            else:
                users.append('group_notification')
                messages.append(entry[0])

        df['user'] = users
        df['message'] = messages
        # Drop only if it exists
        df.drop(columns=['user_message'], inplace=True)

        df['date_'] =df['date'].dt.date
        df['year'] = df['date'].dt.year
        df['month_num']=df['date'].dt.month
        df['month'] = df['date'].dt.month_name()
        df['day'] = df['date'].dt.day
        df['hour'] = df['date'].dt.hour
        df['minute'] = df['date'].dt.minute
        df['day_name'] = df['date'].dt.day_name()



        period=[]
        for hour in df[['day_name','hour']]['hour']:
            if hour == 23:
                period.append(str(hour)+"-"+str('00'))
            elif hour==0:
                period.append(str('00')+"-"+str(hour + 1 ))
            else:
                period.append(str(hour) + "-"+str(hour +1))

        df['period'] = period




        return df





