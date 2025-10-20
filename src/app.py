"""
KnightRecs Flask API Service

Serves movie recommendations via REST API.
Endpoint: GET /recommend?user_id=<int>&n=<int>
"""

from flask import Flask, request, jsonify
import pickle
import pandas as pd
import os
from typing import List, Dict

app = Flask(__name__)

# Global variables for model and data
model = None
trainset = None
movies_df = None
user_rated_items = None


def load_model_and_data():
    """Load the trained model and movie data at startup."""
    global model, trainset, movies_df, user_rated_items
    
    print("Loading model and data...")
    
    # Load trained SVD model
    if not os.path.exists("model.pkl"):
        raise FileNotFoundError(
            "model.pkl not found. Please run 'python src/train.py' first to train the model."
        )
    
    with open("model.pkl", "rb") as f:
        model = pickle.load(f)
    print("✓ Model loaded")
    
    # Load user-rated items mapping (for filtering)
    with open("user_rated_items.pkl", "rb") as f:
        user_rated_items = pickle.load(f)
    print(f"✓ Loaded {len(user_rated_items):,} users' rating history")
    
    # Load movies data
    movies_path = os.path.join("ml-latest", "movies.csv")
    movies_df = pd.read_csv(movies_path)
    print(f"✓ Loaded {len(movies_df):,} movies")
    
    print("Ready to serve recommendations!\n")


def get_recommendations(user_id: int, n: int = 5) -> List[Dict]:
    """
    Generate top-N movie recommendations for a user.
    Exclude movies the user has already rated.
    Return list of dicts with movieId, title, predicted_rating.
    """
    import numpy as np
    
    # Check if user exists in training data
    if user_id not in user_rated_items:
        return None
    
    # Check if user is in model's user mapping
    if user_id not in model['user_to_idx']:
        return None
    
    # Get movies the user has already rated
    seen_movies = user_rated_items[user_id]
    
    # Get user index in model
    user_idx = model['user_to_idx'][user_id]
    
    # Get all movie IDs from the model
    all_movie_ids = model['movie_ids']
    
    # Predict ratings for unseen movies
    predictions = []
    for movie_id in all_movie_ids:
        if movie_id not in seen_movies and movie_id in model['movie_to_idx']:
            # Get movie index
            movie_idx = model['movie_to_idx'][movie_id]
            
            # Predict rating: U[user] * Sigma * Vt[:, movie]
            pred = np.dot(np.dot(model['U'][user_idx, :], model['sigma']), 
                          model['Vt'][:, movie_idx])
            
            # Clip to valid rating range
            pred = np.clip(pred, 0.5, 5.0)
            predictions.append((movie_id, pred))
    
    # Sort by predicted rating (descending) and take top N
    predictions.sort(key=lambda x: x[1], reverse=True)
    top_predictions = predictions[:n]
    
    # Format results with movie titles
    recommendations = []
    for movie_id, predicted_rating in top_predictions:
        movie_info = movies_df[movies_df['movieId'] == movie_id]
        if not movie_info.empty:
            title = movie_info.iloc[0]['title']
            genres = movie_info.iloc[0]['genres']
            recommendations.append({
                'movieId': int(movie_id),
                'title': title,
                'genres': genres,
                'predicted_rating': round(float(predicted_rating), 2)
            })
    
    return recommendations


@app.route('/')
def home():
    """Health check endpoint."""
    return jsonify({
        'service': 'KnightRecs',
        'status': 'running',
        'version': '1.0.0',
        'endpoints': {
            '/': 'Health check',
            '/recommend': 'Get movie recommendations (params: user_id, n)'
        }
    })


@app.route('/recommend')
def recommend():
    """
    Return top N movie recommendations for a given user.
    
    Query parameters:
    - user_id (required): User ID (integer)
    - n (optional): Number of recommendations (default: 5)
    
    Example: /recommend?user_id=1&n=10
    """
    # Get query parameters
    user_id_str = request.args.get('user_id')
    n_str = request.args.get('n', '5')
    
    # Validate user_id
    if not user_id_str:
        return jsonify({
            'error': 'Missing required parameter: user_id',
            'example': '/recommend?user_id=1&n=5'
        }), 400
    
    try:
        user_id = int(user_id_str)
        n = int(n_str)
    except ValueError:
        return jsonify({
            'error': 'Invalid parameter type. user_id and n must be integers.',
            'example': '/recommend?user_id=1&n=5'
        }), 400
    
    # Validate n
    if n < 1 or n > 100:
        return jsonify({
            'error': 'Parameter n must be between 1 and 100',
        }), 400
    
    # Get recommendations
    recommendations = get_recommendations(user_id, n)
    
    if recommendations is None:
        return jsonify({
            'error': f'User {user_id} not found in training data',
            'suggestion': 'Try a different user_id'
        }), 404
    
    # Return recommendations
    return jsonify({
        'user_id': user_id,
        'recommendations': recommendations,
        'count': len(recommendations)
    })


if __name__ == '__main__':
    # Load model and data before starting the server
    load_model_and_data()
    
    # Run Flask app
    # CRITICAL: Use host="0.0.0.0" to make it accessible in Docker container
    print("Starting Flask server on http://0.0.0.0:5000")
    print("Press CTRL+C to stop\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
