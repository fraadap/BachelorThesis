# GeneroCity Smart Parking - Machine Learning Model

## Project Overview

This project is part of the Bachelor Degree Thesis conducted during an internship at the GamificationLab, a research laboratory within the Department of Computer Science at La Sapienza University of Rome. The main focus of the project was to contribute to the development of the GeneroCity smart parking application by building a preliminary Machine Learning model based on sensor data.

GeneroCity is a parking application that uses virtual sensors to determine whether the user is inside their vehicle or not. These virtual sensors are not traditional hardware devices, but software models that analyze data from various hardware sources to intelligently infer the user’s state. The application monitors sensor data in real-time to decide if the user is driving or walking.

## Key Contributions

Since the real sensors for GeneroCity were still in development and not fully operational, a Machine Learning model based on real data was not feasible. Instead, the following steps were taken:
- **Synthetic Data Generation**: A dataset was generated based on interviews administered to a group of car users. The questionnaires collected data on user habits, such as vehicle usage, commuting frequency, employment, and the devices they used.
- **Machine Learning Model**: Using this synthetic data, various Artificial Intelligence models were tested to classify the user's status based on simulated sensor readings.

## Future Outlook

Once the real sensors are fully operational, this work will enable the evaluation and refinement of Machine Learning models to accurately interpret sensor data and improve the decision-making capabilities of the GeneroCity application.

## Technologies Used
- Python
- Machine Learning libraries (Pythorch and scikit-learn)
- Data collection via user questionnaires
- Synthetic data generation
