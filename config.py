import os

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'Covid19-dataset')
TRAIN_DIR = os.path.join(DATA_DIR, 'train')
TEST_DIR = os.path.join(DATA_DIR, 'test')

# Output paths
WEIGHTS_DIR = os.path.join(BASE_DIR, 'weights')
os.makedirs(WEIGHTS_DIR, exist_ok=True)
BEST_WEIGHTS_PATH = os.path.join(WEIGHTS_DIR, 'best_weights.weights.h5')
FINAL_MODEL_H5 = os.path.join(BASE_DIR, 'model.h5')
SAVED_MODEL_DIR = os.path.join(BASE_DIR, 'saved_model')

# Model parameters
TARGET_SIZE = (224, 224)
BATCH_SIZE = 32
VALIDATION_SPLIT = 0.2
LEARNING_RATE = 0.001
EPOCHS = 20

# Class labels
CLASSES = ['Covid', 'Normal', 'Viral Pneumonia']
