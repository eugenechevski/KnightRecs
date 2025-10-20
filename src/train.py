"""
KnightRecs Model Training Script

Train a collaborative filtering SVD model on MovieLens ratings.
Uses scipy for SVD matrix factorization (pure Python, no C dependencies).
Split 80/20, evaluate RMSE, save with pickle.
"""

import pandas as pd
import numpy as np
import pickle
from scipy.sparse.linalg import svds
from scipy.sparse import csr_matrix
from sklearn.metrics import mean_squared_error, mean_absolute_error
import os


def load_data():
    """Load MovieLens ratings data."""
    print("Loading MovieLens dataset...")
    ratings_path = os.path.join("ml-latest", "ratings.csv")
    
    # Load ratings data
    ratings_df = pd.read_csv(ratings_path)
    
    print(f"Loaded {len(ratings_df):,} ratings")
    print(f"Number of users: {ratings_df['userId'].nunique():,}")
    print(f"Number of movies: {ratings_df['movieId'].nunique():,}")
    
    return ratings_df


def sample_data(ratings_df, sample_size=1_000_000):
    """
    Sample data for faster training during development.
    For production, remove this or use full dataset.
    """
    if len(ratings_df) > sample_size:
        print(f"\nSampling {sample_size:,} ratings for faster training...")
        # Sample users first to maintain user history
        unique_users = ratings_df['userId'].unique()
        sampled_users = pd.Series(unique_users).sample(n=int(sample_size / 100), random_state=42)
        ratings_df = ratings_df[ratings_df['userId'].isin(sampled_users)]
        
        # If still too large, sample randomly
        if len(ratings_df) > sample_size:
            ratings_df = ratings_df.sample(n=sample_size, random_state=42)
        
        print(f"Sampled to {len(ratings_df):,} ratings")
        print(f"Sampled users: {ratings_df['userId'].nunique():,}")
        print(f"Sampled movies: {ratings_df['movieId'].nunique():,}")
    
    return ratings_df


def train_model(ratings_df):
    """
    Train a collaborative filtering SVD model using scipy.
    Matrix factorization approach: decompose user-item matrix into latent factors.
    """
    print("\nPreparing user-item rating matrix...")
    
    # Create user and movie ID mappings
    user_ids = ratings_df['userId'].unique()
    movie_ids = ratings_df['movieId'].unique()
    
    user_to_idx = {uid: idx for idx, uid in enumerate(user_ids)}
    movie_to_idx = {mid: idx for idx, mid in enumerate(movie_ids)}
    idx_to_user = {idx: uid for uid, idx in user_to_idx.items()}
    idx_to_movie = {idx: mid for mid, idx in movie_to_idx.items()}
    
    print(f"Matrix dimensions: {len(user_ids)} users × {len(movie_ids)} movies")
    
    # Split data for training and validation (80/20)
    print("Splitting data (80% train, 20% test)...")
    train_df = ratings_df.sample(frac=0.8, random_state=42)
    test_df = ratings_df.drop(train_df.index)
    
    print(f"Train set: {len(train_df):,} ratings")
    print(f"Test set: {len(test_df):,} ratings")
    
    # Create sparse rating matrix for training
    train_rows = train_df['userId'].map(user_to_idx).values
    train_cols = train_df['movieId'].map(movie_to_idx).values
    train_data = train_df['rating'].values
    
    rating_matrix = csr_matrix((train_data, (train_rows, train_cols)), 
                                shape=(len(user_ids), len(movie_ids)))
    
    # Apply SVD matrix factorization
    print("\nTraining SVD model (50 latent factors)...")
    print("This may take a few minutes...")
    
    # Perform SVD (k=50 latent factors)
    k = 50
    U, sigma, Vt = svds(rating_matrix, k=k)
    
    # Convert sigma to diagonal matrix
    sigma = np.diag(sigma)
    
    # Predictions are U * Sigma * Vt
    print("SVD decomposition complete!")
    
    # Evaluate on test set
    print("\nEvaluating model on test set...")
    test_rows = test_df['userId'].map(user_to_idx).values
    test_cols = test_df['movieId'].map(movie_to_idx).values
    actual_ratings = test_df['rating'].values
    
    # Predict ratings for test set
    predicted_ratings = []
    for user_idx, movie_idx in zip(test_rows, test_cols):
        pred = np.dot(np.dot(U[user_idx, :], sigma), Vt[:, movie_idx])
        # Clip predictions to valid rating range (0.5 to 5.0)
        pred = np.clip(pred, 0.5, 5.0)
        predicted_ratings.append(pred)
    
    predicted_ratings = np.array(predicted_ratings)
    
    # Calculate metrics
    rmse = np.sqrt(mean_squared_error(actual_ratings, predicted_ratings))
    mae = mean_absolute_error(actual_ratings, predicted_ratings)
    
    print(f"\nModel Performance:")
    print(f"  RMSE: {rmse:.4f}")
    print(f"  MAE:  {mae:.4f}")
    
    # Package model components
    model = {
        'U': U,
        'sigma': sigma,
        'Vt': Vt,
        'user_to_idx': user_to_idx,
        'movie_to_idx': movie_to_idx,
        'idx_to_user': idx_to_user,
        'idx_to_movie': idx_to_movie,
        'user_ids': user_ids,
        'movie_ids': movie_ids
    }
    
    return model, train_df


def save_model(model, train_df):
    """Save the trained model to disk."""
    print("\nSaving trained model...")
    
    # Save model
    with open("model.pkl", "wb") as f:
        pickle.dump(model, f)
    
    # Save user-rated items mapping (for filtering)
    user_rated_items = train_df.groupby('userId')['movieId'].apply(set).to_dict()
    with open("user_rated_items.pkl", "wb") as f:
        pickle.dump(user_rated_items, f)
    
    print("Model saved to model.pkl")
    print("User-rated items saved to user_rated_items.pkl")


def main():
    """Main training pipeline."""
    print("=" * 60)
    print("KnightRecs - Movie Recommendation Model Training")
    print("=" * 60)
    
    # Load data
    ratings_df = load_data()
    
    # Sample data for faster training (optional)
    # Comment out the next line to use full dataset
    ratings_df = sample_data(ratings_df, sample_size=1_000_000)
    
    # Train model
    model, train_df = train_model(ratings_df)
    
    # Save model
    save_model(model, train_df)
    
    print("\n" + "=" * 60)
    print("Training complete! Model ready for deployment.")
    print("=" * 60)


if __name__ == "__main__":
    main()
