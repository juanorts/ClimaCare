'''

This code provides the machine learning algorithms to make day profile predictions based
on the weather condition parameters provided at a specific datetime for the ClimaCare
project. It uses Decision TreeClassifier from the Scikit-Learn library to classify the
weather conditions and relate them to a type of weather (day profile).

'''

# Imports

import pandas as pd
import pandas as pd
from sklearn.tree import DecisionTreeClassifier # Import Decision Tree Classifier
from sklearn.model_selection import train_test_split # Import train_test_split function
from sklearn import metrics #Import scikit-learn metrics module for accuracy calculation
from sklearn.preprocessing import LabelEncoder


# Read the training dataset

df = pd.read_csv("data/BilbaoWeatherDataset.csv", sep = ";")

# Data processing

# Remove ending hypens in the labels
df['DAY-PROFILE 1'] = df['DAY-PROFILE 1'].apply(lambda x: x[:-3] if x.endswith(" - ") else x)
df['DAY-PROFILE 2'] = df['DAY-PROFILE 2'].apply(lambda x: x[:-3] if x.endswith(" - ") else x)

# Convert the 'date' column to a datetime type
df['DATE'] = pd.to_datetime(df['DATE'], format = '%d/%m/%Y')

# Extract the month and create a new column 'month' to be used as a feature variable
df['MONTH'] = df['DATE'].dt.month

# Training sets

X1_train = df[['TEMPERATURE', 'HUMIDITY', 'WINDSPEED', 'MONTH']] # Features
y1_train = df['DAY-PROFILE 1'] # Target variable

X2_train = df[['PRESSURE', 'UV INDEX', 'AIR QUALITY', 'MONTH']] # Features
y2_train = df['DAY-PROFILE 2'] # Target variable

# Create dataframes for the collected weather conditions

X1_test = pd.DataFrame(data=[[32, 70, 7, 8]], columns=['TEMPERATURE', 'HUMIDITY', 'WINDSPEED', 'MONTH'])

X2_test = pd.DataFrame([[1000, 4, 54, 8]], columns=['PRESSURE', 'UV INDEX', 'AIR QUALITY', 'MONTH'])

# Decision Tree Classification

# Create Decision Tree classifer object
clf = DecisionTreeClassifier()

# First day profile: temp, humidity, wind speed and month

# Train Decision Tree Classifer
clf1 = clf.fit(X1_train, y1_train)

#Predict the response for test dataset
y1_pred = clf1.predict(X1_test)

# Second day profile: atmospheric pressure, uv index, air quality index, month

# Train Decision Tree Classifer
clf2 = clf.fit(X2_train, y2_train)

# Predict the response for test dataset
y2_pred = clf2.predict(X2_test)

# Classification results

result_df1 = pd.DataFrame({'Predicted 1': y1_pred})
result_df2 = pd.DataFrame({'Predicted 2': y2_pred})
result_df = pd.concat([result_df1, result_df2], axis=1)
test_df1 = pd.DataFrame(X1_test, columns=['TEMPERATURE', 'HUMIDITY', 'WINDSPEED', 'MONTH'])
test_df2 = pd.DataFrame(X2_test, columns=['PRESSURE', 'UV INDEX', 'AIR QUALITY', 'MONTH'])
test_df = pd.concat([test_df1, test_df2], axis=1)
result_df = pd.concat([test_df, result_df], axis=1)

pd.set_option('display.max_columns', None)
print(result_df['TEMPERATURE'].values[0])