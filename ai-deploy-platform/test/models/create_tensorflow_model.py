"""
Test script for creating and testing a TensorFlow model for the AI model deployment platform.
"""

import os
import tensorflow as tf
from tensorflow.keras import layers, models
import numpy as np

# Define a simple CNN model for MNIST
def create_tf_model():
    model = models.Sequential([
        layers.Conv2D(32, (3, 3), activation='relu', input_shape=(28, 28, 1)),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.Flatten(),
        layers.Dense(64, activation='relu'),
        layers.Dense(10, activation='softmax')
    ])
    
    model.compile(optimizer='adam',
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])
    
    return model

# Create and train a simple model
def create_and_train_model():
    print("Loading MNIST dataset...")
    # Load MNIST dataset
    (train_images, train_labels), (test_images, test_labels) = tf.keras.datasets.mnist.load_data()
    
    # Normalize pixel values to be between 0 and 1
    train_images = train_images.reshape((60000, 28, 28, 1)).astype('float32') / 255
    test_images = test_images.reshape((10000, 28, 28, 1)).astype('float32') / 255
    
    # Take a subset for quick training
    train_images = train_images[:5000]
    train_labels = train_labels[:5000]
    test_images = test_images[:1000]
    test_labels = test_labels[:1000]
    
    # Create model
    model = create_tf_model()
    
    # Train the model
    print("Training model...")
    model.fit(train_images, train_labels, epochs=1, batch_size=64, verbose=1)
    
    # Evaluate the model
    test_loss, test_acc = model.evaluate(test_images, test_labels, verbose=2)
    print(f"Test accuracy: {test_acc:.4f}")
    
    # Save the model in different formats
    
    # Save in Keras H5 format
    model_path = os.path.join('/home/ubuntu/ai-deploy-platform/test/models', 'mnist_cnn.h5')
    model.save(model_path)
    print(f"Keras model saved to {model_path}")
    
    # Save in TensorFlow SavedModel format
    saved_model_path = os.path.join('/home/ubuntu/ai-deploy-platform/test/models', 'mnist_cnn_tf')
    model.save(saved_model_path)
    print(f"TensorFlow SavedModel saved to {saved_model_path}")
    
    # Convert to TensorFlow Lite
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()
    tflite_model_path = os.path.join('/home/ubuntu/ai-deploy-platform/test/models', 'mnist_cnn.tflite')
    with open(tflite_model_path, 'wb') as f:
        f.write(tflite_model)
    print(f"TensorFlow Lite model saved to {tflite_model_path}")
    
    return model_path, saved_model_path, tflite_model_path

if __name__ == "__main__":
    create_and_train_model()
