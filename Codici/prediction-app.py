import numpy as np
from joblib import load
from flask import Flask, request, jsonify

app = Flask(__name__)

model = load('/home/volume/svc_model.model') # Percorso all'interno del pod che monterà il volume

@app.route('/classify', methods=['POST'])
def classify():
    data = request.json
    if not data or 'features' not in data:
        return jsonify({'error':'Invalid input'}), 400
    
    # Prelievo delle features e predizione
    class_names = {
        0: 'Setosa',
        1: 'Versicolor',
        2: 'Virginica'
    }
    features = data['features']
    prediction = model.predict([features])
    species_name = class_names.get(prediction[0],'Unknown')
    return jsonify({'prediction': species_name})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)