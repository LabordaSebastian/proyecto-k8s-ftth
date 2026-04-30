from flask import Flask, jsonify
import redis
import os

app = Flask(__name__)

# Nos conectamos a Redis usando el nombre del Service de Kubernetes
redis_host = os.getenv("REDIS_HOST", "ftth-redis-service")
cache = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)

@app.route('/status')
def status():
    try:
        # Simulamos guardar un estado de un nodo FTTH
        cache.ping()
        return jsonify({"status": "OK", "message": "Backend conectado a Redis exitosamente", "ftth_network": "Online"})
    except redis.ConnectionError:
        return jsonify({"status": "ERROR", "message": "No se pudo conectar a Redis", "ftth_network": "Offline"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
