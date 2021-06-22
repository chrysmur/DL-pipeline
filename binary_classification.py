import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer

#Preprocessing
hotel = pd.read_csv('../input/dl-course-data/hotel.csv')

X = hotel.copy()
y = X.pop('is_canceled')


#Map the months to values
X['arrival_date_month'] = \
    X['arrival_date_month'].map(
        {'January':1, 'February': 2, 'March':3,
         'April':4, 'May':5, 'June':6, 'July':7,
         'August':8, 'September':9, 'October':10,
         'November':11, 'December':12}
    )

features_num = [
    "lead_time", "arrival_date_week_number",
    "arrival_date_day_of_month", "stays_in_weekend_nights",
    "stays_in_week_nights", "adults", "children", "babies",
    "is_repeated_guest", "previous_cancellations",
    "previous_bookings_not_canceled", "required_car_parking_spaces",
    "total_of_special_requests", "adr",
]
features_cat = [
    "hotel", "arrival_date_month", "meal",
    "market_segment", "distribution_channel",
    "reserved_room_type", "deposit_type", "customer_type",
]

#Use make_pipeline to create to mini pipeline for 
transformer_num = make_pipeline(
    SimpleImputer(strategy="constant"), # there are a few missing values
    StandardScaler(),
)
transformer_cat = make_pipeline(
    SimpleImputer(strategy="constant", fill_value="NA"),
    OneHotEncoder(handle_unknown='ignore'),
)

#Use the make column transfromer to combine the preprocessing pipelies
preprocessor = make_column_transformer(
    (transformer_num, features_num),
    (transformer_cat, features_cat),
)

# stratify - make sure classes are evenlly represented across splits
X_train, X_valid, y_train, y_valid = \
    train_test_split(X, y, stratify=y, train_size=0.75)

# Apply the pipeline to both the training and validation x data set
X_train = preprocessor.fit_transform(X_train)
X_valid = preprocessor.transform(X_valid)

input_shape = [X_train.shape[1]]


### CREATE MODEL
from tensorflow import keras
from tensorflow.keras import layers

#Create a model with Dropout for regularization
#Add Batchnormalization for standardazing the inputs
model = keras.Sequential([
    layers.BatchNormalization(),
    layers.Dense(256, activation='relu', input_shape=input_shape),
    layers.BatchNormalization(),
    layers.Dropout(0.3),
    layers.Dense(256, activation='relu'),
    layers.BatchNormalization(),
    layers.Dropout(0.3),
    layers.Dense(1, activation='sigmoid')
])


### COMPILE MODEL
# binary crossentroopy for binary classification
model.compile(
    optimizer = 'adam',
    loss ='binary_crossentropy',
    metrics = ['binary_accuracy']
)

### CREATE CALLBACK TO STOP TRAINING WHEN IT STARTS TO OVERFIT

callb  = keras.callbacks.EarlyStoppping(
    patience = 10,
    min_delta = 0.001,
    restore_best_weights = True
)

### FIT MODEL
## keras stores the history of the weights per epoch
## Batch_size the sample size from the data that will be used to train it.
## Epochs rounds of training
history = model.fit(
    X_train, y_train,
    validation_data =(X_valid, y_valid),
    batch_size = 512,
    epochs = 200,
    callbacks = [callb]
)

##PLOT Training curves

history_df = pd.DataFrame(history.history)
history_df.loc[:, ['loss', 'val_loss']].plot(title="Cross-entropy") # plot the loss
history_df.loc[:, ['binary_accuracy', 'val_binary_accuracy']].plot(title="Accuracy") # plot accuracy