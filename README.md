# 📸 AIoT Photography Condition Classification System

## 📌 Overview
This project presents a real-time AIoT system that classifies photography conditions using sensor data and provides automated editing guidance.

## 🎯 Objective
To improve photo quality by detecting environmental conditions (lighting and motion) without analyzing image pixels.

## ⚙️ System Pipeline
Sensor Data → Feature Processing → Neural Network → Condition Prediction → Editing Recommendation

## 📊 Data Collection
- Collected using Arduino Nano 33 BLE Sense Rev2
- Features:
  - Ambient light intensity
  - Accelerometer data (ax, ay, az)
  - Gyroscope data (gx, gy, gz)

## 🤖 Model
- Lightweight neural network:
  - Input: 7 features
  - Hidden Layers: 32 → 16
  - Output: 4 classes

## 📈 Results
- Achieved **99% classification accuracy**
- Real-time inference with minimal latency
- Efficient deployment on embedded device

## 🔍 Classification Output
- bright_stable
- bright_shaky
- lowlight_stable
- lowlight_shaky

## 🎨 Editing Recommendations
- Auto-suggests editing adjustments:
  - Exposure correction
  - Noise reduction
  - Sharpening
  - Contrast enhancement

## 🚀 Deployment
- Model deployed on Arduino using TinyML
- Runs entirely on-device (no cloud required)

## 🛠️ Tech Stack
- Python (PyTorch)
- Arduino (C/C++)
- TinyML
- Sensors (IMU + Light)

## 📌 Impact
- Real-time photography assistance
- Efficient alternative to image-based AI systems
- Low-resource embedded AI application

---

## 📷 Future Improvements
- Integrate image-based analysis
- Automate editing pipeline
- Mobile app integration
