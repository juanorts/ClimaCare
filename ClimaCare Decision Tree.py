#!/usr/bin/env python
# coding: utf-8

# ## Imports

# In[1]:


import pandas as pd
import pandas as pd
from sklearn.tree import DecisionTreeClassifier # Import Decision Tree Classifier
from sklearn.model_selection import train_test_split # Import train_test_split function
from sklearn import metrics #Import scikit-learn metrics module for accuracy calculation
from sklearn.preprocessing import LabelEncoder


# In[2]:


df = pd.read_csv("BilbaoWeatherDataset.csv", sep = ";")


# In[3]:


df.head()


# ### Quitar guiones adicionales de los labels

# In[4]:


df['DAY-PROFILE 1'] = df['DAY-PROFILE 1'].apply(lambda x: x[:-3] if x.endswith(" - ") else x)
df['DAY-PROFILE 2'] = df['DAY-PROFILE 2'].apply(lambda x: x[:-3] if x.endswith(" - ") else x)


# In[5]:


df.head()


# In[23]:


df['DAY-PROFILE 2'].value_counts()


# In[7]:


df['DAY-PROFILE 2'].unique()


# ### Extraer mes de la fecha

# In[8]:


# Convert the 'date' column to a datetime type
df['DATE'] = pd.to_datetime(df['DATE'])

# Extract the month and create a new column 'month'
df['MONTH'] = df['DATE'].dt.month


# In[9]:


df.head()


# ## Preparación de los datos para training y test

# ### Datos de entrenamiento

# In[10]:


X1_train = df[['TEMPERATURE', 'HUMIDITY', 'WINDSPEED', 'MONTH']] # Features
y1_train = df['DAY-PROFILE 1'] # Target variable


# In[11]:


X2_train = df[['PRESSURE', 'UV INDEX', 'AIR QUALITY', 'MONTH']] # Features
y2_train = df['DAY-PROFILE 2'] # Target variable


# In[12]:


# Split the first dataset (X1, y1)
#X1_train, X1_test, y1_train, y1_test = train_test_split(X1, y1, test_size=0.2, random_state=1)

# Split the second dataset (X2, y2) using the same indices as the first split
#X2_train, X2_test, y2_train, y2_test = train_test_split(X2, y2, test_size=0.2, random_state=1) 
# Note: Using 'stratify=y1' ensures that the same stratification is applied as in the first split


# ### Dato a evaluar

# In[13]:


X1_test = pd.DataFrame(data=[[32, 70, 7, 8]], columns=['TEMPERATURE', 'HUMIDITY', 'WINDSPEED', 'MONTH'])

X2_test = pd.DataFrame([[1000, 4, 54, 8]], columns=['PRESSURE', 'UV INDEX', 'AIR QUALITY', 'MONTH'])


# In[14]:


X1_test


# In[15]:


X2_test


# ## Clasificación usando Decision Trees

# In[16]:


# Create Decision Tree classifer object
clf = DecisionTreeClassifier()


# ### Decision Tree para el primer perfil de día

# In[17]:


# Train Decision Tree Classifer
clf1 = clf.fit(X1_train, y1_train)

#Predict the response for test dataset
y1_pred = clf1.predict(X1_test)


# In[18]:


# Model Accuracy, how often is the classifier correct?
#print("Accuracy:", metrics.accuracy_score(y1_test, y1_pred))


# ### Decision Tree para el segundo perfil de día

# In[19]:


# Train Decision Tree Classifer
clf2 = clf.fit(X2_train, y2_train)

#Predict the response for test dataset
y2_pred = clf2.predict(X2_test)


# In[20]:


# Model Accuracy, how often is the classifier correct?
#print("Accuracy:", metrics.accuracy_score(y2_test, y2_pred))


# ### Mostrar los resultados de predicción

# In[21]:


result_df1 = pd.DataFrame({'Predicted 1': y1_pred})
result_df2 = pd.DataFrame({'Predicted 2': y2_pred})
result_df = pd.concat([result_df1, result_df2], axis=1)
test_df1 = pd.DataFrame(X1_test, columns=['TEMPERATURE', 'HUMIDITY', 'WINDSPEED', 'MONTH'])
test_df2 = pd.DataFrame(X2_test, columns=['PRESSURE', 'UV INDEX', 'AIR QUALITY', 'MONTH'])
test_df = pd.concat([test_df1, test_df2], axis=1)
result_df = pd.concat([test_df, result_df], axis=1)


# In[22]:


result_df.head(60)

